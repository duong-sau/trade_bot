import sys

from PyQt5.QtWidgets import QMessageBox
import logging

logging.basicConfig(
    filename="../sys_log.log",  # File log
    level=logging.DEBUG,        # Level log (DEBUG -> ghi mọi thứ)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Định dạng
    datefmt="%Y-%m-%d %H:%M:%S"  # Định dạng thời gian
)


def log_error():
    print_log_error(str(sys.exc_info()[1]))

def print_log_error(message):
    logging.error(message)

def print_log_info(message):
    logging.info(message)

def print_log_warning(message):
    logging.warning(message)

def print_log_critical(message):
    logging.critical(message)