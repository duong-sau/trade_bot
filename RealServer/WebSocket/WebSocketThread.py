from PyQt5.QtCore import pyqtSignal, QThread

from Logic.logger import print_log_info


class CSocketThread(QThread):
    """
    CSocketThread is a class that handles the WebSocket connection to Server.
    When receiving a message, it emits to BinanceThread.
    """

    order_trigger_signal = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        print_log_info('start socket')
        depth_stream_name = self
        print_log_info('init socket')



    def stop(self):
        self.socket.stop()

    def run(self) -> None:
        self.socket.join()

    def get_socket(self):
        return self.socket


def test_websocket():
    web_socket = CSocketThread()
    web_socket.get_socket().join()