import websocket
import json
import time

# Hàm xử lý khi nhận được tin nhắn
def on_message(ws, message):
    data = json.loads(message)
    print(f"Price: {data['p']} USDT")  # Giá giao dịch từ stream 'trade'

# Hàm xử lý khi có lỗi
def on_error(ws, error):
    print(f"Error: {error}")

# Hàm xử lý khi kết nối đóng
def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

# Hàm xử lý khi kết nối thành công
def on_open(ws):
    print("Connected to Binance WebSocket")

# Hàm tạo kết nối WebSocket với cơ chế tự kết nối lại
def start_websocket():
    while True:
        try:
            # URL của WebSocket (BTCUSDT trade stream)
            ws_url = "wss://stream.binance.com:9443/ws/btcusdt@trade"

            # Tạo kết nối WebSocket
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )

            # Mở kết nối
            ws.on_open = on_open
            ws.run_forever()

        except Exception as e:
            print(f"Exception occurred: {e}")
            print("Reconnecting in 5 seconds...")
            time.sleep(5)  # Chờ trước khi thử lại

if __name__ == "__main__":
    start_websocket()
