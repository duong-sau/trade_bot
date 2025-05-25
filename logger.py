import sys
import os
import logging
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



