import sys
from queue import Queue
import pandas as pd
from RealServer.Common import open_limit, open_take_profit, cancel_order, open_stop_loss
from Server.Binance.BinanceTestServer import BinanceTestServer, ORDER_ACTION, ServerOrderMessage
from Server.Binance.Types.Order import ORDER_TYPE
from Server.Binance.Types.Position import POSITION_SIDE
from Tool import log_order
from logger import print_log_error, log_error


class BinanceServer:
    """Handles the connection to Server API."""
    symbol = "BTCUSDT"

    def __init__(self):
        super().__init__()
        self.running = None
        self.sub_server = BinanceTestServer(True)
        self.websocket_thread = None
        self.client = None
        self.ws_counter = -1
        self.ws_queue = Queue()

    def process_message(self, message):
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
                if order_id == order.id:
                    m = ServerOrderMessage(action, order)
                    self.sub_server.handel_message(m)
                    self.ws_queue.put(m)



        except:
            log_error()

    def open_order(self, order_type, side, amount, entry, reduce_only =False):
        """Opens a new order."""
        with self.sub_server.lock:
            self.sub_server.open_order(order_type, side, amount, entry, reduce_only)
            if order_type == ORDER_TYPE.LIMIT:
                order_id =  open_limit(self.symbol, "LONG" if side == POSITION_SIDE.LONG else "SHORT", amount, entry)
            elif order_type == ORDER_TYPE.TP:
                order_id =   open_take_profit(self.symbol, "LONG" if side == POSITION_SIDE.LONG else "SHORT", amount, entry)
            elif order_type == ORDER_TYPE.SL:
                order_id =   open_stop_loss(self.symbol, "LONG" if side == POSITION_SIDE.LONG else "SHORT", amount, entry)
            else:
                assert False, "Invalid order type."
            if order_id is None:
                log_order("ERROR", self.sub_server.order_list[-1], self.sub_server.get_current_time())
                sys.exit(1)
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
        """Reads 5-minute interval close prices from CSV file."""
        try:
            import pandas as pd
            from datetime import datetime

            # Generate current date string
            current_date = datetime.now().strftime('%d_%m_%y')

            # Read CSV file with current date
            df = pd.read_csv(f'price_{current_date}.csv', names=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')

            # Set timestamp as index and resample to 5-minute intervals
            df.set_index('timestamp', inplace=True)
            df_5min = df.resample('5min').last()

            # Get last param (or 20 if param is None) prices
            limit = param if param else 20
            close_prices = df_5min['price'].tail(limit).tolist()

            return close_prices

        except:
            log_error()
            return []

    def tick(self):
        try:
            # Read CSV file
            df = pd.read_csv('websocket.csv', names=['counter','time', 'message'])
            #first connect
            if self.ws_counter == -1:
                self.ws_counter = df.iloc[-1]['counter']
                return
            # nothing change
            if self.ws_counter == df.iloc[-1]['counter']:
                return
            while True:
                # Get messages with counter greater than current
                new_messages = df[df['counter'] > self.ws_counter]

                if new_messages.empty:
                    break

                # Process each new message
                for _, row in new_messages.iterrows():
                    message = eval(row['message'])
                    self.process_message(message)
                    self.ws_counter = row['counter']
                break

        except Exception as e:
            log_error()

        self.sub_server.tick()
        return

    def get_total(self):
        return 1000000000