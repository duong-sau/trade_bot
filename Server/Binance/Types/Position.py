from enum import Enum

from Server.Binance.Types.User import tradding_fee


class POSITION_SIDE(Enum):
    LONG = 1
    NONE = 0
    SHORT = -1


class Position:
    side: POSITION_SIDE = POSITION_SIDE.NONE
    entry = 0
    volume = 0
    tp = -1
    sl = -1

    def __init__(self):
        self.side = POSITION_SIDE.NONE
        self.entry = -1
        self.volume = 0
        self.current_profit = 0

    def extend(self, order):

        if self.side != POSITION_SIDE.NONE:
            assert self.side == order.side

        self.side = order.side
        self.entry = (self.entry * self.volume + order.trigger_price * order.amount) / (self.volume + order.amount)
        self.volume += order.amount

    def remove(self, order):

        assert self.side == order.side
        
        self.calulate_profit(order.trigger_price)

        self.volume -= order.amount
        # assert self.volume == 0
        self.entry = 0

        if self.volume == 0:
            self.side = POSITION_SIDE.NONE
            return True
        else:
            return False
    
    def calulate_profit(self, price):
        if self.side == POSITION_SIDE.LONG:
            self.current_profit =  self.volume * (price - self.entry) / self.entry - self.volume * tradding_fee
        elif self.side == POSITION_SIDE.SHORT:
            self.current_profit =  self.volume * (self.entry - price) / self.entry - self.volume * tradding_fee
        else:
            assert False

    def get_profit(self, price):
        return self.current_profit

    def update_tp_sl(self, tp, sl):
        self.tp = tp
        self.sl = sl

    def reset(self):
        self.tp = 0
        self.sl = 0
        self.entry = 0
        self.side = POSITION_SIDE.NONE
        self.volume = 0