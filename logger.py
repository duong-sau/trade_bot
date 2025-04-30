import sys
import os
from PyQt5.QtWidgets import QMessageBox
import logging
from Tool import get_data_folder_path

logging.basicConfig(
    filename=os.path.join(get_data_folder_path(), "sys_log.log"),  # File log
    level=logging.DEBUG,        # Level log (DEBUG -> ghi mọi thứ)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Định dạng
    datefmt="%Y-%m-%d %H:%M:%S"  # Định dạng thời gian
)


def log_error():
    print_log_error(str(sys.exc_info()[1]))

def print_log_error(message):
    logging.error(message)
    print(message)

def print_log_info(message):
    logging.info(message)

def print_log_warning(message):
    logging.warning(message)

def print_log_critical(message):
    logging.critical(message)

