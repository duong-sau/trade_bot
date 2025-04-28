import requests
from tqdm import tqdm

class DCAServer:

    def __init__(self):
        self.host = "127.0.0.1:8000"


    def put_long(self, L_points, n, volume):
        response = requests.post(f"http://{self.host}/put_long", json={"points": L_points, "n": n, "volume": volume})
        print(response.text)

    def put_short(self, S_Points, n,  volume):
        response = requests.post(f"http://{self.host}/put_short", json={"points": S_Points, "n": n, "volume": volume})
        print(response.text)

    def clear_all_orders(self):
        response = requests.post(f"http://{self.host}/clear_all_orders")
        print(response.text)

    def tick(self):
        pass

    def GetDACNum(self):
        repsonse = requests.get(f"http://{self.host}/GetDACNum")
        return int(repsonse.json()['num'])


    def get_trades(self):
        response = requests.get(f"http://{self.host}/get_trades")
        return response.json()['trades']

    def get_dcas(self):
        response = requests.get(f"http://{self.host}/get_dcas")
        return response.json()['dcas']

    def get_total(self):
        return 1000000

    def get_window_klines(self, limit):
        response = requests.get(f"http://{self.host}/get_window_klines")
        return response.json()['window_klines']
