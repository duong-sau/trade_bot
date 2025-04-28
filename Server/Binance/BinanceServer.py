from enum import Enum
from queue import Queue

from tqdm import tqdm
from Server.Binance.Types.Position import Position
from Server.Binance.Kline.KlineServer import KlineServer
from Server.Binance.Types.Order import Order, ORDER_TYPE, ORDER_SIDE
from Server.Binance.Types.User import User
from Tool import log_order


class ORDER_ACTION(Enum):
    FILLED = 1
    CANCELLED = 2

class ServerOrderMessage:
    def __init__(self, action, order):
        self.action = action
        self.order = order

class BinanceServer:
    main_thread = None
    klines_server = None
    user = None

    so_lenh = 0


    # sl_ratio = 0.3 / 100

    def __init__(self):

        self.klines_server = KlineServer()
        self.user = User()

        self.position = Position()
        self.order_list = []
        self.ws_queue = Queue()

    # Private API ----------------------------------------------------
    def tick(self):
        self.klines_server.up_tick()
        current = self.klines_server.get_current_price()
        self.check_order(current)

        sl  = 0
        tp = 0
        for order in self.order_list:
            if order.type == ORDER_TYPE.TP:
                tp = order.trigger_price
            elif order.type == ORDER_TYPE.SL:
                sl = order.trigger_price
        if self.position.side != ORDER_SIDE.NONE:
            self.position.update_tp_sl(tp, sl)
        return


    def check_order(self, current):
        for order in self.order_list:
            if order.check_fill(current):
                log_order("FILLED", order, self.get_current_time())

                self.ws_queue.put(ServerOrderMessage(ORDER_ACTION.FILLED, order))
                if order.type == ORDER_TYPE.LIMIT:
                    self.position.extend(order)
                    self.order_list.remove(order)
                else:
                    self.position.remove(order)
                    self.user.add_profit(self.position.get_profit(current), self)
                    self.order_list.remove(order)


    # Public Order API --------------------------------------------------------------------------------------------------------------------
    def open_order(self, order_type, side, amount, entry, reduce_only =False):

        order = Order(order_type, side, amount, entry, reduce_only)
        log_order("PLACED", order, self.get_current_time())

        self.order_list.append(order)
        return order.id

    def cancel_order(self, order_id):
        for order in self.order_list:
            if order.id == order_id:
                log_order("CANCLD", order, self.get_current_time())
                self.order_list.remove(order)
                self.ws_queue.put(ServerOrderMessage(ORDER_ACTION.CANCELLED, order))
                break



    # Public -----------------------------------------------------------------------------------------------------------

    def get_current(self):
        return self.klines_server.get_current_price()

    def get_current_time(self):
        return self.klines_server.get_current_time()

    def get_window_klines(self, limit):
        return self.klines_server.get_window_price(limit)

    def get_budget(self):
        return self.user.budget

    def get_total(self):
        return self.klines_server.get_total()

