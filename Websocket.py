import datetime
import time
from binance import ThreadedWebsocketManager
from RealServer import api_key, api_secret, testnet
import csv
import os
import signal

if __name__ == '__main__':
    running = True


    def signal_handler(signum, frame):
        global running, counter
        print("\nReceived Ctrl+C! Cleaning up...")

        # Write END message
        with open('websocket.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([counter, datetime.datetime.now(), "END"])

        # Copy to timestamped backup file
        timestamp = datetime.datetime.now().strftime("%d_%m_%y-%H_%M_%S")
        backup_filename = f'websocket_{timestamp}.csv'
        with open('websocket.csv', 'r') as source:
            with open(backup_filename, 'w') as target:
                target.write(source.read())

        running = False
        web_socket.stop()
        exit(0)


    signal.signal(signal.SIGINT, signal_handler)

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


    while running:
        time.sleep(1)
        trim_file()
    
    