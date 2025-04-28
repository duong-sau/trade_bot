from binance.exceptions import BinanceRequestException, BinanceAPIException
from Logic.logger import log_error
import Server

def open_limit(symbol, side, amount, price):
    try:
        order = Server.client.createOrder(symbol=symbol,
                                   type="limit",
                                   side=side,
                                   amount=amount,
                                   price=price)
        return order['id']
    except:
        log_error()
        return None

def open_take_profit(symbol, quantity, price, side):
    try:
        order = Server.client.createOrder(symbol=symbol, type="TAKE_PROFIT", side=side, amount=quantity, price=price, params={"takeProfitPrice": price, "reduceOnly": True})
        return order['id']
    except (BinanceRequestException, BinanceAPIException):
        log_error()
        return None

def open_stop_loss(symbol, quantity, price, side):
    try:
        order = Server.client.createOrder(symbol=symbol, type="STOP", side=side, amount=quantity, price=price, params={"stopLossPrice": price, "reduceOnly": True})
        return order['id']
    except BinanceAPIException as e:
        error_code = e.code
        if error_code == -2021:
            force_stop_loss(symbol, quantity, side)
            return False
        else:
            log_error()
            return False

def force_stop_loss(symbol, quantity, side):
    try:
        order = Server.client.createOrder(symbol=symbol,
                                   type="STOP_MARKET",
                                   side=side,
                                   amount=quantity,
                                   params={"stopLossPrice": 0, "reduceOnly": True}
                                   )
        return order['id']
    except:
        log_error()
        return None


def cancel_order(symbol, order_id):
    try:
        Server.client.cancel_order(symbol=symbol, id=order_id)
    except:
        log_error()

def confirm_order(datas):
    return True