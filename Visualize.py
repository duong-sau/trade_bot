import threading
import time
from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt, animation
import matplotlib.dates as mdates
class Visualizer:

    MAX_COLUMNS = 120

    def __init__(self):
        self.tick = 0
        self.trade_lines = []
        self.trades =  []
        self.last_time = None
        self.fig, self.ax = plt.subplots()
        self.lines = {
            "current": self.ax.plot([], [], label="Current", color="black")[0],
            "upper": self.ax.plot([], [], label="Upper BB", color="blue")[0],
            "lower": self.ax.plot([], [], label="Lower BB", color="blue")[0],
        }
        self.ax.legend()
        self.ax.set_title("Real-time Visualization")
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(96500, 97600)

        self.data = {
            "current": [],
            "upper": [],
            "lower": [],
            "distant": [],
            "ma": [],
            "rsi": [],
        }

        self.trades = []  # List trades lấy từ server
        self.dcas = []  # List DCA orders

        self.text_box = self.ax.text(
            0.05, 0.95, "", transform=self.ax.transAxes, fontsize=12, va="top",
            bbox=dict(facecolor="white", alpha=0.7)
        )

        self.lock = threading.Lock()

    def update_data(self, current, upper, lower, distant, ma, rsi):
        with self.lock:
            if self.tick % 300 != 0:
                self.data["current"][-1] = current[-1]
                self.data["upper"][-1] = upper
                self.data["lower"][-1] = lower
                self.data["distant"][-1] = distant
                self.data["ma"][-1] = ma
                self.data["rsi"][-1] = rsi
            else:
                self.data["current"].append(current[-1])
                self.data["upper"].append(upper)
                self.data["lower"].append(lower)
                self.data["distant"].append(distant)
                self.data["ma"].append(ma)
                self.data["rsi"].append(rsi)

            for key in self.data:
                if len(self.data[key]) > self.MAX_COLUMNS:
                    self.data[key].pop(0)
        self.tick += 1

    def _animate(self, frame):
        with self.lock:
            # if self.last_time is None:
            #     x = np.arange(len(self.data["current"]))
            # else:
            #     timestamp = datetime.strptime(self.last_time, '%m/%d/%Y, %H:%M:%S').timestamp()
            #
            #     # Round timestamp down to nearest 5 minute interval
            #     first_time = int(timestamp - (timestamp % 300))
            #     first_time = first_time - len(self.data["current"]) * 300
            #
            #     x = [(datetime.fromtimestamp(first_time + (len(self.data["current"]) + i) * 300)) for i in range(len(self.data["current"]))]
            #     self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            #     self.ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
            x = np.arange(len(self.data["current"]))

            for key, line in self.lines.items():
                line.set_data(x, self.data[key])

            if len(self.data["distant"]) > 0 and len(self.data["rsi"]) > 0:
                latest_distant = self.data["distant"][-1]
                latest_rsi = self.data["rsi"][-1]
                self.text_box.set_text(
                    f"{self.last_time} \n Price: {self.data["current"][-1]}\nDistant: {latest_distant:.2f}\nRSI: {latest_rsi:.2f}"
                )

            if len(x) > 0:
                self.ax.set_xlim(max(0, len(x) - self.MAX_COLUMNS), len(x))

                upper = max(self.data["upper"]) if self.data["upper"] else 1
                lower = min(self.data["lower"]) if self.data["lower"] else 0
                margin = (upper - lower) * 2
                self.ax.set_ylim(lower - margin, upper + margin)

            # Xoá các line trade cũ
            for line in self.trade_lines:
                line.remove()
            self.trade_lines.clear()

            # Vẽ lại trades mới
            for trade in self.trades:
                # Fill between entry and sl/tp lines
                x_range = [self.ax.get_xlim()[0], self.ax.get_xlim()[1]]
                sl_fill = self.ax.fill_between(x_range, [trade["entry"]] * 2, [trade["sl"]] * 2, color='red', alpha=0.1)
                tp_fill = self.ax.fill_between(x_range, [trade["entry"]] * 2, [trade["tp"]] * 2, color='green',
                                               alpha=0.1)

                self.trade_lines.extend([sl_fill, tp_fill])

            # Vẽ DCA orders
            for dca in self.dcas:
                color = "green" if dca["type"] == "long" else "red"
                dca_line = self.ax.axhline(dca["price"], color=color, linewidth=2)
                self.trade_lines.append(dca_line)

    def start_animation(self):
        ani = animation.FuncAnimation(self.fig, self._animate, interval=100)
        plt.show()

    def set_trades(self, trades):
        self.trades = trades

    def set_dcas(self, dcas):
        self.dcas = dcas

    def set_last_time(self, timestamp):
        self.last_time = timestamp
