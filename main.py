import logging
import sys
import os
from iqoptionapi.stable_api import IQ_Option
import time
import numpy as np
from talib.abstract import *
from datetime import datetime
import requests

if not os.path.isdir("logs"):
    os.makedirs("logs")

logFormatter = logging.Formatter("%(asctime)s|%(filename)s:%(lineno)s|%(levelname)s|%(message)s",
                                 datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger()
log.setLevel(logging.INFO)

fileHandler = logging.FileHandler("{0}/{1}.log".format("logs", f"iqbot_{datetime.now().date()}" ))
fileHandler.setFormatter(logFormatter)
log.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)


class IQ:
    def __init__(self, email, password, mode):
        self.email = email
        self.password = password
        self.mode = mode

        self.API = None

    def Login(self):
        log.info(f'Login... E:{self.email} P:{self.password} M:{self.mode}')
        api = IQ_Option(self.email, self.password)
        status, reason = api.connect()
        if not status:
            log.info('Login failed, ', reason)
            return False

        if api.get_balance_mode() != self.mode:
            api.change_balance(self.mode)

        self.API = api
        log.info('---Login successfully----')
        log.info(f"Email:{api.email}")
        log.info(f"Mode:{api.get_balance_mode()}")
        log.info(f"Balance:{api.get_balance()}")
        log.info('-------------------------')

        # log.info(api.get_all_ACTIVES_OPCODE())
        return True

    def GetTrend(self, prices, maxdict):
        trend = ""
        ema_period = maxdict - 1

        # log.info("Show EMA")
        price = prices["close"][maxdict - 2]
        ema = EMA(prices, timeperiod=ema_period)[maxdict - 2]
        ema = round(ema, 5)

        if price > ema:
            trend = "UP"
        elif price < ema:
            trend = "DOWN"

        detail = f'Trend:{trend}, Price:{price}, Ema{ema_period}:{ema}'
        return trend, detail

    def GetStochSignal(self, prices, maxdict):
        try:
            sto_k, sto_d = STOCH(prices, 5, 3, 0, 3, 0)

            slow_d = round(sto_d[maxdict - 2], 2)
            slow_d_shift = round(sto_d[maxdict - 3], 2)

            slow_k = round(sto_k[maxdict - 2], 2)
            slow_k_shift = round(sto_k[maxdict - 3], 2)

            stoch_sell = slow_d > 70 and slow_k < slow_d and slow_k_shift > slow_d_shift
            if stoch_sell:
                detail = f'stoch_sell:{stoch_sell}, slow_k:{slow_k}, slow_k_shift:{slow_k_shift}, slow_d:{slow_d} slow_d_shift:{slow_d_shift}'
                return True, 'SELL', detail
            else:
                stoch_buy = slow_d < 30 and slow_k > slow_d and slow_k_shift < slow_d_shift
                if stoch_buy:
                    detail = f'stoch_buy:{stoch_buy}, slow_k:{slow_k}, slow_k_shift:{slow_k_shift}, slow_d:{slow_d} slow_d_shift:{slow_d_shift}'
                    return True, 'BUY', detail

        except Exception as e:
            log.info(e)
        return False, '', ''


########## START PROGRAM #######\


log.info("IQBOT V1")

email = input('Email: ')
if email == '':
    email = 'imdarkkab@gmail.com'

password = input('Password: ')
if password == '':
    password = '1qazXSW@'

modeInt = input('Mode [1:PRACTICE, 2:REAL]:')
if modeInt == '':
    modeInt = '1'

mode = "PRACTICE"
if modeInt not in ('1', '2'):
    log.info(f"Invalid mode")
    exit(0)
if modeInt == '2':
    mode = "REAL"

iq = IQ(email, password, mode)
ok = iq.Login()
if not ok:
    exit(0)

# currency = input("Currency [leave blank for auto]: ")

amount = input("Amount: ")
if amount == '':
    amount = 1

size = 60  # size=[1,5,10,15,30,60,120,300,600,900,1800,3600,7200,14400,28800,43200,86400,604800,2592000,"all"]
maxdict = 201
duration = 1  # minute 1 or 5

totalProfit = 0
totalWin = 0
totalLoss = 0
totalBet = 0
winrate = 0
last_hour = 0


################ function ################

