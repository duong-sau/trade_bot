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
    ALL_CLOSED = 4



class DCAServer:

    tp1_ratio = Config.tp1_ratio / 100
    tp2_ratio = Config.tp2_ratio / 100

    def __init__(self):
        # self.binance_server = BinanceTestServer()
        self.binance_server = BinanceServer()
        self.position = POSITION_SIDE.NONE
        self.name = ""

        self.tp1_val = 0
        self.tp2_val = 0
        self.sl_val = 0

        self.step_x_volume = []
        self.step_x_price = []


        self.limit1 = None
        self.limit2 = None

        self.tp1 = None
        self.tp2 = None

        self.sl1 = None
        self.sl2 = None

        self.last_trade_time = None
        self.trade_step = TRADE_STEP.NONE

        self.current_tp1_ratio = 0
        self.current_tp2_ratio = 0

        self.limit2_filled_time = None

    def action_dca_open(self):
        self.log_dca_opened()
        self.current_tp1_ratio = self.tp1_ratio
        self.current_tp2_ratio = self.tp2_ratio

        self.last_trade_time = self.binance_server.get_current_time()
        self.trade_step = TRADE_STEP.NONE



    def put_long(self, dca_s,volumes):

        self.action_dca_open()

        self.step_x_volume = volumes
        self.step_x_price = dca_s

        self.sl_val = round(dca_s[-1], 1)
        self.tp1_val = round(dca_s[0] * (1 + self.tp1_ratio), 1)
        self.tp2_val = round((dca_s[0] * volumes[0] + dca_s[1] * volumes[1]) / (volumes[0] + volumes[1]) * (1 + self.tp2_ratio), 1)

        self.position = POSITION_SIDE.LONG
        self.put_limit1()

    def put_short(self, dca_s, volumes):

        self.action_dca_open()

        self.position = POSITION_SIDE.SHORT

        self.step_x_volume = volumes
        self.step_x_price = dca_s

        self.sl_val = round(dca_s[-1], 1)

        self.tp1_val = round(dca_s[0] * (1 - self.tp1_ratio), 1)
        self.tp2_val = round((dca_s[0] * volumes[0] + dca_s[1] * volumes[1]) / (volumes[0] + volumes[1]) * (1 - self.tp2_ratio), 1)

        self.put_limit1()


    def cancel_by_timeout(self):
        self.position = POSITION_SIDE.NONE

        self.last_trade_time = None
        if self.trade_step == TRADE_STEP.NONE:
            if not self.binance_server.cancel_order(self.limit1):
                self.reset_dca_by_error()
                return
            # if not self.binance_server.cancel_order(self.limit2):
            #     self.reset_dca_by_error()
            #     return

        self.trade_step = TRADE_STEP.NONE

        self.log_dca_closed()

    def get_limit2_filled_time(self):
        if self.trade_step != TRADE_STEP.LIMIT2_FILLED:
            return None
        return self.binance_server.get_current_time() - self.limit2_filled_time

    def decrease_tp(self):
        if self.trade_step != TRADE_STEP.LIMIT2_FILLED:
            return

        if self.current_tp2_ratio - Config.tp_decrease_step / 100 <= Config.tp_min / 100:
            print('error')
            return
        self.current_tp2_ratio = self.current_tp2_ratio - Config.tp_decrease_step / 100


        if self.position == POSITION_SIDE.LONG:
            self.tp2_val = round(
                (self.step_x_volume[0] * self.step_x_price[0] + self.step_x_volume[1] * self.step_x_price[1]) / (
                            self.step_x_volume[0] + self.step_x_volume[1]) *
                 (1 + self.tp2_ratio)
                     , 1)

        elif self.position == POSITION_SIDE.SHORT:
            self.tp2_val = round(
                (self.step_x_volume[0] * self.step_x_price[0] + self.step_x_volume[1] * self.step_x_price[1]) / (
                        self.step_x_volume[0] + self.step_x_volume[1]) *
                (1 - self.tp2_ratio)
                , 1)

        if not self.cancel_tp2():
            return
        if not self.put_tp2():
            return

    def put_limit1(self):
        vl = self.step_x_volume[0]
        entry = self.step_x_price[0]
        self.limit1 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT,
                                                     side=POSITION_SIDE.LONG,
                                                     amount=vl,
                                                     entry=entry,
                                                     reduce_only=False)
        if not self.limit1:
            self.reset_dca_by_error()
            return False
        return True

    def put_limit2(self):
        vl = self.step_x_volume[1]
        entry = self.step_x_price[1]
        self.limit2 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=self.position, amount=vl,
                                                     entry=entry, reduce_only=False)
        if not self.limit2:
            self.reset_dca_by_error()
            return False
        return True

    def put_tp1(self):
        volume = self.step_x_volume[0]
        self.tp1 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position,
                                                  amount=volume, entry=self.tp1_val,
                                                  reduce_only=True)
        if not self.tp1:
            self.reset_dca_by_error()
            return False
        return True

    def put_tp2(self):
        volume = self.step_x_volume[1] + self.step_x_volume[0]

        self.tp2 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position,
                                                  amount=volume, entry=self.tp2_val, reduce_only=True)
        if not self.tp2:
            self.reset_dca_by_error()
            return False
        return True

    def put_sl1(self):
        volume = self.step_x_volume[0]
        self.sl1 = self.binance_server.open_order(order_type=ORDER_TYPE.SL, side=self.position,
                                                  amount=volume, entry=self.sl_val, reduce_only=True)
        if not self.sl1:
            self.reset_dca_by_error()
            return False
        return True

    def put_sl2(self):
        volume = self.step_x_volume[1] + self.step_x_volume[0]
        self.sl2 = self.binance_server.open_order(order_type=ORDER_TYPE.SL, side=self.position,
                                                 amount=volume, entry=self.sl_val, reduce_only=True)
        if not self.sl2:
            self.reset_dca_by_error()
            return False
        return True

    def cancel_limit1(self):
        if not self.binance_server.cancel_order(self.limit1):
            self.reset_dca_by_error()
            return False
        self.limit1 = None
        return True

    def cancel_limit2(self):
        if not self.binance_server.cancel_order(self.limit2):
            self.reset_dca_by_error()
            return False
        self.limit2 = None
        return True

    def cancel_tp1(self):
        if not self.binance_server.cancel_order(self.tp1):
            self.reset_dca_by_error()
            return False
        self.tp1 = None
        return True

    def cancel_tp2(self):
        if not self.binance_server.cancel_order(self.tp2):
            self.reset_dca_by_error()
            return False
        self.tp2 = None
        return True

    def cancel_sl1(self):
        if not self.binance_server.cancel_order(self.sl1):
            self.reset_dca_by_error()
            return False
        self.sl1 = None
        return True

    def cancel_sl2(self):
        if not self.binance_server.cancel_order(self.sl2):
            self.reset_dca_by_error()
            return False
        self.sl2 = None
        return True

    def handel_limit_filled(self, message):
        if message.order.id == self.limit1:
            self.handel_limit1_filled(message)
        if message.order.id == self.limit2:
            self.handel_limit2_filled(message)

    def handel_limit1_filled(self, message):
        if not self.put_sl1():
            return
        if not self.put_tp1():
            return
        if not self.put_limit2():
            return
        self.trade_step = TRADE_STEP.LIMIT1_FILLED

    def handel_limit2_filled(self, message):
        if not self.cancel_tp1():
            return
        if not self.cancel_sl1():
            return
        if not self.put_sl2():
            return
        if not self.put_tp2():
            return
        self.trade_step = TRADE_STEP.LIMIT2_FILLED
        self.limit2_filled_time = self.binance_server.get_current_time()

    def handel_tp_filled(self, message):
        if message.order.id == self.tp1:
            self.handel_tp1_filled(message)
        elif message.order.id == self.tp2:
            self.handel_tp2_filled(message)

        self.position = POSITION_SIDE.NONE
        self.trade_step = TRADE_STEP.ALL_CLOSED
        self.log_dca_closed()

    def handel_tp1_filled(self, message):
        if not self.cancel_sl1():
            return
        if not self.limit2 is None:
            self.cancel_limit2()

    def handel_tp2_filled(self, message):
        self.cancel_sl2()

    def handel_sl_filled(self, message):
        if message.order.id == self.sl1:
            self.handel_sl1_filled(message)
        elif message.order.id ==self.sl2:
            self.handel_sl2_filled(message)

        self.position = POSITION_SIDE.NONE
        self.trade_step = TRADE_STEP.ALL_CLOSED

        self.log_dca_closed()

    def handel_sl1_filled(self, message):
        if not self.cancel_tp1():
            return
        if not self.limit2 is None:
            self.cancel_limit2()

    def handel_sl2_filled(self, message):
        self.cancel_tp2()

    def handel_message(self, message):
        # log_order("HERE", message.order, self.binance_server.sub_server.get_current_time())
        if message.action == ORDER_ACTION.FILLED:
            if message.order.type == ORDER_TYPE.LIMIT:
                if message.order.id == self.limit1 or message.order.id == self.limit2:
                    self.handel_limit_filled(message)

            elif message.order.type == ORDER_TYPE.TP:
                if message.order.id == self.tp1 or message.order.id == self.tp2:
                    self.handel_tp_filled(message)

            elif message.order.type == ORDER_TYPE.SL:
                if message.order.id == self.sl1 or message.order.id == self.sl2:
                    self.handel_sl_filled(message)


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
        return self.binance_server.sub_server.order_list.__len__()

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

    def reset_dca_by_error(self):
        self.position = POSITION_SIDE.NONE
        self.trade_step = TRADE_STEP.NONE

        self.last_trade_time = None

        self.limit1 = None
        self.limit2 = None

        self.tp1 = None
        self.tp2 = None

        self.sl1 = None
        self.sl2 = None

        self.step_x_volume = []
        self.step_x_price = []

        self.tp1_val = 0
        self.tp2_val = 0


        self.log_dca_closed()