from datetime import datetime
from math import floor
import pandas as pd

def prepare(interval):
    df = pd.read_csv('Data/225.csv', header=0, parse_dates=['timestamp'], index_col='timestamp')
    #df = pd.read_csv('klines05060000-1200.csv', header=0, parse_dates=['timestamp'], index_col='timestamp')

    interval_klines = []
    tick_klines = []
    time_klines = []
    ohlc_klines = []

    tick_df = df['close']
    tick_klines = tick_df.to_numpy(dtype=float).tolist()

    time_df = df.index.strftime("%m/%d/%Y, %H:%M:%S")
    time_klines = time_df.to_numpy().tolist()

    # Calculate OHLC data based on interval
    df_resampled = df.resample(f'{interval}s').agg({
        'close': ['first', 'max', 'min', 'last']
    })
    df_resampled.columns = ['open', 'high', 'low', 'close']
    ohlc_klines = df_resampled.to_numpy(dtype=float).tolist()

    for i in range(0, len(tick_klines), interval):
        interval_klines.append(tick_klines[i])

    return interval_klines, tick_klines, time_klines, ohlc_klines


class KlineServer:
    tick = 0
    g_interval_klines = []
    g_tick_klines = None
    g_time_klines = None
    g_ohlc_klines = None
    interval_size = 5 * 60
    base_bb_size = 20

    def __init__(self):
        # tick
        self.tick = self.base_bb_size * self.interval_size

        # klines
        self.g_interval_klines, self.g_tick_klines, self.g_time_klines, self.g_ohlc_klines = prepare(self.interval_size)
        print(f"interval size = {len(self.g_tick_klines) / len(self.g_interval_klines)}")

    def get_window_price(self, window_size):
        interval_tick = floor(self.tick / self.interval_size)
        r = self.g_interval_klines[interval_tick - window_size + 1: interval_tick]
        r.append(self.g_tick_klines[self.tick])
        return r

    def get_current_price(self):
        return self.g_tick_klines[self.tick]

    def get_current_time(self):
        return self.g_time_klines[self.tick]


    def up_tick(self):
        self.tick = self.tick + 1
        if self.tick > len(self.g_tick_klines):
            exit(1)

    def get_total(self):
        return len(self.g_tick_klines) - self.base_bb_size * self.interval_size -1

    def get_window_klines_olhc(self, window_size):
        interval_tick = floor(self.tick / self.interval_size)
        r = self.g_ohlc_klines[interval_tick - window_size + 1:interval_tick + 1]
        return r
