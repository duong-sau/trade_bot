import Config
from RealServer.Binance import BinanceServer
from Server.Binance.BinanceTestServer import BinanceTestServer, ORDER_ACTION
from Server.Binance.Types.Order import ORDER_TYPE
from Server.Binance.Types.Position import POSITION_SIDE

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


    def put_long(self, dca_s, n, volumes):

        assert self.khop_lenh == False
        self.position = POSITION_SIDE.LONG

        self.dcas = dca_s
        self.volumes = volumes

        self.sl_val = round(dca_s[-1], 1)
        self.tp1_val = round(dca_s[0] * (1 + self.tp1_ratio), 1)
        self.tp2_val = round((dca_s[0] * volumes[0] + dca_s[1] * volumes[1]) / (volumes[0] + volumes[1]) * (1 + self.tp2_ratio), 1)

        vl = volumes[0]
        entry = dca_s[0]
        self.limit1 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.LONG, amount=vl, entry=entry, reduce_only=False)

        vl = volumes[1]
        entry = dca_s[1]
        self.limit2 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.LONG, amount=vl, entry=entry, reduce_only=False)

    def put_short(self, dca_s, n,  volumes):

        assert self.khop_lenh == False
        self.position = POSITION_SIDE.SHORT

        self.dcas = dca_s
        self.volumes = volumes
        self.sl_val = round(dca_s[-1], 1)

        self.tp1_val = round(dca_s[0] * (1 - self.tp1_ratio), 1)
        self.tp2_val = round((dca_s[0] * volumes[0] + dca_s[1] * volumes[1]) / (volumes[0] + volumes[1]) * (1 - self.tp2_ratio), 1)

        vl = volumes[0]
        entry = dca_s[0]
        self.limit1 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.SHORT, amount=vl, entry=entry, reduce_only=False)

        vl = volumes[1]
        entry = dca_s[1]
        self.limit2 = self.binance_server.open_order(order_type=ORDER_TYPE.LIMIT, side=POSITION_SIDE.SHORT, amount=vl, entry=entry, reduce_only=False)

    def clear_all_orders(self):
        #tqdm.write(f"Clear all orders: {len(self.DACS)} -- {self.binance_server.get_current_time()} {self.name}")
        self.DACS = []
        self.position = POSITION_SIDE.NONE
        self.khop_lenh = False

    def handel_message(self, message):
        # log_order("HERE", message.order, self.binance_server.sub_server.get_current_time())
        if message.action == ORDER_ACTION.FILLED:
            if message.order.type == ORDER_TYPE.LIMIT:
                if message.order.id == self.limit1:
                    self.sl = self.binance_server.open_order(order_type=ORDER_TYPE.SL, side=self.position, amount=message.order.amount, entry=self.sl_val, reduce_only=True)
                    self.tp1 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position, amount=message.order.amount, entry=self.tp1_val, reduce_only=True)
                if message.order.id == self.limit2:

                    volume = self.volumes[0] + self.volumes[1]

                    self.tp2 = self.binance_server.open_order(order_type=ORDER_TYPE.TP, side=self.position, amount=volume, entry=self.tp2_val, reduce_only=True)
                    self.binance_server.cancel_order(self.tp1)
                    self.tp1 = None

                    self.binance_server.cancel_order(self.sl)
                    self.sl = self.binance_server.open_order(order_type=ORDER_TYPE.SL, side=self.position, amount=volume, entry = self.sl_val, reduce_only=True)

            elif message.order.type == ORDER_TYPE.TP:
                if message.order.id == self.tp1 or message.order.id == self.tp2:
                    self.binance_server.cancel_order(self.sl)
                    self.sl = None

                    self.binance_server.cancel_order(self.limit2)
                    self.limit2 = None
            elif message.order.type == ORDER_TYPE.SL:
                if self.tp2 != None:
                    self.binance_server.cancel_order(self.tp2)
                    self.tp2 = None
                else:
                    self.binance_server.cancel_order(self.tp1)
                    self.tp1 = None

                    self.binance_server.cancel_order(self.limit2)
                    self.limit2 = None


    def tick(self):
        self.binance_server.tick()
        while not self.binance_server.ws_queue.empty():
            message = self.binance_server.ws_queue.get()
            self.handel_message(message)


    def GetDACNum(self):
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
