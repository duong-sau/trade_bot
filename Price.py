import signal
import time

import portalocker
from binance.client import Client
import csv
from datetime import datetime
import os
import sys

from binance import ThreadedWebsocketManager

from Config import DATA_PATH
from RealServer import testnet
from Tool import set_terminal_title, set_alive_counter, read_alive_cmd, ALIVE_CMD

if __name__ == '__main__':
    set_terminal_title('Price')

    timestamp = datetime.now().strftime("%d_%m_%y-%H")
    folder_path = f'{DATA_PATH}/{timestamp}' if len(sys.argv) < 2 else f'{DATA_PATH}/{sys.argv[1]}'
    os.makedirs(folder_path, exist_ok=True)


    def get_historical_klines():
        client = Client(api_key='', api_secret='', testnet=testnet)
        klines = client.futures_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_5MINUTE, limit=500)
        return klines
    # Xóa file cũ nếu tồn tại và tạo file mới
    file_path = os.path.join(folder_path, 'price.csv')
    if os.path.exists(file_path):
        os.remove(file_path)

    def init_data_file():
        # Tạo file CSV và ghi tiêu đề

        # Lấy dữ liệu lịch sử trước khi mở file
        klines = get_historical_klines()

        # Chuẩn bị dữ liệu trước khi ghi
        data_to_write = [
            [datetime.fromtimestamp(kline[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"), kline[4]]
            for kline in klines
        ]

        # Ghi file
        with open(file_path, 'w', newline='') as file:
            portalocker.lock(file, portalocker.LOCK_EX)
            writer = csv.writer(file)
            writer.writerows(data_to_write)  # Ghi toàn bộ dữ liệu một lần
            portalocker.unlock(file)  # Không cần thiết vì `with` tự unlock


    init_data_file()
    # Hàm xử lý khi nhận được dữ liệu từ WebSocket
    message_counter = 0  # Global counter

    web_socket = ThreadedWebsocketManager(
        testnet=testnet)

    def on_message(message):
        global message_counter

        try:
            if 'e' in message:
                if message['e'] == 'error':
                    print('socket reconnect')
                    web_socket.stop_socket('btcusdt@aggTrade')
                    web_socket.start_aggtrade_futures_socket(symbol="BTCUSDT", callback=on_message)
            else:
                price = message['data']['p']  # Giá giao dịch
                time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Thời gian hiện tại
                print(f"Time: {time}, Price: {price}")

                # Ghi vào file CSV
                with open(file_path, 'a', newline='') as file:
                    portalocker.lock(file, portalocker.LOCK_EX)
                    writer = csv.writer(file)
                    writer.writerow([time, price])
                    portalocker.unlock(file)

                message_counter += 1
                if message_counter > 2000:
                    init_data_file()
                    message_counter = 0
        except Exception as e:
            print(f"Error: {e}")
            print(message)

    web_socket.start()
    print('Websocket reconnected')
    web_socket.start_aggtrade_futures_socket(symbol="BTCUSDT", callback=on_message)

    def stop():
        web_socket.stop()
        sys.exit(0)

    def signal_handler(sig, frame):
        print("\nProgram terminated by user (Ctrl + C)")
        stop()

    signal.signal(signal.SIGINT, signal_handler)

    print("Historical data loaded, starting real-time updates...")
    # chạy while true nếu đọc file được STOP thì dừng chương trình
    while True:
        set_alive_counter('price_alive.txt')
        run = read_alive_cmd('PRICE')
        if run == ALIVE_CMD.STOP:
            stop()
        time.sleep(1)