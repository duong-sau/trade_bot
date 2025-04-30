import websocket
import json
import csv
from datetime import datetime
import requests
import os

# Tạo tên file với định dạng dd_mm_yy
file_name = datetime.now().strftime("price_%d_%m_%y.csv")


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
if os.path.exists(file_name):
    os.remove(file_name)

# Tạo file CSV và ghi tiêu đề
with open(file_name, 'w', newline='') as file:
    writer = csv.writer(file)

    # Lấy và ghi dữ liệu lịch sử
    klines = get_historical_klines()
    for kline in klines:
        timestamp = datetime.fromtimestamp(kline[0] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        close_price = kline[4]
        writer.writerow([timestamp, close_price])


# Hàm xử lý khi nhận được dữ liệu từ WebSocket
def on_message(ws, message):
    data = json.loads(message)
    price = data['p']  # Giá giao dịch
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Thời gian hiện tại
    print(f"Time: {time}, Price: {price}")

    # Ghi vào file CSV
    with open(file_name, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([time, price])

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
