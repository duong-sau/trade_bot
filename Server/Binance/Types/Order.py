from enum import Enum
import uuid


class ORDER_TYPE(Enum):
    LIMIT = 1
    TP = 2
    SL = 3
    MARKET = 4
    STOP = 5

class ORDER_SIDE(Enum):
    LONG = 1
    NONE = 0
    SHORT = -1

class Order:
    """
    Order is a class that handles the order management.
    add_position: add a position to the list
    """
    def __init__(self, order_type, side, amount, trigger_price, reduce_only=False):

        self.type = order_type
        self.side = side
        self.amount = amount
        self.trigger_price = trigger_price
        self.reduce_only = reduce_only
        self.id = str(uuid.uuid4())

    def destroy(self):
        pass

    def check_fill(self, current):
        if self.type == ORDER_TYPE.LIMIT:
            # limit long and short
            if self.side == ORDER_SIDE.LONG:
                if current <= self.trigger_price:
                    return True
            else:
                if current >= self.trigger_price:
                    return True
        elif self.type == ORDER_TYPE.TP:
            # tp long and short
            if self.side == ORDER_SIDE.LONG:
                if current >= self.trigger_price:
                    return True
            else:
                if current <= self.trigger_price:
                    return True
        elif self.type == ORDER_TYPE.SL:
            # sl long and short
            if self.side == ORDER_SIDE.LONG:
                if current <= self.trigger_price:
                    return True
            else:
                if current >= self.trigger_price:
                    return True
        return False