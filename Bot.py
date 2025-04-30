import sys
import subprocess
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtCore import QTimer


# Kiểm tra trạng thái của script
def is_process_running(script_name):
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['cmdline'] and script_name in proc.info['cmdline']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


# Chạy process
def run_process(script_name):
    if not is_process_running(script_name):
        return subprocess.Popen([sys.executable, script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return None


# Dừng process
def kill_process(script_name):
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['cmdline'] and script_name in proc.info['cmdline']:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


# Tạo giao diện chính
class ProcessMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Monitor")
        self.setGeometry(100, 100, 600, 400)

        # Danh sách script
        self.scripts = ['Price.py', 'Main.py', 'Websocket.py']

        # Widget chính
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Bảng hiển thị trạng thái
        self.table = QTableWidget(len(self.scripts), 3)
        self.table.setHorizontalHeaderLabels(["Script", "Status", "Action"])
        self.layout.addWidget(self.table)

        # Nút cập nhật trạng thái
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_status)
        self.layout.addWidget(self.refresh_button)

        # Cập nhật trạng thái định kỳ
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

        # Khởi tạo trạng thái ban đầu
        self.update_status()

    def update_status(self):
        for row, script in enumerate(self.scripts):
            # Cột 1: Script name
            self.table.setItem(row, 0, QTableWidgetItem(script))

            # Cột 2: Status
            status = "RUNNING" if is_process_running(script) else "STOPPED"
            self.table.setItem(row, 1, QTableWidgetItem(status))

            # Cột 3: Action Button
            button = QPushButton("Stop" if status == "RUNNING" else "Start")
            button.clicked.connect(lambda checked, s=script: self.toggle_process(s))
            self.table.setCellWidget(row, 2, button)

    def toggle_process(self, script_name):
        if is_process_running(script_name):
            kill_process(script_name)
        else:
            run_process(script_name)
        self.update_status()


# Chạy ứng dụng
def main():
    app = QApplication(sys.argv)
    window = ProcessMonitor()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
