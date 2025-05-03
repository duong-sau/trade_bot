from datetime import datetime
from math import floor
from queue import Queue

import pandas as pd

from Server.Binance.Types.Order import Order


def prepare(interval):
    df = pd.read_csv('Data/225.csv', header=0, parse_dates=['timestamp'], index_col='timestamp')

    interval_klines = []
    tick_klines = []
    time_klines = []

    tick_df = df['close']
    tick_klines = tick_df.to_numpy(dtype=float).tolist()

    time_df = df.index
    time_klines = time_df.to_numpy(dtype=datetime).tolist()

    for i in range(0, len(tick_klines), interval):
        interval_klines.append(tick_klines[i])

    return interval_klines, tick_klines, time_klines


class KlineServer:
    time_tick = 0
    g_interval_klines = []
    g_tick_klines = None
    g_time_klines = None
    g_ohlc_klines = None
    interval_size = 5 * 60
    base_bb_size = 20

    def __init__(self):
        # tick
        self.time_tick = self.base_bb_size * self.interval_size

        # klines

        self.g_interval_klines, self.g_tick_klines, self.g_time_klines = prepare(self.interval_size)
        print(f"interval size = {len(self.g_tick_klines) / len(self.g_interval_klines)}")

        self.ws_queue = Queue()

    def get_window_kline(self, window_size):
        interval_tick = floor(self.time_tick / self.interval_size)
        r = self.g_interval_klines[interval_tick - window_size + 1: interval_tick]
        r.append(self.g_tick_klines[self.time_tick])
        return r

    def get_current_price(self):
        return self.g_tick_klines[self.time_tick]

    def get_current_time(self):
        return self.g_time_klines[self.time_tick]


    def tick(self):
        self.time_tick = self.time_tick + 1
        if self.time_tick > len(self.g_tick_klines):
            exit(1)


    def get_total(self):
        return len(self.g_tick_klines) - self.base_bb_size * self.interval_size -1
