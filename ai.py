from iqoptionapi.stable_api import IQ_Option
from sklearn import tree
import time
from talib import *
import datetime
import numpy as np

while True:
    Useriq = "fbs.darkkab@gmail.com"
    Passwordiq = "1qazXSW@"
    API = IQ_Option(Useriq, Passwordiq)
    ch1, ch2 = API.connect()
    if ch1 == True:
        print("LOGIN OK")
        print(".................................................")
        break
CA = "EURUSD-OTC"
ATM = 10
TF = 60
QC = 400
RT = 1
o = 0
A = 0
ACC = []
AMX = []
AAMX = []
ABMX = []
API.start_mood_stream(CA)
API.start_candles_stream(CA, TF, QC)
while True:
    try:
        times = datetime.datetime.now()
        y = times.year
        m = times.month
        d = times.day
        h = times.hour
        t = times.minute
        s = times.second
        candles = API.get_realtime_candles(CA, TF)
        inputs = {'open': np.array([]), 'high': np.array([]), 'low': np.array([]), 'close': np.array([]),
                  'volume': np.array([])}
        for timestamp in candles:
            inputs["open"] = np.append(inputs["open"], candles[timestamp]["open"])
            inputs["high"] = np.append(inputs["high"], candles[timestamp]["max"])
            inputs["low"] = np.append(inputs["low"], candles[timestamp]["min"])
            inputs["close"] = np.append(inputs["close"], candles[timestamp]["close"])
            inputs["volume"] = np.append(inputs["volume"], candles[timestamp]["volume"])
        open = inputs["open"]
        close = inputs["close"]
        high = inputs["high"]
        low = inputs["low"]
        AB = int("%.0f" % (API.get_traders_mood(CA) * 100))
        AA = API.get_technical_indicators(CA)
        ABC = close[-1] - open[-1]
    except:
        time.sleep(5)
        pass
    if o == 5:
        A = 1
    if s == 58 and A == 0:
        for data in AA:
            print(data)
            if data['candle_size'] == 60:
                AMX.append(data['value'])
                if data['action'] == "hold":
                    M = 0
                    AMX.append(M)
                if data['action'] == "sell":
                    M = 1
                    AMX.append(M)
                if data['action'] == "buy":
                    M = 2
                    AMX.append(M)
            if data['candle_size'] == 300:
                AMX.append(data['value'])
                if data['action'] == "hold":
                    M = 0
                    AMX.append(M)
                if data['action'] == "sell":
                    M = 1
                    AMX.append(M)
                if data['action'] == "buy":
                    M = 2
                    AMX.append(M)
            if len(AMX) == 228:
                AMX.append(AB)
                AAMX.append(AMX)
                AMX = []
        if ABC > 0:
            ABC = "buy"
        elif ABC < 0:
            ABC = "sell"
        else:
            ABC = "doji"
        ACC.append(ABC)
        print(len(ACC))
        time.sleep(1)
        o = o + 1
    if A == 1:
        for data in AA:
            if data['candle_size'] == 60:
                AMX.append(data['value'])
                if data['action'] == "hold":
                    M = 0
                    AMX.append(M)
                if data['action'] == "sell":
                    M = 1
                    AMX.append(M)
                if data['action'] == "buy":
                    M = 2
                    AMX.append(M)
            if data['candle_size'] == 300:
                AMX.append(data['value'])
                if data['action'] == "hold":
                    M = 0
                    AMX.append(M)
                if data['action'] == "sell":
                    M = 1
                    AMX.append(M)
                if data['action'] == "buy":
                    M = 2
                    AMX.append(M)
            if len(AMX) == 228:
                AMX.append(AB)
                ABMX.append(AMX)
                AMX = []
        print(AAMX)
        print(len(AAMX))
        print(ACC)
        print(len(ACC))
        model = tree.DecisionTreeClassifier()
        model.fit(AAMX, ACC)
        AKM = model.predict(ABMX)
        print(AKM)
        break
