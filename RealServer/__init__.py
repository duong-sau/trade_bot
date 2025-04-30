import configparser
import sys

import ccxt
from binance import ThreadedWebsocketManager

import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

time_step = 1

config = configparser.ConfigParser()
config.read('config.ini')

mode = config['APP']['mode']
data = config[mode]

api_key = data['api_key']
api_secret = data['api_secret']

testnet = data['testnet']

if testnet == 'True':
    testnet = True
elif testnet == 'False':
    testnet = False
else:
    testnet = 'error'

connect = config['CONNECT']
retry_client = connect['client']
retry_client = float(retry_client)
retry_socket = float(connect['socket'])

client = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'future', 'adjustForTimeDifference': True},
})
client.set_sandbox_mode(testnet)
print('Client reconnected')


def set_mock_client(mock_client):
    """
    Set the mock client for testing purposes.
    :param mock_client: The mock client to set.
    """
    global client
    client = mock_client




def set_mock_websocket_thread(mock_websocket):
    """
    Set the mock WebSocket thread for testing purposes.
    :param mock_websocket: The mock WebSocket thread to set.
    """
    global web_socket
    web_socket = mock_websocket