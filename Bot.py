import subprocess
from subprocess import run, Popen
import sys
import os
import time
import ctypes
import threading
from datetime import datetime
import Config

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTableWidget, \
    QTableWidgetItem, QGridLayout, QTextEdit
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer
from qt_material import apply_stylesheet
from functools import partial

# Hàm khởi chạy CMD và lấy handle
def start_cmd(script_name, window_name, container_hwnd, window_size):
    os.system(script_name)

    for _ in range(30):
        time.sleep(1)
        hwnd = ctypes.windll.user32.FindWindowW(None, f"{window_name}")
        if hwnd:
            ctypes.windll.user32.SetParent(hwnd, container_hwnd)
            ctypes.windll.user32.MoveWindow(hwnd, 0, 0, window_size[0], window_size[1], True)
            break


def is_window_running(window_name):
    return ctypes.windll.user32.FindWindowW(None, window_name) != 0


class ProcessMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Monitor")
        self.setGeometry(0, 0, 1200, 1000)

        self.data_folder =f"{time.strftime('%d_%m_%y-%H')}"
        os.makedirs(self.data_folder, exist_ok=True)

        self.alive_files = ['price_alive.txt', 'websocket_alive.txt', 'visualizer_alive.txt', 'main_alive.txt']
        self.last_alive = [0] * len(self.alive_files)
        self.alive_time = [datetime.now()] * len(self.alive_files)
        self.script_names = ["Price", "Websocket", "Visualizer", "Main"]
        # f'start cmd /k "cd /d {os.getcwd()} & {script_name} & exit"'
        self.scripts = [f'start cmd /k python Price.py {self.data_folder}',
                        f'start cmd /k python Websocket.py {self.data_folder}',
                        f"start pythonw Visualizer.py {self.data_folder}",
                        f'start cmd /k python Main.py {self.data_folder}'
                        ]
        self.window_name = ['Price', 'Websocket', "Figure 1", 'Main']
        self.row_column_spans = [(2, 2, 1, 1), (1, 2, 1, 1), (1, 0, 2, 2), (0, 1, 1, 2)]
        self.window_sizes = [(600, 300), (600, 300), (1200, 600), (1200, 300)]
        self.process_widgets = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QGridLayout(self.central_widget)

        h_widget = QWidget()
        h_layout = QGridLayout(h_widget)
        h_widget.setFixedSize(600, 300)
        main_layout.addWidget(h_widget, 0, 0, 1, 1)

        self.table = QTableWidget(len(self.scripts), 3)
        self.table.setHorizontalHeaderLabels(["Script", "Status", "Action"])
        self.table.setColumnWidth(0, 120)
        self.table.setFixedSize(400, 200)
        h_layout.addWidget(self.table, 0, 0, 2, 2)

        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setFixedSize(200, 250)
        self.update_config_display()
        h_layout.addWidget(self.config_text, 0, 2, 3, 1)

        # Add button to open config file
        open_config_btn = QPushButton("Open Config")
        open_config_btn.clicked.connect(self.open_config_file)
        h_layout.addWidget(open_config_btn, 2, 0, 1, 1)

        for i, script in enumerate(self.scripts):
            widget = QWidget()
            self.process_widgets.append(widget)
            r, c, rs, cs = self.row_column_spans[i]
            main_layout.addWidget(widget, r, c, rs, cs)
            widget.setFixedSize(self.window_sizes[i][0], self.window_sizes[i][1])

        self.init_table()

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.check_processes)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def init_table(self):
        for row, script in enumerate(self.scripts):
            self.table.setItem(row, 0, QTableWidgetItem(self.script_names[row]))

            status_button = QPushButton("STOPPED")
            status_button.setStyleSheet("background-color: red; color: white")
            status_button.setEnabled(False)
            self.table.setCellWidget(row, 1, status_button)

            button = QPushButton("Start")
            button.clicked.connect(partial(self.toggle_process, script, self.window_name[row], row))
            self.table.setCellWidget(row, 2, button)

    def toggle_process(self, script_name, window_name, row):
        status_button = self.table.cellWidget(row, 1)
        button = self.table.cellWidget(row, 2)

        if status_button.text() == "STOPPED":
            start_cmd(script_name, window_name, int(self.process_widgets[row].winId()), self.window_sizes[row])
            status_button.setText("RUNNING")
            status_button.setStyleSheet("background-color: green; color: white")
            self.start_blinking(status_button)
            button.setText("Stop")
        else:
            self.kill_process(script_name)
            status_button.setText("STOPPED")
            status_button.setStyleSheet("background-color: red; color: white")
            self.stop_blinking(status_button)
            button.setText("Start")

    def kill_process(self, script_name):
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['cmdline'] and script_name in proc.info['cmdline']:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def start_blinking(self, button):
        timer = QTimer(button)
        timer.timeout.connect(lambda: self.toggle_blink(button))
        timer.start(500)
        button.blink_timer = timer
        button.blink_state = True

    def stop_blinking(self, button):
        if hasattr(button, 'blink_timer'):
            button.blink_timer.stop()
            del button.blink_timer
            button.setStyleSheet("background-color: red; color: white")

    def update_config_display(self):
        config_text = f"""Configuration Settings:
    Margin: {Config.leverage}
    BB std: {Config.bb_stddev}
    RSI Period: {Config.rsi_period}
    RSI Long > {int(Config.rsi_long)}
    RSI Short < {int(Config.rsi_short)}
    Distance: {Config.distance}
    N1: {Config.n1}
    N2: {Config.n2}
    SL: {Config.sl_ratio}
    TP1: {Config.tp1_ratio}
    TP2: {Config.tp2_ratio}"""

        self.config_text.setText(config_text)

    def toggle_blink(self, button):
        if button.blink_state:
            button.setStyleSheet("background-color: darkgreen; color: white")
        else:
            button.setStyleSheet("background-color: green; color: white")
        button.blink_state = not button.blink_state

    def open_config_file(self):
        subprocess.run(['notepad.exe', 'Ini/Algorithm.ini'])
        self.update_config_display()

    def check_processes(self):

        while self.monitoring:
            for row, script in enumerate(self.scripts):
                status_button = self.table.cellWidget(row, 1)
                action_button = self.table.cellWidget(row, 2)

                alive_file = os.path.join("Data/" + self.data_folder, self.alive_files[row])

                if not os.path.exists(alive_file):
                    continue
                current_time = datetime.now()
                try:
                    with open(alive_file, 'r') as f:
                        counter = int(f.read().strip())
                        if counter == self.last_alive[row]:
                            if (current_time - self.alive_time[row]).seconds > 2:
                                found = False
                            else:
                                found = True
                        else:
                            self.last_alive[row] = counter
                            self.alive_time[row] = current_time
                            found = True
                except:
                    found = False
                if found:
                    if status_button.text() != "RUNNING":
                        status_button.setText("RUNNING")
                        status_button.setStyleSheet("background-color: green; color: white")
                        self.start_blinking(status_button)
                        action_button.setText("Stop")
                else:
                    if status_button.text() != "STOPPED":
                        status_button.setText("STOPPED")
                        self.stop_blinking(status_button)
                        status_button.setStyleSheet("background-color: red; color: white")
                        action_button.setText("Start")

            time.sleep(0.2)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    extra = {
        'font_family': 'Consolas',
        'font_size': 14,
    }
    apply_stylesheet(app, theme='dark_yellow.xml', extra=extra)

    window = ProcessMonitor()
    window.show()
    sys.exit(app.exec_())