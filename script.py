import time, os
from binance.client import Client
import configparser
import requests
import json

# reads the configuration from settings file
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(__file__), 'config.ini') 
try:
    config.read(config_file)
except:
    print('Error! Please make sure that "config.ini" file exists and properly set.')
    exit(1)

API_KEY = config['api']['API_KEY']
API_SECRET = config['api']['API_SECRET']

client = Client(API_KEY, API_SECRET)

# lending endpoint is not implemented in the package,
# so we need to force it to use the url and version we want
client.API_URL = 'https://api.binance.com/sapi'
client.PRIVATE_API_VERSION = "v1"

params = {
    'timestamp': time.time()
}

capital = client._get("capital/config/getall",
                        True, client.PUBLIC_API_VERSION, data=params)

TARGET_COIN = 'BUSD'
TARGET_DURATION = 90

for coin in capital:
    free = coin.get('free', None)
    coin = coin.get('coin', None)
    free_balance = float(free)
    if free_balance > 0 and coin == TARGET_COIN :
        print(free_balance)

# print(capital)

params = {
    'type': 'CUSTOMIZED_FIXED',
    'timestamp': time.time()
}
projects = client._get("lending/project/list",
                        True, client.PUBLIC_API_VERSION, data=params)


for project in projects:
    status = project.get('status', None)
    asset = project.get('asset', None)
    duration = project.get('duration', None)
    if asset == TARGET_COIN and status == 'PURCHASING' and duration == TARGET_DURATION:
        lotsPurchased = project.get('lotsPurchased', None)
        lotsUpLimit = project.get('lotsUpLimit', None)
        maxLotsPerUser = project.get('maxLotsPerUser', None)
        print(duration, lotsPurchased, lotsUpLimit, maxLotsPerUser)
        purchase_availability = lotsUpLimit - lotsPurchased
        print('purchase_availability', purchase_availability)

