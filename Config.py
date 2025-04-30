import configparser

# Read parameters from config file
config = configparser.ConfigParser()
config.read('Alogithum.ini')

# Get RSI parameters
rsi_long = config.getfloat('ALOG', 'rsi_long')
rsi_short = config.getfloat('ALOG', 'rsi_short')
rsi_period = config.getint('ALOG', 'rsi_period')

# Get Bollinger Bands parameters
bb_period = config.getint('ALOG', 'bb_period')
bb_stddev = config.getfloat('ALOG', 'bb_stddev')

# Get distance parameter
distance = config.getfloat('ALOG', 'distance')

config_bot = configparser.ConfigParser()
config_bot.read('Bot.ini')
# Get SL and TP parameters
sl = config_bot.getfloat('BOT', 'sl')
tp = config_bot.getfloat('BOT', 'tp')
