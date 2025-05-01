import Config
from RealServer.Binance import BinanceServer
from Server.Binance.BinanceTestServer import BinanceTestServer, ORDER_ACTION
from Server.Binance.Types.Order import ORDER_TYPE
from Server.Binance.Types.Position import POSITION_SIDE
from Tool import log_action


class DCA:

    def __init__(self, price, position,  volume):
        self.price = price
        self.position = position
        self.volume = volume


def create_volumes(volume, n):
    volumes = [float(volume)]
    for i in range(n -1):
        volumes.append(float(volumes[-1]) * 4)
    return volumes


class TRADE_STEP:
    NONE = 0
    LIMIT1_FILLED = 1
    LIMIT2_FILLED = 2
    ALL_CLOSED = 3


class DCAServer:

    tp1_ratio = Config.tp1_ratio / 100
    tp2_ratio = Config.tp2_ratio / 100

    def __init__(self):
        # self.binance_server = BinanceTestServer()
        self.binance_server = BinanceServer()
        self.DACS = []
        self.khop_lenh = False
        self.position = POSITION_SIDE.NONE
        self.name = ""

        self.tp1_val = 0
        self.tp2_val = 0
        self.sl_val = 0

        self.limit1 = None
        self.limit2 = None

        self.tp1 = None
        self.tp2 = None

        self.sl = None

        self.last_trade_time = None
        self.trade_step = TRADE_STEP.NONE

        self.current_tp1_ratio = 0
        self.current_tp2_ratio = 0

        self.limit2_filled_time = None

    def put_long(self, dca_s, n, volumes):

        self.log_dca_opened()
        self.current_tp1_ratio = self.tp1_ratio
        self.current_tp2_ratio = self.tp2_ratio

        self.last_trade_time = self.binance_server.get_current_time()

        assert self.khop_lenh == False
        self.position = POSITION_SIDE.LONG
        self.trade_step = TRADE_STEP.NONE

        self.dcas = dca_s
        self.volumes = volumes

        self.sl_val = round(dca_s[-1], 1)
        self.tp1_val = round(dca_s[0] * (1 + self.tp1_ratio), 1)
        self.tp2_val = round((dca_s[0] * volumes[0] + dca_s[1] * volumes[1]) / (volumes[0] + volumes[1]) * (1 + self.tp2_ratio), 1)

        vl = volumes[0]
        entry = dca_s[0]
        self.limit1 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.LONG, amount=vl, entry=entry, reduce_only=False)
        if not self.limit1:
            self.reset_dca_by_error()
            return

        vl = volumes[1]
        entry = dca_s[1]
        self.limit2 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.LONG, amount=vl,
                                                     entry=entry, reduce_only=False)
        if not self.limit2:
            self.reset_dca_by_error()
            return

    def put_short(self, dca_s, n,  volumes):

        self.log_dca_opened()

        self.current_tp1_ratio = self.tp1_ratio
        self.current_tp2_ratio = self.tp2_ratio

        assert self.khop_lenh == False
        self.position = POSITION_SIDE.SHORT
        self.trade_step = TRADE_STEP.NONE

        self.last_trade_time = self.binance_server.get_current_time()

        self.dcas = dca_s
        self.volumes = volumes
        self.sl_val = round(dca_s[-1], 1)

        self.tp1_val = round(dca_s[0] * (1 - self.tp1_ratio), 1)
        self.tp2_val = round((dca_s[0] * volumes[0] + dca_s[1] * volumes[1]) / (volumes[0] + volumes[1]) * (1 - self.tp2_ratio), 1)

        vl = volumes[0]
        entry = dca_s[0]
        self.limit1 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.SHORT, amount=vl, entry=entry, reduce_only=False)
        if not self.limit1:
            self.reset_dca_by_error()
            return

        vl = volumes[1]
        entry = dca_s[1]
        self.limit2 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.SHORT, amount=vl,
                                                     entry=entry, reduce_only=False)
        if not self.limit2:
            self.reset_dca_by_error()
            return

    def cancel_by_timeout(self):
        self.DACS = []
        self.position = POSITION_SIDE.NONE

        self.last_trade_time = None
        if self.trade_step == TRADE_STEP.NONE:
            if not self.binance_server.cancel_order(self.limit1):
                self.error()
                return
            if not self.binance_server.cancel_order(self.limit2):
                self.error()
                return

        self.trade_step = TRADE_STEP.NONE

        self.log_dca_closed()

    def get_limit2_filled_time(self):
        if self.trade_step != TRADE_STEP.LIMIT2_FILLED:
            return None
        return self.binance_server.get_current_time() - self.limit2_filled_time

    def decrease_tp(self):

        if self.current_tp1_ratio <= 1/100:
            return

        if self.trade_step == TRADE_STEP.LIMIT2_FILLED:
            if self.position == POSITION_SIDE.LONG:
                self.current_tp2_ratio = self.current_tp2_ratio - 1/100
                self.binance_server.cancel_order(self.tp2)
                self.tp2_val = round(self.tp2_val * (1 + self.current_tp2_ratio), 1)
                self.tp2 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position, amount=self.volumes[0] + self.volumes[1], entry=self.tp2_val, reduce_only=True)
                if not self.tp2:
                    self.reset_dca_by_error()
                    return
                self.limit2_filled_time = self.binance_server.get_current_time()
            elif self.position == POSITION_SIDE.SHORT:
                self.current_tp2_ratio = self.current_tp2_ratio - 1/100
                self.binance_server.cancel_order(self.tp2)
                self.tp2_val = round(self.tp2_val * (1 - self.current_tp2_ratio), 1)
                self.tp2 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position, amount=self.volumes[0] + self.volumes[1], entry=self.tp2_val, reduce_only=True)
                self.limit2_filled_time = self.binance_server.get_current_time()

    def handel_message(self, message):
        # log_order("HERE", message.order, self.binance_server.sub_server.get_current_time())
        if message.action == ORDER_ACTION.FILLED:
            if message.order.type == ORDER_TYPE.LIMIT:
                if message.order.id == self.limit1:
                    self.sl = self.binance_server.open_order(order_type=ORDER_TYPE.SL, side=self.position, amount=message.order.amount, entry=self.sl_val, reduce_only=True)
                    if not self.sl:
                        self.reset_dca_by_error()
                        return
                    self.tp1 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position,
                                                              amount=message.order.amount, entry=self.tp1_val,
                                                              reduce_only=True)
                    if not self.tp1:
                        self.reset_dca_by_error()
                        return
                    self.trade_step = TRADE_STEP.LIMIT1_FILLED
                if message.order.id == self.limit2:
                    volume = self.volumes[0] + self.volumes[1]

                    self.tp2 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position,
                                                              amount=volume, entry=self.tp2_val, reduce_only=True)
                    if not self.tp2:
                        self.reset_dca_by_error()
                        return
                    self.binance_server.cancel_order(self.tp1)
                    self.tp1 = None

                    self.binance_server.cancel_order(self.sl)
                    self.sl = self.binance_server.open_order(order_type=ORDER_TYPE.SL, side=self.position,
                                                             amount=volume, entry=self.sl_val, reduce_only=True)
                    if not self.sl:
                        self.reset_dca_by_error()
                        return
                    self.trade_step = TRADE_STEP.LIMIT2_FILLED
                    self.limit2_filled_time = self.binance_server.get_current_time()

            elif message.order.type == ORDER_TYPE.TP:
                if message.order.id == self.tp1 or message.order.id == self.tp2:
                    self.binance_server.cancel_order(self.sl)
                    self.sl = None

                    self.binance_server.cancel_order(self.limit2)
                    self.limit2 = None

                    self.position = POSITION_SIDE.NONE
                    self.trade_step = TRADE_STEP.ALL_CLOSED

                    self.log_dca_closed()
            elif message.order.type == ORDER_TYPE.SL:
                if self.tp2 != None:
                    self.binance_server.cancel_order(self.tp2)
                    self.tp2 = None
                else:
                    self.binance_server.cancel_order(self.tp1)
                    self.tp1 = None

                    self.binance_server.cancel_order(self.limit2)
                    self.limit2 = None

                self.position = POSITION_SIDE.NONE
                self.trade_step = TRADE_STEP.ALL_CLOSED

                self.log_dca_closed()

    def tick(self):
        self.binance_server.tick()
        while not self.binance_server.ws_queue.empty():
            message = self.binance_server.ws_queue.get()
            self.handel_message(message)

    def get_alive_time(self):
        return self.binance_server.get_current_time() - self.last_trade_time

    def get_trade_step(self):
        return self.trade_step

    def get_dac_num(self):
        return len(self.DACS) + self.binance_server.sub_server.order_list.__len__()

    def get_trades(self):
        trades = []
        pos = self.binance_server.sub_server.position
        trade = {
            "entry": pos.entry,
            "tp": pos.tp,
            "sl": pos.sl,
            "type": "long" if pos.side == POSITION_SIDE.LONG else "short"
        }
        trades.append(trade)
        return trades

    def get_dcas(self):
        dcas = []
        for order in self.binance_server.sub_server.order_list:
            if order.type == ORDER_TYPE.LIMIT:
                dca_info = {
                    "price": order.trigger_price,
                    "volume": order.amount,
                    "type": "long" if order.side == POSITION_SIDE.LONG else "short"
                }
                dcas.append(dca_info)
        return dcas

    def get_total(self):
        return self.binance_server.get_total()

    def get_window_klines(self, limit):
        return self.binance_server.get_window_klines(limit)

    def log_dca_closed(self):
        log_action(f"↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑DCAS CLOSED↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑\n", self.binance_server.get_current_time())

    def log_dca_opened(self):
        log_action(f"↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓DCAS OPENED↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓", self.binance_server.get_current_time())

    def error(self):
        self.reset_dca_by_error()
        return False

    def reset_dca_by_error(self):
        self.DACS = []
        self.position = POSITION_SIDE.NONE
        self.trade_step = TRADE_STEP.NONE
        self.last_trade_time = None
        self.limit1 = None
        self.limit2 = None
        self.tp1 = None
        self.tp2 = None
        self.sl = None