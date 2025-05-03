import asyncio
import datetime
import threading
from enum import Enum
from queue import Queue

from tqdm import tqdm

from RealServer.Binance import BinanceServer
from Server.Binance.TestServer import TestServer
from Server.Binance.Types.Position import Position, POSITION_SIDE
from Server.Binance.Kline.KlineServer import KlineServer
from Server.Binance.Types.Order import Order, ORDER_TYPE
from Server.Binance.Types.User import User
from Tool import log_order, log_action


class ORDER_ACTION(Enum):
    FILLED = 1
    CANCELLED = 2

class ServerOrderMessage:
    def __init__(self, action, order):
        self.action = action
        self.order = order

class BinanceTestServer:
    user = None
    # sl_ratio = 0.3 / 100

    def __init__(self, test):
        self.test = test
        if self.test:
            self.klines_server = TestServer()
        else:
            self.klines_server = BinanceServer()

        self.user = User()

        self.position = Position()
        self.order_list = []
        self.ws_queue = Queue()
        self.lock = threading.Lock()

    # Private API ----------------------------------------------------
    def tick(self):

        self.klines_server.tick()

        while self.klines_server.ws_queue.qsize() > 0:
            message = self.klines_server.ws_queue.get()
            self.handel_message(message)

        sl  = 0
        tp = 0
        for order in self.order_list:
            if order.type == ORDER_TYPE.TP:
                tp = order.trigger_price
            elif order.type == ORDER_TYPE.SL:
                sl = order.trigger_price
        if self.position.side != POSITION_SIDE.NONE:
            self.position.update_tp_sl(tp, sl)
        else:
            self.position.update_tp_sl(0,0)
        return


    def action_when_filled(self, order, current):
        log_order("FILLED", order, self.get_current_time())

        self.ws_queue.put(ServerOrderMessage(ORDER_ACTION.FILLED, order))
        if order.type == ORDER_TYPE.LIMIT:
            self.position.extend(order)
        else:
            self.position.remove(order)
            self.user.add_profit(self.position.get_profit(current), self, test=self.test)

    # Public Order API --------------------------------------------------------------------------------------------------------------------
    def open_order(self, order_type, side, amount, entry, reduce_only =False):

            order = Order(order_type, side, amount, entry, reduce_only)
            log_order("PLACED", order, self.get_current_time())

            order_id = self.klines_server.open_order(order_type, side, amount, entry, reduce_only)
            if not order_id:
                log_order("ERROR", order, self.get_current_time())
                self.position.reset()
                self.order_list = []
                return False


            order.id = order_id

            self.order_list.append(order)
            return order.id

    def cancel_order(self, order_id):
        with self.lock:
            for order in self.order_list:
                if order.id == order_id:
                    log_order(f"CANCLD",order, self.get_current_time())
            if self.klines_server.cancel_order(order_id):
                return True

            log_action(f"ERROR WHEN CANCEL_ORDER - ID: {order_id}", self.get_current_time())
            self.position.reset()
            self.order_list = []
            return False
    # Public -----------------------------------------------------------------------------------------------------------

    def get_current(self):
        return self.klines_server.get_current_price()

    def get_current_time(self):
        return self.klines_server.get_current_time()

    def get_window_klines(self, limit):
        return self.klines_server.get_window_klines(limit)

    def get_budget(self):
        return self.user.budget

    def get_total(self):
        return self.klines_server.get_total()

    # API from server ----------------------------------------------------------------------------------------------------
    def handel_message(self, msg):
        """Handles WebSocket events."""
        order_id, event, price = str(msg['i']), msg['X'], msg['p']

        action = None
        # put to queue
        if event == "FILLED":
            action = ORDER_ACTION.FILLED

        elif event == "CANCELED":
            action = ORDER_ACTION.CANCELLED

        if action is None:
            return

        for order in self.order_list:
            if order_id == order.id:
                if action == ORDER_ACTION.FILLED:
                    self.action_when_filled(order, self.get_current())
                    self.order_list.remove(order)
                elif action == ORDER_ACTION.CANCELLED:
                    self.order_list.remove(order)
                    # self.ws_queue.put(ServerOrderMessage(ORDER_ACTION.CANCELLED, order))

