import websocket
import json
import csv
from datetime import datetime
import requests
import os
import sys

from Tool import set_terminal_title, set_alive_counter

if __name__ == '__main__':
    set_terminal_title('Price')

    timestamp = datetime.now().strftime("%d_%m_%y-%H")
    folder_path = f'./DATA/{timestamp}' if len(sys.argv) < 2 else f'./DATA/{sys.argv[1]}'
    os.makedirs(folder_path, exist_ok=True)


    def get_historical_klines():
        url = "https://testnet.binancefuture.com/fapi/v1/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": "5m",
            "limit": 500
        }
        response = requests.get(url, params=params)
        return response.json()


    # Xóa file cũ nếu tồn tại và tạo file mới
    file_path = os.path.join(folder_path, 'price.csv')
    if os.path.exists(file_path):
        os.remove(file_path)

    # Tạo file CSV và ghi tiêu đề
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)

        # Lấy và ghi dữ liệu lịch sử
        klines = get_historical_klines()
        for kline in klines:
            timestamp = datetime.fromtimestamp(kline[0] / 1000).strftime("%Y-%m-%d %H:%M:%S")
            close_price = kline[4]
            writer.writerow([timestamp, close_price])


    # Hàm xử lý khi nhận được dữ liệu từ WebSocket
    message_counter = 0  # Global counter


    def on_message(ws, message):
        global message_counter
        data = json.loads(message)
        price = data['p']  # Giá giao dịch
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Thời gian hiện tại
        print(f"Time: {time}, Price: {price}")

        # Ghi vào file CSV
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([time, price])

        message_counter += 1
        if message_counter > 20000:
            # Read all lines
            with open(file_path, 'r') as file:
                lines = file.readlines()
            # Write back excluding first 1000 lines    
            with open(file_path, 'w') as file:
                file.writelines(lines[10000:])
            message_counter -= 10000

        if message_counter % 10 == 0:
            set_alive_counter('price_alive.txt')

    # Hàm xử lý khi kết nối WebSocket
    def on_open(ws):
        print("WebSocket connected")
        # Gửi yêu cầu đăng ký nhận dữ liệu giá
        payload = {
            "method": "SUBSCRIBE",
            "params": [
                "btcusdt@trade"  # Nhận giao dịch future BTC/USDT từ testnet
            ],
            "id": 1
        }
        ws.send(json.dumps(payload))

    # Hàm xử lý khi WebSocket đóng kết nối
    def on_close(ws):
        print("WebSocket closed")

    # Kết nối WebSocket
    url = "wss://stream.binancefuture.com/ws"  # URL cho Binance Futures WebSocket Testnet
    ws = websocket.WebSocketApp(url, on_message=on_message, on_open=on_open, on_close=on_close)

    print("Historical data loaded, starting real-time updates...")
    # Chạy WebSocket
    ws.run_forever()
