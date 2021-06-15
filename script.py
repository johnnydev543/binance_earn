import time
import os
import configparser
import math
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException

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

# 7, 14, 30, 90, 0
TARGET_DURATION = int(config['target']['DURATION'])

# MAX or number
KEEP_LOT = int(config['target']['KEEP_LOT'])

MIN_LOT = int(config['target']['MIN_LOT'])

LOOP_SEC = int(config['general']['LOOP_SEC'])
client = Client(API_KEY, API_SECRET)

"""
Used for sort the key of the duration
"""
def key_duration(json):
    try:
        return int(json['duration'])
    except KeyError:
        return 0

print("COIN", TARGET_COIN,
      "DURATION", TARGET_DURATION,
      "KEEP_LOT", KEEP_LOT,
      "MIN_LOT", MIN_LOT,
      "LOOP_SEC", LOOP_SEC
      )

while(True):

    asset_balance = client.get_asset_balance(asset=TARGET_COIN)

    free = asset_balance.get('free', None)
    free_balance = float(free)

    if free_balance > 0:

        try:
            projects = client.get_fixed_activity_project_list(
                                type='CUSTOMIZED_FIXED',
                                status='SUBSCRIBABLE',
                                timestamp=time.time()
                                )
        except BinanceAPIException as e:
            print(e)
        else:

            # Sort the duration,
            # the longer duration the higher priority if TARGET_DURATION is set to 0(ALL)
            if TARGET_DURATION == 0:
                projects.sort(key=key_duration, reverse=True)

            print(datetime.now(), '|', TARGET_COIN, free_balance)

        for project in projects:
            status = project.get('status', None)
            asset = project.get('asset', None)
            duration = project.get('duration', None)
            lotSize = project.get('lotSize', None)

            is_duration_matched = False

            if TARGET_DURATION == int(duration) or TARGET_DURATION == 0:
                is_duration_matched = True

            if asset == TARGET_COIN and status == 'PURCHASING' and is_duration_matched:
                lotsPurchased = project.get('lotsPurchased', None)
                lotsUpLimit = project.get('lotsUpLimit', None)
                maxLotsPerUser = project.get('maxLotsPerUser', None)
                projectId = project.get('projectId', None)

                print(duration, lotsPurchased, lotsUpLimit, maxLotsPerUser, projectId)

                purchase_availability = lotsUpLimit - lotsPurchased
                balance_lot = free_balance / int(lotSize)
                balance_lot = math.floor(balance_lot)
                print('purchase_availability', purchase_availability, 'balance_lot', balance_lot, 'KEEP_LOT', KEEP_LOT)

                if purchase_availability > 0 and balance_lot > KEEP_LOT:

                    if balance_lot < MIN_LOT or purchase_availability < MIN_LOT:
                        continue

                    if purchase_availability > balance_lot:
                        lot = balance_lot - KEEP_LOT
                    else:
                        lot = purchase_availability

                    params = {
                        'projectId': projectId,
                        'lot': lot,
                        'timestamp': time.time()
                    }

                    try:
                        purchase = client._request_margin_api('post', 'lending/customizedFixed/purchase',
                                            True, data=params)
                    except BinanceAPIException as e:
                        print(e)
                    else:
                        print("Purchase it!")
                        print(purchase)

    time.sleep(LOOP_SEC)