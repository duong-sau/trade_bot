import math
import pandas as pd
from tqdm import tqdm

from Server.Binance.Types.Order import ORDER_SIDE, ORDER_TYPE


# Hàm tính toán Bollinger Bands và khoảng cách giữa upper và lower bands
def compute_bb_2(input_data):
    window_size = 20
    stddev_factor = 3

    # Lấy giá trị cửa sổ dữ liệu gần nhất (từ cuối mảng)
    if len(input_data) < window_size:
        raise ValueError("Input data length must be at least the size of the window")

    window_data = input_data[-window_size:]

    # Tính trung bình động (MA)
    ma = sum(window_data) / window_size

    # Tính độ lệch chuẩn (stddev)
    variance = sum((x - ma) ** 2 for x in window_data) / window_size
    stddev = math.sqrt(variance)

    # Tính Upper, Lower và Distant
    upper = ma + stddev_factor * stddev
    lower = ma - stddev_factor * stddev
    distant = upper - lower

    # Trả về các giá trị cuối cùng
    return input_data[-1], upper, lower, distant, ma

    # Tính MA và độ lệch chuẩn
    ma = sum(window_data) / window_size
    variance = sum((x - ma) ** 2 for x in window_data) / window_size
    stddev = math.sqrt(variance)

    # Tính khoảng cách (distant)
    upper = ma + stddev_factor * stddev
    lower = ma - stddev_factor * stddev
    distant = upper - lower

    return distant

# Hàm tính RSI
def compute_rsi(data, period=14):
    if len(data) < period + 1:
        raise ValueError("Input data length must be at least period + 1")

    # Tính thay đổi giá hằng ngày
    changes = [data[i] - data[i-1] for i in range(1, len(data))]

    # Phân loại lãi (gain) và lỗ (loss)
    gains = [x if x > 0 else 0 for x in changes]
    losses = [-x if x < 0 else 0 for x in changes]

    # Tính trung bình lãi và lỗ ban đầu
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Duy trì giá trị trung bình động (Smoothed Moving Average)
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    # Tính RS và RSI
    if avg_loss == 0:
        rsi = 100  # Nếu không có lỗ, RSI = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    return rsi

# Hàm tính toán các điểm Long (L0, L1, L2) và Short (S0, S1, S2)
def calculate_points(lower, upper, ma, current):
    # Long Points (L0, L1, L2)
    # L0 = lower
    # L1 = L0 - (ma - L0) / (0.618 - 0.5) * (0.786 - 0.618)
    # L2 = L0 - (ma - L0) / (0.618 - 0.5) * (1.5 - 0.618)
    #
    # # Short Points (S0, S1, S2)
    # S0 = upper
    # S1 = S0 + (S0 - ma) / (0.618 - 0.5) * (0.786 - 0.618)
    # S2 = S0 + (S0 - ma) / (0.618 - 0.5) * (1.5 - 0.618)
    L0 = current
    L1 = current - 50
    L2 = current - 100

    S0 = current
    S1 = current + 50
    S2 = current + 100

    return (L0, L1, L2), (S0, S1, S2)

# DCA Long
def dca_long(L_points):
    lenh1 = L_points[0]
    lenh2 = L_points[1]
    lenh3 = L_points[2]

    dca_points = [lenh1, lenh2, lenh3]
    return dca_points

# DCA Short
def dca_short(S_points):
    lenh1 = S_points[0]
    lenh2 = S_points[1]
    lenh3 = S_points[2]

    dca_points = [lenh1, lenh2, lenh3]
    return dca_points

def log_order(action, order, current_time):
    if order.side == ORDER_SIDE.LONG:
        side_text = "LONG"
    else:
        side_text = "SHORT"

    if order.type == ORDER_TYPE.LIMIT:
        order_text = "LIMIT"
    elif order.type == ORDER_TYPE.TP:
        order_text = "___TP"
    elif order.type == ORDER_TYPE.SL:
        order_text = "___SL"
    else:
        assert False
    tqdm.write(f"{action} : id: {order.id} - amount: {order.amount:.6f} - price: {order.trigger_price:.6f} - {side_text} {order_text} --  {current_time}")
