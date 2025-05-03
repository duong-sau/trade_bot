import datetime
import time
from binance import ThreadedWebsocketManager
from Animation import step
from RealServer import api_key, api_secret, testnet
import csv
import os
import signal

from Tool import get_data_folder_path, set_terminal_title, set_alive_counter, read_alive_cmd, ALIVE_CMD

if __name__ == '__main__':
    set_terminal_title("Websocket")
    running = True

    folder_path = get_data_folder_path()

    def signal_handler(signum, frame):
        global running, counter
        print("\nReceived Ctrl+C! Cleaning up...")

        # Write END message
        with open(os.path.join(folder_path, 'websocket.csv'), 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([counter, datetime.datetime.now(), "END"])

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
    file = open(os.path.join(folder_path, 'websocket.csv'), 'w')
    file.write(f'0,{datetime.datetime.now()},START\n')  # Write header
    file.close()

    def process_message(message):
        try:
            global counter
            if 'e' in message and message['e'] == 'ORDER_TRADE_UPDATE':
                order = message['o']
                order_id = str(order['i'])
                event = order['X']
                price = order['p']

                if event == "FILLED":
                    action = "FILLED"
                elif event == "CANCELED":
                    action = "CANCELED"
                else:
                    return

                # Print and log the message
                print(f"\033[K{counter}: {action} - Order ID: {order_id}, Price: {price}")
            else:
                print(f"\033[K{counter}: {str(message)[0:40]}")
            with open(os.path.join(folder_path, 'websocket.csv'), 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([counter,datetime.datetime.now(), message])
                counter += 1
        except Exception as e:
            print(f"Error: {e}")
            print(message)

    web_socket.start_futures_socket(callback=process_message)


    def trim_file():
        # Read existing lines
        with open(os.path.join(folder_path, 'websocket.csv'), 'r') as file:
            lines = file.readlines()

        # Write back trimmed lines
        if len(lines) > 10:
            with open(os.path.join(folder_path, 'websocket.csv'), 'w', newline='') as file:
                file.writelines(lines[5:])

    trim_file_counter = 0
    while running:
        time.sleep(0.1)
        set_alive_counter('websocket_alive.txt')
        step()
        trim_file_counter += 1
        if trim_file_counter == 10:
            trim_file()
            trim_file_counter = 0

        run = read_alive_cmd('WEBSOCKET')
        if run == ALIVE_CMD.STOP:
            running = False
            web_socket.stop()
            exit(0)
    
    