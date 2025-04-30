from datetime import datetime
import threading
import time
import traceback
import json
from tqdm import tqdm

import Config
# from RealServer.DCA import DCAServer
from Server.DCA import DCAServer
from Tool import compute_bb_2, calculate_points, compute_rsi
from Visualize import Visualizer

if __name__ == '__main__':

    visualizer = Visualizer()
    dca_server = DCAServer()


    def run():
        for i in range(dca_server.get_total()):
            time.sleep(1)
            try:
                # Tiến hành các bước tick của server
                dca_server.tick()

                data = dca_server.get_window_klines(20)
                current, upper, lower, distant, ma = compute_bb_2(data)
                rsi = compute_rsi(data)

                def main_run():
                    if distant > Config.distance:  # Điều kiện khác khi distant lớn hơn 2500
                        L_point, S_point = calculate_points(lower, upper, ma, data[-1])

                        # Xử lý lệnh Long
                        if rsi <= Config.rsi_long:
                            if dca_server.GetDACNum() == 0:  # Chưa có lệnh Long nào được khớp
                                dca_server.put_long(L_point, 2, [Config.n1, Config.n2])

                        # Xử lý lệnh Short
                        if rsi >= Config.rsi_short:
                            if dca_server.GetDACNum() == 0:  # Chưa có lệnh Short nào được khớp
                                dca_server.put_short(S_point, 2, [Config.n1, Config.n2])

                main_run()

                def visualize_run():
                    visualizer.update_data(data, upper, lower, distant, ma, rsi)
                    # Tính toán Long và Short Points
                    trades = dca_server.get_trades()
                    data_to_save = {
                        'trades': trades,
                        'dcas': dca_server.get_dcas()
                    }
                    with open('visualize.json', 'w') as f:
                        json.dump(data_to_save, f)
                    visualizer.set_trades(trades)

                    dcas = dca_server.get_dcas()
                    visualizer.set_dcas(dcas)

                    visualizer.set_last_time(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

                visualize_run()

            except Exception as e:
                traceback.print_exc()
                exit(0)
    run()
    # # Chạy luồng phụ để lấy dữ liệu
    # data_thread = threading.Thread(target=run, daemon=True)
    # data_thread.start()
    #
    # # # Chạy visualizer trong luồng chính
    # visualizer.start_animation()