import datetime
import time
from binance import ThreadedWebsocketManager
from RealServer import api_key, api_secret, testnet
import csv
import os

if __name__ == '__main__':

    web_socket = ThreadedWebsocketManager(
        api_secret=api_secret,
        api_key=api_key,
        testnet=testnet)
    web_socket.start()
    print('Websocket reconnected')

    counter = 1

    # Delete existing file at startup
    file = open('websocket.csv', 'w')
    file.write(f'0,{datetime.datetime.now()},START\n')  # Write header
    file.close()

    def process_message(message):
        global counter
        with open('websocket.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([counter,datetime.datetime.now(), message])
            counter += 1


    web_socket.start_futures_socket(callback=process_message)


    def trim_file():
        # Read existing lines
        with open('websocket.csv', 'r') as file:
            lines = file.readlines()

        # Write back trimmed lines
        if len(lines) > 2000:
            with open('websocket.csv', 'w', newline='') as file:
                file.writelines(lines[1000:])

    while True:
        time.sleep(1)
        trim_file()
    
    