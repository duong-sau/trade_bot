from datetime import datetime
import threading
import time
import traceback
from tqdm import tqdm
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

                # Lấy dữ liệu mới và tính RSI
                data = dca_server.get_window_klines(20)
                current, upper, lower, distant, ma = compute_bb_2(data)
                rsi = compute_rsi(data)

                visualizer.update_data(data, upper, lower, distant, ma, rsi)
                # Tính toán Long và Short Points
                trades = dca_server.get_trades()
                visualizer.set_trades(trades)

                dcas = dca_server.get_dcas()
                visualizer.set_dcas(dcas)

                visualizer.set_last_time(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                if distant > 100:  # Điều kiện khác khi distant lớn hơn 2500
                    L_point, S_point = calculate_points(lower, upper, ma, data[-1])

                    # Xử lý lệnh Long
                    if rsi <= 100:
                        if dca_server.GetDACNum() == 0:  # Chưa có lệnh Long nào được khớp
                            print("detect push long")
                            dca_server.put_long(L_point, 2, 0.002)

                    # else:  # RSI không còn ≤ 25
                    #     if dca_server.GetDACNum() != 0:  # Chưa có lệnh nào khớp
                    #         print("detect clear all")
                    #         dca_server.clear_all_orders()  # Hủy tất cả lệnh Long chưa khớp


                    # Xử lý lệnh Short
                    if rsi >= 0:
                        if dca_server.GetDACNum() == 0:  # Chưa có lệnh Short nào được khớp
                            print("detect push short")
                            dca_server.put_short(S_point, 2, 0.002)

                    # else:  # RSI không còn ≥ 75
                    #     if dca_server.GetDACNum() != 0:  # Chưa có lệnh nào khớp
                    #         print("detect clear all")
                    #         dca_server.clear_all_orders()  # Hủy tất cả lệnh Short chưa khớp

            except Exception as e:
                traceback.print_exc()
                exit(0)

    # Chạy luồng phụ để lấy dữ liệu
    data_thread = threading.Thread(target=run, daemon=True)
    data_thread.start()

    # # Chạy visualizer trong luồng chính
    visualizer.start_animation()