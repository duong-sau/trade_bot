import sys

from binance.exceptions import BinanceRequestException, BinanceAPIException

from Server.BinanceControl.Common import open_limit, open_stop_loss, open_take_profit, cancel_order


class OTOListener:

    symbol = "BTCUSDT"

    def __init__(self, side,  amount, price, tp, sl) -> None:
        """
        PARAMETER
        """
        assert len(amount) == len(tp)
        assert len(amount) == len(sl)
        # amount list
        # sl list

        self.price = price
        self.side = side

        self.amount   = amount
        self.sl = sl
        self.tp = tp
        """
        ORDER
        """
        self.limit_order = []
        self.tp_order = []
        self.sl_order = []
        return

    def make_first_limit_order(self):
        try:
            self.limit_order = open_limit(self.symbol, self.side, self.amount, self.price)
            return True
        except(BinanceRequestException, BinanceAPIException):
            error = str(sys.exc_info()[1])
            print(error)
            self.destroy()
            return False

    def handel_message(self):
        pass
    def handel_limit(self):
        self.make_stop_lost_order()
        self.make_take_profit_order()

    def handle_take_profit(self):
        self.cancel_stop_loss_order()
        self.destroy()

    def handle_stop_loss(self):
        self.cancel_take_profit_order()
        self.destroy()

    # ----------------------------------------------------------------------------------------------------
    # Create Order
    # ----------------------------------------------------------------------------------------------------
    def make_stop_lost_order(self):
        # change side to opposite
        if self.side == "BUY":
            side = "SELL"
        else:
            side = "BUY"
        self.sl_order = open_stop_loss(self.symbol, self.amount, self.sl , side)
        return self.sl_order

    def make_take_profit_order(self):
        # change side to opposite
        if self.side == "BUY":
            side = "SELL"
        else:
            side = "BUY"
        self.tp_order = open_take_profit(self.symbol, self.amount, self.tp , side)

    # ----------------------------------------------------------------------------------------------------
    # Cancel Order
    # ----------------------------------------------------------------------------------------------------

    def cancel_stop_loss_order(self):
        cancel_order(self.symbol, self.sl_order)

    def cancel_take_profit_order(self):
        cancel_order(self.symbol, self.tp_order)

    def get_order_ids(self):
        return [self.limit_order, self.sl_order, self.tp_order]
