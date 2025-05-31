import os
import sys
from enum import Enum

import numpy as np
import pandas_ta as ta
import pandas as pd
import portalocker
from tqdm import tqdm
from Config import bb_period, bb_stddev, DATA_PATH, rsi_period
from Server.Binance.Types.Order import ORDER_TYPE
from datetime import datetime

from Server.Binance.Types.Position import POSITION_SIDE


# Hàm tính toán Bollinger Bands và khoảng cách giữa upper và lower bands
def compute_bb_2(input_data):
    # Lấy giá trị cửa sổ dữ liệu gần nhất (từ cuối mảng)
    if len(input_data) < bb_period:
        print(len(input_data))
        raise ValueError("Input data length must be at least the size of the window")

    df = pd.DataFrame()
    df['close'] = input_data

    df.ta.bbands(length=bb_period, std=bb_stddev, append=True)

    # Tính khoảng cách (distant)
    upper =  df[f'BBU_20_{float(bb_stddev):.1f}']
    lower = df[f'BBL_20_{float(bb_stddev):.1f}']
    ma  = df[f'BBM_20_{float(bb_stddev):.1f}']

    distant = upper - lower

    return input_data, upper, lower,  distant, ma

def compute_rsi(data, period=14,  round_rsi: bool = True):
    df = pd.DataFrame(data, columns=['close'])
    delta = df["close"].diff()

    up = delta.copy()
    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha=1/period).mean()

    down = delta.copy()
    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha=1/period).mean()

    rsi = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

    return np.round(rsi, 2)[-1] if round_rsi else rsi[-1]

# Hàm tính toán các điểm Long (L0, L1, L2) và Short (S0, S1, S2)
def calculate_points(lower, upper, ma, current):
    L0 = lower
    L1 = L0 - (ma - L0) / (0.618 - 0.5) * (0.786 - 0.618)
    L2 = L0 - (ma - L0) / (0.618 - 0.5) * (1.5 - 0.618)
#
    # Short Points (S0, S1, S2)
    S0 = upper
    S1 = S0 + (S0 - ma) / (0.618 - 0.5) * (0.786 - 0.618)
    S2 = S0 + (S0 - ma) / (0.618 - 0.5) * (1.5 - 0.618)

    return (L0, L1, L2), (S0, S1, S2)


def get_data_folder_path():
    timestamp = datetime.now().strftime("%d_%m_%y-%H")
    folder_path = f'{DATA_PATH}/{timestamp}' if len(sys.argv) < 2 else f'{DATA_PATH}/{sys.argv[1]}'
    return folder_path

kline_file_path = os.path.join(get_data_folder_path(), 'price.csv')

def get_window_klines(param):
    global kline_file_path
    """Reads 5-minute interval close prices from CSV file."""
    with open(kline_file_path, 'r') as f:
        portalocker.lock(f, portalocker.LOCK_SH)  # Áp dụng Shared Lock
        df = pd.read_csv(f, names=['timestamp', 'price'])  # Đọc dữ liệu vào Pandas
        portalocker.unlock(f)  # Mở khóa sau khi đọc xong

    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')

    # Set timestamp as index and resample to 5-minute intervals
    df.set_index('timestamp', inplace=True)
    df_5min = df.resample('5min').last()

    # Get last param (or 20 if param is None) prices
    limit = param if param else 20
    close_prices = df_5min['price'].tail(limit).tolist()[:-1] + [df['price'].iloc[-1]]
    time_stamps = df_5min['price'].tail(limit).index.tolist()[:-1] + [df.index[-1]]

    return close_prices, time_stamps

import ctypes
def set_terminal_title(title):
    ctypes.windll.kernel32.SetConsoleTitleW(title)

alive_counter = 0
data_folder_path = get_data_folder_path()
def set_alive_counter(file_name):
    global  alive_counter
    alive_counter += 1
    if alive_counter > 10:
        alive_counter = 0

    # Get the folder path
    global data_folder_path
    file_path = os.path.join(data_folder_path, file_name)

    # Write the counter to the file
    with open(file_path, 'w') as file:
        file.write(str(alive_counter))

class ALIVE_CMD(Enum):
    RUN = "RUN"
    STOP = "STOP"
def read_alive_cmd(process_name):
    with open(os.path.join(data_folder_path, 'alive_cmd.txt'), 'r') as file:
        lines = file.readlines()
        for line in lines:
            process, status = line.strip().split(": ")
            if process != process_name:
                continue
            if status == ALIVE_CMD.STOP.value:
                return ALIVE_CMD.STOP
        return ALIVE_CMD.RUN
def write_alive_cmd(proc_name, cmd):

    if not os.path.exists(os.path.join(data_folder_path, 'alive_cmd.txt')):
        file = open(os.path.join(data_folder_path, 'alive_cmd.txt'), 'w')
        file.close()

    lines = []
    with open(os.path.join(data_folder_path, 'alive_cmd.txt'), 'r') as file:
        lines = file.readlines()

    with open(os.path.join(get_data_folder_path(), 'alive_cmd.txt'), 'w') as file:
        found = False
        for line in lines:
            if line.strip() == "":
                continue
            process, status = line.strip().split(": ")
            if process != proc_name:
                file.write(line.strip() + "\n")
                continue
            file.write(f"{process}: {cmd.value}\n")
            found = True
        if not found:
            file.write(f"{proc_name}: {cmd.value}\n")

import math
# Hàm tính toán Bollinger Bands và khoảng cách giữa upper và lower bands
def quick_compute_bb(input_data):

    # Lấy giá trị cửa sổ dữ liệu gần nhất (từ cuối mảng)
    if len(input_data) < bb_period:
        print(len(input_data))
        raise ValueError("Input data length must be at least the size of the window")

    window_data = input_data[-bb_period:]

    # Tính trung bình động (MA)
    ma = sum(window_data) / bb_period

    # Tính độ lệch chuẩn (stddev)
    variance = sum((x - ma) ** 2 for x in window_data) / bb_period
    stddev = math.sqrt(variance)

    # Tính Upper, Lower và Distant
    upper = ma + bb_stddev * stddev
    lower = ma - bb_stddev * stddev
    distant = upper - lower

    # Trả về các giá trị cuối cùng
    return input_data[-1], upper, lower, distant, ma


def create_ram_disk(drive_letter, size_mb):
    """
    Creates a RAM disk with the specified drive letter and size in GB.
    """
    # check if drive is already mounted
    if os.path.exists(f"{drive_letter}:"):
        print(f"Drive {drive_letter}: is already mounted.")
        return
    import subprocess
    command = f"powershell -Command \"Start-Process 'imdisk' -ArgumentList '-a -t vm -s {size_mb}M -m {drive_letter}: -p /fs:NTFS' -Verb RunAs\""
    subprocess.run(command, shell=True, check=True)
    print(f"RAM disk created at {drive_letter}: with size {size_mb}MB")
    exit(0)  # Exit after creating the RAM disk