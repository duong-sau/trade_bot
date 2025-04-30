import os
from datetime import datetime
import threading
import time
import traceback
import json
import sys
import signal
from numpy import ma

import Config
from Animation import step
# from RealServer.DCA import DCAServer
from Server.DCA import DCAServer
from Tool import compute_bb_2, calculate_points, compute_rsi, get_data_folder_path, set_terminal_title


class TradingSystem:
    def __init__(self):
        self.dca_server = DCAServer()
        self.visualize_file = os.path.join(get_data_folder_path(), 'visualize.json')
        self.clearVisualizeFile()
        signal.signal(signal.SIGINT, self.cleanup_handler)

    def clearVisualizeFile(self):
        with open(self.visualize_file, 'w') as f:
            json.dump({}, f)

    def cleanup_handler(self, signum, frame):
        print("Stopping trading system...")
        self.clearVisualizeFile()
        sys.exit(0)

    def run(self):
        while True:
            time.sleep(0.1)
            try:
                # Tiến hành các bước tick của server
                self.dca_server.tick()

                self.main_run()
                self.visualize_run()
                step()

            except KeyboardInterrupt:
                self.cleanup_handler(None, None)
            except Exception as e:
                traceback.print_exc()
                self.clearVisualizeFile()
                exit(0)

    def main_run(self):
        data = self.dca_server.get_window_klines(20)
        current, upper, lower, distant, ma = compute_bb_2(data)
        rsi = compute_rsi(data)

        if distant > Config.distance:  # Điều kiện khác khi distant lớn hơn 2500
            L_point, S_point = calculate_points(lower, upper, ma, data[-1])

            # Xử lý lệnh Long
            if rsi <= Config.rsi_long:
                if self.dca_server.GetDACNum() == 0:  # Chưa có lệnh Long nào được khớp
                    self.dca_server.put_long(L_point, 2, [Config.n1, Config.n2])

            # Xử lý lệnh Short
            if rsi >= Config.rsi_short:
                if self.dca_server.GetDACNum() == 0:  # Chưa có lệnh Short nào được khớp
                    self.dca_server.put_short(S_point, 2, [Config.n1, Config.n2])

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
