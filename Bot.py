
import subprocess
from _winapi import CREATE_NEW_CONSOLE
import sys
import os
import time
import ctypes
import threading
from datetime import datetime
import Config

from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QPushButton, QTableWidget, QTableWidgetItem, QGridLayout, QTextEdit
from qt_material import apply_stylesheet
from functools import partial

from Tool import get_data_folder_path, ALIVE_CMD, write_alive_cmd


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
        self.h = 1080
        self.w = 1920
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
        # f'start cmd /k "cd /d {os.getcwd()} & {script_name} & exit"'
        self.scripts = [f'cmd /k python Price.py {self.data_folder}',
                        f'cmd /k python Websocket.py {self.data_folder}',
                        f"pythonw Visualizer.py {self.data_folder}",
                        f'cmd /k python Main.py {self.data_folder}'
                        ]
        self.window_name = ['Price', 'Websocket', "Figure 1", 'Main']
        self.row_column_spans = [(2, 2, 1, 1), (1, 2, 1, 1), (1, 0, 2, 2), (0, 1, 1, 2)]
        unit_tp = (int(self.w/3), int(self.h/3))
        self.window_sizes = [unit_tp, unit_tp, (int(self.w/3*2), int(self.h/3*2)), (int(self.w/3*2), int(self.h/3))]
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

        self.table = QTableWidget(len(self.scripts), 3)
        self.table.setHorizontalHeaderLabels(["Script", "Status", "Action"])
        self.table.setColumnWidth(0, 90)
        self.table.setFixedSize(300, 250)
        tb_config_layout.addWidget(self.table)

        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setFixedSize(300, 250)
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

        stop_all_button = QPushButton("Stop All")
        stop_all_button.clicked.connect(self.stop_all_process)
        button_layout.addWidget(stop_all_button)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.quit)
        button_layout.addWidget(quit_button)

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
        self.table.verticalHeader().setVisible(False)

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
            start_cmd(script_name, window_name, int(self.process_widgets[row].winId()), self.window_sizes[row], self.proc_Alive_cmd_name[row])
            status_button.setText("RUNNING")
            status_button.setStyleSheet("background-color: green; color: white")
            button.setText("Stop")
        else:
            kill_process(self.proc_id[row])
            status_button.setText("STOPPED")
            status_button.setStyleSheet("background-color: red; color: white")
            button.setText("Start")

    def update_config_display(self):
        config_text = f"""Margin: {Config.leverage}
BB: {Config.bb_period} - std: {Config.bb_stddev}
RSI: {Config.rsi_period}
RSI Long  < {int(Config.rsi_long)}
RSI Short > {int(Config.rsi_short)}
Distance  > {Config.distance}
N1: {Config.n1} - N2: {Config.n2}
TP1: {Config.tp1_ratio* 100}% - TP2: {Config.tp2_ratio* 100}%
limit1_timeout: {Config.limit_timeout}
tp2_decree: after {Config.tp_timeout}m, with {Config.tp_decrease_time}m interval decrease by {Config.tp_decrease_step * 100}%
tp2_min: {Config.tp_min* 100}%
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
        for row, script in enumerate(self.scripts):
            start_cmd(script, self.window_name[row], int(self.process_widgets[row].winId()), self.window_sizes[row], self.proc_Alive_cmd_name[row])

    def stop_all_process(self):
        for row, script in enumerate(self.scripts):
            kill_process(self.proc_Alive_cmd_name[row])

    def quit(self):
        self.stop_all_process()
        self.monitoring = False
        self.close()
        QApplication.quit()

    def check_processes(self):

        while self.monitoring:
            for row, script in enumerate(self.scripts):
                status_button = self.table.cellWidget(row, 1)
                action_button = self.table.cellWidget(row, 2)

                alive_file = os.path.join(f"{Config.DATA_PATH}/" + self.data_folder, self.alive_files[row])

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
                        action_button.setText("Stop")
                else:
                    if status_button.text() != "STOPPED":
                        status_button.setText("STOPPED")
                        status_button.setStyleSheet("background-color: red; color: white")
                        action_button.setText("Start")

            time.sleep(0.2)

if __name__ == "__main__":
    # if not ctypes.windll.shell32.IsUserAnAdmin():
    #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    #     sys.exit()
    # if not ctypes.windll.shell32.IsUserAnAdmin():
    #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    #     sys.exit()
    app = QApplication(sys.argv)

    extra = {
        'font_family': 'Consolas',
        'font_size': 14,
    }
    apply_stylesheet(app, theme='dark_yellow.xml', extra=extra)
    window = ProcessMonitor()
    window.showFullScreen()
    window.show()
    app.exec()