import importlib
import os
import datetime
import shutil
import time
import traceback
import json
import sys
import signal
import Config
from Animation import step
from RealServer.Common import force_stop_loss
from Server.Binance.Types.Position import POSITION_SIDE
# from RealServer.DCA import DCAServer
from Server.DCA import DCAServer, TRADE_STEP
from Tool import compute_bb_2, compute_rsi, get_data_folder_path, set_terminal_title, quick_compute_bb
from logger import log_action, init_system_log

# Hàm tính toán các điểm Long (L0, L1, L2) và Short (S0, S1, S2)
def calculate_Long_points(lower, upper, ma, current):
    L0 = eval(Config.L0)
    L1 = eval(Config.L1)
    L2 = eval(Config.L2)
    return (L0, L1, L2)

def calculate_Short_points(lower, upper, ma, current):
    S0 = eval(Config.S0)
    S1 = eval(Config.S1)
    S2 = eval(Config.S2)
    return (S0, S1, S2)


class TradingSystem:
    def __init__(self):
        self.dca_server = DCAServer()

        self.visualize_file = os.path.join(get_data_folder_path(), 'visualize.json')
        self.clear_visualize_file()
        signal.signal(signal.SIGINT, self.cleanup_handler)

        # đặt margin
        self.dca_server.binance_server.klines_server.set_leverage(Config.leverage)

        self.dca_server.binance_server.klines_server.pre_check()

        self.rsi_long_count = 0
        self.rsi_short_count = 0

        self.mode = '5min'


    def clear_visualize_file(self):
        with open(self.visualize_file, 'w') as f:
            json.dump({}, f)

    def cleanup_handler(self, signum, frame):
        log_action("Stopping trading system...", datetime.datetime.now())
        self.clear_visualize_file()
        sys.exit(0)

    def run(self):
        # total = self.dca_server.binance_server.get_total()
        # for i in tqdm(range(total)):
        while True:
            time.sleep(0.1)
            try:
                # Tiến hành các bước tick của server
                self.check_mode()
                self.dca_server.tick()
                result = self.main_run()
                self.visualize_run()
                step(result + f" -- MODE: {self.mode}")
            except KeyboardInterrupt:
                self.cleanup_handler(None, None)
            except Exception as e:
                traceback.print_exc()
                self.clear_visualize_file()
                exit(0)

    def main_run(self):
        data = self.dca_server.get_window_klines(max(Config.rsi_period, Config.bb_period) + 1, self.mode)
        if len(data) < Config.bb_period:
            return "Error: Not enough data to compute BB"
        current, upper, lower, distant, ma = quick_compute_bb(data)
        rsi = compute_rsi(data)
        pre_rsi = rsi[-2]
        rsi = rsi[-1]

        data2 = self.dca_server.get_window_klines(Config.distance_min_klines_count + Config.bb_period, self.mode)
        if len(data2) < Config.distance_min_klines_count + Config.bb_period:
            return "Error: Not enough data to compute BB"
        current2, upper2, lower2, distant2, ma2 = compute_bb_2(data2)

        if rsi <= Config.rsi_long:
            self.rsi_long_count += 1
            self.rsi_short_count = 0
            if self.rsi_long_count >= 500:
                self.rsi_long_count = 300
        elif rsi >= Config.rsi_short:
            self.rsi_short_count += 1
            self.rsi_long_count = 0
            if self.rsi_short_count >= 500:
                self.rsi_short_count = 300
        else:
            self.rsi_long_count = 0
            self.rsi_short_count = 0

        if eval(Config.distance) and (distant2.tail(Config.distance_min_klines_count) > Config.distance_min).all():
            # Xử lý lệnh Long
            if self.rsi_long_count >= 300:
                if self.dca_server.get_dac_num() == 0:  # Chưa có lệnh Long nào được khớp
                    log_action(f"OPEN LONG -- RSI: {rsi} < LONG RSI {Config.rsi_long}  DISTANCE: {distant}", self.dca_server.binance_server.get_current_time())
                    L_point = calculate_Long_points(lower, upper, ma, data[-1])
                    self.dca_server.put_long(L_point,  [Config.n1, Config.n2])

            # Xử lý lệnh Short
            if self.rsi_short_count >= 300:
                if self.dca_server.get_dac_num() == 0:  # Chưa có lệnh Short nào được khớp
                    log_action(f"OPEN SHORT -- RSI: {rsi} > SHORT RSI {Config.rsi_short}  DISTANCE: {distant}", self.dca_server.binance_server.get_current_time())
                    S_point = calculate_Short_points(lower, upper, ma, data[-1])
                    self.dca_server.put_short(S_point,  [Config.n1, Config.n2])

        # Sau 5 phut
        if self.dca_server.get_dac_num() <= 0:
            return f"No trade now : RSI {rsi} distance {distant} "

        if self.dca_server.get_trade_step() == TRADE_STEP.NONE:
            if self.dca_server.get_alive_time() is None:
              return f"------"
            elif self.dca_server.get_alive_time() > datetime.timedelta(minutes=Config.limit_timeout):
                log_action(f"CANCEL POSITION TIME OUT ------------------------------", self.dca_server.binance_server.get_current_time())
                if not self.dca_server.cancel_by_timeout():
                    return f"------"
            elif self.dca_server.get_alive_time() > datetime.timedelta(minutes=6) and datetime.datetime.now().minute % 5 == 0:
                if pre_rsi > Config.rsi_long and self.dca_server.position == POSITION_SIDE.LONG:
                    log_action(f"CANCEL LONG BY NOT SATISFY RSI -- RSI: {pre_rsi} > LONG RSI {Config.rsi_long}", self.dca_server.binance_server.get_current_time())
                    self.dca_server.cancel_by_timeout()
                if pre_rsi < Config.rsi_short and self.dca_server.position == POSITION_SIDE.SHORT:
                    log_action(f"CANCEL SHORT BY NOT SATISFY RSI  -- RSI: {pre_rsi} < SHORT RSI {Config.rsi_short}", self.dca_server.binance_server.get_current_time())
                    self.dca_server.cancel_by_timeout()

            else:
                return f"WAITING -- ALIVE TIME: {self.dca_server.get_alive_time()} < LIMIT TIME OUT {Config.limit_timeout}"


        if self.dca_server.get_trade_step() == TRADE_STEP.LIMIT2_FILLED :
            if self.dca_server.get_limit_filled_time() is None:
              return f"------"
            if self.dca_server.current_tp2_ratio < (Config.tp_decrease_step + Config.tp_min) / 100:
                return f"MIN TP2 RATIO BE REACHED -- TP2: {self.dca_server.current_tp2_ratio * 100} - DECREASE {Config.tp_decrease_step} < MIN TP2 RATIO {Config.tp_min }"
            elif self.dca_server.get_limit_filled_time() > datetime.timedelta(minutes=Config.tp_timeout) :
                log_action(f"TP2 IS TIMEOUT START DECREASE TP------------------------------", self.dca_server.binance_server.get_current_time())
                if not self.dca_server.decrease_tp():
                    return f"------"
            else:
                return f"LIMIT2 FILLED -- TP2: {self.dca_server.current_tp2_ratio * 100} -- FILLED TIME: {self.dca_server.get_limit_filled_time()} < LIMIT TIME OUT {Config.tp_timeout}"

        elif self.dca_server.get_trade_step() == TRADE_STEP.LIMIT1_FILLED:
            if self.dca_server.get_limit_filled_time() is None:
                return f"------"
            if self.dca_server.current_tp1_ratio < (Config.tp_decrease_step + Config.tp_min) / 100:
                return f"MIN TP1 RATIO BE REACHED -- TP1: {self.dca_server.current_tp1_ratio * 100} - DECREASE {Config.tp_decrease_step} < MIN TP1 RATIO {Config.tp_min }"
            elif self.dca_server.get_limit_filled_time() > datetime.timedelta(minutes=Config.tp_timeout):
                log_action(f"TP1 IS TIMEOUT START DECREASE TP------------------------------", self.dca_server.binance_server.get_current_time())
                if not self.dca_server.decrease_tp():
                    return f"------"
            else:
                return f"LIMIT1 FILLED -- TP1: {self.dca_server.current_tp1_ratio * 100} -- FILLED TIME: {self.dca_server.get_limit_filled_time()} < LIMIT TIME OUT {Config.tp_timeout}"

        elif self.dca_server.get_trade_step() == TRADE_STEP.TP2_DECREASE:
            if self.dca_server.get_tp_decrease_time() is None:
                return f"------"
            elif self.dca_server.current_tp2_ratio < (Config.tp_decrease_step + Config.tp_min) / 100:
                return f"MIN TP2 RATIO BE REACHED -- TP2: {self.dca_server.current_tp2_ratio * 100} - DECREASE {Config.tp_decrease_step} < MIN TP2 RATIO {Config.tp_min }"
            elif self.dca_server.get_tp_decrease_time() > datetime.timedelta(minutes=Config.tp_decrease_time):
                log_action(f"DECREASE TP TIME OUT ------------------------------", self.dca_server.binance_server.get_current_time())
                if not self.dca_server.decrease_tp():
                    return f"------"
            else:
                return f"TP2 DECREASE -- TP2: {self.dca_server.current_tp2_ratio * 100} -- DECREASE TIME: {self.dca_server.get_tp_decrease_time()} < DECREASE TIME {Config.tp_decrease_time}"
        elif  self.dca_server.get_trade_step() == TRADE_STEP.TP1_DECREASE:
            if self.dca_server.get_tp_decrease_time() is None:
                return f"------"
            elif self.dca_server.current_tp1_ratio < (Config.tp_decrease_step + Config.tp_min) / 100:
                return f"MIN TP1 RATIO BE REACHED -- TP1: {self.dca_server.current_tp1_ratio * 100} - DECREASE {Config.tp_decrease_step} < MIN TP1 RATIO {Config.tp_min }"
            elif self.dca_server.get_tp_decrease_time() > datetime.timedelta(minutes=Config.tp_decrease_time):
                log_action(f"DECREASE TP TIME OUT ------------------------------", self.dca_server.binance_server.get_current_time())
                if not self.dca_server.decrease_tp():
                    return f"------"
            else:
                return f"TP1 DECREASE -- TP1: {self.dca_server.current_tp1_ratio * 100} -- DECREASE TIME: {self.dca_server.get_tp_decrease_time()} < DECREASE TIME {Config.tp_decrease_time}"
        return f"RSI {rsi} distance {distant} "

    def visualize_run(self):
        dcas = self.dca_server.get_dcas()
        trades = self.dca_server.get_trades()
        data_to_save = {
            'trades': trades,
            'dcas': dcas
        }
        with open(self.visualize_file, 'w') as f:
            json.dump(data_to_save, f)

    def check_mode(self):
        data2 = self.dca_server.get_window_klines(Config.distance_check_mode_klines_count + Config.bb_period + 1, '5min')
        data2 = data2[:-1]  # không lấy giá trị nến chưa đóng

        if len(data2) < Config.distance_check_mode_klines_count + Config.bb_period:
            return "Error: Not enough data to compute BB"
        _, _, _, distance_check_mode, _ = compute_bb_2(data2)

        if (distance_check_mode.tail(Config.distance_check_mode_klines_count) < Config.distance_check_mode).all():
            if self.mode != '30min':
                log_action(f"CHANGE TO 30 MINUTE MODE", self.dca_server.binance_server.get_current_time())
                self.mode = '30min'
                self.dca_server.binance_server.klines_server.stop_all()
                shutil.copy(r"Ini\Algorithm_30m.ini" , r"Ini\Algorithm.ini")
                importlib.reload(Config)
                self.dca_server = DCAServer() # Tạo lại DCAServer để áp dụng cấu hình mới
        else:
            if self.mode != '5min':
                log_action(f"CHANGE TO 5 MINUTE MODE", self.dca_server.binance_server.get_current_time())
                self.mode = '5min'
                self.dca_server.binance_server.klines_server.stop_all()
                shutil.copy(r"Ini\Algorithm_5m.ini" , r"Ini\Algorithm.ini")
                importlib.reload(Config)
                self.dca_server = DCAServer() # Tạo lại DCAServer để áp dụng cấu hình mới
        return self.mode


if __name__ == '__main__':
    init_system_log()
    set_terminal_title("Main")
    log_action("START WITH 5 MINUTE MODE", datetime.datetime.now())
    shutil.copy(r'Ini\Algorithm_5m.ini', r'Ini\Algorithm.ini')
    importlib.reload(Config)
    trading_system = TradingSystem()
    trading_system.run()
