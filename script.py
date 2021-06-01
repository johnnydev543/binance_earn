import time
import os
import configparser
import math
from datetime import datetime
from binance.client import Client

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
TARGET_COIN = config['target']['COIN']
TARGET_DURATION = int(config['target']['DURATION'])
LOOP_SEC = int(config['target']['LOOP_SEC'])

# MAX or number
TARGET_LOT = config['target']['LOT']

# at least buy X amount of lot in single purchase
MIN_LOT = int(config['target']['MIN_LOT'])

client = Client(API_KEY, API_SECRET)

# lending endpoint is not implemented in the package,
# so we need to force it to use the url and version we want
client.API_URL = 'https://api.binance.com/sapi'
client.PRIVATE_API_VERSION = "v1"

while(True):

    params = {
        'timestamp': time.time()
    }

    capital = client._get("capital/config/getall",
                            True, client.PUBLIC_API_VERSION, data=params)

    for coin in capital:
        free = coin.get('free', None)
        coin = coin.get('coin', None)
        free_balance = float(free)
        if free_balance > 0 and coin == TARGET_COIN :
            print(TARGET_COIN, free_balance)

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
                lotSize = project.get('lotSize', None)

                if asset == TARGET_COIN and status == 'PURCHASING' and int(duration) == TARGET_DURATION:
                    lotsPurchased = project.get('lotsPurchased', None)
                    lotsUpLimit = project.get('lotsUpLimit', None)
                    maxLotsPerUser = project.get('maxLotsPerUser', None)
                    projectId = project.get('projectId', None)

                    print(duration, lotsPurchased, lotsUpLimit, maxLotsPerUser, projectId)

                    purchase_availability = lotsUpLimit - lotsPurchased
                    balance_lot = free_balance / int(lotSize)
                    balance_lot = math.floor(balance_lot)
                    print(datetime.now(), 'purchase_availability', purchase_availability)
                    # if purchase_availability > balance_lot:


                    if balance_lot < MIN_LOT:
                        continue

                    if purchase_availability > balance_lot:

                        if TARGET_LOT == 'MAX':
                            lot = balance_lot
                        else:
                            lot = int(TARGET_LOT)
                    else:
                        lot = purchase_availability

                    params = {
                        'projectId': projectId,
                        'lot': lot,
                        'timestamp': time.time()
                    }

                    print("Purchase it!")
                    purchase = client._post("lending/customizedFixed/purchase",
                                True, client.PUBLIC_API_VERSION, data=params)
    time.sleep(LOOP_SEC)


