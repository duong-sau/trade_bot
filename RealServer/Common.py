import datetime
import sys

import ccxt
from logger import log_action
from logger import log_error
client: ccxt.binance = None

def SetClient(c):
    global client
    client = c

last_limit_price = 0

def open_limit(symbol, side, amount, price):
    global last_limit_price
    last_limit_price = price

    try:
        order = client.createOrder(
            symbol=symbol,
            type="limit",
            side="BUY" if side == "LONG" else "SELL",
            amount=amount,
            price=price)
        return order['id']
    except:
        log_error()
        return False

def open_take_profit(symbol,side, quantity, price):
    global last_limit_price
    try:
        order = client.createOrder(
            symbol=symbol,
            type="limit",
            side="SELL" if side == "LONG" else "BUY",

            amount=quantity,
            # price=last_limit_price,
            # params={"takeProfitPrice": price})
            price=price)
        return order['id']
    except Exception as e:
        log_error()
        return False

def open_stop_loss(symbol, side, quantity, price):
    try:
        order = client.createOrder(
            symbol=symbol,
            type="limit",
            side="SELL" if side == "LONG" else "BUY",
            amount=quantity,
            price=price,
            params={"stopLossPrice": price})

        return order['id']
    except Exception as e:
        log_error()
        return False

def force_stop_loss(symbol, stop = True):
    log_action("-------------- ERROR FORCE STOP LOSS ------------------------", datetime.datetime.now())
    try:

        order = client.cancel_all_orders(symbol=symbol)
        # print(order)

        positions = client.fetch_positions()
        if len(positions) == 0:
            if stop:
                sys.exit(1)

        # print(positions)

        amount = float(positions[0]['info']['positionAmt'])
        side = positions[0]['side']

        order = client.createOrder(symbol=symbol,
                                   type="market",
                                   side="SELL" if side== "long" else "BUY",
                                   amount=amount if side == "long" else -amount,
                                   )
        # print(order)
        if stop:
            sys.exit(1)

    except Exception as e:
        print(e)
        log_error()
        if stop:
            sys.exit(1)


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