import ccxt
from binance.exceptions import BinanceRequestException, BinanceAPIException
from logger import log_error
client: ccxt.binance = None

def SetClient(c):
    global client
    client = c

def open_limit(symbol, side, amount, price):
    try:
        order = client.createOrder(symbol=symbol,
                                   type="limit",
                                   side="BUY",
                                   amount=amount,
                                   price=price,
                                   params={"positionSide": side}
                                )
        return order['id']
    except:
        log_error()
        return None

def open_take_profit(symbol,side, quantity, price):
    try:
        order = client.createOrder(symbol=symbol, type="market", side="SELL", amount=quantity, price=price, params={"takeProfitPrice": price,"positionSide": side})
        return order['id']
    except Exception as e:
        if '"code":-2021' in str(e.args[0]):
            force_stop_loss(symbol, quantity, side)
            return False
        else:
            log_error()
            return False

def open_stop_loss(symbol, side, quantity, price):
    try:
        order = client.createOrder(symbol=symbol,
                                              type="market",
                                              side="SELL",
                                              amount=quantity,
                                              price=price,
                                              params={"stopLossPrice": price, "positionSide": side})
        return order['id']
    except Exception as e:
        if '"code":-2021' in str(e.args[0]):
            force_stop_loss(symbol, quantity, side)
            return False
        else:
            log_error()
            return False

def force_stop_loss(symbol, quantity, side):
    try:
        order = client.createOrder(symbol=symbol,
                                   type="market",
                                   side=side,
                                   amount=quantity,
                                   params={"positionSide": side}
                                   )
        return order['id']
    except Exception as e:
        log_error()
        return None


def cancel_order(symbol, order_id):
    try:
        client.cancel_order(symbol=symbol, id=order_id)
    except:
        log_error()

def confirm_order(datas):
    return True