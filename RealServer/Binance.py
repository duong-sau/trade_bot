import time
from queue import Queue

from RealServer import web_socket, client
from RealServer.BinanceControl.Common import open_limit, open_take_profit, cancel_order
from Server.Binance.BinanceTestServer import BinanceTestServer, ORDER_ACTION
from Server.Binance.Types.Order import ORDER_TYPE
from Server.Binance.Types.Position import POSITION_SIDE
from logger import print_log_error, log_error


class BinanceServer:
    """Handles the connection to Server API."""
    symbol = "BTCUSDT"

    def __init__(self):
        super().__init__()
        self.running = None
        self.sub_server = BinanceTestServer()
        self.websocket_thread = None
        self.client = None

        self.ws_queue = Queue()

    def run(self):
        web_socket.start_futures_user_socket(callback=self.process_message)
        while True:
            """Runs the thread."""
            if not self.running:
                break
            print('Client is still running')
            time.sleep(1)
            """Runs the thread."""

    def stop(self):
        """Stops the thread."""
        self.running = False

    def process_message(self, message):
        # print_log_info(message)
        try:
            if message['e'] == 'ORDER_TRADE_UPDATE':
                self.handle_socket_event(message['o'])
            elif message['e'] == 'error':
                print_log_error(message)
        except:
            log_error()

    def handle_socket_event(self, msg):
        """Handles WebSocket events."""
        try:
            order_id, event, price = str(msg['i']), msg['X'], msg['p']

            action = None
            # put to queue
            if event == "FILLED":
                action = ORDER_ACTION.FILLED

            elif event == "CANCELED":
                action = ORDER_ACTION.CANCELLED

            if action is None:
                return

            for order in self.sub_server.order_list:
                if order_id == order_id:
                    order.handel(action, price)
                    self.ws_queue.put(action, order)



        except:
            log_error()

    def open_order(self, order_type, side, amount, entry, reduce_only =False):
        """Opens a new order."""
        self.sub_server.open_order(order_type, side, amount, entry, reduce_only)
        if order_type == ORDER_TYPE.LIMIT:
            order_id =  open_limit(self.symbol, "BUY" if side == POSITION_SIDE.LONG else "SELL", amount, entry)
        elif order_type == ORDER_TYPE.TP:
            order_id =   open_take_profit(self.symbol, "SELL" if side == POSITION_SIDE.LONG else "BUY", amount, entry)
        elif order_type == ORDER_TYPE.SL:
            order_id =   open_take_profit(self.symbol, "SELL" if side == POSITION_SIDE.LONG else "BUY", amount, entry)
        else:
            assert False, "Invalid order type."

        self.sub_server.order_list[-1].id = order_id # replace the order id with the one from the server
        return order_id

    def cancel_order(self, order_id):
        """Cancels an order."""
        self.sub_server.cancel_order(order_id)
        return cancel_order(self.symbol, order_id)

    def set_margin(self, data):
        """Sets the margin for the order."""
        pass
    
    
    def get_window_klines(self, param):
        """Fetches the last klines from Binance."""
        try:
            symbol = "BTC/USDT"  # Default trading pair
            timeframe = "5m"  # Default timeframe
            limit = param if param else 20  # Use param or default to 20

            klines = client.fetch_ohlcv(symbol, timeframe, limit=limit)
            close_prices = [kline[4] for kline in klines]
            return close_prices

        except:
            log_error()
            return []

    def tick(self):
        return

    def get_total(self):
        return 1000000000