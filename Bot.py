
import subprocess
from _winapi import CREATE_NEW_CONSOLE
import sys
import os
import time
import ctypes
import threading
from datetime import datetime
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

from PyQt6.QtCore import Qt

import Config

from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QPushButton, QTableWidget, QTableWidgetItem, QGridLayout, QTextEdit
from qt_material import apply_stylesheet
from functools import partial

from Tool import get_data_folder_path, ALIVE_CMD, write_alive_cmd, create_ram_disk


# Hàm khởi chạy CMD và lấy handle
def start_cmd(script_name, window_name, container_hwnd, window_size, proc_name):
    write_alive_cmd(proc_name, ALIVE_CMD.RUN)
    proc = subprocess.Popen(f"{script_name}",  creationflags=CREATE_NEW_CONSOLE)

    for _ in range(30):
        time.sleep(1)
        hwnd = ctypes.windll.user32.FindWindowW(None, f"{window_name}")
        if hwnd:
            ctypes.windll.user32.SetParent(hwnd, container_hwnd)
            ctypes.windll.user32.MoveWindow(hwnd, 0, 0, window_size[0], window_size[1], True)
            break

    return proc


def is_window_running(proc):
    if proc is None:
        return False
    return proc.poll() is None

def kill_process(proc_name):
    write_alive_cmd(proc_name, ALIVE_CMD.STOP)
    time.sleep(0.1)


class ProcessMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Monitor")
        self.h = 860
        self.w = 640
        self.setGeometry(0, 0, self.h, self.w)

        self.data_folder =f"{time.strftime('%d_%m_%y-%H')}"
        os.makedirs(f"{Config.DATA_PATH}/" + self.data_folder, exist_ok=True)

        self.proc_Alive_cmd_name = ["PRICE", "WEBSOCKET", "VISUALIZER", "MAIN"]
        for cmd_name in self.proc_Alive_cmd_name:
            write_alive_cmd(cmd_name, ALIVE_CMD.RUN)


        self.alive_files = ['price_alive.txt', 'websocket_alive.txt', 'visualizer_alive.txt', 'main_alive.txt']
        self.last_alive = [0] * len(self.alive_files)
        self.alive_time = [datetime.now()] * len(self.alive_files)
        self.script_names = ["Price", "Websocket", "Visualizer", "Main"]
        self.window_name = ['Price', 'Websocket', "Figure 1", 'Main']
        unit_tp = (int(self.w), int(self.h))
        self.process_widgets = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QGridLayout(self.central_widget)

        h_widget = QWidget()
        h_layout = QGridLayout(h_widget)
        h_widget.setFixedSize(unit_tp[0], unit_tp[1])
        main_layout.addWidget(h_widget, 0, 0, 1, 1)

        tb_config_layout = QHBoxLayout()
        h_layout.addLayout(tb_config_layout, 0, 0, 3, 1)

        self.table = QTableWidget(len(self.script_names), 3)
        self.table.setHorizontalHeaderLabels(["Script", "Status", "Action"])
        self.table.setColumnWidth(0, 90)
        self.table.setFixedSize(300, 250)
        tb_config_layout.addWidget(self.table)

        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setFixedSize(300, 400)
        self.update_config_display()
        tb_config_layout.addWidget(self.config_text)

        # Add button to open config file
        button_layout = QHBoxLayout()
        h_layout.addLayout(button_layout, 3, 0, 1, 3)

        open_config_btn = QPushButton("Open Config")
        open_config_btn.clicked.connect(self.open_config_file)
        button_layout.addWidget(open_config_btn)

        start_all_button = QPushButton("Start All")
        start_all_button.clicked.connect(self.start_all_process)
        button_layout.addWidget(start_all_button)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.quit)
        button_layout.addWidget(quit_button)
        self.init_table()

    def init_table(self):
        self.table.verticalHeader().setVisible(False)

        for row, script in enumerate(self.script_names):
            self.table.setItem(row, 0, QTableWidgetItem(self.script_names[row]))

            status_button = QPushButton("STOPPED")
            status_button.setStyleSheet("background-color: red; color: white")
            status_button.setEnabled(False)
            self.table.setCellWidget(row, 1, status_button)

            button = QPushButton("Start")
            self.table.setCellWidget(row, 2, button)


    def update_config_display(self):
        config_text = f"""Margin: {Config.leverage}
BB: {Config.bb_period} - std: {Config.bb_stddev}
RSI: {Config.rsi_period}
RSI Long  < {int(Config.rsi_long)}
RSI Short > {int(Config.rsi_short)}
Distance  > {Config.distance}
N1: {Config.n1} - N2: {Config.n2}
TP1: {Config.tp1_ratio}% - TP2: {Config.tp2_ratio}%
limit1_timeout: {Config.limit_timeout}
tp_decree: after {Config.tp_timeout}m, with {Config.tp_decrease_time}m interval decrease by {Config.tp_decrease_step}%
tp_min: {Config.tp_min}%
dis_min: {Config.distance_min}, klines_count: {Config.distance_min_klines_count}
"""

        self.config_text.setText(config_text)


    def open_config_file(self):
        subprocess.run(['notepad.exe', 'Ini/Algorithm.ini'])

        import importlib
        importlib.reload(Config)
        self.update_config_display()

        self.update_config_display()

    def start_all_process(self):
        for row, script in enumerate(self.script_names):
            write_alive_cmd(self.proc_Alive_cmd_name[row], ALIVE_CMD.RUN)
        eval(f"{Config.start_script}")
        self.quit()


    def quit(self):
        self.close()
        QApplication.quit()


if __name__ == "__main__":
    # if not ctypes.windll.shell32.IsUserAnAdmin():
    #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    #     sys.exit()
    # QApplication.setAttribute(Qt.ApplicationAttribute(Qt.ApplicationAttribute.AA_Use96Dpi), True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi)
    create_ram_disk("Z", 128)
    # import ctypes
    # ctypes.windll.shcore.SetProcessDpiAwareness(1)
    app = QApplication(sys.argv)

    extra = {
        'font_family': 'Consolas',
        'font_size': 14,
    }
    apply_stylesheet(app, theme='dark_yellow.xml', extra=extra)
    window = ProcessMonitor()
    window.show()
    app.exec()