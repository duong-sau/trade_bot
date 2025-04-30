from enum import Enum

from colorama import Fore, Style
from tqdm import tqdm

tradding_fee = 0.0400 / 100



class User:
    budget = 500

    def add_profit(self, profit, server, test=False):
        if test:
            return
        self.budget = self.budget + profit
        tqdm.write(f"{self.budget:.6f}                  --  {server.get_current_time()}")
        pass
