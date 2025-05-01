import threading
import time
from datetime import datetime
import json
import ctypes
import pandas as pd
import numpy as np
import pandas_ta as ta
from matplotlib import pyplot as plt, animation
import matplotlib.dates as mdates

from Config import rsi_period, bb_period, bb_stddev
from Tool import get_window_klines, compute_bb_2, compute_rsi, get_data_folder_path, set_terminal_title, \
    set_alive_counter


class Visualizer:

    MAX_COLUMNS = 60

    def __init__(self):

        self.data_file = get_data_folder_path() + '/visualize.json'

        self.get_klines()
        self.tick = 0
        self.trade_lines = []
        self.trades =  []
        self.x = []
        self.fig, self.ax = plt.subplots()
        self.lines = {
            "current": self.ax.plot([], [], label="Current", color="black")[0],
            "upper": self.ax.plot([], [], label="Upper BB", color="blue")[0],
            "lower": self.ax.plot([], [], label="Lower BB", color="blue")[0],
        }
        self.ax.legend()
        self.ax.set_title("Real-time Visualization")
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.fig.autofmt_xdate()
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        self.ax.set_ylim(10000, 90000)

        self.distance = 0
        self.rsi = 0
        self.ma = 0

        self.trades = []  # List trades lấy từ server
        self.dcas = []  # List DCA orders

        self.text_box = self.ax.text(
            0.05, 0.95, "", transform=self.ax.transAxes, fontsize=12, va="top",
            bbox=dict(facecolor="white", alpha=0.7)
        )
        self.lock = threading.Lock()

        threading.Thread(target=self.read_data_run, daemon=True).start()

    def _animate(self, frame):

        set_alive_counter('visualizer_alive.txt')

        with self.lock:
            x = self.x

            # Clear existing annotations
            for artist in self.ax.texts:
                if artist == self.text_box:
                    continue
                artist.remove()

            # Update lines and add new annotations
            for key, line in self.lines.items():
                line.set_data(x, self.data[key])
                if len(self.data[key]) > 0:
                    self.ax.annotate(f'{self.data[key][-1]:.0f}',
                                     xy=(x[-1], self.data[key][-1]),
                                     xytext=(5, 0),
                                     textcoords='offset points',
                                     va='center')


                self.text_box.set_text(
                    f"{datetime.now()} \nPrice: {self.data["current"][-1]}\nDistant: {self.distance:.2f}\nRSI: {self.rsi:.2f}"
                )

            if len(x) > 0:
                self.ax.set_xlim(self.x[0], self.x[-1])

                upper = max(self.data["upper"]) if self.data["upper"] else 1
                lower = min(self.data["lower"]) if self.data["lower"] else 0
                margin = (upper - lower) * 0.3
                self.ax.set_ylim(lower - margin, upper + margin)
                # self.ax.set_ylim(self.data["current"][-1] - 200, self.data["current"][-1] + 200)

            # Clear old trade lines
            for line in self.trade_lines:
                line.remove()
            self.trade_lines.clear()

            # Draw new trades
            for trade in self.trades:
                # Fill between entry and sl/tp lines 
                x_range = [self.ax.get_xlim()[0], self.ax.get_xlim()[1]]
                sl_fill = self.ax.fill_between(x_range, [trade["entry"]] * 2, [trade["sl"]] * 2, color='red', alpha=0.5)
                tp_fill = self.ax.fill_between(x_range, [trade["entry"]] * 2, [trade["tp"]] * 2, color='green',
                                               alpha=0.5)

                self.trade_lines.extend([sl_fill, tp_fill])

            # Vẽ DCA orders
            for dca in self.dcas:
                color = "green" if dca["type"] == "long" else "red"
                dca_line = self.ax.axhline(dca["price"], color=color, linewidth=2)
                self.trade_lines.append(dca_line)

    def start_animation(self):
        ani = animation.FuncAnimation(self.fig, self._animate, interval=100)
        plt.show()


    def get_klines(self):
        data, times = get_window_klines(self.MAX_COLUMNS + bb_period )
        # self.x =pd.DatetimeIndex(times[:self.MAX_COLUMNS])  # Chỉ lấy MAX_COLUMNS gần nhất
        self.x = pd.to_datetime(times[bb_period:self.MAX_COLUMNS + bb_period])
        #

        df = pd.DataFrame()
        df['close'] = data

        df.ta.bbands(length=bb_period, std=bb_stddev,append=True)
        self.data = {
            "current": data[bb_period:self.MAX_COLUMNS + bb_period],
            "upper": df[f'BBU_20_{float(bb_stddev):.1f}'].tolist()[bb_period:self.MAX_COLUMNS + bb_period],
            "lower": df[f'BBL_20_{float(bb_stddev):.1f}'].tolist()[bb_period:self.MAX_COLUMNS + bb_period],
        }

        rsi = compute_rsi(data)
        self.rsi = rsi
        self.distance = self.data["upper"][-1] - self.data["lower"][-1]
        self.ma = df[f'BBM_20_{float(bb_stddev):.1f}'].tolist()[bb_period:self.MAX_COLUMNS+ bb_period][-1]

    def read_trades_dcas(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.trades = data.get('trades', [])
                self.dcas = data.get('dcas', [])
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            self.trades = []
            self.dcas = []
            pass

    def read_data_run(self):
        while True:
            self.get_klines()
            self.read_trades_dcas()
            time.sleep(0.1)

if __name__ == '__main__':
    # Hide console window
    kernel32 = ctypes.WinDLL('kernel32')
    user32 = ctypes.WinDLL('user32')
    SW_HIDE = 0
    hWnd = kernel32.GetConsoleWindow()
    user32.ShowWindow(hWnd, SW_HIDE)

    set_terminal_title("Visual")
    visualizer = Visualizer()
    visualizer.start_animation()