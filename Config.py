import configparser

# Read parameters from config file
config = configparser.ConfigParser()
config.read('Ini/Algorithm.ini')

mode = config.get('MODE', 'current')

# Get RSI parameters
rsi_long = config.getfloat('ALOG', 'rsi_long')
rsi_short = config.getfloat('ALOG', 'rsi_short')
rsi_period = config.getint('ALOG', 'rsi_period')

# Get Bollinger Bands parameters
bb_period = config.getint('ALOG', 'bb_period')
bb_stddev = config.getfloat('ALOG', 'bb_stddev')

# Get distance parameter
distance = config.get('ALOG', 'distance')

L0= config.get('BOT', 'L0')
L1= config.get('BOT', 'L1')
L2= config.get('BOT', 'L2')

S0= config.get('BOT', 'S0')
S1= config.get('BOT', 'S1')
S2= config.get('BOT', 'S2')

# Get SL and TP parameters
tp1_ratio = config.getfloat('BOT', 'tp1')
tp2_ratio = config.getfloat('BOT', 'tp2')

n1 = config.getfloat('BOT', 'n1')
n2 = config.getfloat('BOT', 'n2')


leverage = config.getfloat('BOT', 'leverage')


limit_timeout = config.getfloat('BOT', 'limit_timeout')
tp_timeout = config.getfloat('BOT', 'tp_timeout')
tp_decrease_time = config.getfloat('BOT', 'tp_decrease_time')
tp_min = config.getfloat('BOT', 'tp_min')
tp_decrease_step = config.getfloat('BOT', 'tp_decrease_step')

distance_min = config.getint('BOT', 'distance_min')
distance_min_klines_count = config.getint('BOT', 'distance_min_klines_count')

distance_check_mode = config.getint('BOT', 'distance_check_mode')
distance_check_mode_klines_count = config.getint('BOT', 'distance_check_mode_klines_count')

DATA_PATH = r"Z:\DATA"

config = configparser.ConfigParser()
config.read('Ini/Config.ini')
start_script = config.get('SCRIPT', 'start')

