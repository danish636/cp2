import pandas as pd
from datetime import date, timedelta, datetime
import math
import numpy as np
from collections import defaultdict
from bisect import bisect_left
import collections

def load_data(path, ticker):
    data = pd.read_csv(path + ticker + ".csv", usecols=["date","open","high","low"], parse_dates=["date"])   
    return data

def rolling_finder(data, filter_days, rolling_value): 
    data = data[data["date"] >= datetime(2021,12,17) - timedelta(days=filter_days)]
    high_v = []
    open_v = []
    low_v = []
    for i in range(0,len(data)):
        try:
            df = data.iloc[i+rolling_value-1]
        except:
            break
        open_val = data.iloc[i]["open"]

        high_col = data.iloc[i:i+rolling_value]['high'].max()

        low_col = data.iloc[i:i+rolling_value]['low'].min()
        high_v.append(((high_col - open_val)/ open_val)*100)
        open_v.append(((df["open"] - open_val)/ open_val)*100)
        low_v.append(((low_col - open_val)/ open_val)*100)
    return high_v,open_v,low_v

#Order will be in 'high', 'low', 'open'
def get_median(d):
    return [d['high'].describe()['50%'], d['low'].describe()['50%'], d['open'].describe()['50%']]

#Order will be in 'high', 'low', 'open'
def get_mean(d):
    return [d['high'].describe()['mean'], d['low'].describe()['mean'], d['open'].describe()['mean']]

def get_std(d):
    return [d['high'].describe()['std'], d['low'].describe()['std'], d['open'].describe()['std']]

def bins_and_frequency(data, value):
    least_value = int(data[value].min()) 
    high_value = math.ceil(data[value].max()) + 1.0
    bins_array = np.arange(least_value, high_value, 0.05)
    count = defaultdict(int)
    bins_array.sort()
    for item in data[value]:
        pos = bisect_left(bins_array, item)
        if pos == len(bins_array):
            count[None] += 1
        else:
            count[bins_array[pos]] += 1
    od = collections.OrderedDict(sorted(count.items()))
    frequency = []
    probability=[]
    for k, v in od.items():
        frequency.append(v)
    for i in frequency:
            probability.append((i/sum(frequency))*100)
    cumulative = np.cumsum(probability)
    return frequency,bins_array,probability,cumulative

def get_cumsum(cum, prob):
    for i,c in enumerate(cum):
        if c>=prob:
            return i, c

def get_last_col(d, day):
    data = d[-day:]
    low_min_idx = data['low'].idxmin()
    high_max_idx = data['high'].idxmax()
    return (low_min_idx, high_max_idx)

