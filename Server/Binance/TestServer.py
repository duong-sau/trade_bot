import asyncio
import datetime
import threading
from enum import Enum
from queue import Queue

from tqdm import tqdm

from RealServer.Binance import BinanceServer
from Server.Binance.Types.Position import Position, POSITION_SIDE
from Server.Binance.Kline.KlineServer import KlineServer
from Server.Binance.Types.Order import Order, ORDER_TYPE
from Server.Binance.Types.User import User
from Tool import log_order


class TestServer:

    def __init__(self):

        self.klines_server = KlineServer()
        self.order_list = []
        self.ws_queue = Queue()


    # Private API ----------------------------------------------------
    def tick(self):

        self.klines_server.tick()
        current = self.klines_server.get_current_price()
        self.check_order(current)
        return


    def check_order(self, current):
        for order in self.order_list:
            if order.check_fill(current):
                self.action_when_filled(order, current)

    def action_when_filled(self, order, current):
        order_id, event, price = order.id, "FILLED", current
        message = {
            'i': order_id,
            'X': event,
            'p': price
        }
        self.ws_queue.put(message)
        self.order_list.remove(order)

    # Public Order API --------------------------------------------------------------------------------------------------------------------
    def open_order(self, order_type, side, amount, entry, reduce_only =False):
        order = Order(order_type, side, amount, entry, reduce_only)
        self.order_list.append(order)
        return order.id

    def cancel_order(self, order_id):
        for order in self.order_list:
            if order.id == order_id:
                order_id, event, price = order.id, "CANCELED", 0
                message = {
                    'i': order_id,
                    'X': event,
                    'p': price
                }
                self.ws_queue.put(message)
                self.order_list.remove(order)
                return True
        return False

    # Public -----------------------------------------------------------------------------------------------------------

    def get_current_price(self):
        return self.klines_server.get_current_price()

    def get_current_time(self):
        return self.klines_server.get_current_time()

    def get_window_klines(self, limit):
        return self.klines_server.get_window_kline(limit)

    # def get_budget(self):
    #     return self.user.budget

    def get_total(self):
        return self.klines_server.get_total()

    def set_leverage(self, leverage):
        return
    def pre_check(self):
        return
