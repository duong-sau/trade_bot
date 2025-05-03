import math
import os
import sys
from enum import Enum
import pandas_ta as ta
import pandas as pd
from tqdm import tqdm
from Config import bb_period, bb_stddev
from Server.Binance.Types.Order import ORDER_TYPE
from datetime import datetime

from Server.Binance.Types.Position import POSITION_SIDE


# Hàm tính toán Bollinger Bands và khoảng cách giữa upper và lower bands
def compute_bb_2(input_data):

    df = pd.DataFrame()
    df['close'] = input_data

    df.ta.bbands(length=bb_period, std=bb_stddev, append=True)

    # Tính khoảng cách (distant)
    upper =  df[f'BBU_20_{float(bb_stddev):.1f}'].tolist()[-1]
    lower = df[f'BBL_20_{float(bb_stddev):.1f}'].tolist()[-1]
    ma  = df[f'BBM_20_{float(bb_stddev):.1f}'].tolist()[-1]

    distant = upper - lower

    return input_data[-1], upper, lower,  distant, ma

# Hàm tính RSI
def compute_rsi(data, period=14):
    df = pd.DataFrame()
    df['close'] = data
    df['rsi'] = ta.rsi(df['close'], length=14)

    return df['rsi'].tolist()[-1]

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

    return (L0, L1, L2), (S0, S1, S2)

def log_order(action, order, server_time):
    if order.side == POSITION_SIDE.LONG:
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

    # Move cursor up one line and clear it before printing
    plain_text = f"{server_time} -- {action} -- {side_text} -- {order_text} -- {order.amount:.4f} -- {order.trigger_price:.2f} -- id: {str(order.id)[:10]}"

    if action == "FILLED":
        if order.type == ORDER_TYPE.LIMIT:
            log_text = f"\033[93m{plain_text}\033[0m"  # Yellow
        elif order.type == ORDER_TYPE.TP:
            log_text = f"\033[92m{plain_text}\033[0m"  # Green
        elif order.type == ORDER_TYPE.SL:
            log_text = f"\033[91m{plain_text}\033[0m"  # Red
    else:
        log_text = plain_text

    log_text = f"\033[K\033[K{log_text}  |"  # Clear line before printing

    tqdm.write(log_text)

    # Write to CSV file in append mode
    # systemlog_path = os.path.join(get_data_folder_path(), 'systemlog.csv')
    # with open(systemlog_path, 'a', newline='') as csvfile:
    #     csvfile.write(plain_text + '\n')


def log_action(action, server_time):
    log_text = f"\033[K\033[K\033[93m{server_time} -- {action}\033[0m"  # Yellow color with line clear
    tqdm.write(log_text)

    # Write to CSV file in append mode
    systemlog_path = os.path.join(get_data_folder_path(), 'systemlog.csv')
    # with open(systemlog_path, 'a', newline='') as csvfile:
    #     # Remove ANSI color codes when writing to file
    #     plain_text = f"{server_time} -- {action}"
    #     csvfile.write(plain_text + '\n')


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