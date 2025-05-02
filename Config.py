import configparser

# Read parameters from config file
config = configparser.ConfigParser()
config.read('Ini/Algorithm.ini')

# Get RSI parameters
rsi_long = config.getfloat('ALOG', 'rsi_long')
rsi_short = config.getfloat('ALOG', 'rsi_short')
rsi_period = config.getint('ALOG', 'rsi_period')

# Get Bollinger Bands parameters
bb_period = config.getint('ALOG', 'bb_period')
bb_stddev = config.getfloat('ALOG', 'bb_stddev')

# Get distance parameter
distance = config.getfloat('ALOG', 'distance')

# Get Fibonacci values
fibonacci_str = config.get('FIBONACCI', 'fibonacci')
fibonacci_values = [float(x) for x in fibonacci_str.split()]

# Get SL and TP parameters
tp1_ratio = config.getfloat('BOT', 'tp1')/100
tp2_ratio = config.getfloat('BOT', 'tp2')/100

n1 = config.getfloat('BOT', 'n1')
n2 = config.getfloat('BOT', 'n2')


leverage = config.getfloat('BOT', 'leverage')


limit_timeout = config.getint('BOT', 'limit_timeout')
tp_timeout = config.getint('BOT', 'tp_timeout')
tp_decrease_time = config.getint('BOT', 'tp_decrease_time')
tp_min = config.getfloat('BOT', 'tp_min')
tp_decrease_step = config.getfloat('BOT', 'tp_decrease_step')
