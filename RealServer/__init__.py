import configparser
import sys

import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

time_step = 1

config = configparser.ConfigParser()
config.read('Ini/config.ini')

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
