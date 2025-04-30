import math
import os
import sys

import pandas as pd
from tqdm import tqdm
import csv
from datetime import datetime

from Server.Binance.Types.Order import ORDER_SIDE, ORDER_TYPE
import pandas as pd
from datetime import datetime

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
    L0 = lower
    L1 = L0 - (ma - L0) / (0.618 - 0.5) * (0.786 - 0.618)
    L2 = L0 - (ma - L0) / (0.618 - 0.5) * (1.5 - 0.618)

    # Short Points (S0, S1, S2)
    S0 = upper
    S1 = S0 + (S0 - ma) / (0.618 - 0.5) * (0.786 - 0.618)
    S2 = S0 + (S0 - ma) / (0.618 - 0.5) * (1.5 - 0.618)
    # L0 = current
    # L1 = current - 50
    # L2 = current - 100
    #
    # S0 = current
    # S1 = current + 50
    # S2 = current + 100

    return (L0, L1, L2), (S0, S1, S2)

def log_order(action, order, server_time):
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
    log_text = f"{server_time}\taction: {action}\tside: {side_text}\ttype: {order_text}\tamount: {order.amount:.6f}\tprice: {order.trigger_price:.6f}\tid: {order.id}"
    tqdm.write(log_text)

    # Write to CSV file in append mode
    systemlog_path = os.path.join(get_data_folder_path(), 'systemlog.csv')
    with open(systemlog_path, 'a', newline='') as csvfile:
        csvfile.write(log_text + '\n')


def get_data_folder_path():
    timestamp = datetime.now().strftime("%d_%m_%y-%H")
    folder_path = f'./DATA/{timestamp}' if len(sys.argv) < 2 else f'./DATA/{sys.argv[1]}'
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

kline_file_path = os.path.join(get_data_folder_path(), 'price.csv')

def get_window_klines(param):
    global kline_file_path
    """Reads 5-minute interval close prices from CSV file."""
    # Read CSV file with current date
    df = pd.read_csv(kline_file_path, names=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')

    # Set timestamp as index and resample to 5-minute intervals
    df.set_index('timestamp', inplace=True)
    df_5min = df.resample('5min').last()

    # Get last param (or 20 if param is None) prices
    limit = param if param else 20
    close_prices = df_5min['price'].tail(limit).tolist()
    time_stamps = df_5min['price'].tail(limit).index.tolist()

    return close_prices, time_stamps
