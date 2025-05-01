import datetime

import ccxt
from binance.exceptions import BinanceRequestException, BinanceAPIException

from Tool import log_action
from logger import log_error
client: ccxt.binance = None

def SetClient(c):
    global client
    client = c

def open_limit(symbol, side, amount, price):
    try:
        order = client.createOrder(symbol=symbol,
                                   type="limit",
                                   side="BUY" if side == "LONG" else "SELL",
                                   amount=amount,
                                   price=price,
                                   params={"positionSide": side}
                                )
        return order['id']
    except:
        log_error()
        force_stop_loss(symbol)
        return False

def open_take_profit(symbol,side, quantity, price):
    try:
        order = client.createOrder(symbol=symbol,
                                   type="market",
                                   side="SELL" if side== "LONG" else "BUY",
                                   amount=quantity,
                                   price=price,
                                   params={"takeProfitPrice": price,"positionSide": side})
        return order['id']
    except Exception as e:
        log_error()
        force_stop_loss(symbol)
        return False

def open_stop_loss(symbol, side, quantity, price):
    try:
        order = client.createOrder(symbol=symbol,
                                              type="market",
                                              side="SELL" if side== "LONG" else "BUY",
                                              amount=quantity,
                                              price=price,
                                              params={"stopLossPrice": price, "positionSide": side})
        return order['id']
    except Exception as e:
        log_error()
        force_stop_loss(symbol)
        return False

def force_stop_loss(symbol):
    log_action("-------------- ERROR FORCE STOP LOSS ------------------------", datetime.datetime.now())
    try:

        client.cancel_all_orders(symbol=symbol)

        positions = client.fetch_positions()
        if len(positions) == 0:
            return None
        amount = positions[0]['info']['positionAmt']
        side = positions[0]['info']['positionSide']

        order = client.createOrder(symbol=symbol,
                                   type="market",
                                   side="SELL" if side== "LONG" else "BUY",
                                   amount=amount,
                                   params={"positionSide": side}
                                   )
        return order['id']
    except Exception as e:
        log_error()
        force_stop_loss(symbol)
        return False


def cancel_order(symbol, order_id):
    try:
        client.cancel_order(symbol=symbol, id=order_id)
        return True
    except:
        log_error()
        force_stop_loss(symbol)
        return False

def confirm_order(datas):
    return True