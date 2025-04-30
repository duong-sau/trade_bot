import os
import sys
from datetime import datetime
from queue import Queue

import ccxt
import pandas as pd

from RealServer import api_key, api_secret, testnet
from RealServer.Common import open_limit, open_take_profit, cancel_order, open_stop_loss, SetClient
from Server.Binance.BinanceTestServer import BinanceTestServer, ORDER_ACTION, ServerOrderMessage
from Server.Binance.Types.Order import ORDER_TYPE
from Server.Binance.Types.Position import POSITION_SIDE
from Tool import log_order, get_window_klines, get_data_folder_path
from logger import print_log_error, log_error


class BinanceServer:
    """Handles the connection to Server API."""
    symbol = "BTCUSDT"

    def __init__(self):
        super().__init__()

        self.websocket_file = os.path.join(get_data_folder_path(), "websocket.csv")

        client = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'future', 'adjustForTimeDifference': True},
        })
        client.set_sandbox_mode(testnet)
        SetClient(client)

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
        try:
            prices, _ = get_window_klines(param)
            return prices
        except:
            log_error()
            return []

    def tick(self):
        try:
            # Read CSV file
            df = pd.read_csv(self.websocket_file, names=['counter','time', 'message'])
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

    def get_current_time(self):
        return datetime.now()