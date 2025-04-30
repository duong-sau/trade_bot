import sys
import os
import time
import ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTableWidget, \
    QTableWidgetItem, QGridLayout
from qt_material import apply_stylesheet


# Hàm khởi chạy CMD và lấy handle
def start_cmd(script_name, window_name, container_hwnd, window_size):
    # Mở CMD và chạy script
    # cd /d "{os.getcwd()}" &&
    # os.system(f'start cmd /k python "{script_name}"')
    os.system(f'start cmd /k "cd /d {os.getcwd()} & python {script_name} & exit"')

    for _ in range(30):
        time.sleep(1)  # Đợi CMD mở
        # Tìm handle của CMD
        hwnd = ctypes.windll.user32.FindWindowW(None, f"{window_name}")
        if hwnd:
            # Nhúng cửa sổ CMD vào widget container
            ctypes.windll.user32.SetParent(hwnd, container_hwnd)
            ctypes.windll.user32.MoveWindow(hwnd, 0, 0, window_size[0], window_size[1], True)  # Điều chỉnh kích thước CMD trong widget
            break


# Tạo giao diện chính
class ProcessMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Monitor")
        self.setGeometry(0, 0, 1200, 800)

        # Danh sách script
        self.scripts = ['Price.py', 'Main.py', 'Websocket.py', "Visualizer.py"]
        self.window_name = ['Price', 'Main', 'Websocket', "Figure 1"]
        self.row_column_spans = [(2, 2, 1, 1), (0, 1, 1, 2), (1, 2, 1, 1), (1, 0, 2, 2)]  # Các ô trong grid
        self.window_sizes = [(600, 300), (1200, 300), (600, 300), (1200, 600)]  # Kích thước của các widget
        self.process_widgets = []  # Lưu các widget chứa CMD

        # Widget chính
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout chính sử dụng Grid
        main_layout = QGridLayout(self.central_widget)

        # Bảng hiển thị trạng thái
        self.table = QTableWidget(len(self.scripts), 3)
        self.table.setHorizontalHeaderLabels(["Script", "Status", "Action"])
        self.table.setFixedSize(600, 300)
        main_layout.addWidget(self.table, 0, 0, 1, 1)

        # Thêm các ô widget chứa CMD vào grid
        for i, script in enumerate(self.scripts):
            widget = QWidget()
            self.process_widgets.append(widget)
            r, c, rs, cs = self.row_column_spans[i]
            main_layout.addWidget(widget, r, c, rs, cs)
            widget.setFixedSize(self.window_sizes[i][0], self.window_sizes[i][1])

        # Khởi tạo trạng thái ban đầu
        self.init_table()

    def init_table(self):
        for row, script in enumerate(self.scripts):
            # Cột 1: Script name
            self.table.setItem(row, 0, QTableWidgetItem(script))

            # Cột 2: Status
            self.table.setItem(row, 1, QTableWidgetItem("STOPPED"))

            # Cột 3: Action Button
            button = QPushButton("Start")
            button.clicked.connect(lambda checked, s=script,w=self.window_name[row], r=row: self.toggle_process(s,w, r))
            self.table.setCellWidget(row, 2, button)

    def toggle_process(self, script_name,window_name, row):
        status_item = self.table.item(row, 1)
        button = self.table.cellWidget(row, 2)

        if status_item.text() == "STOPPED":
            # Start process và nhúng CMD vào widget
            start_cmd(script_name,window_name, int(self.process_widgets[row].winId()), self.window_sizes[row])
            status_item.setText("RUNNING")
            button.setText("Stop")
        else:
            # Dừng process
            self.kill_process(script_name)
            status_item.setText("STOPPED")
            button.setText("Start")

    def kill_process(self, script_name):
        # Dừng tất cả các process chạy script
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['cmdline'] and script_name in proc.info['cmdline']:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)

    extra = {
        # Font
        'font_family': 'Consolas',
        'font_size': 14,
    }
    apply_stylesheet(app, theme='dark_yellow.xml', extra=extra)

    window = ProcessMonitor()
    window.show()
    sys.exit(app.exec_())