def show_stat(balance):
    # log.info(f"\n----{datetime.now()}-----")
    # log.info(f"BALANCE: {balance}")
    # log.info(f"PROFIT/LOSS: {totalProfit}")
    # log.info(f"BET: {totalBet} WIN: {totalWin} LOSS: {totalLoss}")
    # log.info(f"WINRATE: {winrate}")
    now = datetime.now()
    msg = f'\n----{now.strftime("%Y-%m-%d %H:%M:%S")}-----'
    msg += f"\nBALANCE: {balance}"
    msg += f"\nPROFIT/LOSS: {round(totalProfit, 2)}"
    msg += f"\nBET: {totalBet} WIN: {totalWin} LOSS: {totalLoss}"
    msg += f"\nWIN RATE: {round(winrate, 2)}%"
    log.info(msg)
    return msg


def send_notify(msg):
    url = 'https://notify-api.line.me/api/notify'
    token = 'ImuOoiOAqz2TtO0hsxGsuRne3rnRqLcpcTtyAQGzjFM'
    headers = {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + token}

    r = requests.post(url, headers=headers, data={'message': msg})
    log.info(r.text)


########### start program

while True:
    now = datetime.now()
    while not iq.API.check_connect():
        iq.API.connect()
    assets = iq.API.get_all_open_time()
    digital_assets = assets["digital"]
    for currency in digital_assets:

        if not assets["digital"][currency]["open"]:
            continue

        iq.API.start_candles_stream(currency, size, maxdict)
        # log.info("Start EMA Sample")

        candles = iq.API.get_realtime_candles(currency, size)

        prices = {
            'open': np.array([]),
            'high': np.array([]),
            'low': np.array([]),
            'close': np.array([]),
            'volume': np.array([])
        }
        for timestamp in candles:
            prices["open"] = np.append(prices["open"], candles[timestamp]["open"])
            prices["high"] = np.append(prices["high"], candles[timestamp]["max"])
            prices["low"] = np.append(prices["low"], candles[timestamp]["min"])
            prices["close"] = np.append(prices["close"], candles[timestamp]["close"])
            prices["volume"] = np.append(prices["volume"], candles[timestamp]["volume"])

        trend, trend_detail = iq.GetTrend(prices, maxdict)
        action, direction, sto_detail = iq.GetStochSignal(prices, maxdict)

        # log.info(f"{currency} ## Trend:{trend}, Take Action:{action}, Direction:{direction}")

        if trend == "UP" and action and direction == "BUY":
            log.info(f"BUY {currency}!!!\n{trend_detail}\n{sto_detail}")

            _, id = iq.API.buy_digital_spot(currency, amount, "call", duration)
            notify = f'\nBUY: {currency}]\nAT {now.strftime("%Y-%m-%d %H:%M:%S")}\nID: {id}'
            log.info(id)
            if id != "error":

                while True:
                    check, win = iq.API.check_win_digital_v2(id)
                    if check:
                        break
                totalProfit += win
                if win < 0:
                    log.info("Loss: " + str(win) + "$")
                    totalLoss += 1
                    notify += f"\nLOSS: " + str(win)
                else:
                    log.info("Win: " + str(win) + "$")
                    totalWin += 1
                    notify += f"\nWIN: " + str(win)

                totalBet += 1
                winrate = round(totalWin / totalBet * 100, 2)
                send_notify(notify)
            else:
                log.info("please try again")

        elif trend == "DOWN" and action and direction == "SELL":
            log.info(f"SELL {currency}!!!\n{trend_detail}\n{sto_detail}")
            _, id = iq.API.buy_digital_spot(currency, amount, "put", duration)
            notify = f'\nSELL: {currency}\nAT {now.strftime("%Y-%m-%d %H:%M:%S")}\nID: {id}'
            if id != "error":
                while True:
                    check, win = iq.API.check_win_digital_v2(id)
                    if check:
                        break
                totalProfit += win
                if win < 0:
                    log.info("Loss: " + str(win) + "$")
                    notify += f"\nLOSS: " + str(win)
                    totalLoss += 1
                else:
                    log.info("Win " + str(win) + "$")
                    notify += f"\nWIN: " + str(win)
                    totalWin += 1
                totalBet += 1
                winrate = round(totalWin / totalBet * 100, 2)
                send_notify(notify)
            else:
                log.info("please try again")

        iq.API.stop_candles_stream(currency, size)

    bl = iq.API.get_balance()
    msg = show_stat(bl)
    if last_hour != now.hour:
        send_notify(msg)
        last_hour = now.hour

    time.sleep(1)
