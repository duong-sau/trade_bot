import sys
import os
import logging

from tqdm import tqdm

from Server.Binance.Types.Order import ORDER_TYPE
from Server.Binance.Types.Position import POSITION_SIDE
from Tool import get_data_folder_path
#
# logging.basicConfig(
#     filename=os.path.join(r"Data", "sys_log.log"),  # File log
#     level=logging.DEBUG,        # Level log (DEBUG -> ghi mọi thứ)
#     format="%(asctime)s - %(levelname)s - %(message)s",  # Định dạng
#     datefmt="%Y-%m-%d %H:%M:%S"  # Định dạng thời gian
# )


def log_error():
    print_log_error(str(sys.exc_info()[1]))

def print_log_error(message):
    file_path = r"C:\Bot\log\syslog.csv"
    with open(file_path, mode='a', encoding='utf-8') as file:
        file.write(f"{message}\n")
    print(message)
    pass

def init_system_log():
    systemlog_path = r'C:\Bot\Log\syslog.csv'
    with open(systemlog_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvfile.write("SYS_LOG\n")  # Write header


def log_action(action, server_time):
    log_text = f"\r\033[K\033[93m{server_time} -- {action}\033[0m"  # Yellow color with line clear
    tqdm.write(log_text)

    # Write to CSV file in append mode
    systemlog_path = r'C:\Bot\Log\syslog.csv'
    with open(systemlog_path, 'a', newline='', encoding='utf-8') as csvfile:
        # Remove ANSI color codes when writing to file
        plain_text = f"{server_time} -- {action}"
        csvfile.write(plain_text + '\n')

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

    log_text = f"\r\033[K{log_text}  |"  # Clear line before printing

    tqdm.write(log_text)

    # Write to CSV file in append mode
    systemlog_path =  r'C:\Bot\Log\syslog.csv'
    with open(systemlog_path, 'a', newline='', encoding='utf-8') as csvfile:
        csvfile.write(plain_text + '\n')

