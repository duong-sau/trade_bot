import os
import datetime
import time
import traceback
import json
import sys
import signal

from tqdm import tqdm

import Config
from Animation import step
from RealServer.Common import force_stop_loss
# from RealServer.DCA import DCAServer
from Server.DCA import DCAServer, TRADE_STEP
from Tool import compute_bb_2, calculate_points, compute_rsi, get_data_folder_path, log_order, set_terminal_title, log_action, \
    set_alive_counter, read_alive_cmd, ALIVE_CMD, quick_compute_bb, quick_compute_rsi


class TradingSystem:
    def __init__(self):
        self.dca_server = DCAServer()
        self.visualize_file = os.path.join(get_data_folder_path(), 'visualize.json')
        self.clear_visualize_file()
        signal.signal(signal.SIGINT, self.cleanup_handler)

        # đặt margin
        self.dca_server.binance_server.klines_server.set_leverage(Config.leverage)

        self.dca_server.binance_server.klines_server.pre_check()


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
            time.sleep(0.25)
            set_alive_counter('main_alive.txt')
            try:
                # Tiến hành các bước tick của server
                self.dca_server.tick()

                result = self.main_run()
                self.visualize_run()
                step(result)
                run = read_alive_cmd("MAIN")
                if run == ALIVE_CMD.STOP:
                    exit(0)
            except KeyboardInterrupt:
                self.cleanup_handler(None, None)
            except Exception as e:
                traceback.print_exc()
                self.clear_visualize_file()
                exit(0)

    def main_run(self):
        data = self.dca_server.get_window_klines(20)
        if len(data) < Config.bb_period:
            return "Error: Not enough data to compute BB"
        current, upper, lower, distant, ma = quick_compute_bb(data)
        rsi = compute_rsi(data)

        data2 = self.dca_server.get_window_klines(Config.distance_min_klines_count + Config.bb_period)
        if len(data2) < Config.distance_min_klines_count + Config.bb_period:
            return "Error: Not enough data to compute BB"
        current2, upper2, lower2, distant2, ma2 = compute_bb_2(data2)

        if distant > Config.distance and (distant2.tail(Config.distance_min_klines_count) > Config.distance_min).all():  # Điều kiện khác khi distant lớn hơn 2500
            L_point, S_point = calculate_points(lower, upper, ma, data[-1])

            # Xử lý lệnh Long
            if rsi <= Config.rsi_long:
                if self.dca_server.get_dac_num() == 0:  # Chưa có lệnh Long nào được khớp
                    log_action(f"OPEN LONG -- RSI: {rsi} < LONG RSI {Config.rsi_long}  DISTANCE: {distant}", self.dca_server.binance_server.get_current_time())
                    self.dca_server.put_long(L_point,  [Config.n1, Config.n2])

            # Xử lý lệnh Short
            if rsi >= Config.rsi_short:
                if self.dca_server.get_dac_num() == 0:  # Chưa có lệnh Short nào được khớp
                    log_action(f"OPEN SHORT -- RSI: {rsi} > SHORT RSI {Config.rsi_short}  DISTANCE: {distant}", self.dca_server.binance_server.get_current_time())
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


        if self.dca_server.get_trade_step() == TRADE_STEP.LIMIT2_FILLED or self.dca_server.get_trade_step() == TRADE_STEP.LIMIT1_FILLED:
            if self.dca_server.get_limit_filled_time() is None:
              return f"------"
            elif (self.dca_server.get_limit_filled_time() > datetime.timedelta(minutes=Config.tp_timeout)
                  and self.dca_server.current_tp2_ratio >= (Config.tp_decrease_step + Config.tp_min) / 100):
                log_action(f"TP IS TIMEOUT START DECREASE TP------------------------------", self.dca_server.binance_server.get_current_time())
                if not self.dca_server.decrease_tp():
                    return f"------"
        elif self.dca_server.get_trade_step() == TRADE_STEP.TP2_DECREASE or self.dca_server.get_trade_step() == TRADE_STEP.TP1_DECREASE:
            if self.dca_server.get_tp_decrease_time() is None:
                return f"------"
            elif (self.dca_server.get_tp_decrease_time() > datetime.timedelta(minutes=Config.tp_decrease_time)
                  and self.dca_server.current_tp2_ratio >= (Config.tp_decrease_step + Config.tp_min) / 100):
                log_action(f"DECREASE TP TIME OUT ------------------------------", self.dca_server.binance_server.get_current_time())
                if not self.dca_server.decrease_tp():
                    return f"------"

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


if __name__ == '__main__':
    set_terminal_title("Main")
    trading_system = TradingSystem()
    trading_system.run()
