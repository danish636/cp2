from datetime import datetime, date
from django.http.response import HttpResponse
from django.shortcuts import render
import json
import vaex
import numpy as np
import pandas as pd
from pandas.core.arrays import integer
from pandas.core.frame import DataFrame
from . import final_api, invex_avg
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import glob
import os
import os.path
from datetime import date, timedelta
import math
from collections import defaultdict
from bisect import bisect_left
import collections
from urllib.request import urlopen
import mimetypes
from pathlib import Path
from django.core.files.storage import FileSystemStorage
import statistics
import requests
from .models import *
from .serializer import *
import itertools

# with open("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/etf_list.json") as f:
#     etf_d = json.load(f)
# etf_list = [i["symbol"] for i in etf_d]

base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media")
etf_file = os.path.join(base_path, "etf_list.json")
with open(etf_file, "r") as f:
    etf_d = json.load(f)
etf_list = [i["symbol"] for i in etf_d] #@danish

# Create your views here.
def home(request):
    return render(request, "home.html")

def daily(request):
    return render(request, "daily.html")

# def load_data(path, ticker, in_date):
#     data = pd.read_csv(path + ticker + ".csv", usecols=["date","open","high","low", "close"], parse_dates=["date"])
#     data = data[data['date'] <= in_date]
#     return data

def load_data(path, ticker, in_date):
    file_path = os.path.join(path, f"{ticker}.csv")
    data = pd.read_csv(file_path, usecols=["date", "open", "high", "low", "close"], parse_dates=["date"])
    data = data[data['date'] <= in_date]
    return data #@danish

def rolling_finder(data, filter_days, rolling_value, in_date): 
    # data["date"] = pd.to_datetime(data["date"])
    # #print(len(data))
    #print(in_date)
    data = data[data["date"] >= (in_date - timedelta(days=filter_days))]
    # #print(len(data))
    high_v = []
    open_v = []
    low_v = []
    for i in range(0,len(data)):
        # #print(data.iloc[i+rolling_value-1])
        try:
            # #print('try')
            df = data.iloc[i+rolling_value-1]
            #print(df)
        except:
            #print('except---------')
            break
        open_val = data.iloc[i]["open"]

        high_col = data.iloc[i:i+rolling_value]['high'].max()
        #print(high_col)

        low_col = data.iloc[i:i+rolling_value]['low'].min()
        high_v.append(((high_col - open_val)/ open_val)*100)
        open_v.append(((df["open"] - open_val)/ open_val)*100)
        low_v.append(((low_col - open_val)/ open_val)*100)
    #print(high_v)
    return high_v,open_v,low_v

#Order will be in 'high', 'low', 'open'
def get_median(d):
    return [d['high'].describe()['50%']/100, d['low'].describe()['50%']/100, d['open'].describe()['50%']/100]

#Order will be in 'high', 'low', 'open'
def get_mean(d):
    return [d['high'].describe()['mean']/100, d['low'].describe()['mean']/100, d['open'].describe()['mean']/100]

def get_std(d):
    return [d['high'].describe()['std']/100, d['low'].describe()['std']/100, d['open'].describe()['std']/100]

def bins_and_frequency(data, value):
    # #print('bins frequency')
    # #print(data)
    # #print(value)
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
    bins = []
    for k, v in od.items():
        bins.append(k)
        frequency.append(v)
    for i in frequency:
            probability.append((i/sum(frequency))*100)
    if value == "low":
        cumulative = np.cumsum(probability[::-1])
    else:
        cumulative = np.cumsum(probability)
    return frequency,bins,probability,cumulative

def get_cumsum(cum, prob):
    for i,c in enumerate(cum):
        if c>=prob:
            return i, c

def get_last_col(d, day):
    data = d[-day:]
    low_min_idx = data['low'].idxmin()
    high_max_idx = data['high'].idxmax()
    return (low_min_idx, high_max_idx)

def get_high_close_eod(d, day, close_val, h_bin):
    data = d[-day:]
    low_min_idx = data.low.sort_values().index[0] #low nu minimum
    predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
    count_i = 0
    while predicted_high<close_val:
        #data = data.drop(data.index[low_min_idx])
        # low_min_idx = data['low'].idxmin()
        low_min_idx = data.low.sort_values().index[count_i]
        predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
        count_i += 1
        if count_i==day:
            break
    if count_i == day:
        return (float(close_val + ((close_val*h_bin)/100.0)), close_val, "close_val")
    else:
        return (float(d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)), low_min_idx, "high_idx_val")

def get_low_close_eod(d, day, close_val, l_bin):
    data = d[-day:]
    high_max_idx = data.high.sort_values().index[-1] # high nu maximum
    predicted_close = d['open'].iloc[high_max_idx] + (d['open'].iloc[high_max_idx]*l_bin)/100.0
    count_i = 0
    while predicted_close>=close_val:
        # #print(data.index)
        # data = data.drop(data.index[high_max_idx-len(d)+day])
        high_max_idx = data.high.sort_values().index[-(count_i+1)]
        predicted_close = d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)
        count_i += 1
        if count_i==day:
            break
    if count_i == day:
        return (float(close_val + ((close_val*l_bin)/100.0)), close_val, "close_val")
    else:
        return (float(d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)), high_max_idx, "low_idx_val")

def get_last_col_api(d, day, latest_api_data):
    data = d[-(day - 1):]
    high_ls = []
    low_ls = []
    for lad in latest_api_data["historical"]:
        # try:
        if (lad['high'] != None) and (lad['low'] != None):
            # #print(lad['high'])
            high_ls.append(float(lad['high']))
            low_ls.append(float(lad['low']))

    # #print(high_ls)
    high_val = float(max(high_ls))
    low_val = float(min(low_ls))
    if latest_api_data["historical"][0]['open'] != None:
        open_val = float(latest_api_data["historical"][0]['open'])
    elif latest_api_data["historical"][1]['open'] != None:
        open_val = float(latest_api_data["historical"][1]['open'])
    else:
        open_val = float(latest_api_data["historical"][-1]['open'])
    data.append([high_val, open_val, low_val])
    low_min_idx = data['low'].idxmin()
    high_max_idx = data['high'].idxmax()
    return (low_min_idx, high_max_idx)

def get_high_close_api(d, day, latest_api_data, close_val, h_bin):
    data = d[-(day - 1):]
    high_ls = []
    low_ls = []
    for lad in latest_api_data["historical"]:
        if (lad['high'] != None) and (lad['low'] != None):
            high_ls.append(float(lad['high']))
            low_ls.append(float(lad['low']))
    high_val = float(max(high_ls))
    low_val = float(min(low_ls))
    if latest_api_data["historical"][0]['open'] != None:
        open_val = float(latest_api_data["historical"][0]['open'])
    elif latest_api_data[1]['open'] != None:
        open_val = float(latest_api_data["historical"][1]['open'])
    else:
        open_val = float(latest_api_data["historical"][-1]['open'])
    data.append([close_val, high_val, low_val, open_val])
    low_min_idx = data.low.sort_values().index[0]   ## [4,5,6,3,8,9,10] => [3,8,9,10]
    # high_max_idx = data['high'].idxmax()
    predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
    count_i = 0
    while predicted_high<close_val:
        if count_i==day:
            break
        # data = data.drop(data.index[low_min_idx-len(d)+day])
        # low_min_idx = data['low'].idxmin()
        low_min_idx = data.low.sort_values().index[count_i]
        predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
        count_i += 1

    if count_i == day:
        return (float(close_val + ((close_val*h_bin)/100.0)), close_val, "close_val")
    else:
        return (float(d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)), low_min_idx, "high_idx_val")

def get_low_close_api(d, day, latest_api_data, close_val, l_bin):
    data = d[-(day - 1):]
    high_ls = []
    low_ls = []
    for lad in latest_api_data["historical"]:
        if (lad['high'] != None) and (lad['low'] != None):
            high_ls.append(float(lad['high']))
            low_ls.append(float(lad['low']))
    high_val = float(max(high_ls))
    low_val = float(min(low_ls))
    if latest_api_data["historical"][0]['open'] != None:
        open_val = float(latest_api_data["historical"][0]['open'])
    elif latest_api_data[1]['open'] != None:
        open_val = float(latest_api_data["historical"][1]['open'])
    else:
        open_val = float(latest_api_data["historical"][-1]['open'])
    data.append([close_val, high_val, low_val, open_val])
    # low_min_idx = data['low'].idxmin()
    high_max_idx = data.high.sort_values().index[-1]
    predicted_close = d['open'].iloc[high_max_idx] + (d['open'].iloc[high_max_idx]*l_bin)/100.0
    count_i = 0
    while predicted_close>=close_val:
        # data = data.drop(data.index[high_max_idx-len(d)+day])
        # high_max_idx = data['high'].idxmax()
        high_max_idx = data.high.sort_values().index[-(count_i+1)]
        predicted_close = d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)
        count_i += 1
        if count_i==day:
            break
    if count_i == day:
        return (float(close_val + ((close_val*l_bin)/100.0)), close_val, "close_val")
    else:
        return (float(d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)), high_max_idx, "low_idx_val")
    
    
@api_view(['GET', 'POST'])
def predict_price(request):
    request = json.loads(request.body.decode('utf-8'))
    #path = "/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "hist data2") #@danish
    ticker = request['ticker']
    filter_days = int(request['filter_days'])   #180
    in_date = datetime.strptime(request['in_date'], "%Y-%m-%d")
    rolling_value = [5, 10, 20, 60]#5
    percentage = int(request['percentage'])#65
    percentages = [90,80,70,60,50,40,30,20]
    percentages.append(percentage)
    final_dict = {}
    
    data = load_data(path, ticker, in_date)
    # url_latest_api = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
    latest_api_data = {}
    #latest_api_data["historical"] = pd.read_csv("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/" + ticker + ".csv").to_dict('records')
    latest_api_data["historical"] = pd.read_csv(os.path.join(path, f"{ticker}.csv")).to_dict('records') #@danish
    #old
    #f"https://cloud.iexapis.com/stable/stock/{ticker.lower()}/intraday-prices?token=pk_55e019e9e4db4baaa9493d29a095bf63"
    # response = urlopen(url_latest_api)
    # latest_api_data = json.loads(response.read())
    
    d_date = datetime.utcnow() - timedelta(hours=4)
    nw = datetime.now()
    hrs = nw.hour
    mins = nw.minute
    secs = nw.second
    zero = timedelta(seconds = secs+mins*60+hrs*3600)
    st = nw - zero # this take me to 0 hours. 
    time1 = st + timedelta(seconds=9*3600+30*60) # this gives 09:30 AM
    time2 = st + timedelta(seconds=16*3600+1*60) # 04:00 PM

    if d_date.time()>=time1.time() and d_date.time()<=time2.time():
        # If market is Open
        for rolling in rolling_value:
            pred_open_high = []
            pred_open_low = []
            h_bins_array = []
            l_bins_array = []
            pred_final_open_high = []
            pred_final_open_low = []
            month_fixed_high = []
            month_fixed_low = []

            low_min_idx, high_max_idx = get_last_col_api(data, rolling, latest_api_data)
            data_last = data[-rolling:]
            if rolling != 5:
                half_roll = int(rolling/2)
                open_final_val = data_last['open'].iloc[half_roll+1]

            for idx,percentage in enumerate(percentages):
                if idx==0:
                    #For 90% only calculate the value
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]

                    predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
                    predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
                    close_val = float(data.tail(1)['close'])

                    if rolling != 5:
                        pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                        pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))

                    if predicted_high>=close_val:
                        pred_open_high.append(predicted_high)
                        r_type_high = "high_idx_val"
                        val_id_high = low_min_idx
                    else:
                        p_high, val_id_high, r_type_high = get_high_close_api(data, rolling, latest_api_data, close_val, h_bin)
                        pred_open_high.append(p_high)
                    
                    if predicted_low<close_val:
                        pred_open_low.append(predicted_low)
                        r_type_low = "low_idx_val"
                        val_id_low = high_max_idx
                    else:
                        p_low, val_id_low, r_type_low = get_low_close_api(data, rolling, latest_api_data, close_val, l_bin)
                        pred_open_low.append(p_low)
                else:
                    #For every other percentage
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]
                    close_val = float(data.tail(1)['close'])
                    
                    if rolling != 5:
                        pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                        pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))

                    if r_type_high == "high_idx_val":
                        predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
                        val_l = data['open'].iloc[val_id_high]

                    else:
                        predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
                        val_l = val_id_high
                        
                    if r_type_low == "low_idx_val":
                        predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
                        val_h = data['open'].iloc[val_id_low]
                    else:
                        predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
                        val_h = val_id_low
                    pred_open_high.append(predicted_high)
                    pred_open_low.append(predicted_low)
                    
                if rolling == 20:
                    open_val_cal = float(data.tail(1)['close'])
                    month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
                    month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
                    
                h_bins_array.append(h_bin)
                l_bins_array.append(l_bin)

            median = get_median(d)[2]
            standard_deviation = get_std(d)[2]
            
            first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
            second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
            third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
            
            first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
            second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
            third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
            if rolling != 5:
                pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
                pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
                pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
                
            if rolling == 20:
                open_val_cal = float(data.tail(1)['close'])
                month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
                month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
                month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
                
            if rolling == 5:
                final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":[], "fixed_predicted_low":[], "fixed_predicted_first_std":[], "fixed_predicted_second_std":[], "fixed_predicted_third_std":[]}
            elif rolling == 20:
                final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS, "month_fixed_high":month_fixed_low[::-1], "month_fixed_low":month_fixed_high[::-1], "month_pred_final_FS":month_pred_final_FS, "month_pred_final_SS":month_pred_final_SS, "month_pred_final_TS":month_pred_final_TS}
            else:
                final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS}

    else:
        #If market is Close 
        for rolling in rolling_value:
            # #print(rolling)
            pred_open_high = []
            pred_open_low = []
            h_bins_array = []
            l_bins_array = []
            pred_final_open_high = []
            pred_final_open_low = []
            month_fixed_high = []
            month_fixed_low = []
            low_min_idx, high_max_idx = get_last_col(data, rolling)
            data_last = data[-rolling:]
            if rolling != 5:
                half_roll = int(rolling/2)
                open_final_val = data_last['open'].iloc[half_roll+1]

            for idx,percentage in enumerate(percentages):
                if idx==0:
                    #For 90% only calculate the value
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]

                    predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
                    predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
                    #print(data.tail(1))
                    close_val = float(data.tail(1)['close'])

                    if rolling != 5:
                        pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                        pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))

                    if predicted_high>=close_val:
                        pred_open_high.append(predicted_high)
                        r_type_high = "high_idx_val"
                        val_id_high = low_min_idx
                    else:
                        p_high, val_id_high, r_type_high = get_high_close_eod(data, rolling, close_val, h_bin)
                        pred_open_high.append(p_high)
                    
                    if predicted_low<close_val:
                        pred_open_low.append(predicted_low)
                        r_type_low = "low_idx_val"
                        val_id_low = high_max_idx
                    else:
                        p_low, val_id_low, r_type_low = get_low_close_eod(data, rolling, close_val, l_bin)
                        pred_open_low.append(p_low)
                    
                    
                else:
                    #For every other percentage
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]
                    close_val = float(data.tail(1)['close'])

                    if rolling != 5:
                        pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                        pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
                        
                    if r_type_high == "high_idx_val":
                        predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
                        val_l = data['open'].iloc[val_id_high]
                    else:
                        predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
                        val_l = val_id_high
                        
                    if r_type_low == "low_idx_val":
                        predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
                        val_h = data['open'].iloc[val_id_low]
                    else:
                        predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
                        val_h = val_id_low
                    pred_open_high.append(predicted_high)
                    pred_open_low.append(predicted_low)
                    
                if rolling == 20:
                    open_val_cal = float(data.tail(1)['close'])
                    month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
                    month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
                    
                h_bins_array.append(h_bin)
                l_bins_array.append(l_bin)

            median = get_median(d)[2]
            standard_deviation = get_std(d)[2]
            
            first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
            second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
            third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
            
            first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
            second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
            third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
        
            if rolling != 5:
                pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
                pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
                pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
            
            if rolling == 20:
                open_val_cal = float(data.tail(1)['close'])
                month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
                month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
                month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
                
            if rolling == 5:
                final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":[], "fixed_predicted_low":[], "fixed_predicted_first_std":[], "fixed_predicted_second_std":[], "fixed_predicted_third_std":[]}
            elif rolling == 20:
                final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS, "month_fixed_high":month_fixed_low[::-1], "month_fixed_low":month_fixed_high[::-1], "month_pred_final_FS":month_pred_final_FS, "month_pred_final_SS":month_pred_final_SS, "month_pred_final_TS":month_pred_final_TS}
            else:
                final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS}
    # final_dict["Access-Control-Allow-Origin"] = "*"
    response =  HttpResponse(json.dumps(final_dict, indent=4,default=str),content_type = "application/json")
    response["Access-Control-Allow-Origin"] = "*"
    return response


#=============================================================---------++++++------------+++++++-----------++++++---------=========================================================================================

@api_view(['GET', 'POST'])
def predict_price_new(request):
    request = json.loads(request.body.decode('utf-8'))
    #path = "/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "hist data2")  # @danish
    ticker = request['ticker']
    filter_days = int(request['filter_days'])   #180
    rolling = int(request["rolling"])
    in_date = datetime.strptime(request['in_date'], "%Y-%m-%d")
    if rolling == 5:
        dates = [in_date, in_date - timedelta(days=7)]
    elif rolling == 10:
        dates = [in_date, in_date - timedelta(days=14)]
    elif rolling == 20:
        dates = [in_date, in_date - timedelta(days=30)]
    elif rolling == 60:
        dates = [in_date, in_date - timedelta(days=90)]
    final_dates = []
    # rolling_value = [5, 10, 20, 60]#5
    #df = pd.read_csv(path + ticker + ".csv", usecols = ["close","date"], parse_dates=["date"])
    df = pd.read_csv(os.path.join(path, f"{ticker}.csv"), usecols=["close", "date"], parse_dates=["date"]) #@danish
    d = df[(df["date"] <= dates[0]) & (df["date"] >= dates[1])]

    percentages = [95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5]

    final_dict = {"close":list(d["close"]), "dates":list(d["date"].dt.date)}
    for in_date in dates:
        data = load_data(path, ticker, in_date)
        # url_latest_api = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
        latest_api_data = {}
        #latest_api_data["historical"] = pd.read_csv("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/" + ticker + ".csv").to_dict('records')
        latest_api_data["historical"] = pd.read_csv(os.path.join(path, f"{ticker}.csv")).to_dict('records')  # @danish
        #old
        #f"https://cloud.iexapis.com/stable/stock/{ticker.lower()}/intraday-prices?token=pk_55e019e9e4db4baaa9493d29a095bf63"
        # response = urlopen(url_latest_api)
        # latest_api_data = json.loads(response.read())
        
        d_date = datetime.utcnow() - timedelta(hours=4)
        nw = datetime.now()
        hrs = nw.hour
        mins = nw.minute
        secs = nw.second
        zero = timedelta(seconds = secs+mins*60+hrs*3600)
        st = nw - zero # this take me to 0 hours. 
        time1 = st + timedelta(seconds=9*3600+30*60) # this gives 09:30 AM
        time2 = st + timedelta(seconds=16*3600+1*60) # 04:00 PM
    
        if d_date.time()>=time1.time() and d_date.time()<=time2.time():
            # If market is Open
            pred_open_high = []
            pred_open_low = []
            h_bins_array = []
            l_bins_array = []
            pred_final_open_high = []
            pred_final_open_low = []
            month_fixed_high = []
            month_fixed_low = []
    
            low_min_idx, high_max_idx = get_last_col_api(data, rolling, latest_api_data)
            data_last = data[-rolling:]
            if rolling != 5:
                half_roll = int(rolling/2)
                open_final_val = data_last['open'].iloc[half_roll+1]
    
            for idx,percentage in enumerate(percentages):
                if idx==0:
                    #For 90% only calculate the value
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]
    
                    predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
                    predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
                    close_val = float(data.tail(1)['close'])
    
                    if rolling != 5:
                        pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                        pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
    
                    if predicted_high>=close_val:
                        pred_open_high.append(predicted_high)
                        r_type_high = "high_idx_val"
                        val_id_high = low_min_idx
                    else:
                        p_high, val_id_high, r_type_high = get_high_close_api(data, rolling, latest_api_data, close_val, h_bin)
                        pred_open_high.append(p_high)
                    
                    if predicted_low<close_val:
                        pred_open_low.append(predicted_low)
                        r_type_low = "low_idx_val"
                        val_id_low = high_max_idx
                    else:
                        p_low, val_id_low, r_type_low = get_low_close_api(data, rolling, latest_api_data, close_val, l_bin)
                        pred_open_low.append(p_low)
                else:
                    #For every other percentage
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]
                    close_val = float(data.tail(1)['close'])
                    
                    if rolling != 5:
                        pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                        pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
    
                    if r_type_high == "high_idx_val":
                        predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
                        val_l = data['open'].iloc[val_id_high]
    
                    else:
                        predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
                        val_l = val_id_high
                        
                    if r_type_low == "low_idx_val":
                        predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
                        val_h = data['open'].iloc[val_id_low]
                    else:
                        predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
                        val_h = val_id_low
                    pred_open_high.append(predicted_high)
                    pred_open_low.append(predicted_low)
                    
                # if rolling == 20:
                #     open_val_cal = float(data.tail(1)['close'])
                #     month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
                #     month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
                    
                h_bins_array.append(h_bin)
            #     l_bins_array.append(l_bin)
    
            # median = get_median(d)[2]
            # standard_deviation = get_std(d)[2]
            
            # first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
            # second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
            # third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
            
            # first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
            # second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
            # third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
            # if rolling != 5:
            #     pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
            #     pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
            #     pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
                
            # if rolling == 20:
            #     open_val_cal = float(data.tail(1)['close'])
            #     month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
            #     month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
            #     month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
                
            final_dict[rolling] = {"predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "percentage":percentages[::-1]}
            
        else:
            #If market is Close 
            # #print(rolling)
            pred_open_high = []
            pred_open_low = []
            h_bins_array = []
            l_bins_array = []
         
            low_min_idx, high_max_idx = get_last_col(data, rolling)
            data_last = data[-rolling:]
            if rolling != 5:
                half_roll = int(rolling/2)
                open_final_val = data_last['open'].iloc[half_roll+1]
    
            for idx,percentage in enumerate(percentages):
                if idx==0:
                    #For 90% only calculate the value
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]
    
                    predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
                    predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
                    #print(data.tail(1))
                    close_val = float(data.tail(1)['close'])
    
                    # if rolling != 5:
                    #     pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                    #     pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
    
                    if predicted_high>=close_val:
                        pred_open_high.append(predicted_high)
                        r_type_high = "high_idx_val"
                        val_id_high = low_min_idx
                    else:
                        p_high, val_id_high, r_type_high = get_high_close_eod(data, rolling, close_val, h_bin)
                        pred_open_high.append(p_high)
                    
                    if predicted_low<close_val:
                        pred_open_low.append(predicted_low)
                        r_type_low = "low_idx_val"
                        val_id_low = high_max_idx
                    else:
                        p_low, val_id_low, r_type_low = get_low_close_eod(data, rolling, close_val, l_bin)
                        pred_open_low.append(p_low)
                    
                    
                else:
                    #For every other percentage
                    d = pd.DataFrame([])
                    d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                    high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                    index, cum_cal = get_cumsum(high_cum, percentage)
                    h_bin = high_bins[index]
                
                    low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                    index, cum_cal = get_cumsum(low_cum, percentage)
                    l_bin = low_bins[len(low_bins) - index]
                
                    open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                    index, cum_cal = get_cumsum(open_cum, percentage)
                    o_bin = open_bins[index]
                    close_val = float(data.tail(1)['close'])
    
                    # if rolling != 5:
                    #     pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                    #     pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
                        
                    if r_type_high == "high_idx_val":
                        predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
                        val_l = data['open'].iloc[val_id_high]
                    else:
                        predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
                        val_l = val_id_high
                        
                    if r_type_low == "low_idx_val":
                        predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
                        val_h = data['open'].iloc[val_id_low]
                    else:
                        predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
                        val_h = val_id_low
                    pred_open_high.append(predicted_high)
                    pred_open_low.append(predicted_low)
                    
                # if rolling == 20:
                #     open_val_cal = float(data.tail(1)['close'])
                #     month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
                #     month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
                    
                h_bins_array.append(h_bin)
                l_bins_array.append(l_bin)
    
            # median = get_median(d)[2]
            # standard_deviation = get_std(d)[2]
            
            # first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
            # second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
            # third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
            
            # first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
            # second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
            # third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
        
            # if rolling != 5:
            #     pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
            #     pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
            #     pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
            
            # if rolling == 20:
            #     open_val_cal = float(data.tail(1)['close'])
            #     month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
            #     month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
            #     month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
                
            final_dict[in_date.strftime("%d-%m-%Y")] = {"predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1],"percentage":percentages[::-1]}
            
    # final_dict["Access-Control-Allow-Origin"] = "*"
    response =  HttpResponse(json.dumps(final_dict, indent=4,default=str),content_type = "application/json")
    response["Access-Control-Allow-Origin"] = "*"
    return response


#=============================================================---------++++++------------+++++++-----------++++++---------=========================================================================================


def predict_price_csv(data, filter_days, percentage):
    filter_days = int(filter_days)  #180
    rolling_value = [5, 10, 20, 60]#5
    percentage = int(percentage)#65
    percentages = [90,80,70,60,50,40,30,20]
    percentages.append(percentage)
    final_dict = {}
    today = date.today()
    in_date = today.strftime("%Y-%m-%d")
    in_date = datetime.strptime(in_date, "%Y-%m-%d")
    data = data
    d_date = datetime.utcnow() - timedelta(hours=4)
    for rolling in rolling_value:
        #print(f"===================================={rolling}")
        pred_open_high = []
        pred_open_low = []
        h_bins_array = []
        l_bins_array = []
        pred_final_open_high = []
        pred_final_open_low = []
        month_fixed_high = []
        month_fixed_low = []
        
        low_min_idx, high_max_idx = get_last_col(data, rolling)
        data_last = data[-rolling:]
        
        if rolling != 5:
            half_roll = int(rolling/2)
            open_final_val = data_last['open'].iloc[half_roll+1]

        for idx,percentage in enumerate(percentages):
            if idx==0:
                #For 90% only calculate the value
                d = pd.DataFrame([])
                d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                #print(d)
                high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                index, cum_cal = get_cumsum(high_cum, percentage)
                h_bin = high_bins[index]
            
                low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                index, cum_cal = get_cumsum(low_cum, percentage)
                l_bin = low_bins[len(low_bins) - index]
            
                open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                index, cum_cal = get_cumsum(open_cum, percentage)
                o_bin = open_bins[index]

                predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
                predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
                # #print(data.tail(1))
                close_val = float(data.tail(1)['close'])

                if rolling != 5:
                    pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                    pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))

                if predicted_high>=close_val:
                    pred_open_high.append(predicted_high)
                    r_type_high = "high_idx_val"
                    val_id_high = low_min_idx
                else:
                    p_high, val_id_high, r_type_high = get_high_close_eod(data, rolling, close_val, h_bin)
                    pred_open_high.append(p_high)
                
                if predicted_low<close_val:
                    pred_open_low.append(predicted_low)
                    r_type_low = "low_idx_val"
                    val_id_low = high_max_idx
                else:
                    p_low, val_id_low, r_type_low = get_low_close_eod(data, rolling, close_val, l_bin)
                    pred_open_low.append(p_low)
                
                
            else:
                #For every other percentage
                d = pd.DataFrame([])
                d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                index, cum_cal = get_cumsum(high_cum, percentage)
                h_bin = high_bins[index]
            
                low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                index, cum_cal = get_cumsum(low_cum, percentage)
                l_bin = low_bins[len(low_bins) - index]
            
                open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                index, cum_cal = get_cumsum(open_cum, percentage)
                o_bin = open_bins[index]
                close_val = float(data.tail(1)['close'])

                if rolling != 5:
                    pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
                    pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
                    
                if r_type_high == "high_idx_val":
                    predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
                    val_l = data['open'].iloc[val_id_high]
                else:
                    predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
                    val_l = val_id_high
                    
                if r_type_low == "low_idx_val":
                    predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
                    val_h = data['open'].iloc[val_id_low]
                else:
                    predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
                    val_h = val_id_low
                pred_open_high.append(predicted_high)
                pred_open_low.append(predicted_low)
                
            if rolling == 20:
                open_val_cal = float(data.tail(1)['close'])
                month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
                month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
                
            h_bins_array.append(h_bin)
            l_bins_array.append(l_bin)

        median = get_median(d)[2]
        standard_deviation = get_std(d)[2]
        
        first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
        second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
        third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
        
        first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
        second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
        third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
    
        if rolling != 5:
            pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
            pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
            pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
        
        if rolling == 20:
            open_val_cal = float(data.tail(1)['close'])
            month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
            month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
            month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
            
        if rolling == 5:
            final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":[], "fixed_predicted_low":[], "fixed_predicted_first_std":[], "fixed_predicted_second_std":[], "fixed_predicted_third_std":[]}
        elif rolling == 20:
            final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS, "month_fixed_high":month_fixed_low[::-1], "month_fixed_low":month_fixed_high[::-1], "month_pred_final_FS":month_pred_final_FS, "month_pred_final_SS":month_pred_final_SS, "month_pred_final_TS":month_pred_final_TS}
        else:
            final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS}
    return final_dict


#######################################################################################################################################

@api_view(['GET', 'POST'])
def predict_price_graph(request):
    request = json.loads(request.body.decode('utf-8'))
    #path = "/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "hist data2")  # @danish

    date = request['date']
    date_range = request['date_range']
    ticker = request['ticker']
    filter_days = int(request['filter_days'])
    rolling = int(request['rolling'])
    date_time = pd.to_datetime(date, format='%Y-%m-%d')
    in_date = datetime.strptime(date, "%Y-%m-%d")

    #commone for both
    percentages = [95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5]
    new_data = {}
    
    data = load_data(path, ticker, in_date)
    # f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?serietype=line&apikey=b1360803f80dd08bdd0211c5c004ad03"
    # f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
    # url_latest_api = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
    latest_api_data = {}
    #latest_api_data["historical"] = pd.read_csv("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/" + ticker + ".csv").to_dict('records')
    latest_api_data["historical"] = pd.read_csv(os.path.join(path, f"{ticker}.csv")).to_dict('records')  # @danish

    #old API
    #f"https://cloud.iexapis.com/stable/stock/{ticker.lower()}/intraday-prices?token=pk_55e019e9e4db4baaa9493d29a095bf63"
    
    # response = urlopen(url_latest_api)
    # latest_api_data = json.loads(response.read())
    
    d_date = datetime.utcnow() - timedelta(hours=4)
    nw = datetime.now()
    hrs = nw.hour
    mins = nw.minute
    secs = nw.second
    zero = timedelta(seconds = secs+mins*60+hrs*3600)
    st = nw - zero # this take me to 0 hours. 
    time1 = st + timedelta(seconds=9*3600+30*60) # this gives 09:30 AM
    time2 = st + timedelta(seconds=16*3600+1*60) # 04:00 PM

    if d_date.time()>=time1.time() and d_date.time()<=time2.time():
        # If market is Open

        pred_open_high = []
        pred_open_low = []
        h_bins_array = []
        l_bins_array = []
        pred_final_open_high = []
        pred_final_open_low = []
        month_fixed_high = []
        month_fixed_low = []

        low_min_idx, high_max_idx = get_last_col_api(data, rolling, latest_api_data)
        data_last = data[-rolling:]
        if rolling != 5:
            half_roll = int(rolling/2)
            open_final_val = data_last['open'].iloc[half_roll+1]
        else:
            half_roll = int((rolling-1)/2)
            open_final_val = data_last['open'].iloc[half_roll+1]

        for idx,percentage in enumerate(percentages):
            #For 90% only calculate the value
            d = pd.DataFrame([])
            d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
            high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
            index, cum_cal = get_cumsum(high_cum, percentage)
            h_bin = high_bins[index]
        
            low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
            index, cum_cal = get_cumsum(low_cum, percentage)
            l_bin = low_bins[len(low_bins) - index]
        
            open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
            index, cum_cal = get_cumsum(open_cum, percentage)
            o_bin = open_bins[index]
            close_val = float(data.tail(1)['close'])
          
            predicted_high = close_val + ((close_val*h_bin)/100.0)
            predicted_low = close_val + ((close_val*l_bin)/100.0)
            pred_open_high.append(predicted_high)
            pred_open_low.append(predicted_low)
            h_bins_array.append(h_bin)
            l_bins_array.append(-1*(l_bin))
        new_data[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1]}

    else:
        #If market is Close 
        pred_open_high = []
        pred_open_low = []
        h_bins_array = []
        l_bins_array = []
        pred_final_open_high = []
        pred_final_open_low = []
        month_fixed_high = []
        month_fixed_low = []
     
        low_min_idx, high_max_idx = get_last_col(data, rolling)
        data_last = data[-rolling:]
        if rolling != 5:
            half_roll = int(rolling/2)
            open_final_val = data_last['open'].iloc[half_roll+1]
        else:
            half_roll = int((rolling-1)/2)
            open_final_val = data_last['open'].iloc[half_roll+1]

        for idx,percentage in enumerate(percentages):
            #For 90% only calculate the value
            d = pd.DataFrame([])
            d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
            high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
            index, cum_cal = get_cumsum(high_cum, percentage)
            h_bin = high_bins[index]
        
            low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
            index, cum_cal = get_cumsum(low_cum, percentage)
            l_bin = low_bins[len(low_bins) - index]
        
            open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
            index, cum_cal = get_cumsum(open_cum, percentage)
            o_bin = open_bins[index]
            close_val = float(data.tail(1)['close'])
            
            predicted_high = close_val + ((close_val*h_bin)/100.0)
            predicted_low = close_val + ((close_val*l_bin)/100.0)
            pred_open_high.append(predicted_high)
            pred_open_low.append(predicted_low)
            
            h_bins_array.append(h_bin)
            l_bins_array.append(-1*(l_bin))
        new_data[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1]}

    temp = date_range[-1]
    temp_value = int(date_range[:-1])
    if temp.lower() == "d":
        date_range_date = date_time - timedelta(days=temp_value)
    elif temp.lower() == "m":
        date_range_date = date_time - timedelta(days=temp_value*30)
    elif temp.lower() == "y":
        date_range_date = date_time - timedelta(days=temp_value*365)
    else:
        return None
    
    # start_date = str(date_time).split(" ")[0]
    # end_date = str(date_range_date).split(" ")[0]
    # d = requests.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={end_date}&to={start_date}&apikey=b1360803f80dd08bdd0211c5c004ad03')
    # data = d.json()
    # df = pd.DataFrame(data['historical'])

    #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/'+ticker+'.csv',parse_dates=['date'])
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "hist data2")  # @danish
    df = pd.read_csv(os.path.join(path, f"{ticker}.csv"), parse_dates=['date'])
    df = df[(df["date"] >= date_range_date) & (df["date"] <= date_time)]
    df2 = df[::-1]
    temp_date = date_time
    while True:
        try:
            next_day = str(temp_date).split(" ")[0]
            next_day = next_day.split("-")[::-1]
            next_day = "-".join(next_day)
            new_pred_high = new_data[rolling]['predicted_high']
            new_pred_low = new_data[rolling]["predicted_low"]
            percentages = percentages[::-1]
            break
        except:
            temp_date = temp_date + timedelta(days=1)
    x_dates = percentages
    y_values_high = new_pred_high
    y_values_low = new_pred_low

    final_dict = {}
    final_dict['date'] = df2['date'].to_list()
    final_dict['open'] = df2['open'].to_list()
    final_dict['high'] = df2['high'].to_list()
    final_dict['low'] = df2['low'].to_list()
    final_dict['close'] = df2['close'].to_list()

    final_dict['percentages'] = x_dates
    final_dict['pred_high'] = y_values_high
    final_dict['pred_low'] = y_values_low
    final_dict['pred_high_percentage'] = h_bins_array[::-1]
    final_dict['pred_low_percentage'] = l_bins_array[::-1]

    return  HttpResponse(json.dumps(final_dict, indent=4,default=str),content_type = "application/json")
 
@api_view(['GET', 'POST'])   
def predict_price_hv_graph(request):
    request = json.loads(request.body.decode('utf-8'))
    #path = "/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "hist data2")  # @danish
    date = request['date']
    # date_range = request['date_range']
    ticker = request['ticker']
    filter_days = int(request['date_range'])
    rollings = [22, 44, 65, 86, 108, 130, 259]
    date_time = pd.to_datetime(date, format='%Y-%m-%d')
    in_date = datetime.strptime(date, "%Y-%m-%d")

    #commone for both
    percentage = 65
    new_data = {}
    
    data = load_data(path, ticker, in_date)
    # f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?serietype=line&apikey=b1360803f80dd08bdd0211c5c004ad03"
    # f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
    # url_latest_api = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
    latest_api_data = {}
    #latest_api_data["historical"] = pd.read_csv("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/" + ticker + ".csv").to_dict('records')
    latest_api_data["historical"] = pd.read_csv(os.path.join(path, f"{ticker}.csv")).to_dict('records') #@danish

    #old API
    #f"https://cloud.iexapis.com/stable/stock/{ticker.lower()}/intraday-prices?token=pk_55e019e9e4db4baaa9493d29a095bf63"
    
    # response = urlopen(url_latest_api)
    # latest_api_data = json.loads(response.read())
    
    d_date = datetime.utcnow() - timedelta(hours=4) 
    nw = datetime.now()
    hrs = nw.hour
    mins = nw.minute
    secs = nw.second
    zero = timedelta(seconds = secs+mins*60+hrs*3600)
    st = nw - zero # this take me to 0 hours. 
    time1 = st + timedelta(seconds=9*3600+30*60) # this gives 09:30 AM
    time2 = st + timedelta(seconds=16*3600+1*60) # 04:00 PM

    if d_date.time()>=time1.time() and d_date.time()<=time2.time():
        # If market is Open

        pred_open_high = []
        pred_open_low = []
        h_bins_array = []
        l_bins_array = []
        pred_final_open_high = []
        pred_final_open_low = []
        month_fixed_high = []
        month_fixed_low = []
        
        for idx,rolling in enumerate(rollings):
            try:
                low_min_idx, high_max_idx = get_last_col_api(data, rolling, latest_api_data)
                data_last = data[-rolling:]
                if rolling != 5:
                    half_roll = int(rolling/2)
                    open_final_val = data_last['open'].iloc[half_roll+1]
                else:
                    half_roll = int((rolling-1)/2)
                    open_final_val = data_last['open'].iloc[half_roll+1]
    
            
                #For 90% only calculate the value
                d = pd.DataFrame([])
                d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                index, cum_cal = get_cumsum(high_cum, percentage)
                h_bin = high_bins[index]
            
                low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                index, cum_cal = get_cumsum(low_cum, percentage)
                l_bin = low_bins[len(low_bins) - index]
            
                open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                index, cum_cal = get_cumsum(open_cum, percentage)
                o_bin = open_bins[index]
                close_val = float(data.tail(1)['close'])
              
                predicted_high = close_val + ((close_val*h_bin)/100.0)
                predicted_low = close_val + ((close_val*l_bin)/100.0)
                pred_open_high.append(predicted_high)
                pred_open_low.append(predicted_low)
                h_bins_array.append(h_bin)
                l_bins_array.append(-1*(l_bin))
            except:
                pred_open_high.append(None)
                pred_open_low.append(None)
                h_bins_array.append(None)
                l_bins_array.append(None)
        new_data[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high, "predicted_low":pred_open_low}

    else:
        #If market is Close 
        pred_open_high = []
        pred_open_low = []
        h_bins_array = []
        l_bins_array = []
        pred_final_open_high = []
        pred_final_open_low = []
        month_fixed_high = []
        month_fixed_low = []
     
        for idx,rolling in enumerate(rollings):
            try:
                low_min_idx, high_max_idx = get_last_col(data, rolling)
                data_last = data[-rolling:]
                if rolling != 5:
                    half_roll = int(rolling/2)
                    open_final_val = data_last['open'].iloc[half_roll+1]
                else:
                    half_roll = int((rolling-1)/2)
                    open_final_val = data_last['open'].iloc[half_roll+1]
    
            
                #For 90% only calculate the value
                d = pd.DataFrame([])
        
                d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
                high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
                index, cum_cal = get_cumsum(high_cum, percentage)
                h_bin = high_bins[index]
            
                low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
                index, cum_cal = get_cumsum(low_cum, percentage)
                l_bin = low_bins[len(low_bins) - index]
            
                open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
                index, cum_cal = get_cumsum(open_cum, percentage)
                o_bin = open_bins[index]
                close_val = float(data.tail(1)['close'])
                
                predicted_high = close_val + ((close_val*h_bin)/100.0)
                predicted_low = close_val + ((close_val*l_bin)/100.0)
                pred_open_high.append(predicted_high)
                pred_open_low.append(predicted_low)
                
                h_bins_array.append(h_bin)
                l_bins_array.append(-1*(l_bin))
            except:
                pred_open_high.append(None)
                pred_open_low.append(None)
                h_bins_array.append(None)
                l_bins_array.append(None)
        new_data[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high, "predicted_low":pred_open_low}

    # temp = date_range[-1]
    # temp_value = int(date_range[:-1])
    # if temp.lower() == "d":
    #     date_range_date = date_time - timedelta(days=temp_value)
    # elif temp.lower() == "m":
    #     date_range_date = date_time - timedelta(days=temp_value*30)
    # elif temp.lower() == "y":
    #     date_range_date = date_time - timedelta(days=temp_value*365)
    # else:
    #     return None
    
    # start_date = str(date_time).split(" ")[0]
    # end_date = str(date_range_date).split(" ")[0]
    # d = requests.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={end_date}&to={start_date}&apikey=b1360803f80dd08bdd0211c5c004ad03')
    # data = d.json()
    # df = pd.DataFrame(data['historical'])
    # df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/'+ticker+'.csv',parse_dates=['date'])
    # df = df[(df["date"] >= date_range_date) & (df["date"] <= date_time)]
    # df2 = df[::-1]
    # temp_date = date_time
    # while True:
    #     try:
    #         next_day = str(temp_date).split(" ")[0]
    #         next_day = next_day.split("-")[::-1]
    #         next_day = "-".join(next_day)
    #         new_pred_high = new_data[rolling]['predicted_high']
    #         new_pred_low = new_data[rolling]["predicted_low"]
    #         break
    #     except:
    #         temp_date = temp_date + timedelta(days=1)

    final_dict = {}

    final_dict['rollings'] = [30, 60, 90, 120, 150, 180, 360]
    final_dict['pred_high'] = pred_open_high
    final_dict['pred_low'] = pred_open_low
    final_dict['pred_high_percentage'] = h_bins_array
    final_dict['pred_low_percentage'] = l_bins_array

    return HttpResponse(json.dumps(final_dict, indent=4,default=str),content_type = "application/json")
# def predict_price_graph(request):
#     request = json.loads(request.body.decode('utf-8'))

#     date = request['date']
#     date_range = request['date_range']
#     ticker = request['ticker']
#     filter_days = int(request['filter_days'])
#     rolling = int(request['rolling'])

#     # pay_dict = {{
#     #     "ticker": "AAPL",
#     #     "filter_days": 365,
#     #     "in_date": "2022-05-28",
#     #     "rolling": 5
#     # }}
    
#     date_time = pd.to_datetime(date, format='%Y-%m-%d')
#     url = "https://cp2.invexwealth.com/predict_price_new"
#     pay_dict = {}
#     pay_dict['ticker'] = ticker
#     pay_dict['filter_days'] = filter_days
#     pay_dict['in_date'] = date
#     pay_dict['rolling'] = rolling

#     payload = json.dumps(pay_dict)
#     headers = {
#         'Content-Type': 'application/json'
#     }
    
#     new_data = requests.request("GET", url, headers=headers, data=payload)
#     new_data = new_data.json()

#     temp = date_range[-1]
#     temp_value = int(date_range[:-1])
#     if temp.lower() == "d":
#         date_range_date = date_time - timedelta(days=temp_value)
#     elif temp.lower() == "m":
#         date_range_date = date_time - timedelta(days=temp_value*30)
#     elif temp.lower() == "y":
#         date_range_date = date_time - timedelta(days=temp_value*365)
#     else:
#         return None
    
#     start_date = str(date_time).split(" ")[0]
#     end_date = str(date_range_date).split(" ")[0]
#     d = requests.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={end_date}&to={start_date}&apikey=b1360803f80dd08bdd0211c5c004ad03')
#     data = d.json()
#     df = pd.DataFrame(data['historical'])
#     df2 = df[::-1]
#     temp_date = date_time
#     while True:
#         try:
#             next_day = str(temp_date).split(" ")[0]
#             next_day = next_day.split("-")[::-1]
#             next_day = "-".join(next_day)
#             new_pred_high = new_data[next_day]['predicted_high']
#             new_pred_low = new_data[next_day]["predicted_low"]
#             percentages = new_data[next_day]["percentage"]
#             break
#         except:
#             temp_date = temp_date + timedelta(days=1)
#     x_dates = percentages
#     y_values_high = new_pred_high
#     y_values_low = new_pred_low

#     final_dict = {}
#     final_dict['date'] = df2['date'].to_list()
#     final_dict['open'] = df2['open'].to_list()
#     final_dict['high'] = df2['high'].to_list()
#     final_dict['low'] = df2['low'].to_list()
#     final_dict['close'] = df2['close'].to_list()

#     final_dict['percentages'] = x_dates
#     final_dict['pred_high'] = y_values_high
#     final_dict['pred_low'] = y_values_low

#     return  HttpResponse(json.dumps(final_dict, indent=4,default=str),content_type = "application/json")

@api_view(['GET', 'POST'])
def get_screener_data(request):
    request = json.loads(request.body.decode('utf-8'))
    curr_date = request['curr_date']  #2022-07-26
    curr_date = str(curr_date.split('-')[0]) +str(curr_date.split('-')[1]) + str(curr_date.split('-')[2])
    #out_data = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv', nrows=100)
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data") #@danish
    file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
    out_data = pd.read_csv(file_path, nrows=100)

    # out_data = json.loads(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.json')
    out_data = out_data.to_dict()
    return HttpResponse(json.dumps(out_data, indent=4,default=str),content_type = "application/json")

# @api_view(['GET', 'POST'])
# def upload_csv(request):
#     if request.method == 'POST':
#         option = request.FILES['option']
#         if os.path.isfile(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/uploaded_prediction_file/{option.name}"):
#             os.remove(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/uploaded_prediction_file/{option.name}")
#         fs1 = FileSystemStorage(location=f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/uploaded_prediction_file/")
#         fs1.save(option.name, option)
#
#         filter_days = int(request.POST.get('filter_days'))
#         percentage = int(request.POST.get('percentage'))
#
#         data = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/uploaded_prediction_file/{option.name}', parse_dates=['date'])
#         pred_output = predict_price_csv(data, filter_days, percentage)
#         return HttpResponse(json.dumps(pred_output, indent=4,default=str),content_type = "application/json")
#         #return HttpResponse(json.dumps(data.to_dict('list'), indent=4,default=str),content_type = "application/json")
#     else:
#         return render(request, 'upload_csv.html')
#
#
# @api_view(['GET', 'POST'])
# def calc(request):
#     if request.method == "POST":
#         request = json.loads(request.body.decode('utf-8'))
#         company_name = request["symbol_value"]
#         stepsize = float(request["stepsize"])
#         months = int(request["month"])
#         strike_perc = int(request["Strike_percentage"])
#         start = request["startdate"].split("-")
#         end = request["enddate"].split("-")
#
#         startdate = datetime(int(start[0]), int(start[1]), int(start[2]))
#         enddate = datetime(int(end[0]), int(end[1]), int(end[2]))
#         data_date = request["datadate"]
#         formated_date = data_date.split("-")
#         data_date = formated_date[0] + formated_date[1] + formated_date[2]
#         invex,current_price,datadate,real_rolling,expirations = final_api.calculation(company_name,stepsize,months,strike_perc,startdate,enddate,data_date)
#         invex = invex.fillna(0)
#
#         invex_dict = {"current_price":current_price, "DataDate":datadate, "rolling_value":real_rolling, "Expiration":expirations}
#         for i in invex:
#             invex_dict[i] = list(invex[i])
#         return HttpResponse(json.dumps(invex_dict, indent=4,default=str),content_type = "application/json")
#
#
# @api_view(['GET', 'POST'])
# def total(request):
#     if request.method == "POST":
#         request = json.loads(request.body.decode('utf-8'))
#         print(request)
#         month = int(request["month"])
#         strike_perc = int(request["strike_percent"])
#         date = request["date"]
#         erf = request["erf"]
#         calls = request["call_value"]
#         call_min = float(calls.split('_')[0])
#         call_max = float(calls.split('_')[1])
#
#         puts = request["put_value"]
#         put_min = float(puts.split('_')[0])
#         put_max = float(puts.split('_')[1])
#
#         cps = request["cp_value"]
#         cp_min = float(cps.split('_')[0])
#         cp_max = float(cps.split('_')[1])
#
#         close_val = request["close_value"]
#         close_min = float(close_val.split('_')[0])
#         close_max = float(close_val.split('_')[1])
#
#         vol_val = request["vol_value"]
#         vol_min = float(vol_val.split('_')[0])
#         vol_max = float(vol_val.split('_')[1])
#
#         oi_val = request["oi_value"]
#         oi_min = float(oi_val.split('_')[0])
#         oi_max = float(oi_val.split('_')[1])
#
#         filter_days = str(request["filter_days"])
#
#         formated_date = date.split("-")
#         #datadate = datetime(int(formated_date[0]), int(formated_date[1]), int(formated_date[2]))
#         final_date = formated_date[0] + formated_date[1] + formated_date[2]
#         if filter_days == "180" or filter_days == "720":
#             path = "/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/invex_ratio_daily/invex_"+ filter_days + "_" +str(final_date) + ".json"
#         else:
#             path = "/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/invex_ratio_daily/invex_max_" +str(final_date) + ".json"
#
#         df_quote = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_stockquotes_{str(final_date)}.csv')
#         df_stats = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_optionstats_{str(final_date)}.csv')
#
#         file = open(path,"r")
#         data = json.load(file)
#         final_data = {}
#         #strike_perc = 30
#         #month = 200
#         symbols = data.keys()
#         # #print(symbols)
#         for symbol in symbols:
#             try:
#                 arr = []
#                 s = pd.DataFrame(data[symbol])
#                 current_price = float(s.iloc[0,0])
#                 rol_value = s["0"]
#                 arr = pd.DataFrame(rol_value)
#                 # #print('invex calculation')
#                 # #print(arr)
#                 rolling = arr.dropna()
#                 rolling = pd.to_numeric(rolling["0"])
#                 rolling = rolling[1:].astype(int)
#                 # #print('rolling valuds')
#                 # #print(rolling)
#
#                 exp_value = s["Expiration"]
#                 arr2 = pd.DataFrame(exp_value)
#                 expiration = arr2.dropna()
#                 expiration = expiration[:-1]
#
#                 lower_value = float(current_price - ((current_price*(strike_perc / 10))/10.0))
#                 higher_value = float(current_price + ((current_price*(strike_perc / 10))/10.0))
#
#                 call_array = 0.0
#                 put_array = 0.0
#                 cp = 0.0
#                 hvtf_array = 0.0
#                 len_roll = 0
#                 cp_median = []
#                 com = {}
#                 for r,e in zip(rolling,expiration.values):
#                     if int(r) <= int(month):
#                         try:
#                             filter_s = s[(s["Strike_"+str(r)]>=lower_value) & (s["Strike_"+str(r)]<=higher_value)]
#                             strike = filter_s["Strike_"+str(r)].values
#                             call_ir = filter_s["Invex_ratio_call_"+str(r)].mean()
#                             put_ir = filter_s["Invex_ratio_put_"+str(r)].mean()
#                             cp_ratio = filter_s["CP_ratio_"+str(r)].mean()
#                             cp_ratio_median = filter_s['CP_ratio_'+str(r)].median()
#                             hvtf = filter_s["HVTF_put_" + str(r)].iloc[0]
#                             # com["Expiration"] = filter_s["Expiration"]
#
#                             call_array += call_ir
#                             put_array += put_ir
#                             cp += (call_ir/put_ir)
#                             hvtf_array += hvtf
#                             cp_median.append(call_ir/put_ir)
#
#                             com[e[0]]=[call_ir, put_ir, call_ir/put_ir, hvtf]
#                             len_roll += 1
#                         except:
#                             continue
#             except:
#                 #print('except')
#                 continue
#             try:
#                 call_array = call_array/len_roll
#                 put_array = put_array/len_roll
#                 cp = cp/len_roll
#                 hvtf_array = hvtf_array/len_roll
#                 cp_m = statistics.median(cp_median)
#
#             except:
#                 continue
#
#             close = df_quote[df_quote['symbol']==symbol]['adjustedclose'].values[0]
#             totalvol = int(df_stats[df_stats['symbol']==symbol]['totalvol'].values[0])
#             totaloi = int(df_stats[df_stats['symbol']==symbol]['totaloi'].values[0])
#
#             if (call_array>call_min and call_array<call_max) and (put_array>put_min and put_array<put_max) and (cp_m>cp_min and cp_m<cp_max) and (close>close_min and close<close_max) and (totalvol>vol_min and totalvol<vol_max) and (totaloi>oi_min and totaloi<oi_max):
#                 com["total"] = [call_array, put_array, cp_m, hvtf_array, close, totalvol, totaloi]
#                 final_data[symbol] = com
#
#         if erf:
#             final_data_filter = {}
#             erf_list = requests.get("https://financialmodelingprep.com/api/v3/etf/list?apikey=b1360803f80dd08bdd0211c5c004ad03")
#             for i in erf_list.json():
#                 if i["symbol"] in final_data:
#                     final_data_filter[i["symbol"]] = final_data[i["symbol"]]
#             file.close()
#             return HttpResponse(json.dumps(final_data_filter, indent=4,default=str),content_type = "application/json")
#         else:
#             erf_list = requests.get("https://financialmodelingprep.com/api/v3/etf/list?apikey=b1360803f80dd08bdd0211c5c004ad03")
#             for i in erf_list.json():
#                 if i["symbol"] in final_data:
#                     final_data.pop(i["symbol"])
#             file.close()
#             return HttpResponse(json.dumps(final_data, indent=4,default=str),content_type = "application/json")
#
#         # file.close()
#         # return HttpResponse(json.dumps(final_data, indent=4,default=str),content_type = "application/json")
#
#
# @api_view(['GET', 'POST'])
# def graph(request):
#     path = "/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/graph_data/final_graph_2.json"
#     file = open(path, 'r')
#     graph_data = json.load(file)
#     file.close()
#     return HttpResponse(json.dumps(graph_data, indent=4), content_type="application/json")
#
#
# def upload(request):
#     if request.method == "POST":
#         option = request.FILES['option']
#         optionstat = request.FILES['optionstat']
#         optionquotes = request.FILES['optionquotes']
#
#         file_name = option.name
#         file_date = file_name.split('_')[2]
#         file_year = file_date[:4]
#         file_month = int(file_date[4:6])
#
#         fs = FileSystemStorage(location=f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/")
#         fs.save(option.name, option)
#         dir_path = f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/"
#         df_chunk = vaex.open(dir_path + option.name)
#
#         fs1 = FileSystemStorage(location=f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/")
#         fs1.save(optionstat.name, optionstat)
#
#         fs2 = FileSystemStorage(location=f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/")
#         fs2.save(optionquotes.name, optionquotes)
#
#         return HttpResponse("File uploaded successfully")
#     else:
#         curr_month = datetime.now().month
#         curr_year = str(int(datetime.now().year))
#         dirpath = f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/'
#         input_path = Path("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/")
#         dirls = list(input_path.rglob("*.csv"))
#         # dirpath = f'{dirpath}{str(curr_month)}'
#         options_ls = []
#         stockquotes_ls = []
#         optionstats_ls = []
#         final_output = {}
#         out_dir = os.listdir('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/')
#         skip = ['script.py']
#         for od in out_dir:
#             if od in skip:
#                 continue
#             else:
#                 final_output[str(od)] = {'1':[], '2':[], '3':[], '4':[], '5':[], '6':[], '7':[], '8':[], '9':[], '10':[], '11':[], '12':[]}
#
#         for r, d, f in os.walk(dirpath):
#             for filename in f:
#                 if filename.endswith('.csv'):
#                     #print(str(filename))
#                     filepath = os.path.join(dirpath + str(filename.split('_')[2][0:4]) + '/' +str(int(filename.split('_')[2][4:6])) +"/", filename)
#                     dirls.append(filepath)
#                     # #print(filename.split('.'))
#                     final_output[str(filename.split('.')[0]).split('_')[2][0:4]][str(int(str(filename.split('.')[0]).split('_')[2][4:6]))].append(filename)
#                     if filename.split('_')[1] == 'options' and filename.split('.')[-1] == 'csv':
#                         options_ls.append(filename)
#                     elif filename.split('_')[1] == 'stockquotes':
#                         stockquotes_ls.append(filename)
#                     elif filename.split("_")[1] == 'optionstats':
#                         optionstats_ls.append(filename)
#                     else:
#                         continue
#         #print(f'=========================           {options_ls}       {stockquotes_ls}     {stockquotes_ls}')
#
#         if not dirls:
#             #print('not')
#             return render(request, 'upload.html', {"data":"No Files till now", "options_ls":options_ls[::-1], "optionstats_ls":optionstats_ls[::-1], "stockquotes_ls":stockquotes_ls[::-1], "file_names":zip(options_ls[::-1], optionstats_ls[::-1], stockquotes_ls[::-1])})
#         else:
#             latest_file = max(dirls, key=os.path.getctime)
#             l_f = str(latest_file).split("/")[-1]
#             options_ls.sort()
#             optionstats_ls.sort()
#             stockquotes_ls.sort()
#             return render(request, 'upload.html', {"data":l_f, "options_ls":options_ls[::-1], "optionstats_ls":optionstats_ls[::-1], "stockquotes_ls":stockquotes_ls[::-1], "file_names":zip(options_ls[::-1], optionstats_ls[::-1], stockquotes_ls[::-1]), 'final_out':final_output})
#
# @api_view(['GET', 'POST'])
# def get_files(request):
#     dirpath = f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/'
#     input_path = Path("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/")
#     dirls = list(input_path.rglob("*.csv"))
#     final_output = {}
#     out_dir = os.listdir('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/')
#     skip = ['script.py']
#     for od in out_dir:
#         if od in skip:
#             continue
#         else:
#             final_output[str(od)] = {'1':[], '2':[], '3':[], '4':[], '5':[], '6':[], '7':[], '8':[], '9':[], '10':[], '11':[], '12':[]}
#
#     for r, d, f in os.walk(dirpath):
#         for filename in f:
#             if filename.endswith('.csv'):
#                 #print(str(filename))
#                 filepath = os.path.join(dirpath + str(filename.split('_')[2][0:4]) + '/' +str(int(filename.split('_')[2][4:6])) +"/", filename)
#                 dirls.append(filepath)
#                 # #print(filename.split('.'))
#                 final_output[str(filename.split('.')[0]).split('_')[2][0:4]][str(int(str(filename.split('.')[0]).split('_')[2][4:6]))].append(filename)
#     return HttpResponse(json.dumps(final_output, indent=4,default=str),content_type = "application/json")
#
# @api_view(['GET'])
# def download_file(request):
#     try:
#         # request = json.loads(request.body.decode('utf-8'))
#         file_name = request.query_params['file_name']
#         # file_name = str(request['file_name'])
#         file_year = str(str(file_name.split('.')[0]).split('_')[2][0:4])
#         file_month = str(int(str(file_name.split('.')[0]).split('_')[2][4:6]))
#         filepath =  f'/home/cp2invexwealth/pythonDir//home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{file_year}/{file_month}/{file_name}'
#         if os.path.isfile(filepath):
#             path = open(filepath, 'rb')
#             mime_type, _ = mimetypes.guess_type(filepath)
#             response = HttpResponse(path, content_type=mime_type)
#             response['Content-Disposition'] = "attachment; filename=%s" % file_name
#             return response
#         else:
#             return HttpResponse('File not found on our server')
#     except:
#         return HttpResponse("Something went wrong")
#
#
# class NpEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, np.integer):
#             return int(obj)
#         if isinstance(obj, np.floating):
#             return float(obj)
#         if isinstance(obj, np.ndarray):
#             return obj.tolist()
#         return super(NpEncoder, self).default(obj)
#
#
# @api_view(['GET', 'POST'])
# def website_quote(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     ticker = request["ticker"]
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     data = {}
#     df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#     df1 = df[df['symbol'] == ticker]
#
#     ## For Volume
#     data["Volume"] = {
#         "Calls" : round(df1["callvol"].values[0], 2),
#         "Puts" : round(df1["putvol"].values[0], 2),
#         "Total" : round(df1["totalvol"].values[0], 2),
#     }
#
#     ## For Open_Interest
#     data["Open_Interest"] = {
#         "Calls" : round(df1["calloi"].values[0], 2),
#         "Puts" : round(df1["putoi"].values[0], 2),
#         "Total" : round(df1["totaloi"].values[0], 2),
#     }
#
#
#     ## For Implied Volatility Index
#     week_ago = str(date_time - timedelta(days=7))
#     week_ago = week_ago.split(" ")[0].replace("-", "")
#     i =0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             week = week[week["symbol"] == ticker]
#             break
#         except:
#             i = i + 1
#             week_ago = str(date_time - timedelta(days=7-i))            ### if any change in days then Put same value as used in week_ago (7)
#             week_ago = week_ago.split(" ")[0].replace("-", "")
#             pass
#
#
#     a_month_ago = str(date_time - timedelta(days=30))
#     a_month_ago = a_month_ago.split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             a_month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{a_month_ago[0:4]}/{str(int(a_month_ago[4:6]))}/L3_optionstats_{a_month_ago}.csv")
#             a_month = a_month[a_month["symbol"] == ticker]
#             break
#         except:
#             i = i+1
#             a_month_ago = str(date_time - timedelta(days=30-i))         ### if any change in days then Put same value as used in a_month_ago (30)
#             a_month_ago = a_month_ago.split(" ")[0].replace("-", "")
#             pass
#
#
#     three_month_ago = str(date_time - timedelta(days=90))
#     three_month_ago = three_month_ago.split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             three_month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{three_month_ago[0:4]}/{str(int(three_month_ago[4:6]))}/L3_optionstats_{three_month_ago}.csv")
#             three_month = three_month[three_month["symbol"] == ticker]
#             break
#         except:
#             i = i+1
#             three_month_ago = str(date_time - timedelta(days=90-i))          ### if any change in days then Put same value as used in three_month_ago (90)
#             three_month_ago = three_month_ago.split(" ")[0].replace("-", "")
#             #print(three_month_ago)
#             pass
#
#
#     data["Implied_Volatility_Index"] = {
#         "Current_IV_Index" : {
#             "30_Days" : {
#                 "Call" : round(df1["iv30call"].values[0] * 100, 2),
#                 "Put" : round(df1["iv30put"].values[0] * 100, 2),
#                 "Mean" : round(df1["iv30mean"].values[0] * 100, 2),
#             },
#             "60_Days" : {
#                 "Call" : round(df1["iv60call"].values[0] * 100, 2),
#                 "Put" : round(df1["iv60put"].values[0] * 100, 2),
#                 "Mean" : round(df1["iv60mean"].values[0] * 100, 2),
#             },
#             "90_Days" : {
#                 "Call" : round(df1["iv90call"].values[0] * 100, 2),
#                 "Put" : round(df1["iv90put"].values[0] * 100, 2),
#                 "Mean" : round(df1["iv90mean"].values[0] * 100, 2),
#             },
#             "120_Days" : {
#                 "Call" : round(df1["iv120call"].values[0] * 100, 2),
#                 "Put" : round(df1["iv120put"].values[0] * 100, 2),
#                 "Mean" : round(df1["iv120mean"].values[0] * 100, 2),
#             },
#             "150_Days" : {
#                 "Call" : round(df1["iv150call"].values[0] * 100, 2),
#                 "Put" : round(df1["iv150put"].values[0] * 100, 2),
#                 "Mean" : round(df1["iv150mean"].values[0] * 100, 2),
#             },
#             "180_Days" : {
#                 "Call" : round(df1["iv180call"].values[0] * 100, 2),
#                 "Put" : round(df1["iv180put"].values[0] * 100, 2),
#                 "Mean" : round(df1["iv180mean"].values[0] * 100, 2),
#             },
#             "360_Days" : {
#                 "Call" : round(df1["iv360call"].values[0] * 100, 2),
#                 "Put" : round(df1["iv360put"].values[0] * 100, 2),
#                 "Mean" : round(df1["iv360mean"].values[0] * 100, 2),
#             },
#         },
#         "1_Week_Ago" : {
#             "30_Days" : {
#                 "Call" : round(week["iv30call"].values[0] * 100, 2),
#                 "Put" : round(week["iv30put"].values[0] * 100, 2),
#                 "Mean" : round(week["iv30mean"].values[0] * 100, 2),
#             },
#             "60_Days" : {
#                 "Call" : round(week["iv60call"].values[0] * 100, 2),
#                 "Put" : round(week["iv60put"].values[0] * 100, 2),
#                 "Mean" : round(week["iv60mean"].values[0] * 100, 2),
#             },
#             "90_Days" : {
#                 "Call" : round(week["iv90call"].values[0] * 100, 2),
#                 "Put" : round(week["iv90put"].values[0] * 100, 2),
#                 "Mean" : round(week["iv90mean"].values[0] * 100, 2),
#             },
#             "120_Days" : {
#                 "Call" : round(week["iv120call"].values[0] * 100, 2),
#                 "Put" : round(week["iv120put"].values[0] * 100, 2),
#                 "Mean" : round(week["iv120mean"].values[0] * 100, 2),
#             },
#             "150_Days" : {
#                 "Call" : round(week["iv150call"].values[0] * 100, 2),
#                 "Put" : round(week["iv150put"].values[0] * 100, 2),
#                 "Mean" : round(week["iv150mean"].values[0] * 100, 2),
#             },
#             "180_Days" : {
#                 "Call" : round(week["iv180call"].values[0] * 100, 2),
#                 "Put" : round(week["iv180put"].values[0] * 100, 2),
#                 "Mean" : round(week["iv180mean"].values[0] * 100, 2),
#             },
#             "360_Days" : {
#                 "Call" : round(week["iv360call"].values[0] * 100, 2),
#                 "Put" : round(week["iv360put"].values[0] * 100, 2),
#                 "Mean" : round(week["iv360mean"].values[0] * 100, 2),
#             },
#
#         },
#         "1_month_Ago" : {
#             "30_Days" : {
#                 "Call" : round(a_month["iv30call"].values[0] * 100, 2),
#                 "Put" : round(a_month["iv30put"].values[0] * 100, 2),
#                 "Mean" : round(a_month["iv30mean"].values[0] * 100, 2),
#             },
#             "60_Days" : {
#                 "Call" : round(a_month["iv60call"].values[0] * 100, 2),
#                 "Put" : round(a_month["iv60put"].values[0] * 100, 2),
#                 "Mean" : round(a_month["iv60mean"].values[0] * 100, 2),
#             },
#             "90_Days" : {
#                 "Call" : round(a_month["iv90call"].values[0] * 100, 2),
#                 "Put" : round(a_month["iv90put"].values[0] * 100, 2),
#                 "Mean" : round(a_month["iv90mean"].values[0] * 100, 2),
#             },
#             "120_Days" : {
#                 "Call" : round(a_month["iv120call"].values[0] * 100, 2),
#                 "Put" : round(a_month["iv120put"].values[0] * 100, 2),
#                 "Mean" : round(a_month["iv120mean"].values[0] * 100, 2),
#             },
#             "150_Days" : {
#                 "Call" : round(a_month["iv150call"].values[0] * 100, 2),
#                 "Put" : round(a_month["iv150put"].values[0] * 100, 2),
#                 "Mean" : round(a_month["iv150mean"].values[0] * 100, 2),
#             },
#             "180_Days" : {
#                 "Call" : round(a_month["iv180call"].values[0] * 100, 2),
#                 "Put" : round(a_month["iv180put"].values[0] * 100, 2),
#                 "Mean" : round(a_month["iv180mean"].values[0] * 100, 2),
#             },
#             "360_Days" : {
#                 "Call" : round(a_month["iv360call"].values[0] * 100, 2),
#                 "Put" : round(a_month["iv360put"].values[0] * 100, 2),
#                 "Mean" : round(a_month["iv360mean"].values[0] * 100, 2),
#             },
#
#         },
#         "3_month_Ago" : {
#             "30_Days" : {
#                 "Call" : round(three_month["iv30call"].values[0] * 100, 2),
#                 "Put" : round(three_month["iv30put"].values[0] * 100, 2),
#                 "Mean" : round(three_month["iv30mean"].values[0] * 100, 2),
#             },
#             "60_Days" : {
#                 "Call" : round(three_month["iv60call"].values[0] * 100, 2),
#                 "Put" : round(three_month["iv60put"].values[0] * 100, 2),
#                 "Mean" : round(three_month["iv60mean"].values[0] * 100, 2),
#             },
#             "90_Days" : {
#                 "Call" : round(three_month["iv90call"].values[0] * 100, 2),
#                 "Put" : round(three_month["iv90put"].values[0] * 100, 2),
#                 "Mean" : round(three_month["iv90mean"].values[0] * 100, 2),
#             },
#             "120_Days" : {
#                 "Call" : round(three_month["iv120call"].values[0] * 100, 2),
#                 "Put" : round(three_month["iv120put"].values[0] * 100, 2),
#                 "Mean" : round(three_month["iv120mean"].values[0] * 100, 2),
#             },
#             "150_Days" : {
#                 "Call" : round(three_month["iv150call"].values[0] * 100, 2),
#                 "Put" : round(three_month["iv150put"].values[0] * 100, 2),
#                 "Mean" : round(three_month["iv150mean"].values[0] * 100, 2),
#             },
#             "180_Days" : {
#                 "Call" : round(three_month["iv180call"].values[0] * 100, 2),
#                 "Put" : round(three_month["iv180put"].values[0] * 100, 2),
#                 "Mean" : round(three_month["iv180mean"].values[0] * 100, 2),
#             },
#             "360_Days" : {
#                 "Call" : round(three_month["iv360call"].values[0] * 100, 2),
#                 "Put" : round(three_month["iv360put"].values[0] * 100, 2),
#                 "Mean" : round(three_month["iv360mean"].values[0] * 100, 2),
#             },
#
#         },
#
#     }
#
#
#     ## For Graph Representaion
#     start_date = date.replace("/", "-")
#     end_date = str(date_time - timedelta(days=365)).split(" ")[0]                     ## For year used 365
#     year_dates = pd.bdate_range(start=end_date, end=start_date)
#     columns = ['symbol', 'quotedate', 'iv30call', 'iv30put', 'iv30mean', 'iv60call',
#            'iv60put', 'iv60mean', 'iv90call', 'iv90put', 'iv90mean', 'iv120call',
#            'iv120put', 'iv120mean', 'iv150call', 'iv150put', 'iv150mean',
#            'iv180call', 'iv180put', 'iv180mean', 'iv360call', 'iv360put',
#            'iv360mean', 'callvol', 'putvol', 'totalvol', 'calloi', 'putoi',
#            'totaloi']
#     # one_year = pd.DataFrame(columns=columns)
#
#     # for x in year_dates:
#     #     try:
#     #         y = str(x.date()).replace("-", "")
#     #         temp = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{y[0:4]}/{str(int(y[4:6]))}/L3_optionstats_{y}.csv")
#     #         temp = temp[temp["symbol"] == ticker]
#     #         one_year = pd.concat([one_year, temp])
#     #     except:
#     #         pass
#     # #
#     # one_year = one_year.reset_index(drop=True)
#     # one_year["quotedate"] = pd.to_datetime(one_year["quotedate"], format="%m/%d/%Y")
#     # one_year.to_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/website/quote/{ticker}.csv')
#
#     one_year = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/website/quote/{ticker}.csv")
#     one_year["quotedate"] = pd.to_datetime(one_year["quotedate"], format="%Y-%m-%d")
#
#     yearly_data = {
#         "date": [str(x.date()) for x in one_year["quotedate"]],
#         "iv30call" : list(one_year["iv30call"]),
#         "iv30put" : list(one_year["iv30put"]),
#         "iv30mean" : list(one_year["iv30mean"]),
#         "iv60call" : list(one_year["iv60call"]),
#         "iv60put" : list(one_year["iv60put"]),
#         "iv60mean" : list(one_year["iv60mean"]),
#         "iv90call" : list(one_year["iv90call"]),
#         "iv90put" : list(one_year["iv90put"]),
#         "iv90mean" : list(one_year["iv90mean"]),
#         "iv120call" : list(one_year["iv120call"]),
#         "iv120put" : list(one_year["iv120put"]),
#         "iv120mean" : list(one_year["iv120mean"]),
#         "iv150call" : list(one_year["iv150call"]),
#         "iv150put" : list(one_year["iv150put"]),
#         "iv150mean" : list(one_year["iv150mean"]),
#         "iv180call" : list(one_year["iv180call"]),
#         "iv180put" : list(one_year["iv180put"]),
#         "iv180mean" : list(one_year["iv180mean"]),
#         "iv360call" : list(one_year["iv360call"]),
#         "iv360put" : list(one_year["iv360put"]),
#         "iv360mean" : list(one_year["iv360mean"]),
#         "callvol" : list(one_year["callvol"]),
#         "putvol" : list(one_year["putvol"]),
#         "totalvol" : list(one_year["totalvol"]),
#         "calloi" : list(one_year["calloi"]),
#         "putoi" : list(one_year["putoi"]),
#         "totaloi" : list(one_year["totaloi"]),
#     }
#     data["Graph_data"] = yearly_data
#
#     ## For Historical Volatility
#
#     df2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/hist data2/{ticker}.csv")
#     df2["date"] = pd.to_datetime(df2["date"], format="%Y-%m-%d")
#
#     ## For Current HV
#     days = [30,60,90,120,150,180,360]
#     start_date = date.replace("/", "-")
#     current_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(date_time - timedelta(x)).split(" ")[0]) & (df2["date"] <= start_date)].reset_index(drop=True)
#         current_hv = round(((float(current_hv_df["high"].max()) - current_hv_df["low"].min()) / current_hv_df["open"][len(current_hv_df)-1])*100, 2)
#         current_hv_dict[f"{x}_Days"] = round((current_hv*19.105)/float(x), 2)
#         # #print(current_hv_df)
#
#     ## For one Week Ago HV
#     modify_date = date_time - timedelta(7)
#     one_week_ago_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((float(current_hv_df["high"].max()) - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         one_week_ago_hv_dict[f"{x}_Days"] = round((current_hv*19.105)/float(x), 2)
#
#
#     ## For one Month Ago HV
#     modify_date = date_time - timedelta(30)
#     one_month_ago_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((float(current_hv_df["high"].max()) - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         one_month_ago_hv_dict[f"{x}_Days"] = round((current_hv*19.105)/float(x), 2)
#
#
#     ## For Three Month Ago HV
#     modify_date = date_time - timedelta(90)
#     three_month_ago_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((float(current_hv_df["high"].max()) - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         three_month_ago_hv_dict[f"{x}_Days"] = round((current_hv*19.105)/float(x), 2)
#
#     ## For 52 weeks
#     modify_date = date_time - timedelta(365)
#     high_52_week = {}
#     low_52_week = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         high_52_week[f"{x}_Days"] = round(float(current_hv_df["high"].max()), 2)
#         low_52_week[f"{x}_Days"] = round((current_hv*19.105)/float(x), 2)
#
#         # current_hv = round(((float(current_hv_df["high"].max()) - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         # one_week_ago_hv_dict[f"{x}_Days"] = current_hv
#
#     data["Historical_Volatility"] = {
#         "Current_HV" : current_hv_dict,
#         "1_Week_Ago" : one_week_ago_hv_dict,
#         "1_Month_Ago" : one_month_ago_hv_dict,
#         "3_Month_Ago" : three_month_ago_hv_dict,
#         "52_Week_High": high_52_week,
#         "52_Week_Low" : low_52_week
#     }
#
#
#
#     ## For Historical Volatility
#     ## For 365 days of IV
#     d = str(date_time - timedelta(28)).split(" ")[0]                 ## For one year used 365
#     y = d.replace("-", "")
#     temp = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{y[0:4]}/{str(int(y[4:6]))}/L3_optionstats_{y}.csv")
#     temp = temp[temp["symbol"] == ticker]
#
#     ## For 365 days of HV
#     modify_date = date_time - timedelta(365)
#     one_year_ago_hv_dict = {}
#     for x in days[:1]:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((float(current_hv_df["high"].max()) - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         one_year_ago_hv_dict[f"{x}_Days"] = current_hv
#
#     data["52_Week_Range"] = {
#         "IV30" : {
#             "Low" : round(temp["iv30mean"].values[0] * 100,2),
#             "High" : round(df1["iv30mean"].values[0] * 100, 2),
#         },
#         "HV30" : {
#             "Low" : one_year_ago_hv_dict["30_Days"],
#             "High" : current_hv_dict["30_Days"],
#         },
#     }
#
#     data["Volatility"] = {
#         "IV30" : round(df1["iv30mean"].values[0] * 100, 2),
#         "IV60" : round(df1["iv60mean"].values[0] * 100, 2),
#         "IV90" : round(df1["iv90mean"].values[0] * 100, 2),
#         "HV30" : current_hv_dict["30_Days"],
#         "HV60" : current_hv_dict["60_Days"],
#         "HV90" : current_hv_dict["90_Days"],
#     }
#
#     return HttpResponse(json.dumps(data, indent=4, cls=NpEncoder), content_type="application/json")
#     # return data


# def website_quote(request):
#     datadate = '20220103'
#     ticker = 'AAPL'
#     filename = f'media/option_data/Option Data/Historical/{datadate[0:4]}/str(int(datadate[4:6]))/L3_optionstats_{datadate}.csv'
#     final_out = {}
    
#     #filter symbol data only
#     optionstats_data = pd.read_csv(filename)
#     optionstats_data = optionstats_data[optionstats_data['symbol']==ticker]
    
#     # iv = 30,60,90
#     final_out['volatility'] = {'iv': [optionstats_data['iv30mean'], optionstats_data['iv60mean'], optionstats_data['iv90mean']], 'hv': []}
#     # total = volume => call,put,total
#     # total = OI => call,put,total
#     final_out['total'] = {'volume': [optionstats_data['callvol'], optionstats_data['putvol'], optionstats_data['totalvol']], 'oi': [optionstats_data['calloi'], optionstats_data['putoi'], optionstats_data['totaloi']]}



# website market
# @api_view(['GET', 'POST'])
# def most_active_options(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     df = main_df.sort_values(by='totalvol', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     symbol = list(df["symbol"])
#     most_active_options= pd.DataFrame()
#
#      ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(None)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(None)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(None)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(None)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     most_active_options["Symbol"] = symbol
#     most_active_options["Last"] = last
#     most_active_options["volume"] = df["totalvol"]
#     most_active_options["Daily_change"] = day_change
#     most_active_options["Weekly_change"] = week_change
#     most_active_options["Monthly_change"] = month_change
#     most_active_options["Quarterly_change"] = quarter_change
#     most_active_options = most_active_options.replace({np.nan: None, np.inf: None, np.inf: None})
#     return HttpResponse(json.dumps(most_active_options[~most_active_options["Symbol"].isin(etf_list)].to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
# @api_view(['GET', 'POST'])
# def highest_implied_volatility(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     day_list = request['day_list']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     column = f"iv{day_list}mean"
#     df = main_df.sort_values(by=column, ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     symbol = list(df["symbol"])
#     highest_implied_volatility = pd.DataFrame()
#
#      ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Weekly Change
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Monthly Change
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Quarterly Change
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#
#     highest_implied_volatility["Symbol"] = symbol
#     highest_implied_volatility["Last"] = last
#     highest_implied_volatility[f"iv{day_list}"] = df[column]
#     highest_implied_volatility["Daily_change"] = day_change
#     highest_implied_volatility["Weekly_change"] = week_change
#     highest_implied_volatility["Monthly_change"] = month_change
#     highest_implied_volatility["Quarterly_change"] = quarter_change
#     highest_implied_volatility = highest_implied_volatility.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(highest_implied_volatility[~highest_implied_volatility["Symbol"].isin(etf_list)].to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
#
# @api_view(['GET', 'POST'])
# def exploding_IV(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     day_list = request['day_list']
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     column = f"iv{day_list}mean"
#     df = main_df.sort_values(by=column, ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     exploding_IV = pd.DataFrame()
#     symbol = list(df["symbol"])
#
#      ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Weekly Change
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Monthly Change
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Quarterly Change
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#
#
#     exploding_IV["Symbol"] = symbol
#     exploding_IV["Last"] = last
#     exploding_IV[f"iv{day_list}"] = df[column]
#     exploding_IV["Daily_change"] = day_change
#     exploding_IV["Weekly_change"] = week_change
#     exploding_IV["Monthly_change"] = month_change
#     exploding_IV["Quarterly_change"] = quarter_change
#     exploding_IV = exploding_IV.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#     exploding_IV = exploding_IV.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(exploding_IV[~exploding_IV["Symbol"].isin(etf_list)].to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
#
#
# @api_view(['GET', 'POST'])
# def imploding_IV(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     day_list = request['day_list']
#     order_data = request['order_data']
#
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     column = f"iv{day_list}mean"
#     df = main_df.sort_values(by=column, ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     imploding_IV = pd.DataFrame()
#     symbol = list(df["symbol"])
#
#      ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Weekly Change
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Monthly Change
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Quarterly Change
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#
#
#     imploding_IV["Symbol"] = symbol
#     imploding_IV["Last"] = last
#     imploding_IV["iv30"] = df[column]
#     imploding_IV["Daily_change"] = day_change
#     imploding_IV["Weekly_change"] = week_change
#     imploding_IV["Monthly_change"] = month_change
#     imploding_IV["Quarterly_change"] = quarter_change
#     imploding_IV = imploding_IV.sort_values(by=order_data, ascending=True).reset_index(drop=True)
#     imploding_IV = imploding_IV.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(imploding_IV[~imploding_IV["Symbol"].isin(etf_list)].to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
#
# @api_view(['GET', 'POST'])
# def option_volume_gainers(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     df = main_df.sort_values(by='totalvol', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     symbol = list(df["symbol"])
#     option_volume_gainers= pd.DataFrame()
#
#      ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Weekly Change
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Monthly Change
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             # #print(month_ago)
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Quarterly Change
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_volume_gainers["Symbol"] = symbol
#     option_volume_gainers["Last"] = last
#     option_volume_gainers["volume"] = df["totalvol"]
#     option_volume_gainers["Daily_change"] = day_change
#     option_volume_gainers["Weekly_change"] = week_change
#     option_volume_gainers["Monthly_change"] = month_change
#     option_volume_gainers["Quarterly_change"] = quarter_change
#
#     option_volume_gainers = option_volume_gainers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#     option_volume_gainers = option_volume_gainers.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(option_volume_gainers[~option_volume_gainers["Symbol"].isin(etf_list)].reset_index(drop=True).to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
#
# @api_view(['GET', 'POST'])
# def option_volume_losers(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     df = main_df.sort_values(by='totalvol', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     symbol = list(df["symbol"])
#     option_volume_losers= pd.DataFrame()
#
#      ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Weekly Change
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Monthly Change
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Quarterly Change
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_volume_losers["Symbol"] = symbol
#     option_volume_losers["Last"] = last
#     option_volume_losers["volume"] = df["totalvol"]
#     option_volume_losers["Daily_change"] = day_change
#     option_volume_losers["Weekly_change"] = week_change
#     option_volume_losers["Monthly_change"] = month_change
#     option_volume_losers["Quarterly_change"] = quarter_change
#
#     option_volume_losers = option_volume_losers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#     option_volume_losers = option_volume_losers.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(option_volume_losers[~option_volume_losers["Symbol"].isin(etf_list)].reset_index(drop=True).to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
# @api_view(['GET', 'POST'])
# def option_open_interest_gainers(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     df = main_df.sort_values(by='totaloi', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     symbol = list(df["symbol"])
#     option_open_interest_gainers= pd.DataFrame()
#
#      ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = day[day["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#             except:
#                 pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Weekly Change
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#
#     ## Monthly Change
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#
#     ## Quarterly Change
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_open_interest_gainers["Symbol"] = symbol
#     option_open_interest_gainers["Last"] = last
#     option_open_interest_gainers["volume"] = df["totaloi"]
#     option_open_interest_gainers["Daily_change"] = day_change
#     option_open_interest_gainers["Weekly_change"] = week_change
#     option_open_interest_gainers["Monthly_change"] = month_change
#     option_open_interest_gainers["Quarterly_change"] = quarter_change
#
#     option_open_interest_gainers = option_open_interest_gainers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#     option_open_interest_gainers = option_open_interest_gainers.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(option_open_interest_gainers[~option_open_interest_gainers["Symbol"].isin(etf_list)].reset_index(drop=True).to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
#
#
# @api_view(['GET', 'POST'])
# def option_open_interest_losers(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     df = main_df.sort_values(by='totaloi', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     symbol = list(df["symbol"])
#     option_open_interest_losers= pd.DataFrame()
#
#     ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_open_interest_losers["Symbol"] = symbol
#     option_open_interest_losers["Last"] = last
#     option_open_interest_losers["volume"] = df["totaloi"]
#     option_open_interest_losers["Daily_change"] = day_change
#     option_open_interest_losers["Weekly_change"] = week_change
#     option_open_interest_losers["Monthly_change"] = month_change
#     option_open_interest_losers["Quarterly_change"] = quarter_change
#
#     option_open_interest_losers = option_open_interest_losers.sort_values(by=order_data, ascending=True).reset_index(drop=True)
#     option_open_interest_losers = option_open_interest_losers.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(option_open_interest_losers[~option_open_interest_losers["Symbol"].isin(etf_list)].reset_index(drop=True).to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
#
#
# @api_view(['GET', 'POST'])
# def webiste_market(request):
#     request = json.loads(request.body.decode('utf-8'))
#     day_list = 30
#     order_data = "Weekly_change"
#
#     # most active options
#     date_time = pd.to_datetime(request['date'], format='%Y/%m/%d')
#     date_string = request['date'].replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     df = main_df.sort_values(by='totalvol', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(30)
#     symbol = list(df["symbol"])
#     most_active_options= pd.DataFrame()
#     last_price = [1,2,3,4,5,6,7,8,9,10]
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     ## Last
#     last = []
#     df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_stockquotes_{str(day_ago)}.csv")
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     most_active_options["Symbol"] = symbol
#     most_active_options["Last"] = last
#     most_active_options["volume"] = df["totalvol"]
#     most_active_options["Daily_change"] = day_change
#     most_active_options["Weekly_change"] = week_change
#     most_active_options["Monthly_change"] = month_change
#     most_active_options["Quarterly_change"] = quarter_change
#
#     #highest_implied_volatility             =================================   ==================
#     column = f"iv{day_list}mean"
#     highest_implied_volatility = pd.DataFrame()
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     last=[]
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     highest_implied_volatility["Symbol"] = symbol
#     highest_implied_volatility["Last"] = last
#     highest_implied_volatility["iv30"] = df[column]
#     highest_implied_volatility["Daily_change"] = day_change
#     highest_implied_volatility["Weekly_change"] = week_change
#     highest_implied_volatility["Monthly_change"] = month_change
#     highest_implied_volatility["Quarterly_change"] = quarter_change
#
#     # Exploding IV
#     column = f"iv{day_list}mean"
#     exploding_IV = pd.DataFrame()
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     last=[]
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     exploding_IV["Symbol"] = symbol
#     exploding_IV["Last"] = last
#     exploding_IV["iv30"] = df[column]
#     exploding_IV["Daily_change"] = day_change
#     exploding_IV["Weekly_change"] = week_change
#     exploding_IV["Monthly_change"] = month_change
#     exploding_IV["Quarterly_change"] = quarter_change
#     exploding_IV = exploding_IV.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#
#     # Imploding IV
#     imploding_IV = pd.DataFrame()
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y][column].values[0]
#                     new = df[df["symbol"] == y][column].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append(0)
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     last=[]
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     imploding_IV["Symbol"] = symbol
#     imploding_IV["Last"] = last
#     imploding_IV["iv30"] = df[column]
#     imploding_IV["Daily_change"] = day_change
#     imploding_IV["Weekly_change"] = week_change
#     imploding_IV["Monthly_change"] = month_change
#     imploding_IV["Quarterly_change"] = quarter_change
#     imploding_IV = imploding_IV.sort_values(by=order_data, ascending=True).reset_index(drop=True)
#
#     #Option Volume gainer
#     option_volume_gainers= pd.DataFrame()
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     last=[]
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     option_volume_gainers["Symbol"] = symbol
#     option_volume_gainers["Last"] = last
#     option_volume_gainers["volume"] = df["totalvol"]
#     option_volume_gainers["Daily_change"] = day_change
#     option_volume_gainers["Weekly_change"] = week_change
#     option_volume_gainers["Monthly_change"] = month_change
#     option_volume_gainers["Quarterly_change"] = quarter_change
#     option_volume_gainers = option_volume_gainers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#
#     #option_volume_losers
#     option_volume_losers= pd.DataFrame()
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     last=[]
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     option_volume_losers["Symbol"] = symbol
#     option_volume_losers["Last"] = last
#     option_volume_losers["volume"] = df["totalvol"]
#     option_volume_losers["Daily_change"] = day_change
#     option_volume_losers["Weekly_change"] = week_change
#     option_volume_losers["Monthly_change"] = month_change
#     option_volume_losers["Quarterly_change"] = quarter_change
#     option_volume_losers = option_volume_losers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#
#     #option_open_interest_gainers
#     option_open_interest_gainers= pd.DataFrame()
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     last=[]
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     option_open_interest_gainers["Symbol"] = symbol
#     option_open_interest_gainers["Last"] = last
#     option_open_interest_gainers["volume"] = df["totaloi"]
#     option_open_interest_gainers["Daily_change"] = day_change
#     option_open_interest_gainers["Weekly_change"] = week_change
#     option_open_interest_gainers["Monthly_change"] = month_change
#     option_open_interest_gainers["Quarterly_change"] = quarter_change
#     option_open_interest_gainers = option_open_interest_gainers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#
#     #option_open_interest_losers
#     option_open_interest_losers= pd.DataFrame()
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = day[day["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     day_change.append(difference)
#                 except:
#                     day_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     week_change = []
#     week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = week[week["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#                 except:
#                     week_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     month_change = []
#     month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = month[month["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#                 except:
#                     month_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#             pass
#     quarter_change = []
#     quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#
#             for y in symbol:
#                 try:
#                     old = quarter[quarter["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#                 except:
#                     quarter_change.append('')
#                     pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     last=[]
#     for y in symbol:
#         try:
#             l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#             last.append(l)
#         except:
#             last.append(None)
#     option_open_interest_losers["Symbol"] = symbol
#     option_open_interest_losers["Last"] = last
#     option_open_interest_losers["volume"] = df["totaloi"]
#     option_open_interest_losers["Daily_change"] = day_change
#     option_open_interest_losers["Weekly_change"] = week_change
#     option_open_interest_losers["Monthly_change"] = month_change
#     option_open_interest_losers["Quarterly_change"] = quarter_change
#     option_open_interest_losers = option_open_interest_losers.sort_values(by=order_data, ascending=True).reset_index(drop=True)
#
#     data = {
#         "mao" : most_active_options.to_dict(),
#         "hiv" : highest_implied_volatility.to_dict(),
#         "ei" : exploding_IV.to_dict(),
#         "ii" : imploding_IV.to_dict(),
#         "ovg" : option_volume_gainers.to_dict(),
#         "ovl" : option_volume_losers.to_dict(),
#         "ooig" : option_open_interest_gainers.to_dict(),
#         "ooil" : option_open_interest_losers.to_dict(),
#     }
#     # return JsonResponse(data)
#     # data = data.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(data, indent=4, default=json), content_type = "application/json")
#
# #To Calculate Time value
# def time_value_call_cal(strike, current_price, mid_price, ask_price):
#   time_value = []
#   for i,s in enumerate(strike):
#     if strike[i]<current_price:
#       final_value = mid_price[i] + strike[i] - current_price
#       if final_value<0:
#         final_value = ask_price[i] + strike[i] - current_price
#     else:
#       final_value = mid_price[i]
#
#     time_value.append(final_value)
#   return time_value
#
#
# def time_value_put_cal(strike, current_price, mid_price, ask_price):
#   time_value = []
#   for i,s in enumerate(strike):
#     if strike[i]>current_price:
#       final_value = mid_price[i] - strike[i] + current_price
#       if final_value<0:
#         final_value = ask_price[i] - strike[i] + current_price
#     else:
#       final_value = mid_price[i]
#     time_value.append(final_value)
#   return time_value
#
# @api_view(['GET', 'POST'])
# def option_chain(request):
#     request = json.loads(request.body.decode('utf-8'))
#     low_s = 0.1
#     high_s = 1000000
#     date = request["date"]
#     symbol = request["symbol"].upper()
#     # date = "2023/03/06"
#     # date = date.replace("/", "")
#     output = {}
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     # date_time = datetime.today()
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date = str(date_time).split(" ")[0].replace("-", "")
#
#         try:
#             df = vaex.open(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date[0:4]}/{str(int(date[4:6]))}/L3_options_{date}.csv.hdf5")
#             break
#         except:
#             i = i + 1
#
#     df1 = df[(df["UnderlyingSymbol"] == symbol) & ((df["Strike"] > low_s) & (df["Strike"] < high_s))]
#
#     expiration_d = df1["Expiration"].unique()
#     expiration_d = sorted(expiration_d)
#     Expiration = list(pd.to_datetime(expiration_d, format="%m/%d/%Y"))
#     Expiration = sorted(Expiration)
#     expiration_dates = [str(x.date()) for x in Expiration]
#
#     data = {}
#     # i =0
#     # #print('hello')
#     for x in expiration_dates:
#         x1 = x
#         temp = x.split("-")
#         x = temp[1] + "/" + temp[2] + "/" + temp[0]
#         calls = pd.DataFrame()
#         puts = pd.DataFrame()
#         df2 = df1[df1["Expiration"] == x].to_pandas_df()
#         # df2 = df1[df1["Expiration"] == x]
#         # df3 = df2[df2["Type"] == "call"].to_pandas_df()
#         # df4 = df2[df2["Type"] == "put"].to_pandas_df()
#         current_price = df2["UnderlyingPrice"].unique()[0]
#         # calls["Symbol"] = [str(x) for x in df3["OptionSymbol"]]
#         # calls["Last"] = df3["Last"]
#         # calls["Change"] = 0.0
#         # calls["Bid"] = df3["Bid"]
#         # calls["Ask"] = df3["Ask"]
#         # calls["Mid"] = (df3["Bid"] + df3["Ask"])/2
#         # calls["Volume"] = df3["Volume"]
#         # calls["OpenInterest"] = df3["OpenInterest"]
#         # calls["IVMean"] = [round(i*100,2) for i in df3["IVMean"]]
#         # calls["Delta"] = df3["Delta"]
#         # calls["Theta"] = df3["Theta"]
#         # calls["Gamma"] = df3["Gamma"]
#         # calls["Vega"] = df3["Vega"]
#         # calls["Strike"] = df4["Strike"]
#         # calls["Time_value"] = time_value_call_cal(calls["Strike"].values, current_price, calls["Mid"].values, calls["Ask"].values)
#         # puts["symbol"] = [str(x) for x in df4["OptionSymbol"]]
#         # puts["last"] = df4["Last"]
#         # puts["change"] = 0.0
#         # puts["bid"] = df4["Bid"]
#         # puts["ask"] = df4["Ask"]
#         # puts["mid"] = (df4["Bid"] + df4["Ask"])/2
#         # puts["volume"] = df4["Volume"]
#         # puts["openInterest"] = df4["OpenInterest"]
#         # puts["iVMean"] = [round(i*100,2) for i in df4["IVMean"]]
#         # puts["delta"] = df4["Delta"]
#         # puts["theta"] = df4["Theta"]
#         # puts["gamma"] = df4["Gamma"]
#         # puts["vega"] = df4["Vega"]
#         # puts["Time_value"] = time_value_put_cal(calls["Strike"].values, current_price, puts["mid"].values, puts["ask"].values)
#
#         calls = df2.loc[df2["Type"] == "call", ["Strike","OptionSymbol", "Last", "Bid", "Ask", "Volume", "OpenInterest", "IVMean", "Delta", "Theta", "Gamma", "Vega"]]
#         calls = calls.assign(
#         Symbol=calls["OptionSymbol"].astype(str),
#         Change=0.0,
#         Mid=(calls["Bid"] + calls["Ask"]) / 2,
#         IVMean=(calls["IVMean"] * 100).round(2),
#         ).drop("OptionSymbol", axis=1)
#         # calls["Time_value"] = time_value_call_cal(calls["Strike"].values, current_price, calls["Mid"].values, calls["Ask"].values)
#         puts = df2.loc[df2["Type"] == "put", ["Strike","OptionSymbol", "Last", "Bid", "Ask", "Volume", "OpenInterest", "IVMean", "Delta", "Theta", "Gamma", "Vega"]]
#         puts = puts.assign(
#             symbol=puts["OptionSymbol"].astype(str),
#             last = puts["Last"],
#             ask = puts["Ask"],
#             bid = puts["Bid"],
#             volume = puts["Volume"],
#             openInterest = puts["OpenInterest"],
#             delta = puts["Delta"],
#             theta = puts["Theta"],
#             gamma = puts["Gamma"],
#             vega = puts["Vega"],
#             change=0.0,
#             mid=(puts["Bid"] + puts["Ask"]) / 2,
#             iVMean=(puts["IVMean"] * 100).round(2),
#         ).drop(["OptionSymbol","Delta","Theta","Gamma","OpenInterest","Volume","Ask","Bid","Strike","Last","IVMean"], axis=1)
#         # puts["Time_value"] = time_value_put_cal(calls["Strike"].values, current_price, puts["mid"].values, puts["ask"].values)
#         temp_df = pd.concat([calls.reset_index(), puts.reset_index()], axis=1)
#
#         temp_dict = {
#             f"{x1}" :  temp_df.to_dict()
#         }
#         data.update(temp_dict)
#         # i = i + 1
#     #print('hello')
#     output['exp_date'] = expiration_dates
#     output['data'] = data
#     output['close'] = current_price
#     # output = output.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(output, indent=4),content_type = "application/json")


# @api_view(['GET', 'POST'])
# def implied_volatility(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     days = request["days"]
#     param = request["param"]
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
    
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try: 
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
    
#     symbol = main_df["symbol"]
#     df = main_df.copy()


#     if param == "default":
#         df2 = pd.DataFrame()
#         df2["symbol"] = df["symbol"])
#         df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         last = []
#         for y in symbol:
#             try:
#                 l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                 last.append(l)
#             except:
#                 last.append(None)
#                 pass
#         df2["last"] = last
#         df2[f"iv{days}mean"] = df[f"iv{days}mean"]

#         # return df2


#     if param == "daily":
#         df2 = pd.DataFrame()
#         day_change = []
#         iv_mean = []
#         last = []
#         day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#         #print(day_ago)
#         i = 0
#         while True:
#             try:
#                 day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{str(day_ago)}.csv")                
#                 day2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_stockquotes_{str(day_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = day[f'iv{days}mean'].to_numpy()[day['symbol'].to_numpy() == y].item()
#                         new = df[f'iv{days}mean'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/old)*100, 2)
#                         l = day2[day2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         day_change.append(difference)
#                         iv_mean.append(old*100)
#                     except:
#                         last.append(None)
#                         day_change.append(None)
#                         iv_mean.append(None)
#                         pass

#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"iv{days}mean_today"] = df[f"iv{days}mean"]*100
#                 df2[f"iv{days}mean_before"] = iv_mean
#                 df2["daily_change"] = day_change
#                 break
#             except:
#                 i = i+1
#                 #print(i)
#                 day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#         # return df2

#     if param == "weekly":
#         df2 = pd.DataFrame()
#         week_change = []
#         iv_mean = []
#         last = []
#         week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#                 week2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_stockquotes_{str(week_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = week[f'iv{days}mean'].to_numpy()[week['symbol'].to_numpy() == y].item()
#                         new = df[f'iv{days}mean'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/old)*100, 2)
#                         l = week2[week2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         week_change.append(difference)
#                         iv_mean.append(old*100)
#                     except:
#                         last.append(None)
#                         week_change.append(None)
#                         iv_mean.append(None)
#                         pass

#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"iv{days}mean_today"] = df[f"iv{days}mean"]*100
#                 df2[f"iv{days}mean_before"] = iv_mean
#                 df2["weekly_change"] = week_change
#                 break
#             except:
#                 i = i+1
#                 week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#         # return df2

#     if param == "monthly":
#         df2 = pd.DataFrame()
#         month_change = []
#         iv_mean = []
#         last = []
#         month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#                 month2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_stockquotes_{str(month_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = month[f'iv{days}mean'].to_numpy()[month['symbol'].to_numpy() == y].item()
#                         new = df[f'iv{days}mean'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/old)*100, 2)
#                         l = month2[month2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         month_change.append(difference)
#                         iv_mean.append(old*100)
#                     except:
#                         last.append(None)
#                         month_change.append(None)
#                         iv_mean.append(None)
#                         pass
#                 #print("hii")
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"iv{days}mean_today"] = df[f"iv{days}mean"]*100
#                 df2[f"iv{days}mean_before"] = iv_mean
#                 df2["monthly_change"] = month_change
#                 break
#             except:                
#                 i = i+1
#                 month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass

#     if param == "quarterly":
#         df2 = pd.DataFrame()
#         quarter_change = []
#         iv_mean = []
#         last = []
#         quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#                 quarter2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_stockquotes_{str(quarter_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = quarter[f'iv{days}mean'].to_numpy()[quarter['symbol'].to_numpy() == y].item()
#                         new = df[f'iv{days}mean'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/old)*100, 2)
#                         l = quarter2[quarter2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         quarter_change.append(difference)
#                         iv_mean.append(old*100)
#                     except:
#                         last.append(None)
#                         quarter_change.append(None)
#                         iv_mean.append(None)
#                         pass

#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"iv{days}mean_today"] = df[f"iv{days}mean"]*100
#                 df2[f"iv{days}mean_before"] = iv_mean
#                 df2["quarterly_change"] = quarter_change
#                 break
#             except:
#                 i = i+1
#                 quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#                 pass

#     if param == "call/put":
#         df2 = df.loc[:, ["symbol", f"iv{days}call", f"iv{days}put"]]
#         df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         last = []
#         for y in symbol:
#             try:
#                 l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                 last.append(l)
#             except:
#                 last.append(None)
#                 pass
#         df2.insert(1, "last", last)
#         df2[f"iv{days}call"] = df2[f"iv{days}call"]*100
#         df2[f"iv{days}put"] = df2[f"iv{days}put"] * 100
#         df2["ratio"] = round(df[f"iv{days}call"] / df[f"iv{days}put"], 4) 

#     if param == "vs_iv360":
#         df2 = df.loc[:, ["symbol", f"iv{days}mean", f"iv360mean"]]
#         df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         last = []
#         for y in symbol:
#             try:
#                 l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                 last.append(l)
#             except:
#                 last.append(None)
#                 pass
#         df2.insert(1, "last", last)
#         ratio = []
#         for x in range(len(df["symbol"])):
#             difference = round(((df[f"iv{days}mean"].loc[x] - df[f"iv360mean"].loc[x]) / df[f"iv{days}mean"].loc[x])*100, 2)
#             ratio.append(difference)
#         df2['%change'] = ratio
#     # #print("dd")
#     df2 = df2.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(df2.to_dict(), indent=4, cls=NpEncoder),content_type = "application/json")

#####################################################################################################################
# @api_view(['GET', 'POST'])
# def implied_volatility(request):
#   flag = True
#   request = json.loads(request.body.decode('utf-8'))
#   date = request["date"]
#   days = request.get("days")
#   param = request.get("param")
# #   curr_date = str(date.split('/')[0]) + str(date.split('/')[1]) + str(date.split('/')[2])
# #   screener = vaex.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv', parse_dates=["ipoDate"], usecols=['Symbol', 'Price', 'MktCap', 'exchangeShortName', 'country', 'Beta', 'currency', 'LastDiv', 'sector', 'industry', 'VolAvg', 'Changes', 'fullTimeEmployees', 'ipoDate'])
# #   screener.rename('Symbol', 'symbol')
#   # page_number = int(request['page_number'])
#
#   date_time = pd.to_datetime(date, format='%Y/%m/%d')
#   date_string = date.replace("/", "")
#
#   i = 0
#   while True:
#       if i > 0:
#           date_time = date_time - timedelta(days=1)
#           date_string = str(date_time).split(" ")[0].replace("-", "")
#       try:
#           main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#           screener = vaex.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{date_string}.csv', parse_dates=["ipoDate"], usecols=['symbol', 'Price', 'MktCap', 'exchangeShortName', 'country', 'Beta', 'currency', 'LastDiv', 'sector', 'industry', 'VolAvg', 'Changes', 'fullTimeEmployees', 'ipoDate'])
#           df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         #   screener.rename('Symbol', 'symbol')
#           break
#       except:
#           i = i + 1
#
#   symbol = main_df["symbol"]
#   df = main_df.copy()
#   if days != None or param != None:
#   # change = ['default','daily','weekly','monthly','quarterly', 'call/put']
#
#   # for i in change:
#       day_change = []
#       iv_mean = []
#       last = []
#       df2 = pd.DataFrame([])
#       if request.get('param') == 'daily':
#           day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#
#       elif request.get('param') == 'weekly':
#           day_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#
#       elif request.get('param') == 'monthly':
#           day_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#
#       elif request.get('param') == 'quarterly':
#           day_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#
#       elif param == "default":
#           df2 = pd.DataFrame()
#           df2["symbol"] = list(df["symbol"])
#           last = []
#           for y in symbol:
#               try:
#                   l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                   last.append(l)
#               except:
#                   last.append(None)
#                   pass
#           df2["last"] = last
#           df2[f"iv{days}mean"] = df[f"iv{days}mean"]
#           flag = False
#
#       elif request.get('param') == 'iv360mean' or request.get('param') == 'call/put':
#           df2 = df.loc[:, ["symbol", f"iv{days}mean", f"iv{days}mean"]]
#           # df3 = stock
#           last = []
#           for x, y in enumerate(symbol):
#               try:
#                   l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                   last.append(l)
#                   if request.get("param") == "iv360mean":
#                       difference = round(
#                           ((df[f"iv{days}mean"].loc[x] - df[f"iv360mean"].loc[x]) / df[f"iv{days}mean"].loc[x])*100, 2)
#                       ratio.append(difference)
#               except:
#                   last.append(None)
#                   pass
#           df2.insert(1, "last", last)
#           ratio = []
#           if request.get("param") == "iv360mean":
#               df2['ratio'] = ratio
#           else:
#               df2["ratio"] = round(df[f"iv{days}call"] / df[f"iv{days}put"], 4)
#               df2['last'] = last
#               df2[f'iv{days}call'] = df[f"iv{days}call"]
#               df2[f'iv{days}put'] = df[f"iv{days}put"]
#
#           flag = False
#
#       else:
#           return HttpResponse(json.dumps({"error": "Not valid param"}, indent=4, cls=NpEncoder), content_type="application/json")
#
#       while flag:
#           try:
#               day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{str(day_ago)}.csv")
#               day2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_stockquotes_{str(day_ago)}.csv")
#
#               for y in symbol:
#                   try:
#                       old = day[f'iv{days}mean'].to_numpy()[day['symbol'].to_numpy() == y].item()
#                       new = df[f'iv{days}mean'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                       difference = round(((new - old)/old)*100, 2)
#                       l = day2[day2["symbol"] == y]["adjustedclose"].values[0]
#                       # print(l)
#                       last.append(l)
#
#                       day_change.append(difference)
#                       iv_mean.append(old*100)
#                   except:
#                       last.append(None)
#                       day_change.append(None)
#                       iv_mean.append(None)
#                       pass
#
#               df2["symbol"] = list(df["symbol"])
#               df2["last"] = last
#               df2[f"iv{days}mean_today"] = df[f"iv{days}mean"]*100
#               df2[f"iv{days}mean_before"] = iv_mean
#               df2[f'{param}_change'] = day_change
#               break
#           except:
#               i = i+1
#               # print(i)
#               # if any change in days then Put same value as used in a_month_ago (30)
#               day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")
#               pass
#
#       df2 = df2.replace({np.nan: None, np.inf: None})
#       data = pd.merge(df2, screener.to_pandas_df(), on='symbol',how="inner")
#
#       if request.get('param') == 'call/put':
#           cols = ['symbol',	'last', f'iv{days}call',f'iv{days}put', 'sector', 'industry', 'ratio']
#           cols2 = ['currency', 'exchangeShortName', 'sector', 'industry', 'country', 'ipoDate','ratio', 'Price', 'MktCap', 'Beta', 'LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#           cols3 = ['ratio', 'Price', 'MktCap', 'Beta','LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#       elif request.get('param') == 'default':
#           cols = ['symbol',	'last','sector', 'industry',f'iv{days}mean']
#           cols2 = ['currency', 'exchangeShortName', 'sector', 'industry', 'country', 'ipoDate','ratio', 'Price', 'MktCap', 'Beta', 'LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#           cols3 = ['ratio', 'Price', 'MktCap', 'Beta','LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#         #   cols2 = []
#         #   cols3 = []
#       else:
#           cols = ['symbol',	'last', f'iv{days}mean_today',f'iv{days}mean_before', 'sector', 'industry', f'{param}_change']
#           cols2 = ['currency', 'exchangeShortName', 'sector', 'industry', 'country', 'ipoDate',f'{param}_change', 'Price', 'MktCap', 'Beta', 'LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#           cols3 = [f'{param}_change', 'Price', 'MktCap', 'Beta','LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#   else:
#       data = screener[screener["symbol"].isin(list(df["symbol"]))].to_pandas_df()
#       cols = ['symbol','sector', 'industry']
#       cols2 = ['currency', 'exchangeShortName', 'sector', 'industry', 'country', 'ipoDate', 'Price', 'MktCap', 'Beta', 'LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#       cols3 = ['Price', 'MktCap', 'Beta','LastDiv', 'VolAvg', 'Changes', 'fullTimeEmployees']
#   for i in cols2:
#       if request.get(i) == None or request.get(i) == "None":
#           pass
#       else:
#           if i == 'currency':
#               if request.get(i) != "any":
#                   temp = request.get(i).split("_")
#                   data = data[data[i].isin(temp)]
#               cols.append(i)
#           if i == 'exchangeShortName':
#               if request.get(i) != "any":
#                   temp = request.get(i).upper().split("_")
#                   data = data[data[i].isin(temp)]
#               cols.append(i)
#           if i == 'sector':
#               if request.get(i) != "any":
#                   temp = [' '.join([x.title() for x in sec.split(' ')]) for sec in request.get(i).split("_")]
#                   data = data[data[i].isin(temp)]
#               cols.append(i)
#           if i == 'industry':
#               if request.get(i) != "any":
#                   temp = [' '.join([x.title() for x in ind.split(' ')]) for ind in request.get(i).split("_")]
#                   data = data[data[i].isin(temp)]
#               cols.append(i)
#           if i == 'country':
#               if request.get(i) != "any":
#                   temp = request.get(i).upper().split("_")
#                   data = data[data[i].isin(temp)]
#               cols.append(i)
#           if i == 'ipoDate':
#               if request.get(i) != "any":
#                   temp = request.get(i).split("_")
#                   data = data[data[i].isin(temp)]
#               cols.append(i)
#           if i in cols3:
#               # print(df2)
#               rng = [float(x) for x in request.get(i).split('_')]
#               data = data[(data[i] >= rng[0]) & (data[i] <= rng[1])]
#               cols.append(i)
#
#   # return final_df1
#   return HttpResponse(json.dumps(data[cols].reset_index(drop=True).to_dict(), indent=4, cls=NpEncoder), content_type="application/json")
#
#
# ######################################################################################################################
#
# @api_view(['GET', 'POST'])
# def volume(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     option = request["option"]
#     param = request["param"]
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     symbol = main_df["symbol"]
#     df = main_df.copy()
#
#     if param == "default":
#         df2 = pd.DataFrame()
#         df2["symbol"] = list(df["symbol"])
#         df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         last = []
#         for y in symbol:
#             try:
#                 l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                 last.append(l)
#             except:
#                 last.append(None)
#                 pass
#         df2["last"] = last
#         df2[f"{option}vol"] = df[f"{option}vol"]
#
#
#     if param == "daily":
#         df2 = pd.DataFrame()
#         day_change = []
#         call_volume = []
#         last = []
#         day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#                 day2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_stockquotes_{str(day_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = day[f'{option}vol'].to_numpy()[day['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}vol'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#                         l = day2[day2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         day_change.append(difference)
#                         call_volume.append(old)
#                     except:
#                         last.append(None)
#                         day_change.append(None)
#                         call_volume.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}vol_today"] = df[f"{option}vol"]
#                 df2[f"{option}vol_before"] = day[f"{option}vol"]
#                 df2["daily_change"] = day_change
#                 break
#             except:
#                 i = i+1
#                 day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#
#     if param == "weekly":
#         df2 = pd.DataFrame()
#         week_change = []
#         call_volume = []
#         last = []
#         week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#                 week2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_stockquotes_{str(week_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = week[f'{option}vol'].to_numpy()[week['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}vol'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#                         l = week2[week2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         week_change.append(difference)
#                         call_volume.append(old)
#                     except:
#                         last.append(None)
#                         week_change.append(None)
#                         call_volume.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}vol_today"] = df[f"{option}vol"]
#                 df2[f"{option}vol_before"] = day[f"{option}vol"]
#                 df2["weekly_change"] = week_change
#                 break
#             except:
#                 i = i+1
#                 week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#
#     if param == "monthly":
#         df2 = pd.DataFrame()
#         month_change = []
#         call_volume = []
#         last = []
#         month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#                 month2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_stockquotes_{str(month_ago)}.csv")
#
#                 for y in symbol:
#                     try:
#                         old = month[f'{option}vol'].to_numpy()[month['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}vol'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#                         l = month2[month2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         month_change.append(difference)
#                         call_volume.append(old)
#                     except:
#                         last.append(None)
#                         month_change.append(None)
#                         call_volume.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}vol_today"] = df[f"{option}vol"]
#                 df2[f"{option}vol_before"] = month[f"{option}vol"]
#                 df2["monthly_change"] = month_change
#                 break
#             except:
#                 i = i+1
#                 month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#
#
#     if param == "quarterly":
#         df2 = pd.DataFrame()
#         quarter_change = []
#         call_volume = []
#         last = []
#         quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#                 quarter2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_stockquotes_{str(quarter_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = quarter[f'{option}vol'].to_numpy()[quarter['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}vol'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#                         l = quarter2[quarter2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         quarter_change.append(difference)
#                         call_volume.append(old)
#                     except:
#                         last.append(None)
#                         quarter_change.append(None)
#                         call_volume.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}vol_today"] = df[f"{option}vol"]
#                 df2[f"{option}vol_before"] = quarter[f"{option}vol"]
#                 df2["quarterly_change"] = quarter_change
#                 break
#             except:
#                 i = i+1
#                 quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#                 pass
#
#
#     if param == "call/put":
#         df2 = df.loc[:, ["symbol", "callvol", "putvol"]]
#         df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         last = []
#         for y in symbol:
#             try:
#                 l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                 last.append(l)
#             except:
#                 last.append(None)
#                 pass
#         df2.insert(1, "last", last)
#         df2["ratio"] = round(df["callvol"] / df["putvol"], 4)
#     df2 = df2.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(df2.to_dict(), indent=4, cls=NpEncoder),content_type = "application/json")
#
#
# @api_view(['GET', 'POST'])
# def open_interest(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     option = request["option"]
#     param = request["param"]
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date_string = str(date_time).split(" ")[0].replace("-", "")
#         try:
#             main_df = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
#             break
#         except:
#             i = i + 1
#
#     symbol = main_df["symbol"]
#     df = main_df.copy()
#
#     if param == "default":
#         df2 = pd.DataFrame()
#         df2["symbol"] = list(df["symbol"])
#         df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         last = []
#         for y in symbol:
#             try:
#                 l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                 last.append(l)
#             except:
#                 last.append(None)
#                 pass
#         df2["last"] = last
#         df2[f"{option}oi"] = df[f"{option}oi"]
#
#
#     if param == "daily":
#         df2 = pd.DataFrame()
#         day_change = []
#         last = []
#         call_oi = []
#         day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 day = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_optionstats_{day_ago}.csv")
#                 day2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{day_ago[0:4]}/{str(int(day_ago[4:6]))}/L3_stockquotes_{str(day_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = day[f'{option}oi'].to_numpy()[day['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}oi'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#                         l = day2[day2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         day_change.append(difference)
#                         call_oi.append(old)
#                     except:
#                         last.append(None)
#                         day_change.append(None)
#                         call_oi.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}oi_today"] = df[f"{option}oi"]
#                 df2[f"{option}oi_before"] = day[f"{option}oi"]
#                 df2["daily_change"] = day_change
#                 break
#             except:
#                 i = i+1
#                 day_ago = str(date_time - timedelta(days=1+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#
#     if param == "weekly":
#         df2 = pd.DataFrame()
#         week_change = []
#         call_oi = []
#         last = []
#         week_ago = str(date_time - timedelta(days=7)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 week = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
#                 week2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_stockquotes_{str(week_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = week[f'{option}oi'].to_numpy()[week['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}oi'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#                         l = week2[week2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         week_change.append(difference)
#                         call_oi.append(old)
#                     except:
#                         last.append(None)
#                         week_change.append(None)
#                         call_oi.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}oi_today"] = df[f"{option}oi"]
#                 df2[f"{option}oi_before"] = day[f"{option}oi"]
#                 df2["weekly_change"] = week_change
#                 break
#             except:
#                 i = i+1
#                 week_ago = str(date_time - timedelta(days=7+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#
#     if param == "monthly":
#         df2 = pd.DataFrame()
#         month_change = []
#         call_oi = []
#         last = []
#         month_ago = str(date_time - timedelta(days=30)).split(" ")[0].replace("-", "")
#         i = 0
#
#         while True:
#             try:
#                 month = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_optionstats_{month_ago}.csv")
#                 month2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{month_ago[0:4]}/{str(int(month_ago[4:6]))}/L3_stockquotes_{str(month_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = month[f'{option}oi'].to_numpy()[month['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}oi'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#
#                         l = month2[month2["symbol"] == y]["adjustedclose"].values[0]
#
#                         last.append(l)
#                         month_change.append(difference)
#                         call_oi.append(old)
#                     except:
#                         last.append(None)
#                         month_change.append(None)
#                         call_oi.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}oi_today"] = df[f"{option}oi"]
#                 df2[f"{option}oi_before"] = month[f"{option}oi"]
#                 df2["monthly_change"] = month_change
#                 break
#             except:
#                 i = i+1
#                 month_ago = str(date_time - timedelta(days=30+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_month_ago (30)
#                 pass
#
#
#     if param == "quarterly":
#         df2 = pd.DataFrame()
#         quarter_change = []
#         call_oi = []
#         last = []
#         quarter_ago = str(date_time - timedelta(days=90)).split(" ")[0].replace("-", "")
#         i = 0
#         while True:
#             try:
#                 quarter = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_optionstats_{quarter_ago}.csv")
#                 quarter2 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{quarter_ago[0:4]}/{str(int(quarter_ago[4:6]))}/L3_stockquotes_{str(quarter_ago)}.csv")
#                 for y in symbol:
#                     try:
#                         old = quarter[f'{option}oi'].to_numpy()[quarter['symbol'].to_numpy() == y].item()
#                         new = df[f'{option}oi'].to_numpy()[df['symbol'].to_numpy() == y].item()
#                         difference = round(((new - old)/new)*100, 2)
#                         l = quarter2[quarter2["symbol"] == y]["adjustedclose"].values[0]
#                         last.append(l)
#                         quarter_change.append(difference)
#                         call_oi.append(old)
#                     except:
#                         last.append(None)
#                         quarter_change.append(None)
#                         call_oi.append(None)
#                         pass
#                 df2["symbol"] = list(df["symbol"])
#                 df2["last"] = last
#                 df2[f"{option}oi_today"] = df[f"{option}oi"]
#                 df2[f"{option}oi_before"] = quarter[f"{option}oi"]
#                 df2["quarterly_change"] = quarter_change
#                 break
#             except:
#                 i = i+1
#                 quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#                 pass
#
#     if param == "call/put":
#         df2 = df.loc[:, ["symbol", "calloi", "putoi"]]
#         df3 = pd.read_csv(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_stockquotes_{str(date_string)}.csv")
#         last = []
#         for y in symbol:
#             try:
#                 l = df3[df3["symbol"] == y]["adjustedclose"].values[0]
#                 last.append(l)
#             except:
#                 last.append(None)
#                 pass
#         df2.insert(1, "last", last)
#         df2["ratio"] = round(df["calloi"] / df["putoi"], 4)
#     df2 = df2.replace({np.nan: None, np.inf: None})
#     return HttpResponse(json.dumps(df2.to_dict(), indent=4, cls=NpEncoder),content_type = "application/json")
#
#
#
#
# @api_view(['GET', 'POST'])
# def option_chain_graph(request):
#     request = json.loads(request.body.decode('utf-8'))
#     # date = request['date'] #'2021/11/24'
#
#     option_symbol = request['option_symbol'] #'A211217C00080000'.
#     symbol = ""
#     for x in option_symbol:
#         if(ord(x) >= 48 and ord(x) <= 57):
#             break
#         else:
#             symbol = symbol + str(x)
#     # df = pd.read_csv("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/company_data/" + symbol + ".csv")
#     # df2 = pd.read_csv("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/closed_price/" + symbol + ".csv")
#     # data = df[:255].reset_index(drop=True)
#     # df = df[255:].append(data)
#     # df = df[:256].append(df[256:].reset_index(drop=True))
#
#     # df = df[df["OptionSymbol"] == option_symbol]
#
#     # mid = (df["Bid"] + df["Ask"])/2
#
#     # output = {
#     #     "mid":list(mid.values),
#     #     "date":list(df[" DataDate"].values),
#     #     # "close":list(df2[df2["quotedate"].isin(list(df[" DataDate"].values))]["close"].values)
#     #     "close":list(df2.iloc[:len(df["Bid"])]["close"].values)
#     # }
#     output = {
#         "mid":[1,6,2,8,4,7,2,4,6,8,2,5],
#         "date":["2022-09-23",
#         "2022-09-30",
#         "2022-10-07",
#         "2022-10-14",
#         "2022-10-21",
#         "2022-10-28",
#         "2022-11-04",
#         "2022-11-18",
#         "2022-12-16",
#         "2023-01-20",
#         "2023-02-17",
#         "2023-03-17"],
#         "close":[5,37,2,7,4,5,6,2,9,3,7,12]
#     }
#     return HttpResponse(json.dumps(output, indent=4), content_type = "application/json")
#
#
#
# def option_chain_graph_1(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     option_symbol = request["option_symbol"] #AAPL211022C00080000 in this type format
#     a = option_symbol[-8:][:-3].split("0")
#     add = [(i,x) for i, x in enumerate(a) if x!= ""]
#     tem = len(a)-add[0][0]-1
#     tem = "0"*tem
#     option_strike = int(f"{add[0][1]}{tem}")
#     symbol = ""
#     for x in option_symbol:
#         if(ord(x) >= 48 and ord(x) <= 57):
#             break
#         else:
#             symbol = symbol + str(x)
#     # symbol = option_symbol.split("2")[0]
#     date = date.replace("/", "")
#     date_time = pd.to_datetime(request["date"],format='%Y/%m/%d')
#     i = 0
#     while True:
#         if i > 0:
#             date_time = date_time - timedelta(days=1)
#             date = str(date_time).split(" ")[0].replace("-", "")
# #             print(date)
#         try:
#             df = vaex.open(f"/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{date[0:4]}/{str(int(date[4:6]))}/L3_options_{str(date)}.csv.hdf5")
#             new_df = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{str(date[0:4])}/{str(int(date[4:6]))}/L3_stockquotes_{str(date)}.csv')
#             # df = pd.DataFrame([])
#             break
#         except:
#             i = i + 1
#
#     df1 = df[df["UnderlyingSymbol"] == symbol]
#     expiration_d = df1["Expiration"].unique()
#     Expiration = list(pd.to_datetime(expiration_d, format="%m/%d/%Y"))
#     expiration_dates = [str(x.date()) for x in Expiration]
#
#     data = {}
#     i = 0
#     for x in expiration_d:
#         calls = pd.DataFrame()
#         puts = pd.DataFrame()
#         df2 = df1[df1["Expiration"] == x]
#         df3 = df2[df2["Type"] == "call"]
#         df4 = df2[df2["Type"] == "put"]
#         calls["Symbol"] = [str(x) for x in list(df3["OptionSymbol"].values)]
#         calls["Mid"] = [(x+y)/2 for x,y in zip(list(df3["Ask"].values),list(df3["Bid"].values))]
#         calls["Strike"] = list(df3["Strike"].values)
#         puts["mid"] = [(x+y)/2 for x,y in zip(list(df4["Ask"].values),list(df4["Bid"].values))]
#         puts["symbol"] = [str(x) for x in list(df4["OptionSymbol"].values)]
#
#         temp_df = pd.concat([calls, puts], axis=1)
#         temp_dict = {
#             f"{expiration_dates[i]}" :  temp_df.to_dict()
#         }
#         data.update(temp_dict)
#         i = i + 1
#
#     gr = {}
#     for k,v in data.items():
#         dg = pd.DataFrame(v)
#         try:
#             ddd = list(dg[dg["Strike"] == option_strike].values[0])
#             gr[k] = ddd
#         except:
#             pass
#
#     g = sorted(gr.items(), key =lambda kv:(kv[1], kv[0]))
#     graph = {}
#     for x in g:
#         graph[x[0]] = x[1]
#     dates = [x for x in graph.keys()]
#     calls_symbols = [x[0] for x in graph.values()]
#     calls_mid = [x[1] for x in graph.values()]
#     puts_mid = [x[3] for x in graph.values()]
#     puts_symbols = [x[4] for x in graph.values()]
#
#     output = {}
#     output["Dates"] = dates
#     # output["Calls_symbols"] = calls_symbols
#     output["Calls_mid"] = calls_mid
#     # output["Puts_symbols"] = puts_symbols
#     output["Strike"] = option_strike
#     output["Puts_mid"] = puts_mid
#
#     return HttpResponse(json.dumps(output, indent=4), content_type = "application/json")

@api_view(['GET', 'POST'])
def get_screener_api_1(request):
    request = json.loads(request.body.decode('utf-8'))
    curr_date = request['curr_date']  #2022-07-26
    curr_date = str(curr_date.split('-')[0]) +str(curr_date.split('-')[1]) + str(curr_date.split('-')[2])
    #df1 = vaex.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv', parse_dates=["ipoDate"])

    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
    file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
    # Load CSV using vaex
    df1 = vaex.read_csv(file_path, parse_dates=["ipoDate"]) #@danish

    page_number = int(request['page_number'])
    # ipo_dates = []
    # for x in df['ipoDate']:
    #     try:
    #         ipo_dates.append(
    #             str(pd.to_datetime(x, format="%d-%m-%Y")).split(' ')[0])
    #     except:
    #         ipo_dates.append(
    #             str(pd.to_datetime(x, format="%Y-%m-%d")).split(' ')[0])
    # df['ipoDate'] = pd.to_datetime(ipo_dates, format="%Y-%m-%d")
    # df1 = vaex.from_pandas(df)

    # Price
    price = request['price']
    if price != "None":
        try:
            price = [float(x) for x in price.split('_')]
            df1 = df1[(df1['Price'] >= price[0]) & (
                df1['Price'] <= price[1])]
        except:
            print("Put Valid Price Range")
            
    currency = request.get('currency')
    if currency != "None":
        try:
            df1 = df1[df1['currency'] == currency]
        except:
            print("Put Valid currency")
    
    # Beta
    beta = request['beta']
    if beta != "None":
        try:
            beta = [float(x) for x in beta.split('_')]
            df1 = df1[(df1['Beta'] >= beta[0]) & (df1['Beta'] <= beta[1])].copy()
        except:
            print("Put Valid Beta Range")

    # VolAvg
    volavg = request['volavg']
    if volavg != "None":
        try:
            volavg = [float(x) for x in volavg.split('_')]
            df1 = df1[(df1['VolAvg'] >= volavg[0]) & (df1['VolAvg'] <= volavg[1])].copy()
        except:
            print("Put Valid VolAvg Range")

    # MktCap
    mktcap = request['mktcap']
    if mktcap != "None":
        try:
            mktcap = [float(x) for x in mktcap.split('_')]
            df1 = df1[(df1['MktCap'] >= mktcap[0]) & (df1['MktCap'] <= mktcap[1])].copy()
        except:
            print("Put Valid MktCap Range")

    # LastDiv
    lastdiv = request['lastdiv']
    if lastdiv != "None":
        try:
            lastdiv = [float(x) for x in lastdiv.split('_')]
            df1 = df1[(df1['LastDiv'] >= lastdiv[0]) & (df1['LastDiv'] <= lastdiv[1])].copy()
        except:
            print("Put Valid LastDiv Range")

    # Changes
    changes = request['changes']
    if changes != "None":
        try:
            changes = [float(x) for x in changes.split('_')]
            df1 = df1[(df1['Changes'] >= changes[0]) & (df1['Changes'] <= changes[1])].copy()
        except:
            print("Put Valid Changes Range")

    # exchangeShortName
    exchangeShortName = request['exchangeShortName']
    if exchangeShortName != "None":
        try:
            exchangeShortName = exchangeShortName.upper()
            df1 = df1[df1['exchangeShortName'] == exchangeShortName].copy()
        except:
            print("Put Valid Exchange Short Name")

    # Sector
    sector = request['sector']
    if sector != "None":
        try:
            sector = ' '.join([x.title() for x in sector.split(' ')])
            df1 = df1[df1['sector'] == sector].copy()
        except:
            print("Put Valid Sector Name")

    # Industry
    industry = request['industry']
    if industry != "None":
        try:
            industry = ' '.join([x.title() for x in industry.split(' ')])
            df1 = df1[df1['industry'] == industry].copy()
        except:
            print("Put Valid Industry Name")

    # country
    country = request['country']
    if country != "None":
        try:
            country = country.upper()
            df1 = df1[df1['country'] == country].copy()
        except:
            print("Put Valid Country Name")

    # fullTimeEmployees
    fullTimeEmployees = request['fullTimeEmployees']
    if fullTimeEmployees != "None":
        try:
            fullTimeEmployees = [float(x)
                                 for x in fullTimeEmployees.split('_')]
            df1 = df1[(df1['fullTimeEmployees'] >= fullTimeEmployees[0]) & (df1['fullTimeEmployees'] <= fullTimeEmployees[1])].copy()
        except:
            print("Put Valid fullTimeEmployees Range")

    # ipoDate
    ipoDate = request['ipoDate']  # "1991-01-03_2001-07-07"
    if ipoDate != "None":
        try:
            ipoDate = [np.datetime64(x) for x in ipoDate.split('_')]
            df1 = df1[(df1['ipoDate'] >= ipoDate[0]) & (df1['ipoDate'] <= ipoDate[1])].copy()
        except:
            print("Put Valid Ipo_date Range")

    # bookValuePerShareTTM
    bookValuePerShareTTM = request['bookValuePerShareTTM']
    if bookValuePerShareTTM != "None":
        try:
            bookValuePerShareTTM = [float(x)
                                    for x in bookValuePerShareTTM.split('_')]
            df1 = df1[(df1['bookValuePerShareTTM'] >= bookValuePerShareTTM[0]) & (df1['bookValuePerShareTTM'] <= bookValuePerShareTTM[1])].copy()
        except:
            print("Put Valid bookValuePerShareTTM Range")

    # capexPerShareTTM
    capexPerShareTTM = request['capexPerShareTTM']
    if capexPerShareTTM != "None":
        try:
            capexPerShareTTM = [float(x) for x in capexPerShareTTM.split('_')]
            df1 = df1[(df1['capexPerShareTTM'] >= capexPerShareTTM[0]) & (df1['capexPerShareTTM'] <= capexPerShareTTM[1])].copy()
        except:
            print("Put Valid capexPerShareTTM Range")

    # capexToDepreciationTTM
    capexToDepreciationTTM = request['capexToDepreciationTTM']
    if capexToDepreciationTTM != "None":
        try:
            capexToDepreciationTTM = [
                float(x) for x in capexToDepreciationTTM.split('_')]
            df1 = df1[(df1['capexToDepreciationTTM'] >= capexToDepreciationTTM[0]) & (df1['capexToDepreciationTTM'] <= capexToDepreciationTTM[1])].copy()
        except:
            print("Put Valid capexToDepreciationTTM Range")

    # capexToOperatingCashFlowTTM
    capexToOperatingCashFlowTTM = request['capexToOperatingCashFlowTTM']
    if capexToOperatingCashFlowTTM != "None":
        try:
            capexToOperatingCashFlowTTM = [
                float(x) for x in capexToOperatingCashFlowTTM.split('_')]
            df1 = df1[(df1['capexToOperatingCashFlowTTM'] >= capexToOperatingCashFlowTTM[0]) & (df1['capexToOperatingCashFlowTTM'] <= capexToOperatingCashFlowTTM[1])].copy()
        except:
            print("Put Valid capexToOperatingCashFlowTTM Range")

    # capexToRevenueTTM
    capexToRevenueTTM = request['capexToRevenueTTM']
    if capexToRevenueTTM != "None":
        try:
            capexToRevenueTTM = [float(x)
                                 for x in capexToRevenueTTM.split('_')]
            df1 = df1[(df1['capexToRevenueTTM'] >= capexToRevenueTTM[0]) & (df1['capexToRevenueTTM'] <= capexToRevenueTTM[1])].copy()
        except:
            print("Put Valid capexToRevenueTTM Range")

    # capitalExpenditureCoverageRatioTTM
    capitalExpenditureCoverageRatioTTM = request['capitalExpenditureCoverageRatioTTM']
    if capitalExpenditureCoverageRatioTTM != "None":
        try:
            capitalExpenditureCoverageRatioTTM = [
                float(x) for x in capitalExpenditureCoverageRatioTTM.split('_')]
            df1 = df1[(df1['capitalExpenditureCoverageRatioTTM'] >= capitalExpenditureCoverageRatioTTM[0]) & (df1['capitalExpenditureCoverageRatioTTM'] <= capitalExpenditureCoverageRatioTTM[1])].copy()
        except:
            print("Put Valid capitalExpenditureCoverageRatioTTM Range")

    # effectiveTaxRateTTM
    effectiveTaxRateTTM = request['effectiveTaxRateTTM']
    if effectiveTaxRateTTM != "None":
        try:
            effectiveTaxRateTTM = [float(x)
                                  for x in effectiveTaxRateTTM.split('_')]
            df1 = df1[(df1['effectiveTaxRateTTM'] >= effectiveTaxRateTTM[0]) & (df1['effectiveTaxRateTTM'] <= effectiveTaxRateTTM[1])].copy()
        except:
            print("Put Valid effectiveTaxRateTTM Range")

    # enterpriseValueTTM
    enterpriseValueTTM = request['enterpriseValueTTM']
    if enterpriseValueTTM != "None":
        try:
            enterpriseValueTTM = [float(x)
                                  for x in enterpriseValueTTM.split('_')]
            df1 = df1[(df1['enterpriseValueTTM'] >= enterpriseValueTTM[0]) & (df1['enterpriseValueTTM'] <= enterpriseValueTTM[1])].copy()
        except:
            print("Put Valid enterpriseValueTTM Range")

    # intangiblesToTotalAssetsTTM
    intangiblesToTotalAssetsTTM = request['intangiblesToTotalAssetsTTM']
    if intangiblesToTotalAssetsTTM != "None":
        try:
            intangiblesToTotalAssetsTTM = [
                float(x) for x in intangiblesToTotalAssetsTTM.split('_')]
            df1 = df1[(df1['intangiblesToTotalAssetsTTM'] >= intangiblesToTotalAssetsTTM[0]) & (df1['intangiblesToTotalAssetsTTM'] <= intangiblesToTotalAssetsTTM[1])].copy()
        except:
            print("Put Valid intangiblesToTotalAssetsTTM Range")

    # investedCapitalTTM
    investedCapitalTTM = request['investedCapitalTTM']
    if investedCapitalTTM != "None":
        try:
            investedCapitalTTM = [float(x)
                                  for x in investedCapitalTTM.split('_')]
            df1 = df1[(df1['investedCapitalTTM'] >= investedCapitalTTM[0]) & (df1['investedCapitalTTM'] <= investedCapitalTTM[1])].copy()
        except:
            print("Put Valid investedCapitalTTM Range")

    # marketCapTTM
    marketCapTTM = request['marketCapTTM']
    if marketCapTTM != "None":
        try:
            marketCapTTM = [float(x) for x in marketCapTTM.split('_')]
            df1 = df1[(df1['marketCapTTM'] >= marketCapTTM[0]) & (df1['marketCapTTM'] <= marketCapTTM[1])].copy()
        except:
            print("Put Valid marketCapTTM Range")

    # netCurrentAssetValueTTM
    netCurrentAssetValueTTM = request['netCurrentAssetValueTTM']
    if netCurrentAssetValueTTM != "None":
        try:
            netCurrentAssetValueTTM = [
                float(x) for x in netCurrentAssetValueTTM.split('_')]
            df1 = df1[(df1['netCurrentAssetValueTTM'] >= netCurrentAssetValueTTM[0]) & (df1['netCurrentAssetValueTTM'] <= netCurrentAssetValueTTM[1])].copy()
        except:
            print("Put Valid netCurrentAssetValueTTM Range")

    # revenuePerShareTTM
    revenuePerShareTTM = request['revenuePerShareTTM']
    if revenuePerShareTTM != "None":
        try:
            temp = [float(x) for x in revenuePerShareTTM.split('_')]
            df1 = df1[(df1['revenuePerShareTTM'] >= temp[0]) & (df1['revenuePerShareTTM'] <= temp[1])].copy()
        except:
            print("Put Valid revenuePerShareTTM Range")

    # stockBasedCompensationToRevenueTTM
    stockBasedCompensationToRevenueTTM = request['stockBasedCompensationToRevenueTTM']
    if stockBasedCompensationToRevenueTTM != "None":
        try:
            temp = [float(x)
                    for x in stockBasedCompensationToRevenueTTM.split('_')]
            df1 = df1[(df1['stockBasedCompensationToRevenueTTM'] >= temp[0]) & (df1['stockBasedCompensationToRevenueTTM'] <= temp[1])].copy()
        except:
            print("Put Valid stockBasedCompensationToRevenueTTM Range")

    # tangibleAssetValueTTM
    tangibleAssetValueTTM = request['tangibleAssetValueTTM']
    if tangibleAssetValueTTM != "None":
        try:
            temp = [float(x) for x in tangibleAssetValueTTM.split('_')]
            df1 = df1[(df1['tangibleAssetValueTTM'] >= temp[0]) & (df1['tangibleAssetValueTTM'] <= temp[1])].copy()
        except:
            print("Put Valid tangibleAssetValueTTM Range")

    # tangibleBookValuePerShareTTM
    tangibleBookValuePerShareTTM = request['tangibleBookValuePerShareTTM']
    if tangibleBookValuePerShareTTM != "None":
        try:
            temp = [float(x) for x in tangibleBookValuePerShareTTM.split('_')]
            df1 = df1[(df1['tangibleBookValuePerShareTTM'] >= temp[0]) & (df1['tangibleBookValuePerShareTTM'] <= temp[1])].copy()
        except:
            print("Put Valid tangibleBookValuePerShareTTM Range")

    # workingCapitalTTM
    workingCapitalTTM = request['workingCapitalTTM']
    if workingCapitalTTM != "None":
        try:
            temp = [float(x) for x in workingCapitalTTM.split('_')]
            df1 = df1[(df1['workingCapitalTTM'] >= temp[0]) & (df1['workingCapitalTTM'] <= temp[1])].copy()
        except:
            print("Put Valid workingCapitalTTM Range")

    # enterpriseValueMultipleTTM
    enterpriseValueMultipleTTM = request['enterpriseValueMultipleTTM']
    if enterpriseValueMultipleTTM != "None":
        try:
            temp = [float(x) for x in enterpriseValueMultipleTTM.split('_')]
            df1 = df1[(df1['enterpriseValueMultipleTTM'] >= temp[0]) & (df1['enterpriseValueMultipleTTM'] <= temp[1])].copy()
        except:
            print("Put Valid enterpriseValueMultipleTTM Range")

    # evToFreeCashFlowTTM
    evToFreeCashFlowTTM = request['evToFreeCashFlowTTM']
    if evToFreeCashFlowTTM != "None":
        try:
            temp = [float(x) for x in evToFreeCashFlowTTM.split('_')]
            df1 = df1[(df1['evToFreeCashFlowTTM'] >= temp[0]) & (df1['evToFreeCashFlowTTM'] <= temp[1])].copy()
        except:
            print("Put Valid evToFreeCashFlowTTM Range")

    # evToOperatingCashFlowTTM
    evToOperatingCashFlowTTM = request['evToOperatingCashFlowTTM']
    if evToOperatingCashFlowTTM != "None":
        try:
            temp = [float(x) for x in evToOperatingCashFlowTTM.split('_')]
            df1 = df1[(df1['evToOperatingCashFlowTTM'] >= temp[0]) & (df1['evToOperatingCashFlowTTM'] <= temp[1])].copy()
        except:
            print("Put Valid evToOperatingCashFlowTTM Range")

    # evToSalesTTM
    evToSalesTTM = request['evToSalesTTM']
    if evToSalesTTM != "None":
        try:
            temp = [float(x) for x in evToSalesTTM.split('_')]
            df1 = df1[(df1['evToSalesTTM'] >= temp[0]) & (df1['evToSalesTTM'] <= temp[1])].copy()
        except:
            print("Put Valid evToSalesTTM Range")

    # grahamNumberTTM
    grahamNumberTTM = request['grahamNumberTTM']
    if grahamNumberTTM != "None":
        try:
            temp = [float(x) for x in grahamNumberTTM.split('_')]
            df1 = df1[(df1['grahamNumberTTM'] >= temp[0]) & (df1['grahamNumberTTM'] <= temp[1])].copy()
        except:
            print("Put Valid grahamNumberTTM Range")

    # priceEarningsRatioTTM
    priceEarningsRatioTTM = request['priceEarningsRatioTTM']
    if priceEarningsRatioTTM != "None":
        try:
            temp = [float(x) for x in priceEarningsRatioTTM.split('_')]
            df1 = df1[(df1['priceEarningsRatioTTM'] >= temp[0]) & (df1['priceEarningsRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid priceEarningsRatioTTM Range")

    # priceEarningsToGrowthRatioTTM
    priceEarningsToGrowthRatioTTM = request['priceEarningsToGrowthRatioTTM']
    if priceEarningsToGrowthRatioTTM != "None":
        try:
            temp = [float(x) for x in priceEarningsToGrowthRatioTTM.split('_')]
            df1 = df1[(df1['priceEarningsToGrowthRatioTTM'] >= temp[0]) & (df1['priceEarningsToGrowthRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid priceEarningsToGrowthRatioTTM Range")

    # priceToBookRatioTTM
    priceToBookRatioTTM = request['priceToBookRatioTTM']
    if priceToBookRatioTTM != "None":
        try:
            temp = [float(x) for x in priceToBookRatioTTM.split('_')]
            df1 = df1[(df1['priceToBookRatioTTM'] >= temp[0]) & (df1['priceToBookRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid priceToBookRatioTTM Range")

    # priceToFreeCashFlowsRatioTTM
    priceToFreeCashFlowsRatioTTM = request['priceToFreeCashFlowsRatioTTM']
    if priceToFreeCashFlowsRatioTTM != "None":
        try:
            temp = [float(x) for x in priceToFreeCashFlowsRatioTTM.split('_')]
            df1 = df1[(df1['priceToFreeCashFlowsRatioTTM'] >= temp[0]) & (df1['priceToFreeCashFlowsRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid priceToFreeCashFlowsRatioTTM Range")

    # priceToOperatingCashFlowsRatioTTM
    priceToOperatingCashFlowsRatioTTM = request['priceToOperatingCashFlowsRatioTTM']
    if priceToOperatingCashFlowsRatioTTM != "None":
        try:
            temp = [float(x)
                    for x in priceToOperatingCashFlowsRatioTTM.split('_')]
            df1 = df1[(df1['priceToOperatingCashFlowsRatioTTM'] >= temp[0]) & (df1['priceToOperatingCashFlowsRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid priceToOperatingCashFlowsRatioTTM Range")

    # priceToSalesRatioTTM_x
    priceToSalesRatioTTM_x = request['priceToSalesRatioTTM_x']
    if priceToSalesRatioTTM_x != "None":
        try:
            temp = [float(x) for x in priceToSalesRatioTTM_x.split('_')]
            df1 = df1[(df1['priceToSalesRatioTTM_x'] >= temp[0]) & (df1['priceToSalesRatioTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid priceToSalesRatioTTM_x Range")

    # assetTurnoverTTM
    assetTurnoverTTM = request['assetTurnoverTTM']
    if assetTurnoverTTM != "None":
        try:
            temp = [float(x) for x in assetTurnoverTTM.split('_')]
            df1 = df1[(df1['assetTurnoverTTM'] >= temp[0]) & (df1['assetTurnoverTTM'] <= temp[1])].copy()
        except:
            print("Put Valid assetTurnoverTTM Range")

    # fixedAssetTurnoverTTM
    fixedAssetTurnoverTTM = request['fixedAssetTurnoverTTM']
    if fixedAssetTurnoverTTM != "None":
        try:
            temp = [float(x) for x in fixedAssetTurnoverTTM.split('_')]
            df1 = df1[(df1['fixedAssetTurnoverTTM'] >= temp[0]) & (df1['fixedAssetTurnoverTTM'] <= temp[1])].copy()
        except:
            print("Put Valid fixedAssetTurnoverTTM Range")

    # inventoryTurnoverTTM_x
    inventoryTurnoverTTM_x = request['inventoryTurnoverTTM_x']
    if inventoryTurnoverTTM_x != "None":
        try:
            temp = [float(x) for x in inventoryTurnoverTTM_x.split('_')]
            df1 = df1[(df1['inventoryTurnoverTTM_x'] >= temp[0]) & (df1['inventoryTurnoverTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid inventoryTurnoverTTM_x Range")

    # payablesTurnoverTTM_x
    payablesTurnoverTTM_x = request['payablesTurnoverTTM_x']
    if payablesTurnoverTTM_x != "None":
        try:
            temp = [float(x) for x in payablesTurnoverTTM_x.split('_')]
            df1 = df1[(df1['payablesTurnoverTTM_x'] >= temp[0]) & (df1['payablesTurnoverTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid payablesTurnoverTTM_x Range")

    # receivablesTurnoverTTM_x
    receivablesTurnoverTTM_x = request['receivablesTurnoverTTM_x']
    if receivablesTurnoverTTM_x != "None":
        try:
            temp = [float(x) for x in receivablesTurnoverTTM_x.split('_')]
            df1 = df1[(df1['receivablesTurnoverTTM_x'] >= temp[0]) & (df1['receivablesTurnoverTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid receivablesTurnoverTTM_x Range")

    # returnOnAssetsTTM
    returnOnAssetsTTM = request['returnOnAssetsTTM']
    if returnOnAssetsTTM != "None":
        try:
            temp = [float(x) for x in returnOnAssetsTTM.split('_')]
            df1 = df1[(df1['returnOnAssetsTTM'] >= temp[0]) & (df1['returnOnAssetsTTM'] <= temp[1])].copy()
        except:
            print("Put Valid returnOnAssetsTTM Range")

    # returnOnCapitalEmployedTTM
    returnOnCapitalEmployedTTM = request['returnOnCapitalEmployedTTM']
    if returnOnCapitalEmployedTTM != "None":
        try:
            temp = [float(x) for x in returnOnCapitalEmployedTTM.split('_')]
            df1 = df1[(df1['returnOnCapitalEmployedTTM'] >= temp[0]) & (df1['returnOnCapitalEmployedTTM'] <= temp[1])].copy()
        except:
            print("Put Valid returnOnCapitalEmployedTTM Range")

    # retur"nOnE"quityTTM
    returnOnEquityTTM = request['returOnEquityTTM']
    if returnOnEquityTTM != "None":
        try:
            temp = [float(x) for x in returnOnEquityTTM.split('_')]
            df1 = df1[(df1['returnOnEquityTTM'] >= temp[0]) & (df1['returnOnEquityTTM'] <= temp[1])].copy()
        except:
            print("Put Valid returnOnEquityTTM Range")

    # returnOnTangibleAssetsTTM
    returnOnTangibleAssetsTTM = request['returnOnTangibleAssetsTTM']
    if returnOnTangibleAssetsTTM != "None":
        try:
            temp = [float(x) for x in returnOnTangibleAssetsTTM.split('_')]
            df1 = df1[(df1['returnOnTangibleAssetsTTM'] >= temp[0]) & (df1['returnOnTangibleAssetsTTM'] <= temp[1])].copy()
        except:
            print("Put Valid returnOnTangibleAssetsTTM Range")

    # ebtPerEbitTTM
    ebtPerEbitTTM = request['ebtPerEbitTTM']
    if ebtPerEbitTTM != "None":
        try:
            temp = [float(x) for x in ebtPerEbitTTM.split('_')]
            df1 = df1[(df1['ebtPerEbitTTM'] >= temp[0]) & (df1['ebtPerEbitTTM'] <= temp[1])].copy()
        except:
            print("Put Valid ebtPerEbitTTM Range")

    # grossProfitMarginTTM
    grossProfitMarginTTM = request['grossProfitMarginTTM']
    if grossProfitMarginTTM != None:
        try:
            temp = [float(x) for x in grossProfitMarginTTM.split('_')]
            df1 = df1[(df1['grossProfitMarginTTM'] >= temp[0]) & (df1['grossProfitMarginTTM'] <= temp[1])].copy()
        except:
            print("Put Valid grossProfitMarginTTM Range")

    # netIncomePerEBTTTM
    netIncomePerEBTTTM = request['netIncomePerEBTTTM']
    if netIncomePerEBTTTM != "None":
        try:
            temp = [float(x) for x in netIncomePerEBTTTM.split('_')]
            df1 = df1[(df1['netIncomePerEBTTTM'] >= temp[0]) & (df1['netIncomePerEBTTTM'] <= temp[1])].copy()
        except:
            print("Put Valid netIncomePerEBTTTM Range")

    # netProfitMarginTTM
    netProfitMarginTTM = request['netProfitMarginTTM']
    if netProfitMarginTTM != "None":
        try:
            temp = [float(x) for x in netProfitMarginTTM.split('_')]
            df1 = df1[(df1['netProfitMarginTTM'] >= temp[0]) & (df1['netProfitMarginTTM'] <= temp[1])].copy()
        except:
            print("Put Valid netProfitMarginTTM Range")

    # operatingProfitMarginTTM
    operatingProfitMarginTTM = request['operatingProfitMarginTTM']
    if operatingProfitMarginTTM != "None":
        try:
            temp = [float(x) for x in operatingProfitMarginTTM.split('_')]
            df1 = df1[(df1['operatingProfitMarginTTM'] >= temp[0]) & (df1['operatingProfitMarginTTM'] <= temp[1])].copy()
        except:
            print("Put Valid operatingProfitMarginTTM Range")

    # pretaxProfitMarginTTM
    pretaxProfitMarginTTM = request['pretaxProfitMarginTTM']
    if pretaxProfitMarginTTM != "None":
        try:
            temp = [float(x) for x in pretaxProfitMarginTTM.split('_')]
            df1 = df1[(df1['pretaxProfitMarginTTM'] >= temp[0]) & (df1['pretaxProfitMarginTTM'] <= temp[1])].copy()
        except:
            print("Put Valid pretaxProfitMarginTTM Range")

    # researchAndDevelopementToRevenueTTM
    researchAndDevelopementToRevenueTTM = request['researchAndDevelopementToRevenueTTM']
    if researchAndDevelopementToRevenueTTM != "None":
        try:
            temp = [float(x)
                    for x in researchAndDevelopementToRevenueTTM.split('_')]
            df1 = df1[(df1['researchAndDevelopementToRevenueTTM'] >= temp[0]) & (df1['researchAndDevelopementToRevenueTTM'] <= temp[1])].copy()
        except:
            print("Put Valid researchAndDevelopementToRevenueTTM Range")

    # salesGeneralAndAdministrativeToRevenueTTM
    salesGeneralAndAdministrativeToRevenueTTM = request['salesGeneralAndAdministrativeToRevenueTTM']
    if salesGeneralAndAdministrativeToRevenueTTM != "None":
        try:
            temp = [float(x)
                    for x in salesGeneralAndAdministrativeToRevenueTTM.split('_')]
            df1 = df1[(df1['salesGeneralAndAdministrativeToRevenueTTM'] >= temp[0]) & (df1['salesGeneralAndAdministrativeToRevenueTTM'] <= temp[1])].copy()
        except:
            print("Put Valid salesGeneralAndAdministrativeToRevenueTTM Range")

    # cashFlowCoverageRatiosTTM
    cashFlowCoverageRatiosTTM = request['cashFlowCoverageRatiosTTM']
    if cashFlowCoverageRatiosTTM != "None":
        try:
            temp = [float(x) for x in cashFlowCoverageRatiosTTM.split('_')]
            df1 = df1[(df1['cashFlowCoverageRatiosTTM'] >= temp[0]) & (df1['cashFlowCoverageRatiosTTM'] <= temp[1])].copy()
        except:
            print("Put Valid cashFlowCoverageRatiosTTM Range")

    # debtEquityRatioTTM
    debtEquityRatioTTM = request['debtEquityRatioTTM']
    if debtEquityRatioTTM != "None":
        try:
            temp = [float(x) for x in debtEquityRatioTTM.split('_')]
            df1 = df1[(df1['debtEquityRatioTTM'] >= temp[0]) & (df1['debtEquityRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid debtEquityRatioTTM Range")

    # debtToAssetsTTM
    debtToAssetsTTM = request['debtToAssetsTTM']
    if debtToAssetsTTM != "None":
        try:
            temp = [float(x) for x in debtToAssetsTTM.split('_')]
            df1 = df1[(df1['debtToAssetsTTM'] >= temp[0]) & (df1['debtToAssetsTTM'] <= temp[1])].copy()
        except:
            print("Put Valid debtToAssetsTTM Range")

    # interestCoverageTTM_x
    interestCoverageTTM_x = request['interestCoverageTTM_x']
    if interestCoverageTTM_x != "None":
        try:
            temp = [float(x) for x in interestCoverageTTM_x.split('_')]
            df1 = df1[(df1['interestCoverageTTM_x'] >= temp[0]) & (df1['interestCoverageTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid interestCoverageTTM_x Range")

    # interestDebtPerShareTTM
    interestDebtPerShareTTM = request['interestDebtPerShareTTM']
    if interestDebtPerShareTTM != "None":
        try:
            temp = [float(x) for x in interestDebtPerShareTTM.split('_')]
            df1 = df1[(df1['interestDebtPerShareTTM'] >= temp[0]) & (df1['interestDebtPerShareTTM'] <= temp[1])].copy()
        except:
            print("Put Valid interestDebtPerShareTTM Range")

    # longTermDebtToCapitalizationTTM
    longTermDebtToCapitalizationTTM = request['longTermDebtToCapitalizationTTM']
    if longTermDebtToCapitalizationTTM != "None":
        try:
            temp = [float(x)
                    for x in longTermDebtToCapitalizationTTM.split('_')]
            df1 = df1[(df1['longTermDebtToCapitalizationTTM'] >= temp[0]) & (df1['longTermDebtToCapitalizationTTM'] <= temp[1])].copy()
        except:
            print("Put Valid longTermDebtToCapitalizationTTM Range")

    # netDebtToEBITDATTM
    netDebtToEBITDATTM = request['netDebtToEBITDATTM']
    if netDebtToEBITDATTM != "None":
        try:
            temp = [float(x) for x in netDebtToEBITDATTM.split('_')]
            df1 = df1[(df1['netDebtToEBITDATTM'] >= temp[0]) & (df1['netDebtToEBITDATTM'] <= temp[1])].copy()
        except:
            print("Put Valid netDebtToEBITDATTM Range")

    # shortTermCoverageRatiosTTM
    shortTermCoverageRatiosTTM = request['shortTermCoverageRatiosTTM']
    if shortTermCoverageRatiosTTM != "None":
        try:
            temp = [float(x) for x in shortTermCoverageRatiosTTM.split('_')]
            df1 = df1[(df1['shortTermCoverageRatiosTTM'] >= temp[0]) & (df1['shortTermCoverageRatiosTTM'] <= temp[1])].copy()
        except:
            print("Put Valid shortTermCoverageRatiosTTM Range")

    # totalDebtToCapitalizationTTM
    totalDebtToCapitalizationTTM = request['totalDebtToCapitalizationTTM']
    if totalDebtToCapitalizationTTM != "None":
        try:
            temp = [float(x) for x in totalDebtToCapitalizationTTM.split('_')]
            df1 = df1[(df1['totalDebtToCapitalizationTTM'] >= temp[0]) & (df1['totalDebtToCapitalizationTTM'] <= temp[1])].copy()
        except:
            print("Put Valid totalDebtToCapitalizationTTM Range")

    # cashConversionCycleTTM
    cashConversionCycleTTM = request['cashConversionCycleTTM']
    if cashConversionCycleTTM != "None":
        try:
            temp = [float(x) for x in cashConversionCycleTTM.split('_')]
            df1 = df1[(df1['cashConversionCycleTTM'] >= temp[0]) & (df1['cashConversionCycleTTM'] <= temp[1])].copy()
        except:
            print("Put Valid cashConversionCycleTTM Range")

    # cashPerShareTTM_y
    cashPerShareTTM_y = request['cashPerShareTTM_y']
    if cashPerShareTTM_y != "None":
        try:
            temp = [float(x) for x in cashPerShareTTM_y.split('_')]
            df1 = df1[(df1['cashPerShareTTM_y'] >= temp[0]) & (df1['cashPerShareTTM_y'] <= temp[1])].copy()
        except:
            print("Put Valid cashPerShareTTM_y Range")

    # cashRatioTTM
    cashRatioTTM = request['cashRatioTTM']
    if cashRatioTTM != "None":
        try:
            temp = [float(x) for x in cashRatioTTM.split('_')]
            df1 = df1[(df1['cashRatioTTM'] >= temp[0]) & (df1['cashRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid cashRatioTTM Range")

    # currentRatioTTM_y
    currentRatioTTM_y = request['currentRatioTTM_y']
    if currentRatioTTM_y != "None":
        try:
            temp = [float(x) for x in currentRatioTTM_y.split('_')]
            df1 = df1[(df1['currentRatioTTM_y'] >= temp[0]) & (df1['currentRatioTTM_y'] <= temp[1])].copy()
        except:
            print("Put Valid currentRatioTTM_y Range")

    # daysOfInventoryOutstandingTTM
    daysOfInventoryOutstandingTTM = request['daysOfInventoryOutstandingTTM']
    if daysOfInventoryOutstandingTTM != "None":
        try:
            temp = [float(x) for x in daysOfInventoryOutstandingTTM.split('_')]
            df1 = df1[(df1['daysOfInventoryOutstandingTTM'] >= temp[0]) & (df1['daysOfInventoryOutstandingTTM'] <= temp[1])].copy()
        except:
            print("Put Valid daysOfInventoryOutstandingTTM Range")

    # daysOfPayablesOutstandingTTM
    daysOfPayablesOutstandingTTM = request['daysOfPayablesOutstandingTTM']
    if daysOfPayablesOutstandingTTM != "None":
        try:
            temp = [float(x) for x in daysOfPayablesOutstandingTTM.split('_')]
            df1 = df1[(df1['daysOfPayablesOutstandingTTM'] >= temp[0]) & (df1['daysOfPayablesOutstandingTTM'] <= temp[1])].copy()
        except:
            print("Put Valid daysOfPayablesOutstandingTTM Range")

    # daysOfSalesOutstandingTTM
    daysOfSalesOutstandingTTM = request['daysOfSalesOutstandingTTM']
    if daysOfSalesOutstandingTTM != "None":
        try:
            temp = [float(x) for x in daysOfSalesOutstandingTTM.split('_')]
            df1 = df1[(df1['daysOfSalesOutstandingTTM'] >= temp[0]) & (df1['daysOfSalesOutstandingTTM'] <= temp[1])].copy()
        except:
            print("Put Valid daysOfSalesOutstandingTTM Range")

    # operatingCycleTTM
    operatingCycleTTM = request['operatingCycleTTM']
    if operatingCycleTTM != "None":
        try:
            temp = [float(x) for x in operatingCycleTTM.split('_')]
            df1 = df1[(df1['operatingCycleTTM'] >= temp[0]) & (df1['operatingCycleTTM'] <= temp[1])].copy()
        except:
            print("Put Valid operatingCycleTTM Range")

    # quickRatioTTM
    quickRatioTTM = request['quickRatioTTM']
    if quickRatioTTM != "None":
        try:
            temp = [float(x) for x in quickRatioTTM.split('_')]
            df1 = df1[(df1['quickRatioTTM'] >= temp[0]) & (df1['quickRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid quickRatioTTM Range")

    # dividendPaidAndCapexCoverageRatioTTM
    dividendPaidAndCapexCoverageRatioTTM = request['dividendPaidAndCapexCoverageRatioTTM']
    if dividendPaidAndCapexCoverageRatioTTM != "None":
        try:
            temp = [float(x)
                    for x in dividendPaidAndCapexCoverageRatioTTM.split('_')]
            df1 = df1[(df1['dividendPaidAndCapexCoverageRatioTTM'] >= temp[0]) & (df1['dividendPaidAndCapexCoverageRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid dividendPaidAndCapexCoverageRatioTTM Range")

    # dividendYieldTTM_x
    dividendYieldTTM_x = request['dividendYieldTTM_x']
    if dividendYieldTTM_x != "None":
        try:
            temp = [float(x) for x in dividendYieldTTM_x.split('_')]
            df1 = df1[(df1['dividendYieldTTM_x'] >= temp[0]) & (df1['dividendYieldTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid dividendYieldTTM_x Range")

    # earningsYieldTTM
    earningsYieldTTM = request['earningsYieldTTM']
    if earningsYieldTTM != "None":
        try:
            temp = [float(x) for x in earningsYieldTTM.split('_')]
            df1 = df1[(df1['earningsYieldTTM'] >= temp[0]) & (df1['earningsYieldTTM'] <= temp[1])].copy()
        except:
            print("Put Valid earningsYieldTTM Range")

    # netIncomePerShareTTM
    netIncomePerShareTTM = request['netIncomePerShareTTM']
    if netIncomePerShareTTM != "None":
        try:
            temp = [float(x) for x in netIncomePerShareTTM.split('_')]
            df1 = df1[(df1['netIncomePerShareTTM'] >= temp[0]) & (df1['netIncomePerShareTTM'] <= temp[1])].copy()
        except:
            print("Put Valid netIncomePerShareTTM Range")

    # freeCashFlowOperatingCashFlowRatioTTM
    freeCashFlowOperatingCashFlowRatioTTM = request['freeCashFlowOperatingCashFlowRatioTTM']
    if freeCashFlowOperatingCashFlowRatioTTM != "None":
        try:
            temp = [float(x)
                    for x in freeCashFlowOperatingCashFlowRatioTTM.split('_')]
            df1 = df1[(df1['freeCashFlowOperatingCashFlowRatioTTM'] >= temp[0]) & (df1['freeCashFlowOperatingCashFlowRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid freeCashFlowOperatingCashFlowRatioTTM Range")

    # freeCashFlowPerShareTTM_x
    freeCashFlowPerShareTTM_x = request['freeCashFlowPerShareTTM_x']
    if freeCashFlowPerShareTTM_x != "None":
        try:
            temp = [float(x) for x in freeCashFlowPerShareTTM_x.split('_')]
            df1 = df1[(df1['freeCashFlowPerShareTTM_x'] >= temp[0]) & (df1['freeCashFlowPerShareTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid freeCashFlowPerShareTTM_x Range")

    # freeCashFlowYieldTTM
    freeCashFlowYieldTTM = request['freeCashFlowYieldTTM']
    if freeCashFlowYieldTTM != "None":
        try:
            temp = [float(x) for x in freeCashFlowYieldTTM.split('_')]
            df1 = df1[(df1['freeCashFlowYieldTTM'] >= temp[0]) & (df1['freeCashFlowYieldTTM'] <= temp[1])].copy()
        except:
            print("Put Valid freeCashFlowYieldTTM Range")

    # incomeQualityTTM
    incomeQualityTTM = request['incomeQualityTTM']
    if incomeQualityTTM != "None":
        try:
            temp = [float(x) for x in incomeQualityTTM.split('_')]
            df1 = df1[(df1['incomeQualityTTM'] >= temp[0]) & (df1['incomeQualityTTM'] <= temp[1])].copy()
        except:
            print("Put Valid incomeQualityTTM Range")

    # operatingCashFlowPerShareTTM_x
    operatingCashFlowPerShareTTM_x = request['operatingCashFlowPerShareTTM_x']
    if operatingCashFlowPerShareTTM_x != "None":
        try:
            temp = [float(x)
                    for x in operatingCashFlowPerShareTTM_x.split('_')]
            df1 = df1[(df1['operatingCashFlowPerShareTTM_x'] >= temp[0]) & (df1['operatingCashFlowPerShareTTM_x'] <= temp[1])].copy()
        except:
            print("Put Valid operatingCashFlowPerShareTTM_x Range")

    # operatingCashFlowSalesRatioTTM
    operatingCashFlowSalesRatioTTM = request['operatingCashFlowSalesRatioTTM']
    if operatingCashFlowSalesRatioTTM != "None":
        try:
            temp = [float(x)
                    for x in operatingCashFlowSalesRatioTTM.split('_')]
            df1 = df1[(df1['operatingCashFlowSalesRatioTTM'] >= temp[0]) & (df1['operatingCashFlowSalesRatioTTM'] <= temp[1])].copy()
        except:
            print("Put Valid operatingCashFlowSalesRatioTTM Range")

    df1 = df1.to_pandas_df()

    # Set According to Page Number
    df1 = df1.reset_index(drop=True)
    # total_pages = math.ceil(len(df1)/500)
    # # print(len(df1))
    # if page_number <= total_pages:
    #     if page_number == 1:
    #         end = page_number * 499
    #         start = end - 500
    #         df2 = df1[(df1.index >= start) & (df1.index <= end)].copy()
    #     else:
    #         end = page_number * 500
    #         start = end - 500
    #         df2 = df1[(df1.index >= start) & (df1.index < end)].copy()
    # else:
    #     df2 = pd.DataFrame()
    #     print("Put Valid Page Number")
    # df2 = df2.to_dict()
    # df2['total_pages'] = total_pages
    df1 = df1.loc[:26,:]
    df1 = df1.round(2).to_dict()
    # for dict_value in df1:
    #     for k, v in dict_value.items():
    #         dict_value[k] = round(v, 2)
            
    return HttpResponse(json.dumps(df1, indent=4, default=str), content_type="application/json")

#df2 = df2.replace({np.nan: None, np.inf: None})

####################################################################################################################################
@api_view(['POST','GET'])
def get_screener_api(request):
  request = json.loads(request.body.decode('utf-8'))
  curr_date = request['curr_date']  #2022-07-26
  curr_date = str(curr_date.split('-')[0]) +str(curr_date.split('-')[1]) + str(curr_date.split('-')[2])
  #df1 = vaex.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv', parse_dates=["ipoDate"])
  base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
  file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
  df1 = vaex.read_csv(file_path, parse_dates=["ipoDate"]) #@danish

  screener = df1.to_pandas_df()
  cols1 = ['currency','exchangeShortName', 'sector', 'industry', 'country', 'ipoDate']
  col = ['symbol', 'companyName']
  page = int(request.get("page_number"))
  offset = int(request.get("offset"))
  l = ['MktCap', 'LastDiv','VolAvg', 'Beta', 'Price', 'Changes']
  for i in l:
      request[i] = request.get(i.lower())
  for i in screener.columns:
    if (request.get(i) == None or request.get(i) == "None") and request.get(i.lower()) == None:
        pass
    else:
      if i in cols1:
        if i == 'currency':
            if request.get(i) != "any":
                currency = request.get(i).split("_")
                screener = screener[screener[i].isin(currency)]
            col.append(i)
        if i == 'exchangeShortName':
            if request.get(i) != "any":
                exchange = request.get(i).upper().split("_")
                screener = screener[screener[i].isin(exchange)]
            col.append(i)
        if i == 'sector':
            if request.get(i) != "any":
                sector = [' '.join([x.title() for x in sec.split(' ')]) for sec in request.get(i).split("_")]
                screener = screener[screener[i].isin(sector)]
            col.append(i)
        if i == 'industry':
            if request.get(i) != "any":
                industry = [' '.join([x.title() for x in ind.split(' ')]) for ind in request.get(i).split("_")]
                screener = screener[screener[i].isin(industry)] 
            col.append(i)
        if i == 'country':
            if request.get(i) != "any":
                country = request.get(i).upper().split("_")
                screener = screener[screener[i].isin(country)]
            col.append(i)
        if i == 'ipoDate':
            if request.get(i) != "any":
                ipoDate = [np.datetime64(x) for x in request.get(i).split('_')]
                screener = screener[(screener[i] >= ipoDate[0]) & (screener[i] <= ipoDate[1])]
            col.append(i)
      else:    
        rng = [float(x) for x in request.get(i.lower()).split('_')]
        if len(rng) == 3:
            screener = screener[((screener[i] >= rng[0]) & (screener[i] <= rng[1])) | (screener[i].isnull())]
        else:
            screener = screener[(screener[i] >= rng[0]) & (screener[i] <= rng[1])]
        col.append(i)
  screener = screener.replace({np.nan: None, np.inf: None})
  screener = screener.reset_index()
#   screener = screener[col].loc[:26,:]
  if request.get("sorting_param") == "None" or request.get("sorting_param") == None:
      sorting_param = "MktCap"
      sorting_type = False
  else:
      sorting_param = request.get("sorting_param")
      if request.get("sorting_type") == "ASC":
          sorting_type = True
      else:
          sorting_type = False
          
  if request.get("watchlist",False):
    screener = screener[screener.symbol.isin(request.get("watchlist").split("_"))]
  final = screener.sort_values(by=[sorting_param], ascending=sorting_type).reset_index(drop=True)[(page-1)*offset:(page-1)*offset+offset][col].to_dict()
  final["total_records"] = len(screener)
  
  return HttpResponse(json.dumps(final, indent=4, default=str), content_type="application/json")
#   return HttpResponse(json.dumps(screener[page*25:page*25+25].to_dict(), indent=4, default=str), content_type="application/json")

#####################################################################################################################################

def replace_none(test_dict):
    # checking for dictionary and replacing if None
    if isinstance(test_dict, dict):
        for key in test_dict:
            if test_dict[key] is np.nan:
                test_dict[key] = None
            else:
                replace_none(test_dict[key])
  
    # checking for list, and testing for each value
    elif isinstance(test_dict, list):
        for val in test_dict:
            replace_none(val)

def number_to_string(number):
    suffixes = ["", "K", "M", "B", "T", "Qua", "Qui"]
    number = round(number,2)
    # Turn the int number into a string and format with ,'s
    number = str("{:,}".format(number))
    # For loop to find the amount of commas in the newly made string
    commas = 0
    x = 0
    while x < len(number):
        if number[x] == ',':
            commas += 1
        x += 1
    # Use the amount of commas to decide the element in the array that will be used as a suffix
    # for example, if there are 2 commas it will use million.
    return number.split(',')[0]+ suffixes[commas]


@api_view(['POST','GET'])
def screener_1(request):
    today_date = date.today()
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #data_limit = json.loads(open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_percentiles_data/screener_'+str(curr_date)+'.json').read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_percentiles_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.json")
            with open(file_path, 'r') as f:
                data_limit = json.load(f) #@danish

            break
        except:
            i = i + 1
    return HttpResponse(json.dumps(data_limit, indent=4, default=str), content_type="application/json")
    
@api_view(['POST'])
def screener_2(request):
    output = {}
    today_date = date.today()
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #output = json.loads(open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_2_'+str(curr_date)+'.json').read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_2_{curr_date}.json")
            with open(file_path, 'r') as f:
                output = json.load(f) #@danish

            # screener_data = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            break
        except:
            i = i + 1
    try:
        request = json.loads(request.body.decode('utf-8'))   
        print(request) 
        if request.get("industry") != None:
            final = {}
            final["industry"] = {}
            for i in ["0.1", "0.25", "0.5", "0.75", "0.9"]:
                final["industry"][i] = {}
                for j in list(output["industry"][i].keys()):
                    final["industry"][i][j] = {}
                    final["industry"][i][j][request.get("industry")] = output["industry"][i][j][request.get("industry")]
        if request.get("sector") != None:
            final = {}
            final["sector"] = {}
            for i in ["0.1", "0.25", "0.5", "0.75", "0.9"]:
                final["sector"][i] = {}
                for j in list(output["sector"][i].keys()):
                    final["sector"][i][j] = {}
                    final["sector"][i][j][request.get("sector")] = output["sector"][i][j][request.get("sector")]

        return HttpResponse(json.dumps(final, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({}, indent=4, default=str), content_type="application/json")
    # screener_data = screener_data.index[screener_data['valuecol1'] > 0]
    # screener_data = screener_data[~screener_data.isin([np.nan, np.inf, -np.inf]).any(1)]
    # screener_data= screener_data[(screener_data > 0).all(1)]
    # screener_data = screener_data[screener_data.select_dtypes(include=[np.number]).ge(0).all(1)]
    
    #industry quantiles calculations
    # in_025 = screener_data.groupby(['industry']).quantile(0.25)
    # in_05 = screener_data.groupby(['industry']).quantile(0.5)
    # in_075 = screener_data.groupby(['industry']).quantile(0.75)
    # in_09 = screener_data.groupby(['industry']).quantile(0.9)
    
    # #sector quantiles calculaitons
    # se_025 = screener_data.groupby(['sector']).quantile(0.25)
    # se_05 = screener_data.groupby(['sector']).quantile(0.5)
    # se_075 = screener_data.groupby(['sector']).quantile(0.75)
    # se_09 = screener_data.groupby(['sector']).quantile(0.9)
    
    # output['industry'] = {}
    # output['sector'] = {}
    
    # output['industry']['0.25'] = in_025.to_dict()
    # output['industry']['0.5'] = in_05.to_dict()
    # output['industry']['0.75'] = in_075.to_dict()
    # output['industry']['0.9'] = in_09.to_dict()
    
    # output['sector']['0.25'] = se_025.to_dict()
    # output['sector']['0.5'] = se_05.to_dict()
    # output['sector']['0.75'] = se_075.to_dict()
    # output['sector']['0.9'] = se_09.to_dict()

        

@api_view(['POST'])
def screener_3(request):
    request = json.loads(request.body.decode('utf-8'))
    today_date = date.today()
    
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path) #@danish
            df = df[df["priceToSalesRatioTTM_x"] > 0.05]
            df = df[df['currency'] == "USD"]
            break
        except:
            i = i + 1
    
    if int(request['all_sectors']) == 1:
        data_all_sectors = {}
        for x in df['sector'].unique():
            total_mktcap = df[df['sector'] == x]["MktCap"].sum()
            data_all_sectors[x] = int(total_mktcap)
        return HttpResponse(json.dumps(data_all_sectors, indent=4, default=str), content_type="application/json")
        
    if request['is_sector'] is not None:
        try:
            data_is_sector = {}
            industries = df[df['sector'] == request['is_sector']]['industry'].unique()
            for x in industries:
                total_mktcap = df[df['industry'] == x]["MktCap"].sum()
                data_is_sector[x] = int(total_mktcap)
            return HttpResponse(json.dumps(data_is_sector, indent=4, default=str), content_type="application/json")
        except:
            return HttpResponse(json.dumps({'error':'sector name is incorrect'}, indent=4, default=str), content_type="application/json")
    
    if request['is_industry'] is not None:
        # try:
        data_is_industry = {}
        company_name = {}
        total = 0
        companies = df[df['industry'] == request['is_industry']]['symbol'].unique()
        for x in companies:
            total_mktcap = df[df['symbol'] == x]["MktCap"].sum()
            company_name[df[df['symbol'] == x]["companyName"].tolist()[0]] = total_mktcap
            total += total_mktcap
            data_is_industry[x] = int(total_mktcap)
        
        sorted_dict = dict(sorted(data_is_industry.items(), key=lambda item: item[1], reverse=True))
        sorted_dict_2 = dict(sorted(company_name.items(), key=lambda item: item[1], reverse=True))
        data_is_industry['companyName'] = list(sorted_dict_2.keys())[:10]
        data_is_industry['top_10_company'] = list(sorted_dict.keys())[:10]
        data_is_industry['top_10_revenue'] = list(sorted_dict.values())[:10]
        top_10_sum = sum(data_is_industry['top_10_revenue'])
        data_is_industry['others'] = total-top_10_sum
        return HttpResponse(json.dumps(data_is_industry, indent=4, default=str), content_type="application/json")
        # except:
        #     return HttpResponse(json.dumps({'error':'industry name is incorrect'}, indent=4, default=str), content_type="application/json")

@api_view(['POST'])
def screener_4(request):
    request = json.loads(request.body.decode('utf-8'))
    today_date = date.today()
    
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path) #@danish
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df = df[df['Revenue'] >= 0]
            df.dropna(subset=["Revenue"], how="all", inplace=True)
            df = df[df["priceToSalesRatioTTM_x"] > 0.05]
            df = df[df['currency'] == "USD"]
            break
        except:
            i = i + 1
    
    if int(request['all_sectors']) == 1:
        data_all_sectors = {}
        for x in df['sector'].unique():
            total_mktcap = df[df['sector'] == x]["Revenue"].sum()
            data_all_sectors[x] = total_mktcap
        replace_none(data_all_sectors)
        return HttpResponse(json.dumps(data_all_sectors, indent=4, default=str), content_type="application/json")
        
    if request['is_sector'] is not None:
        try:
            data_is_sector = {}
            industries = df[df['sector'] == request['is_sector']]['industry'].unique()
            for x in industries:
                total_mktcap = df[df['industry'] == x]["Revenue"].sum()
                data_is_sector[x] = total_mktcap
            replace_none(data_is_sector)
            return HttpResponse(json.dumps(data_is_sector, indent=4, default=str), content_type="application/json")
        except:
            return HttpResponse(json.dumps({'error':'sector name is incorrect'}, indent=4, default=str), content_type="application/json")
    
    if request['is_industry'] is not None:
        try:
            data_is_industry = {}
            total = 0
            company_name = {}
            companies = df[df['industry'] == request['is_industry']]['symbol'].unique()
            for x in companies:
                total_mktcap = df[df['symbol'] == x]["Revenue"].sum()
                company_name[df[df['symbol'] == x]["companyName"].tolist()[0]] = total_mktcap
                data_is_industry[x] = total_mktcap
                total += total_mktcap
            # data_is_industry = dict((k, v) for k, v in data_is_industry.iteritems() if v)
            replace_none(data_is_industry)
            
            sorted_dict = dict(sorted(data_is_industry.items(), key=lambda item: item[1], reverse=True))
            sorted_dict_2 = dict(sorted(company_name.items(), key=lambda item: item[1], reverse=True))
            data_is_industry['companyName'] = list(sorted_dict_2.keys())[:10]
            # data_is_industry['companyName'] = company_name
            data_is_industry['top_10_company'] = list(sorted_dict.keys())[:10]
            data_is_industry['top_10_revenue'] = list(sorted_dict.values())[:10]
            top_10_sum = sum(data_is_industry['top_10_revenue'])
            data_is_industry['others'] = total-top_10_sum
            
            return HttpResponse(json.dumps(data_is_industry, indent=4, default=str), content_type="application/json")
        except:
            return HttpResponse(json.dumps({'error':'industry name is incorrect'}, indent=4, default=str), content_type="application/json")

@api_view(['GET', 'POST'])
def get_company(request):
    request = json.loads(request.body.decode('utf-8'))
    today_date = date.today()
    industry_name = request['industry']
    currency = request.get("currency")
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try:
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path) #@danish
            
            df2 = df
            break
        except:
            i = i + 1
    df = df[df['industry'] == industry_name]
    df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)
    #############################################################################
    df.dropna(subset=["Revenue"], how="all", inplace=True)
    df = df[df['Revenue']>=0]
    
    in_05 = df.groupby(['industry']).quantile(0.5)
    best = []
    base = []
    worst = []
    best_perc = []
    base_perc = []
    worst_perc = []
    temp = {}
    # output['industry']['0.5'] = in_05.to_dict()
    if currency == None:
        df = df[df['currency'] == "USD"]
    companies = df[df['industry'] == industry_name]['symbol'].unique()
    for x in companies:
        total_mktcap = df[df['symbol'] == x]["MktCap"].sum()
        temp[x] = total_mktcap
    
    for s in sorted(temp, key=temp.get, reverse=True):
        t = df[df['symbol'] == s].reset_index()
         
        t_data = [t.loc[0,'enterpriseValueMultipleTTM'], t.loc[0,'evToFreeCashFlowTTM'], t.loc[0,'evToOperatingCashFlowTTM'], t.loc[0,'evToSalesTTM'], 
                    t.loc[0,'priceEarningsRatioTTM'], t.loc[0,'priceEarningsToGrowthRatioTTM'], t.loc[0,'priceToBookRatioTTM'],
                    t.loc[0,'priceToFreeCashFlowsRatioTTM'], t.loc[0,'priceToOperatingCashFlowsRatioTTM'], t.loc[0,'priceToSalesRatioTTM_x']]
        in_data = [in_05.loc[industry_name,'enterpriseValueMultipleTTM'], in_05.loc[industry_name,'evToFreeCashFlowTTM'], in_05.loc[industry_name,'evToOperatingCashFlowTTM'], in_05.loc[industry_name,'evToSalesTTM'], 
                    in_05.loc[industry_name,'priceEarningsRatioTTM'], in_05.loc[industry_name,'priceEarningsToGrowthRatioTTM'], in_05.loc[industry_name,'priceToBookRatioTTM'],
                    in_05.loc[industry_name,'priceToFreeCashFlowsRatioTTM'], in_05.loc[industry_name,'priceToOperatingCashFlowsRatioTTM'], in_05.loc[industry_name,'priceToSalesRatioTTM_x']]
        average_1 = [i / j for i, j in zip(in_data, t_data) if j != 0]
        # if float('inf') in average_1:
        #     average_1.remove(float('inf'))
        average = [i*t["Price"][0] for i in average_1]
        average = [i for i in average if i>0]
        # average.pop(4)
        average = sorted(average)
        if len(average) == 0:
            value = 0
            percentage = 0
            
            best.append(value)
            best_perc.append(percentage)
            
            # average.append(t.loc[0,'grahamNumberTTM'])
            
            base.append(value)
            base_perc.append(percentage)
            
            # average_2 = [i for i in average if i>0]
            worst.append(value)
            worst_perc.append(percentage)
        elif len(average) < 5:
            value = statistics.mean(average)
            percentage = ((t["Price"][0] - statistics.mean(average)) / t["Price"][0]) * 100
            
            best.append(value)
            best_perc.append(percentage)
            
            # average.append(t.loc[0,'grahamNumberTTM'])
            
            base.append(value)
            base_perc.append(percentage)
            
            # average_2 = [i for i in average if i>0]
            worst.append(value)
            worst_perc.append(percentage)
        else:
            best.append(statistics.mean(average[:5]))
            best_perc.append(((t["Price"][0] - statistics.mean(average[:5])) / t["Price"][0]) * 100)
            
            # average.append(t.loc[0,'grahamNumberTTM'])
            
            base.append(statistics.mean(average))
            base_perc.append(((t["Price"][0] - statistics.mean(average)) / t["Price"][0]) * 100)
            
            # average_2 = [i for i in average if i>0]
            worst.append(statistics.mean(average))
            worst_perc.append(((t["Price"][0] - statistics.mean(average[-5:])) / t["Price"][0]) * 100)
    df["Best"] = best
    df["relative_best"] = best_perc
    df["Base"] = base
    df["relative_base"] = base_perc
    df["worst"] = worst
    df["relative_worst"] = worst_perc
    df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)
    ################################################################################
    d = df.to_dict()
    return HttpResponse(json.dumps(d, indent=4, default=str), content_type="application/json")

##########################################################################

@api_view(['GET', 'POST'])
def get_company_2(request):
    request = json.loads(request.body.decode('utf-8'))
    today_date = date.today()
    industry_name = request['industry']
    currency = request.get("currency")
 
    in_05 = {}
    while True:
        # date_string = str(today_date).split(" ")[0].replace("-", "")
        try:
            today_date = today_date - timedelta(days=1)
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path) #@danish
            cols = ['Price','enterpriseValueMultipleTTM','evToFreeCashFlowTTM','evToOperatingCashFlowTTM','evToSalesTTM', 'grahamNumberTTM','priceEarningsRatioTTM','priceEarningsToGrowthRatioTTM','priceToBookRatioTTM','priceToFreeCashFlowsRatioTTM','priceToOperatingCashFlowsRatioTTM','priceToSalesRatioTTM_x','Revenue','MktCap']
            df2 = df
            df = df[df['industry'] == industry_name]
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.dropna(subset=["Revenue"], how="all", inplace=True)
            df = df[df['Revenue']>=0]
            
            for j in cols:
                in_05[j] = {}
                in_05[j][industry_name] = df[df[j]>0][j].median()
                    
            break
        except:
            continue
    
    best = []
    base = []
    worst = []
    best_perc = []
    base_perc = []
    worst_perc = []
    temp = {}
    # output['industry']['0.5'] = in_05.to_dict()
    if currency == "USD":
        df = df[df['currency'] == "USD"]
    companies = df[df['industry'] == industry_name]['symbol'].unique()
    
    for s in companies:
        t = df[df['symbol'] == s].reset_index()
         
        t_data = [t.loc[0,'enterpriseValueMultipleTTM'], t.loc[0,'evToFreeCashFlowTTM'], t.loc[0,'evToOperatingCashFlowTTM'], t.loc[0,'evToSalesTTM'], 
                    t.loc[0,'priceEarningsRatioTTM'], t.loc[0,'priceToBookRatioTTM'],
                    t.loc[0,'priceToFreeCashFlowsRatioTTM'], t.loc[0,'priceToOperatingCashFlowsRatioTTM'], t.loc[0,'priceToSalesRatioTTM_x']]
        in_data = [in_05['enterpriseValueMultipleTTM'][industry_name], in_05['evToFreeCashFlowTTM'][industry_name], in_05['evToOperatingCashFlowTTM'][industry_name], in_05['evToSalesTTM'][industry_name], 
                         in_05['priceEarningsRatioTTM'][industry_name], in_05['priceToBookRatioTTM'][industry_name],
                        in_05['priceToFreeCashFlowsRatioTTM'][industry_name], in_05['priceToOperatingCashFlowsRatioTTM'][industry_name], in_05['priceToSalesRatioTTM_x'][industry_name]]
        average_1 = [i / j for i, j in zip(in_data, t_data) if j != 0]
        
        # if float('inf') in average_1:
        #     average_1.remove(float('inf'))
        average = [i*t["Price"][0] for i in average_1]
        average = [i for i in average if i>0]
        # average.pop(4)
        average = sorted(average)[::-1]
    
        # if len(average) == 0:
        #     value = 0
        #     percentage = 0
            
        #     best.append(value)
        #     best_perc.append(percentage)
            
        #     # average.append(t.loc[0,'grahamNumberTTM'])
            
        #     base.append(value)
        #     base_perc.append(percentage)
            
        #     # average_2 = [i for i in average if i>0]
        #     worst.append(value)
        #     worst_perc.append(percentage)
        # elif len(average) < 5:
        #     value = statistics.mean(average[:math.ceil(len(average)/2)])
        #     percentage = ((t["Price"][0] - value) / t["Price"][0]) * 100
            
        #     best.append(value)
        #     best_perc.append(percentage)
            
        #     # average.append(t.loc[0,'grahamNumberTTM'])
            
        #     base.append(value)
        #     base_perc.append(percentage)
            
        #     # average_2 = [i for i in average if i>0]
        #     worst.append(value)
        #     worst_perc.append(percentage)
        # else:
        best.append(statistics.mean(average[:math.ceil(len(average)/2)]))
        best_perc.append(((t["Price"][0] - statistics.mean(average[:math.ceil(len(average)/2)])) / t["Price"][0]) * 100)
        
        # average.append(t.loc[0,'grahamNumberTTM'])
        
        base.append(statistics.mean(average))
        base_perc.append(((t["Price"][0] - statistics.mean(average)) / t["Price"][0]) * 100)
        
        # average_2 = [i for i in average if i>0]
        worst.append(statistics.mean(average[-math.ceil(len(average)/2):]))
       
        worst_perc.append(((t["Price"][0] - statistics.mean(average[-math.ceil(len(average)/2):])) / t["Price"][0]) * 100)
    df["Best"] = best
    df["relative_best"] = best_perc
    df["Base"] = base
    df["relative_base"] = base_perc
    df["worst"] = worst
    df["relative_worst"] = worst_perc
    df.replace([np.nan, np.inf, -np.inf], 0, inplace=True)
    ################################################################################
    df = df.reset_index(drop=True)
    if request.get("symbol") != None:
        row_index = df.index[df['symbol'] == request.get("symbol")].tolist()[0]
        df = pd.concat([df.iloc[row_index:row_index+1], df.iloc[:row_index], df.iloc[row_index+1:]]).reset_index(drop=True)
    d = df.to_dict('records')
   
    return HttpResponse(json.dumps(d, indent=4, default=str), content_type="application/json")


###########################################################################
# def load_data(intc_df, median_df):
#     # intc_df = pd.DataFrame(data)
#     # median_df = pd.DataFrame(data1)
#     intc_df1 = intc_df.loc[:,'Enterprise Value Multiple':'Price To Sales Ratio']

#     return intc_df, median_df, intc_df1



# def average(intc_df, median_df, intc_df1):
#     average = median_df/intc_df1
#     average = average * intc_df['Current Price'][0]

#     return average



@api_view(['GET', 'POST'])
def relative_valuation_2(request):
    request = json.loads(request.body.decode('utf-8'))
    today_date = date.today()
    
    industry_name = request['industry']
    current_sym = request['symbol']
 
    in_05 = {}
    i=0
    while True:
        today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try:
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv', usecols=['symbol','industry','enterpriseValueMultipleTTM','evToFreeCashFlowTTM','evToOperatingCashFlowTTM','evToSalesTTM', 'grahamNumberTTM','priceEarningsRatioTTM','priceEarningsToGrowthRatioTTM','priceToBookRatioTTM','priceToFreeCashFlowsRatioTTM','priceToOperatingCashFlowsRatioTTM','priceToSalesRatioTTM_x','Revenue','MktCap','Price','country','currency','relative_fy0_best','relative_fy0_base','relative_fy0_worst'])
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv") #@danish
            df = pd.read_csv(file_path, usecols=['symbol','industry','enterpriseValueMultipleTTM','evToFreeCashFlowTTM','evToOperatingCashFlowTTM','evToSalesTTM', 'grahamNumberTTM','priceEarningsRatioTTM','priceEarningsToGrowthRatioTTM','priceToBookRatioTTM','priceToFreeCashFlowsRatioTTM','priceToOperatingCashFlowsRatioTTM','priceToSalesRatioTTM_x','Revenue','MktCap','Price','country','currency','relative_fy0_best','relative_fy0_base','relative_fy0_worst'])
            cols = ['Price','enterpriseValueMultipleTTM','evToFreeCashFlowTTM','evToOperatingCashFlowTTM','evToSalesTTM', 'grahamNumberTTM','priceEarningsRatioTTM','priceEarningsToGrowthRatioTTM','priceToBookRatioTTM','priceToFreeCashFlowsRatioTTM','priceToOperatingCashFlowsRatioTTM','priceToSalesRatioTTM_x','Revenue','MktCap']
            break
        except:
            i = i + 1
    df = df[df['industry'] == industry_name]
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(subset=["Revenue"], how="all", inplace=True)
    df = df[df['Revenue']>=0]
    if len(df[df['symbol'] == current_sym]["country"].values) != 0:
        country = df[df['symbol'] == current_sym]["country"].values[0]
    else:
        return HttpResponse(json.dumps({"data":[], "status":500}, indent=4, default=str), content_type="application/json")
    if country == "US":
        if len(df[(df["country"] == "US") & (df['industry'] == industry_name)]) > 50:
            df = df[df["country"] == "US"]
    in_05_1 = {}
    for j in cols:
        in_05[j] = {}
        in_05[j][industry_name] = df[df[j]>0][j].median()
        in_05_1[j] = df[df[j]>0][j].median()
    # else:
    #     df = df[df["country"] != "US"]
        
            
    
    # df = df[df['industry'] == industry_name]
    # df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # df.dropna(subset=["Revenue"], how="all", inplace=True)
    # df = df[df['Revenue']>=0]
    # in_05 = df.groupby(['industry']).quantile(0.5)
   ###################################
    # dfprev = df[df["symbol"] == "AAPL"]
    # df['Abbreviation'] = df['symbol'].str.split('.', n=1, expand=True)[0]
    # df = df[~(df['Abbreviation'].duplicated(keep='first') & df['Abbreviation'].notna())]
    # df = df.drop('Abbreviation', axis=1)
    # dfafter = df[df["symbol"] == "AAPL"]
    ####################################
    if country == "US":
        df = df[df["country"] == "US"] 
    range_relative = {
            "relative_best" : str(df[df["relative_fy0_best"] < 0]["relative_fy0_best"].quantile(.1)) + "_" + str(df[df["relative_fy0_best"] > 0]["relative_fy0_best"].quantile(.9)) ,
            "relative_fy0_base" : str(df[df["relative_fy0_base"] < 0]["relative_fy0_base"].quantile(.1)) + "_" + str(df[df["relative_fy0_base"] > 0]["relative_fy0_base"].quantile(.9)) ,
            "relative_fy0_worst" : str(df[df["relative_fy0_worst"] < 0]["relative_fy0_worst"].quantile(.1)) + "_" + str(df[df["relative_fy0_worst"] > 0]["relative_fy0_worst"].quantile(.9)) 
        }
    # output['industry']['0.5'] = in_05.to_dict()
    if True:
        data_is_industry = {}
        temp = {}
        if len(df[(df['industry'] == industry_name) & (df['currency'] == "USD")]) > 10:
            df = df[df['currency'] == "USD"]
        companies = df[df['industry'] == industry_name]['symbol'].unique()
        for x in companies:
            if x != current_sym:
                total_mktcap = df[df['symbol'] == x]["MktCap"].sum()
                temp[x] = total_mktcap
    
        data_is_industry['top_10'] = sorted(temp, key=temp.get, reverse=True)[:10]
        
        data_is_industry['top_10'].insert(0, current_sym)
        
        datas = df["symbol"]
       
        for s in data_is_industry['top_10']:
            t = df[df['symbol'] == s].reset_index()
             
            t_data = [t.loc[0,'enterpriseValueMultipleTTM'], t.loc[0,'evToFreeCashFlowTTM'], t.loc[0,'evToOperatingCashFlowTTM'], t.loc[0,'evToSalesTTM'], 
                         t.loc[0,'priceEarningsRatioTTM'], t.loc[0,'priceToBookRatioTTM'],
                        t.loc[0,'priceToFreeCashFlowsRatioTTM'], t.loc[0,'priceToOperatingCashFlowsRatioTTM'], t.loc[0,'priceToSalesRatioTTM_x']]
            in_data = [in_05['enterpriseValueMultipleTTM'][industry_name], in_05['evToFreeCashFlowTTM'][industry_name], in_05['evToOperatingCashFlowTTM'][industry_name], in_05['evToSalesTTM'][industry_name], 
                         in_05['priceEarningsRatioTTM'][industry_name], in_05['priceToBookRatioTTM'][industry_name],
                        in_05['priceToFreeCashFlowsRatioTTM'][industry_name], in_05['priceToOperatingCashFlowsRatioTTM'][industry_name], in_05['priceToSalesRatioTTM_x'][industry_name]]
            average_1 = [i / j for i, j in zip(in_data, t_data) if j != 0]
            
            average = [i*t["Price"][0] for i in average_1]
          
            # average.pop(4)
            average = [i for i in average if i >0.05]
            
            average = sorted(average)[::-1]
            if len(average) != 0:
                t["Best"] = statistics.mean(average[:math.ceil(len(average)/2)])
                t["relative_best"] = ((t["Price"][0] - statistics.mean(average[:math.ceil(len(average)/2)])) / t["Price"][0]) * 100
                
                # average.append(t.loc[0,'grahamNumberTTM'])
                
                t["Base"] = statistics.mean(average)
                t["relative_base"] = ((t["Price"][0] - statistics.mean(average)) / t["Price"][0]) * 100
                
                # average_2 = [i for i in average if i>0]
                t["worst"] = statistics.mean(average[-math.ceil(len(average)/2):])
                t["relative_worst"] = ((t["Price"][0] - statistics.mean(average[-math.ceil(len(average)/2):])) / t["Price"][0]) * 100
            else:
                t["Best"] = 0
                t["relative_best"] = 0
                
                # average.append(t.loc[0,'grahamNumberTTM'])
                
                t["Base"] = 0
                t["relative_base"] = 0
                
                # average_2 = [i for i in average if i>0]
                t["worst"] = 0
                t["relative_worst"] = 0
                
            t.replace([np.nan, np.inf, -np.inf], 0, inplace=True)
            # else:
            #     t["Best"] = statistics.mean(average[:5])
            #     t["relative_best"] = ((t["Price"][0] - statistics.mean(average[:5])) / t["Price"][0]) * 100
                
            #     # average.append(t.loc[0,'grahamNumberTTM'])
                
            #     t["Base"] = statistics.mean(average)
            #     t["relative_base"] = ((t["Price"][0] - statistics.mean(average)) / t["Price"][0]) * 100
                
            #     # average_2 = [i for i in average if i>0]
            #     t["worst"] = statistics.mean(average[-5:])
            #     t["relative_worst"] = ((t["Price"][0] - statistics.mean(average[-5:])) / t["Price"][0]) * 100
            #     t.replace([np.nan, np.inf, -np.inf], 0, inplace=True)
            data_is_industry[s] = t.to_dict()
        
        
        
        # t = df2[df2['symbol'] == current_sym]
        in_05["Best"] = "-"
        in_05["relative_best"] = "-"
        in_05["Base"] = "-"
        in_05["relative_base"] = "-"
        in_05["worst"] = "-"
        in_05["relative_worst"] = "-"
        # data_is_industry[current_sym] = t.to_dict()
        data_is_industry['in_05'] = in_05
        data_is_industry['in_05_1'] = in_05_1
        data_is_industry['range_percentile'] = range_relative
    
        
        return HttpResponse(json.dumps(data_is_industry, indent=4, default=str), content_type="application/json")
    # except:
    #     return HttpResponse(json.dumps({'error':'industry name is incorrect'}, indent=4, default=str), content_type="application/json")


##########################################################################


@api_view(['GET', 'POST'])
def relative_valuation(request):
    request = json.loads(request.body.decode('utf-8'))
    today_date = date.today()
    industry_name = request['industry']
    current_sym = request['symbol']
   
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try:
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data") #@danish
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path)
            country = df[df['symbol'] == current_sym]["country"].values[0]
            industry_name = df[df['symbol'] == current_sym]["industry"].values[0]
            if country == "US":
                if len(df[(df["country"] == "US") & (df['industry'] == industry_name)]) > 50:
                    df = df[df["country"] == "US"]
            
            df2 = df
            break
        except:
            i = i + 1
    df = df[df['industry'] == industry_name]
    
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(subset=["Revenue"], how="all", inplace=True)
    df = df[df['Revenue']>=0]
    
    in_05 = df.groupby(['industry']).quantile(0.5)
    # create a new column with the first part of each company name
    df['Abbreviation'] = df['symbol'].str.split('.', n=1, expand=True)[0]
    
    # remove duplicates based on the first part of the name
    df = df[~(df['Abbreviation'].duplicated(keep='first') & df['Abbreviation'].notna())]
    
    # drop the abbreviation column
    df = df.drop('Abbreviation', axis=1)
    if country == "US":
        df = df[df["country"] == "US"]
    # output['industry']['0.5'] = in_05.to_dict()
    try:
        data_is_industry = {}
        temp = {}
        if len(df[(df['industry'] == industry_name) & (df['currency'] == "USD")]) > 10:
            df = df[df['currency'] == "USD"]
        companies = df[df['industry'] == industry_name]['symbol'].unique()
        for x in companies:
            if x != current_sym:
                total_mktcap = df[df['symbol'] == x]["MktCap"].sum()
                temp[x] = total_mktcap
        data_is_industry['top_10'] = sorted(temp, key=temp.get, reverse=True)[:20]
        data_is_industry['top_10'].insert(0, current_sym)
        for s in data_is_industry['top_10']:
            t = df[df['symbol'] == s]
            data_is_industry[s] = t.to_dict()
        t = df2[df2['symbol'] == current_sym]
        
        # print('test')
        # print(t['symbol'])
        
        data_is_industry[current_sym] = t.to_dict()
        data_is_industry['in_05'] = in_05.to_dict()
        # data_is_industry['dataframe'] = df['symbol'].values
        return HttpResponse(json.dumps(data_is_industry, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({'error':'industry name is incorrect'}, indent=4, default=str), content_type="application/json")

@api_view(['POST'])
def get_rv_symbol(request):
    request = json.loads(request.body.decode('utf-8'))
    today_date = date.today()
    current_sym = request['symbol']
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path) #@danish
            break
        except:
            i = i + 1
    t = df[df['symbol']==current_sym]
    return HttpResponse(json.dumps(t.to_dict(), indent=4, default=str), content_type="application/json")

@api_view(['POST'])
def get_industry_percentile(request):
    res = json.loads(request.body.decode('utf-8'))
    industry = res["industry"]
    today_date = date.today()
    i=0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path) #@danish
            break
        except:
            i = i + 1
            
    industry_df = df[df["industry"] == industry]
    revenue = industry_df["Revenue"].dropna()
    data = {"Total Market Sales Of the Industry":sum(revenue)}
    for i in range(1,101):
        data[i] = np.percentile(revenue, i)
    
    return HttpResponse(json.dumps(data, indent=4, default=str), content_type="application/json")

# OLD total function working completely     
# def total(request):
#     if request.method == "POST":
#         request = json.loads(request.body.decode('utf-8'))
#         month = int(request["month"])
#         strike_perc = int(request["strike_percent"])
#         date = request["date"]
        
#         calls = request["call_value"]
#         call_min = float(calls.split('_')[0])
#         call_max = float(calls.split('_')[1])
        
#         puts = request["put_value"]
#         put_min = float(puts.split('_')[0])
#         put_max = float(puts.split('_')[1])
        
#         cps = request["cp_value"]
#         cp_min = float(cps.split('_')[0])
#         cp_max = float(cps.split('_')[1])
        
#         formated_date = date.split("-")
#         final_date = formated_date[0] + formated_date[1] + formated_date[2]
#         file = open("/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/invex_ratio_daily/final_invex_avg_"+str(final_date) + ".json","r")
#         data = json.load(file)
        
#         final_data = {}
#         #strike_perc = 30
#         #month = 200
#         symbols = data.keys()
        
#         for symbol in symbols:
#             try:
#                 arr = []
#                 s = pd.DataFrame(data[symbol])
#                 current_price = float(s.iloc[0,0])
#                 rol_value = s["0"]
#                 arr = pd.DataFrame(rol_value)
#                 rolling = arr.dropna()
#                 rolling = pd.to_numeric(rolling["0"])
#                 rolling = rolling[1:].astype(int)
                #print(rolling)
                
#                 exp_value = s["Expiration"]
#                 arr2 = pd.DataFrame(exp_value)
#                 expiration = arr2.dropna()
#                 expiration = expiration[:-1]
                
#                 lower_value = float(current_price - ((current_price*(strike_perc / 10))/10.0))
#                 higher_value = float(current_price + ((current_price*(strike_perc / 10))/10.0))
            
#                 call_array = 0.0
#                 put_array = 0.0
#                 cp = 0.0
#                 hvtf_array = 0.0
#                 len_roll = 0
#                 com = {}
#                 for r,e in zip(rolling,expiration.values):
#                     if r <= month:
                        
#                         filter_s = s[(s["Strike_"+str(r)]>=lower_value) & (s["Strike_"+str(r)]<=higher_value)]
#                         strike = filter_s["Strike_"+str(r)].values
#                         call_ir = filter_s["Invex_ratio_call_"+str(r)].mean()
#                         put_ir = filter_s["Invex_ratio_put_"+str(r)].mean()
#                         cp_ratio = filter_s["CP_ratio_"+str(r)].mean()
#                         hvtf = filter_s["HVTF_put_" + str(r)].iloc[0]
#                         # com["Expiration"] = filter_s["Expiration"]
                        
#                         call_array += call_ir
#                         put_array += put_ir
#                         cp += cp_ratio
#                         hvtf_array += hvtf
            
#                         com[e[0]]=[call_ir, put_ir, cp_ratio, hvtf]
#                         len_roll += 1
#             except:
#                 continue
#             try:
#                 call_array = call_array/len_roll
#                 put_array = put_array/len_roll
#                 cp = cp/len_roll
#                 hvtf_array = hvtf_array/len_roll
#             except:
#                 continue
            
#             if (call_array>call_min and call_array<call_max) and (put_array>put_min and put_array<put_max) and (cp>cp_min and cp<cp_max):
#                 com["total"] = [call_array, put_array, cp,hvtf_array]
#                 final_data[symbol] = com
                
#         file.close()
#         return HttpResponse(json.dumps(final_data, indent=4,default=str),content_type = "application/json")
#         #return JsonResponse(final_data, safe=False)  


# @api_view(['POST'])
# def view_revenue_operating_netincome_data(request):
#     request = json.loads(request.body.decode('utf-8'))
#     try:
#         ticker = request["ticker"]
#         ticker = ticker+'.json'
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/revenue/'+ticker, 'r') as f:
#             data_rev = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/operating/'+ticker, 'r') as f:
#             data_operating = f.read()
#         # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/netincome/'+ticker, 'r') as f:
#             # netincome = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/net_margin/'+ticker, 'r') as f:
#             net_margin = f.read()
#
#         api_data = {}
#         api_data["revenue"] = json.loads(data_rev)
#         api_data["operating_margin"] = json.loads(data_operating)
#         # api_data["net_income"] = json.loads(netincome)
#         api_data["net_margin"] = json.loads(net_margin)
#         return HttpResponse(json.dumps(api_data, indent=4, default=str), content_type="application/json")
#     except:
#         return HttpResponse(json.dumps({"status":"ERROR","data":"File not found"}, indent=4, default=str), content_type="application/json")
    
# @api_view(['POST'])
# def view_sales_beta_revenue_operating(request):
#     request = json.loads(request.body.decode('utf-8'))
#     if request["country"] == "usa":
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/beta_with_us.json', 'r') as f:
#             beta = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/sales_with_us.json', 'r') as f:
#             sales = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/operating_with_us.json', 'r') as f:
#             operating = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/revenue_with_us.json', 'r') as f:
#             revenue = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/netincome_with_us.json', 'r') as f:
#             income = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/payout_with_us.json', 'r') as f:
#             payout = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/roe_with_us.json', 'r') as f:
#             roe = f.read()
#
#     else:
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/beta_without_us.json', 'r') as f:
#             beta = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/sales_without_us.json', 'r') as f:
#             sales = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/operating_without_us.json', 'r') as f:
#             operating = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/revenue_without_us.json', 'r') as f:
#             revenue = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/netincome_without_us.json', 'r') as f:
#             income = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/payout_without_us.json', 'r') as f:
#             payout = f.read()
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/roe_without_us.json', 'r') as f:
#             roe = f.read()
#
#     api_data = {}
#     api_data["salestocapital"] = json.loads(sales)
#     api_data["beta"] = json.loads(beta)
#     api_data["operating"] = json.loads(operating)
#     api_data["revenue"] = json.loads(revenue)
#     api_data["netincome"] = json.loads(income)
#     api_data["payout"] = json.loads(payout)
#     api_data["roe"] = json.loads(roe)
#
#     return HttpResponse(json.dumps(api_data, indent=4, default=str), content_type="application/json")

# with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/historicalnew1.json','r') as f:
#         hist_data = f.read()
#         hist = json.loads(hist_data)

base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media")
hist_file = os.path.join(base_path, "historicalnew1.json")
with open(hist_file, 'r') as f:
    hist_data = f.read()
    hist = json.loads(hist_data) #@danish

@api_view(['POST'])
def historical_relative_valuation(request):
    request = json.loads(request.body.decode('utf-8'))
    # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/historical2.json','r') as f:
    #     hist_data = f.read()
    #     hist = json.loads(hist_data)
    # return HttpResponse(json.dumps(request, indent=4, default=str), content_type="application/json")
    cols = ['date','period','enterpriseValueMultiple','priceEarningsRatio','priceEarningsToGrowthRatio','priceToBookRatio','priceToFreeCashFlowsRatio','priceToOperatingCashFlowsRatio','priceToSalesRatio']
    cols1 = ['evToFreeCashFlow','evToOperatingCashFlow','evToSales','grahamNumber','date']
    symbol = request['symbol']
    industry = request['industry']
    dictt = {}
  
    d = pd.read_json("https://financialmodelingprep.com/api/v3/ratios/"+symbol+"?period=quarter&limit=140&apikey=b1360803f80dd08bdd0211c5c004ad03")[cols]
    df = pd.read_json("https://financialmodelingprep.com/api/v3/key-metrics/"+symbol+"?period=quarter&limit=120&apikey=b1360803f80dd08bdd0211c5c004ad03")[cols1]
    
    df = pd.merge(d,df)
    
    jsn = requests.get('https://financialmodelingprep.com/api/v3/historical-chart/1day/' + symbol + '?from=1991-05-16&to=2023-05-15&apikey=b1360803f80dd08bdd0211c5c004ad03')
    aapl = pd.DataFrame(jsn.json())
    aapl["date"] = pd.to_datetime(aapl["date"])
    
    df['year'] = [i.date().year for i in list(df['date'])]
    
    year = df['year'].unique()
    
    year = list(year)
    
    dff = df[df['year'].isin(year)]
    
    dff['quarter'] = dff['period'].map(str)+ " " + dff['year'].map(str)
    
    
        
    
    col = ['enterpriseValueMultiple','evToOperatingCashFlow','evToSales','priceEarningsRatio','priceEarningsToGrowthRatio','priceToBookRatio','priceToFreeCashFlowsRatio','priceToOperatingCashFlowsRatio','priceToSalesRatio']
    best = []
    base = []
    worst = []
    relative_best = []
    relative_base = []
    relative_worst = []
    price_list = []
    for d in range(len(dff)):
      average = []
      for c in col:
        att = dff.loc[d,c]
        try:
           # histd = hist[industry][c][dff.loc[d,'quarter']]['50']
            histd = hist.get(industry, hist["Default Industry"]).get(c, {}).get(dff.loc[d, 'quarter'], {}).get('50', 0) #@danish

        except:
            average.append(0)
            price=1
            continue
        if att != 0:
          avg = histd/att
        dates = dff.loc[d,'date']
        symbol_dates = list(aapl["date"].apply(lambda x : str(x.date())))
        for i in range(4):
          if str(dates.date()) in symbol_dates:
            price = list(aapl[aapl['date'] == str(dates.date())]["close"])[0]
            
            break
          else:
            dates = dates - timedelta(days=1)
        average.append(avg * price)
        
      average = [i for i in average if i >= 0]
      average = sorted(average)[::-1]
    
      price_list.append(price)
      if len(average) == 0:
          best.append(0)
          relative_best.append(0)
          
          base.append(0)
          relative_base.append(0)

          worst.append(0)
          relative_worst.append(0)
      else:
          best.append(statistics.mean(average[:math.ceil(len(average)/2)]))
          relative_best.append(((price - statistics.mean(average[:math.ceil(len(average)/2)])) / price) * 100)
          
          base.append(statistics.mean(average))
          relative_base.append(((price - statistics.mean(average)) / price) * 100)
          
          worst.append(statistics.mean(average[-math.ceil(len(average)/2):]))
          relative_worst.append(((price - statistics.mean(average[-math.ceil(len(average)/2):])) / price) * 100)

    dff['best'] = best
    dff['base'] = base
    dff['worst'] = worst
    
    dff['relative_best'] = relative_best
    dff['relative_base'] = relative_base
    dff['relative_worst'] = relative_worst
    
    dff['price'] = price_list
    
    dictt['calclations'] = dff.to_dict('records')
    
    return HttpResponse(json.dumps(dictt, indent=4, default=str), content_type="application/json")
      # t.replace([np.nan, np.inf, -np.inf], 0, inplace=True)

# @api_view(['POST'])
# def technical_analysis_implied(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request['date']
#     ticker = request['ticker']
#
#     in_date = datetime.strptime(date, "%Y-%m-%d")
#
#     while True:
#         try:
#             # data = data[data['date'] <= in_date]
#             formated_date = str(in_date.date()).split("-")
#             final_date = formated_date[0] + formated_date[1] + formated_date[2]
#             print(final_date)
#             # print(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_stockquotes_{str(final_date)}.csv')
#             df_quote = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_stockquotes_{str(final_date)}.csv')
#             df_stats = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_optionstats_{str(final_date)}.csv')
#             break
#
#         except:
#             in_date = in_date - timedelta(days=1)
#             continue
#     days = [30,60,90,120,150,180,360]
#     high = []
#     low = []
#     percentage = []
#     current_price = df_quote[df_quote["symbol"]==ticker]["close"].iloc[0]
#     api_data = {}
#     print(current_price)
#     api_data = {}
#     dates = []
#     for i in days:
#         iv = df_stats["iv"+str(i)+"mean"].iloc[0]
#         iv_annual = math.sqrt(i/365) * iv
#         high.append(round((1 + iv_annual)*current_price,2))
#         low.append(round((1 - iv_annual)*current_price,2))
#         percentage.append(round(math.sqrt(i/365) * current_price,2))
#         dates.append(in_date + timedelta(days=i))
#     api_data["high"] = high
#     api_data["days"] = days
#     api_data["low"] = low
#     api_data["percentage"] = percentage
#     api_data["date"] = dates
#
#     return HttpResponse(json.dumps(api_data, indent=4, default=str), content_type="application/json")


@api_view(['POST'])
def read_fcff(request):
    res = json.loads(request.body.decode('utf-8'))
    if True:
        request = res['quarter']
        symbol = res['symbol']
        model = res['valuation_model']
        case = res['case']
    
        fcf = {}
        dcfinp = {}
        er = {}
        # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfcalc/'+symbol+'.json', 'r') as f:
        #     dcfinput = json.loads(f.read())
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfcalc")
        file_path = os.path.join(base_path, f"{symbol}.json")
        with open(file_path, 'r') as f:
            dcfinput = json.loads(f.read()) #@danish

        # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/current_stock_price/'+symbol+'.json', 'r') as f:
        #     dcfprice = json.loads(f.read())
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "current_stock_price")
        file_path = os.path.join(base_path, f"{symbol}.json")
        with open(file_path, 'r') as f:
            dcfprice = json.loads(f.read()) #@danish

        if model == 'FCFF' or model == 'fcff' :   
            try:
                # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfoutputbest'+'/'+ symbol+'.json','r') as f:
                #     fcffbest = json.loads(f.read())
                base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfoutputbest")
                file_path = os.path.join(base_path, f"{symbol}.json")
                with open(file_path, 'r') as f:
                    fcffbest = json.loads(f.read()) #@danish
            except:
                # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfoutputbest'+'/'+ symbol+'output.json','r') as f:
                #     fcffbest = json.loads(f.read())
                base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfoutputbest")
                file_path = os.path.join(base_path, f"{symbol}output.json")
                with open(file_path, 'r') as f:
                    fcffbest = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfoutputbase'+'/'+ symbol+'.json','r') as f:
            #         fcffbase = json.loads(f.read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfoutputbase")
            file_path = os.path.join(base_path, f"{symbol}.json")
            with open(file_path, 'r') as f:
                fcffbase = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfoutputworst'+'/'+ symbol+'.json','r') as f:
            #         fcffworst = json.loads(f.read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfoutputworst")
            file_path = os.path.join(base_path, f"{symbol}.json")
            with open(file_path, 'r') as f:
                fcffworst = json.loads(f.read()) #@danish
            
            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/fcff_quarter'+'/'+ symbol+'.json','r') as f:
            #         fcffquarter = json.loads(f.read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "fcff_quarter")
            file_path = os.path.join(base_path, f"{symbol}.json")
            with open(file_path, 'r') as f:
                fcffquarter = json.loads(f.read()) #@danish
                    
            # publish_date = dcfinput['Publish date']
            # publish_dates = {}
            graph_data = {}
            for j in list(fcffquarter.values()):
                date = datetime.strptime(j, '%Y-%m-%d').date()
                q = math.ceil(int(str(date)[5:7])/3)
                # publish_dates[str(date)[:4]+'Q'+str(q)] = j
            
                try:
                    best = fcffbest[str(date)[:4]+'Q'+str(q)]['Estimated value /share (Local Currency)'] 
                    base = fcffbase[str(date)[:4]+'Q'+str(q)]['Estimated value /share (Local Currency)'] 
                    worst = fcffworst[str(date)[:4]+'Q'+str(q)]['Estimated value /share (Local Currency)'] 
                    if best == np.inf or best == -np.inf:
                        base=0
                        best=0
                        worst=0
                    graph_data[j] = {'Best':best, 'Base':base, 'Worst':worst, 'Current_price':dcfprice[str(date)[:4]+'Q'+str(q)]}
                except:
                    continue
        else:   
            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/ermbest'+'/'+ symbol+'.json','r') as f:
            #     fcffbest = json.loads(f.read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "ermbest")
            file_path = os.path.join(base_path, f"{symbol}.json")
            with open(file_path, 'r') as f:
                fcffbest = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/ermbase'+'/'+ symbol+'.json','r') as f:
            #     fcffbase = json.loads(f.read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "ermbase")
            file_path = os.path.join(base_path, f"{symbol}.json")
            with open(file_path, 'r') as f:
                fcffbase = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/ermworst'+'/'+ symbol+'.json','r') as f:
            #     fcffworst = json.loads(f.read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "ermworst")
            file_path = os.path.join(base_path, f"{symbol}.json")
            with open(file_path, 'r') as f:
                fcffworst = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/erm_quarter'+'/'+ symbol+'.json','r') as f:
            #     ermquarter = json.loads(f.read())
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "erm_quarter")
            file_path = os.path.join(base_path, f"{symbol}.json")
            with open(file_path, 'r') as f:
                ermquarter = json.loads(f.read()) #@danish

                    
            # publish_date = dcfinput['Publish date']
            # publish_dates = {}
            graph_data = {}
            for j in list(ermquarter.values()):
                date = datetime.strptime(j, '%Y-%m-%d').date()
                q = math.ceil(int(str(date)[5:7])/3)
                # publish_dates[str(date)[:4]+'Q'+str(q)] = j
            
                try:
                    best = fcffbest[str(date)[:4]+'Q'+str(q)]['Estimated Value/Share (Local Currency)'] 
                    base = fcffbase[str(date)[:4]+'Q'+str(q)]['Estimated Value/Share (Local Currency)'] 
                    worst = fcffworst[str(date)[:4]+'Q'+str(q)]['Estimated Value/Share (Local Currency)'] 
                    if best == np.inf or best == -np.inf:
                        base=0
                        best=0
                        worst=0
                    graph_data[j] = {'Best':best, 'Base':base, 'Worst':worst, 'Current_price':dcfprice[str(date)[:4]+'Q'+str(q)]}
                except:
                    continue
        
            
        if model == 'FCFF' or model == 'fcff' :
            if case == "best":
                try:
                    # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfoutput'+case.lower()+'/'+ symbol+'.json','r') as f:
                    #     fcff = json.loads(f.read())
                    dcf_output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", f"dcfoutput{case.lower()}", f"{symbol}.json")
                    with open(dcf_output_path, 'r') as f:
                        fcff = json.loads(f.read()) #@danish
                except:
                    # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfoutput'+case.lower()+'/'+ symbol+'output.json','r') as f:
                    #     fcff = json.loads(f.read())
                    dcf_output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", f"dcfoutput{case.lower()}", f"{symbol}output.json")
                    with open(dcf_output_path, 'r') as f:
                        fcff = json.loads(f.read()) #@danish
            else:
                # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfoutput'+case.lower()+'/'+ symbol+'.json','r') as f:
                #     fcff = json.loads(f.read())
                dcf_output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", f"dcfoutput{case.lower()}", f"{symbol}.json")
                with open(dcf_output_path, 'r') as f:
                    fcff = json.loads(f.read()) #@danish

            fcf[request] = fcff[request]
            for i in dcfinput:
                try:
                    dcfinp[i] = dcfinput[i][request]
                except:
                    continue
            dcfinp.update(fcf)
            
        else:
            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/erm'+case.lower()+'/'+ symbol+'.json','r') as f:
            #     erm = json.loads(f.read())
            erm_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", f"erm{case.lower()}", f"{symbol}.json")

            with open(erm_path, 'r') as f:
                erm = json.loads(f.read())
            
            er[request] = erm[request]
            for i in dcfinput:
                try:
                    dcfinp[i] = dcfinput[i][request]
                except:
                    continue
            dcfinp.update(er)
            
        dcfinp.update(dcfinp[request])
        if model == 'FCFF'  or model == 'fcff':
            dcfinp["Capitalized Operating Margin"] = (dcfinp["Operating Income (TTM)"] + dcfinp["Capitalized R & D"])/dcfinp["Revenues"][0]
        else:
            dcfinp["Capitalized Operating Margin"] = (dcfinp["Operating Income (TTM)"] + dcfinp["Capitalized R & D"])/dcfinp["revenue"][0]
        
        dcfinp["Valuation Currency"] = dcfinput["Valuation Currency"]
        dcfinp["graph data"] = graph_data
        del dcfinp[request]
        dcfinp["Date"][0] = "Base"
        dcfinp["Local Currency"] = "USD"
        dcfinp["Incorporation company"] = "US"
        return HttpResponse(json.dumps(dcfinp, indent=4, default=str), content_type="application/json")
    # except:
    #     return HttpResponse(json.dumps({"Error":"Data not found"}, indent=4, default=str), content_type="application/json")

# @api_view(['POST'])
# def checklist(request):
#     res = json.loads(request.body.decode('utf-8'))
#     type = res["type"]
#
#     sectors = {}
#     if type == 'sector':
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/checklist/sectorfinal.json', 'r') as f:
#             sector = json.loads(f.read().replace("Fi0cial","Financial"))
#
#         # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/checklist/sector11.json', 'r') as f:
#         #     sector = json.loads(f.read().replace("Fi0cial","Financial"))
#
#         # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/checklist/sec.json', 'r') as f:
#         #     sector1 = json.loads(f.read())
#
#
#     else:
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/checklist/industriesfinal.json', 'r') as f:
#             sector = json.loads(f.read().replace("Fi0cial","Financial"))
#
#         # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/checklist/industries11.json', 'r') as f:
#         #     sector = json.loads(f.read())
#
#         # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/checklist/ind.json', 'r') as f:
#         #     sector1 = json.loads(f.read())
#     # sector.update(sector1)
#
#     return HttpResponse(json.dumps(sector, indent=4, default=str), content_type="application/json")
#
# @api_view(['POST'])
# def checklist_comapny(request):
#     res = json.loads(request.body.decode('utf-8'))
#
#     sec = res["sector"].split(",")
#     ind = res["industries"].split(",")
#     s = {}
#     for i in sec:
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/checklist/sectors/'+ i +'.json', 'r') as f:
#             sector = json.loads(f.read().replace("Fi0cial","Financial"))
#
#
#         final = dict((k, sector[i][k]) for k in ind if k in sector[i])
#         s.update(final)
#     ranking = {}
#     for i in s:
#         ranking.update(s[i])
#     s["ranking_relative_best"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["best"])]
#     s["ranking_relative_base"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["base"])]
#     s["ranking_relative_worst"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["worst"])]
#
#     s["ranking_fcff_best"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["best_fcff"])]
#     s["ranking_fcff_base"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["base_fcff"])]
#     s["ranking_fcff_worst"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["worst_fcff"])]
#
#     s["ranking_erm_best"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["best_erm"])]
#     s["ranking_erm_base"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["base_erm"])]
#     s["ranking_erm_worst"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["worst_erm"])]
#
#     s["ranking_relative_fcff_best"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["best_relative_fcff"])]
#     s["ranking_relative_fcff_base"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["base_relative_fcff"])]
#     s["ranking_relative_fcff_worst"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["worst_relative_fcff"])]
#
#     s["ranking_relative_erm_best"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["best_relative_erm"])]
#     s["ranking_relative_erm_base"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["base_relative_erm"])]
#     s["ranking_relative_erm_worst"] = [k for k, v in sorted(ranking.items(), key=lambda item: item[1]["worst_relative_erm"])]
#
#     return HttpResponse(json.dumps(s, indent=4, default=str), content_type="application/json")
   
@api_view(['POST'])
def industry_report(request):
    request = json.loads(request.body.decode('utf-8'))
    try:
        ind = Industry_report.objects.get(industry_name=request.get("industry"))
        
        ser = Industryreportserializer(ind)
        
        return HttpResponse(json.dumps(ser.data, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({}, indent=4, default=str), content_type="application/json")

@api_view(['POST'])
def get_blog(request):
    request = json.loads(request.body.decode('utf-8'))
    try:
        ind = General_topic.objects.get(chapter_id=str(request.get("id")))
        
        ser = Generaltopicserializer(ind)
        
        return HttpResponse(json.dumps(ser.data, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({"error":"Industry data not found"}, indent=4, default=str), content_type="application/json")

@api_view(['GET'])
def get_all_blog(request):
    try:
        ind = Blog.objects.all()
        
        ser = AllBlogserializer(ind, many=True)
        
        return HttpResponse(json.dumps(ser.data, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({"error":"Error"}, indent=4, default=str), content_type="application/json")

@api_view(['POST'])
def get_blog_by_id(request):
    request = json.loads(request.body.decode('utf-8'))
    try:
        ind = Blog.objects.get(id=str(request.get("id")))
        
        ser = Blogserializer(ind)
        
        return HttpResponse(json.dumps(ser.data, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({"error":"Industry data not found"}, indent=4, default=str), content_type="application/json")

@api_view(['POST'])
def get_macroeconomics(request):
    request = json.loads(request.body.decode('utf-8'))
    try:
        ind = Macroeconomics.objects.get(Macroeconomic_field=str(request.get("field")))
        
        ser = Macroeconomictopicserializer(ind)
        
        return HttpResponse(json.dumps(ser.data, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({"error":"Industry data not found"}, indent=4, default=str), content_type="application/json")


@api_view(['POST'])
def get_quarters(request):
    request = json.loads(request.body.decode('utf-8'))
    symbol = request["symbol"]
    # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/fcff_quarter/'+symbol+'.json', 'r') as f:
    #     dcfinput = json.loads(f.read())
    fcff_quarter_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "fcff_quarter", f"{symbol}.json")
    with open(fcff_quarter_path, 'r') as f:
        dcfinput = json.loads(f.read()) #@danish

    keys = sorted(list(dcfinput.keys()))[::-1]
    return HttpResponse(json.dumps(keys, indent=4, default=str), content_type="application/json")

@api_view(['GET', 'POST'])
def student_version(request):
    request = json.loads(request.body.decode('utf-8'))
    s = request['symbol']
    q = request['quarter']
    curr_date = request['curr_date']  #2022-07-26
    curr_date = str(curr_date.split('-')[0]) +str(curr_date.split('-')[1]) + str(curr_date.split('-')[2])
    #with open('stock_data/media/DCF/dcfcalc/'+s+'.json','r') as f:
    #	aaplinput = json.loads(f.read())
    
    #with open('stock_data/media/DCF/income_state_error/'+s+'.json', 'r') as f:
    #	income = json.loads(f.read())
    #data = pd.read_csv(f'stock_data/media/screener_data/screener_{curr_date}.csv')
    #filling_date1 = {}
    #for i in income:
        #filling_date1[i['calendarYear']+i['period']] = i['fillingDate']
    
    revenue_TTM = request['revenue_TTM']
    book_value_equity = request['book_value_equity']
    exchange_rate = request['exchange_rate']
    book_value_debt = request['book_value_debt']
    interest_expense = request['interest_expense']
    valuation_currency = request['valuation_currency']
    industry = request['industry']
    no_of_shares_outstanding = request['no_of_shares_outstanding']
    current_stock_price = request['current_stock_price'] 
    rfr = request['risk_free_rate']
    unlevered_beta = request['unlevered_beta']
    pre_tax_cod = request['pre_tax_cost_of_debt']
    equity_risk_premium = request['equity_risk_premium']
    average_maturity = request['average_maturity']
    quarter_dict = {}
    mode = request['best_base_worst']
    
    base_year = request['base_year']
    date = [base_year+1]
    for i in range(0,4):
        date.append(1+date[i])


    revenue_growth = []
    revenue_growth.append(request['revenue_year_1'])
    revenue_growth.append(request['revenue_year_2'])
    revenue_growth.append(request['revenue_year_3'])
    revenue_growth.append(request['revenue_year_4'])
    revenue_growth.append(request['revenue_year_5'])

    cost_of_equity = rfr + unlevered_beta * equity_risk_premium
    
    if request['model'] == "fcff" or request['model'] == "FCFF":
        MarketValueofEquity = no_of_shares_outstanding*current_stock_price
        EstimatedMarketValueofDebt = (book_value_debt / ((1+(pre_tax_cod/100)) ** average_maturity)) + (interest_expense * ((1-(1 / (1+(pre_tax_cod/100)) ** (average_maturity))) / (pre_tax_cod/100)))
        cost_of_debt = pre_tax_cod*(1-marginal_tax_rate)
        cost_of_capital = ((cost_of_equity*MarketValueofEquity) / (EstimatedMarketValueofDebt + MarketValueofEquity)) + ((cost_of_debt*EstimatedMarketValueofDebt) / (EstimatedMarketValueofDebt+MarketValueofEquity))
        
        operating_margin = []
        operating_margin.append(request['operating_year_1'])
        operating_margin.append(request['operating_year_2'])
        operating_margin.append(request['operating_year_3'])
        operating_margin.append(request['operating_year_4'])
        operating_margin.append(request['operating_year_5'])
        # operating_terminal = request['operating_terminal']
        capitalized_r_d = 1

        operating_TTM = request['operating_TTM']
        sales_to_capital = request['sales_to_capital']
        cash_marketable = request['cash_marketable']
        cross_holdings_other_non_operating_assets = 0
        minority_interest = request['minority_interest']
        rdYN = request['r&dY/N']
        effective_tax_rate = request['effective_tax_rate']
        marginal_tax_rate = request['marginal_tax_rate']
        if rdYN == 'y':
                print('yes y')
                r_d_expenses = request['amortize_r&d_expenses']
                current_r_d_expenses = request['current_r&d_expenses']
                if r_d_expenses == 1:
                    print("yes")
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/year1_r_d_expenses
                elif r_d_expenses == 2:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/year2_r_d_expenses
                elif r_d_expenses == 3:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/year3_r_d_expenses
                elif r_d_expenses == 4:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    year4_r_d_expenses = request['4_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/(r_d_expenses+year4_r_d_expenses*(r_d_expenses-year4_r_d_expenses))/year4_r_d_expenses
                elif r_d_expenses == 5:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    year4_r_d_expenses = request['4_year_r&d_expense']
                    year5_r_d_expenses = request['5_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/(r_d_expenses+year4_r_d_expenses*(r_d_expenses-year4_r_d_expenses))/(r_d_expenses+year5_r_d_expenses*(r_d_expenses-year5_r_d_expenses))/year5_r_d_expenses
                elif r_d_expenses == 6:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    year4_r_d_expenses = request['4_year_r&d_expense']
                    year5_r_d_expenses = request['5_year_r&d_expense']
                    year6_r_d_expenses = request['6_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/(r_d_expenses+year4_r_d_expenses*(r_d_expenses-year4_r_d_expenses))/(r_d_expenses+year5_r_d_expenses*(r_d_expenses-year5_r_d_expenses))/(r_d_expenses+year6_r_d_expenses*(r_d_expenses-year6_r_d_expenses))/year6_r_d_expenses
                elif r_d_expenses == 7:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    year4_r_d_expenses = request['4_year_r&d_expense']
                    year5_r_d_expenses = request['5_year_r&d_expense']
                    year6_r_d_expenses = request['6_year_r&d_expense']
                    year7_r_d_expenses = request['7_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/(r_d_expenses+year4_r_d_expenses*(r_d_expenses-year4_r_d_expenses))/(r_d_expenses+year5_r_d_expenses*(r_d_expenses-year5_r_d_expenses))/(r_d_expenses+year6_r_d_expenses*(r_d_expenses-year6_r_d_expenses))/(r_d_expenses+year7_r_d_expenses*(r_d_expenses-year7_r_d_expenses))/year7_r_d_expenses
                elif r_d_expenses == 8:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    year4_r_d_expenses = request['4_year_r&d_expense']
                    year5_r_d_expenses = request['5_year_r&d_expense']
                    year6_r_d_expenses = request['6_year_r&d_expense']
                    year7_r_d_expenses = request['7_year_r&d_expense']
                    year8_r_d_expenses = request['8_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/(r_d_expenses+year4_r_d_expenses*(r_d_expenses-year4_r_d_expenses))/(r_d_expenses+year5_r_d_expenses*(r_d_expenses-year5_r_d_expenses))/(r_d_expenses+year6_r_d_expenses*(r_d_expenses-year6_r_d_expenses))/(r_d_expenses+year7_r_d_expenses*(r_d_expenses-year7_r_d_expenses))/(r_d_expenses+year8_r_d_expenses*(r_d_expenses-year8_r_d_expenses))/year8_r_d_expenses
                elif r_d_expenses == 9:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    year4_r_d_expenses = request['4_year_r&d_expense']
                    year5_r_d_expenses = request['5_year_r&d_expense']
                    year6_r_d_expenses = request['6_year_r&d_expense']
                    year7_r_d_expenses = request['7_year_r&d_expense']
                    year8_r_d_expenses = request['8_year_r&d_expense']
                    year9_r_d_expenses = request['9_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/(r_d_expenses+year4_r_d_expenses*(r_d_expenses-year4_r_d_expenses))/(r_d_expenses+year5_r_d_expenses*(r_d_expenses-year5_r_d_expenses))/(r_d_expenses+year6_r_d_expenses*(r_d_expenses-year6_r_d_expenses))/(r_d_expenses+year7_r_d_expenses*(r_d_expenses-year7_r_d_expenses))/(r_d_expenses+year8_r_d_expenses*(r_d_expenses-year8_r_d_expenses))/(r_d_expenses+year9_r_d_expenses*(r_d_expenses-year9_r_d_expenses))/year9_r_d_expenses
                elif r_d_expenses == 10:
                    year1_r_d_expenses = request['1_year_r&d_expense']
                    year2_r_d_expenses = request['2_year_r&d_expense']
                    year3_r_d_expenses = request['3_year_r&d_expense']
                    year4_r_d_expenses = request['4_year_r&d_expense']
                    year5_r_d_expenses = request['5_year_r&d_expense']
                    year6_r_d_expenses = request['6_year_r&d_expense']
                    year7_r_d_expenses = request['7_year_r&d_expense']
                    year8_r_d_expenses = request['8_year_r&d_expense']
                    year9_r_d_expenses = request['9_year_r&d_expense']
                    year10_r_d_expenses = request['10_year_r&d_expense']
                    value_of_research_asset = (current_r_d_expenses+year1_r_d_expenses*(r_d_expenses-year1_r_d_expenses))/(r_d_expenses+year2_r_d_expenses*(r_d_expenses-year2_r_d_expenses))/(r_d_expenses+year3_r_d_expenses*(r_d_expenses-year3_r_d_expenses))/(r_d_expenses+year4_r_d_expenses*(r_d_expenses-year4_r_d_expenses))/(r_d_expenses+year5_r_d_expenses*(r_d_expenses-year5_r_d_expenses))/(r_d_expenses+year6_r_d_expenses*(r_d_expenses-year6_r_d_expenses))/(r_d_expenses+year7_r_d_expenses*(r_d_expenses-year7_r_d_expenses))/(r_d_expenses+year8_r_d_expenses*(r_d_expenses-year8_r_d_expenses))/(r_d_expenses+year9_r_d_expenses*(r_d_expenses-year9_r_d_expenses))/(r_d_expenses+year10_r_d_expenses*(r_d_expenses-year10_r_d_expenses))/year10_r_d_expenses
        else:
                r_d_expenses = 0
                current_r_d_expenses = 0
                year1_r_d_expenses = 0
                year2_r_d_expenses = 0
                year3_r_d_expenses = 0
                year4_r_d_expenses = 0
                year5_r_d_expenses = 0
                value_of_research_asset = 0

        nest = [date, revenue_growth]
            
        df = pd.DataFrame((_ for _ in itertools.zip_longest(*nest)), columns=['Date', 'revenueGrowth'])
        new_row = pd.DataFrame({'Date':int(df.loc[0,'Date'])-1, 'revenueGrowth':np.nan}, index=[0])
        df = pd.concat([new_row,df.loc[:]]).reset_index(drop=True)
        # l = []
        l = [revenue_TTM]
        
        for k in range(2,7):    
            try:  
                l.append(l[-1] * (1 +  (df.iloc[k-1]['revenueGrowth']/100)))
            except:
                break
        
        df['Revenues'] = l

        operatingincome_base = operating_TTM + capitalized_r_d
        operatingmargin_base = (operatingincome_base / revenue_TTM)*100
        operating_growth_list = operating_margin
        operating_growth_list.insert(0, operatingmargin_base)
        df['operatingMargin'] = operating_growth_list

        # df.loc[0,'operating_margin'] = (operating_TTM / (df.loc[0,'Revenues'])) * 100
        # df.loc[0,'netMargin'] = (net_TTM / (df.loc[0,'Revenues'])) * 100

        for j in range(6,11):
            revenuerest = df.iloc[j-1]['revenueGrowth'] + (rfr - df.iloc[5]['revenueGrowth']) / 5
            operatingrest = df.iloc[j-1]['operatingMargin']
            # netrest = df.iloc[j-1]['netMargin'] + (net_terminal - df.iloc[5]['netMargin']) / 5
            revenues = df.iloc[j-1]['Revenues'] * (1 +  (revenuerest/100))
            datesrest = int(int(df.iloc[j-1]['Date']) + 1)
            
            df = pd.concat([df, pd.DataFrame([{'Date':datesrest, 'revenueGrowth':revenuerest, 'operatingMargin':operatingrest, 'Revenues':revenues}])], ignore_index=True)
            
        df['Date'] = df['Date'].astype(int)
        # df = df.append({'Date':'Terminal', 'revenueGrowth':rfr, 'operating_margin':operating_terminal}, ignore_index=True)
        df = pd.concat([df, pd.DataFrame([{'Date':'Terminal', 'revenueGrowth':rfr, 'operatingMargin':df.loc[10,'operatingMargin']}])], ignore_index=True)
        df.loc[11,'Revenues'] = df.iloc[-2]['Revenues'] * (1 +  (df.iloc[-1]['revenueGrowth']/100))
        
        df['OperatingIncome'] = (df['operatingMargin']/100) * df['Revenues']
        # df['netIncome'] = (df['netMargin']/100) * df['Revenues']
        
        df.loc[0,"OperatingIncome"] = operatingincome_base
        # print(df)

        ###### Tax rate
        df1 = pd.DataFrame([])
        
        for j in range(0,10): 
                # try:
            if j > 4:
                effectiverest = df1.iloc[j-1]['effectiveTaxRate'] + (marginal_tax_rate - df1.iloc[4]['effectiveTaxRate']) / 5
                # df1 = df1.append({'Date':int(q[:-2])+j, 'effectiveTaxRate':effectiverest}, ignore_index=True)
                df1 = pd.concat([df1, pd.DataFrame([{'Date':int(base_year)+1+j, 'effectiveTaxRate':effectiverest}])], ignore_index=True)
            else:
                # df1 = df1.append({'Date':int(q[:-2])+j, 'effectiveTaxRate':effective_tax_rate}, ignore_index=True)
                df1 = pd.concat([df1, pd.DataFrame([{'Date':int(base_year)+1+j, 'effectiveTaxRate':effective_tax_rate}])], ignore_index=True)
                
        new_row = pd.DataFrame({'Date':int(df.loc[0,'Date'])-1, 'effectiveTaxRate':effective_tax_rate}, index=[0])
        df1 = pd.concat([new_row,df1.loc[:]]).reset_index(drop=True)
        # df1 = df1.append({'Date':'Terminal', 'effectiveTaxRate':marginal_tax_rate}, ignore_index=True)
        df1 = pd.concat([df1, pd.DataFrame([{'Date':'Terminal', 'effectiveTaxRate':marginal_tax_rate}])], ignore_index=True)
        df['Effective_tax_rate'] = df1['effectiveTaxRate']
        
        
        
        ##### E-bit 1-t
        ebit = []
        for op,ef in zip(df['OperatingIncome'],df['Effective_tax_rate']):
            if op > 0:
                ebit.append(op * (1 - (ef)/100))
            else:
                ebit.append(op)
        df['EBIT(1-t)'] =  ebit
        
        
        
        #####  - Reinvestment
        if df.iloc[1]['Revenues'] > df.iloc[0]['Revenues']:
            df['Reinvestment'] = (df.iloc[1]['Revenues'] - df.iloc[0]['Revenues']) / sales_to_capital
        else:
            df['Reinvestment'] = 0
        
        l1 = []
        
        for r in range(2,len(df)):
            l1.append((df.iloc[r]['Revenues'] - df.iloc[r-1]['Revenues']) / sales_to_capital)
        df.loc[2:, 'Reinvestment'] = l1
        
        
        
        ##### Invested capital
        inv = []
        inv.append(book_value_debt + book_value_equity + value_of_research_asset - cash_marketable)
        for re in df['Reinvestment']:
            try:
                inv.append(inv[-1] + re)
            except:
                continue
        
        df['Invested Capital'] = inv[:-1]
        
        
        
        ##### Cost of capital
        df2 = pd.DataFrame([])
        
        if mode == 'best':
            terminal = df.iloc[-1]['revenueGrowth'] + 4
        elif mode == 'base':
            terminal = df.iloc[-1]['revenueGrowth'] + 4.5
        else:
            terminal = df.iloc[-1]['revenueGrowth'] + 6
        
        # try:
        # df2 = df2.append({'Date':int(q[:-2]), 'cost_to_capital':cost_of_capital}, ignore_index=True)
        df2 = pd.concat([df2, pd.DataFrame([{'Date':int(base_year)+1, 'cost_to_capital':cost_of_capital}])], ignore_index=True)

        
        for j in range(1,10): 
            try:
                if j > 4:
                    cost = df2.iloc[j-1]['cost_to_capital'] + (terminal - df2.iloc[4]['cost_to_capital']) / 5
                    # df2 = df2.append({'Date':int(q[:-2])+j, 'cost_to_capital':cost}, ignore_index=True)
                    df2 = pd.concat([df2, pd.DataFrame([{'Date':int(base_year)+1+j, 'cost_to_capital':cost}])], ignore_index=True)
                else:
                    # df2 = df2.append({'Date':int(q[:-2])+j, 'cost_to_capital':cost_of_capital}, ignore_index=True)
                    df2 = pd.concat([df2, pd.DataFrame([{'Date':int(base_year)+1+j, 'cost_to_capital':cost_of_capital}])], ignore_index=True)
            except:
                print('quarter error')
                continue
            
        # df2 = df2.append({'Date':'Terminal', 'cost_to_capital':terminal}, ignore_index=True)
        df2 = pd.concat([df2, pd.DataFrame([{'Date':'Terminal', 'cost_to_capital':terminal}])], ignore_index=True)
        new_row = pd.DataFrame({'Date':int(df2.loc[0,'Date'])-1, 'cost_to_capital':np.nan}, index=[0])
        df2 = pd.concat([new_row,df2.loc[:]]).reset_index(drop=True)
        
        df['cost_to_capital'] = df2['cost_to_capital']
        
        
        
        ##### ROIC
        df['ROIC'] = (df['EBIT(1-t)'] / df['Invested Capital']) * 100
        
        if mode == 'best':
            df.loc[11,'ROIC'] = df.iloc[-1]['cost_to_capital']+5
        elif mode == 'base':
            df.loc[11,'ROIC'] = df.iloc[-1]['cost_to_capital']+2.5
        else:
            df.loc[11,'ROIC'] = df.iloc[-1]['cost_to_capital']
            
        
        
        ##### Reinvestment terminal
        if df.iloc[-1]['revenueGrowth'] > 0:
            df.loc[11,'Reinvestment'] = (df.iloc[-1]['revenueGrowth'] / df.iloc[-1]['ROIC']) * df.iloc[-1]['EBIT(1-t)']
        else:
            df.loc[11,'Reinvestment'] = 0
            
            
            
        ##### FCFF
        df['FCFF'] = df['EBIT(1-t)'] - df['Reinvestment']
            
            
            
        ##### Cumulated discount factor
        cum = []
        cum.append(1 / (1 + (df.loc[1,'cost_to_capital']/100)))
        for coc in df['cost_to_capital'][2:11]:
            try:
                cum.append(cum[-1] * (1 / (1 + (coc/100))))
            except:
                continue
        cum.append(np.nan)
        cum.insert(0,np.nan)
        df['Cumulated discount factor'] = cum
        
        
        
        ##### PV FCFF
        df['PV FCFF'] = df['FCFF'] * df['Cumulated discount factor']
        
        single_dict = {}
        single_dict['Terminal cash flow'] = df.iloc[-1]['FCFF']
        single_dict['Terminal cost of capital'] = df2.iloc[-1]['cost_to_capital']
        
        single_dict['Terminal value'] = single_dict['Terminal cash flow'] / ((single_dict['Terminal cost of capital']/100) - (df.iloc[-1]['revenueGrowth']/100))
        single_dict['PV(Terminal value)'] = single_dict['Terminal value'] * df.iloc[-2]['Cumulated discount factor']
        single_dict['PV (CF over next 10 years)'] = sum(df['PV FCFF'][1:11])
        single_dict['Sum of PV'] = single_dict['PV(Terminal value)'] + single_dict['PV (CF over next 10 years)']
        single_dict['Value of operating assets'] = single_dict['Sum of PV']
        single_dict['Debt']  = book_value_debt  
        single_dict['Minority Interests'] = minority_interest
        single_dict['Cash Marketable'] = cash_marketable
        single_dict['Non-operating assets'] = 0
        single_dict['Value of equity'] = single_dict['Value of operating assets'] - single_dict['Debt'] - single_dict['Minority Interests'] + single_dict['Cash Marketable'] + single_dict['Non-operating assets']
        single_dict['Value of equity in common stock'] = single_dict['Value of equity']
        single_dict['Number of shares'] = no_of_shares_outstanding
        single_dict['Estimated value /share'] = single_dict['Value of equity in common stock'] / single_dict['Number of shares']
        single_dict['Cross Holdings & Other Non-Operating Assets'] = 0
        
        
        ##### exchange rate
        single_dict['Estimated value /share (Local Currency)'] = single_dict['Estimated value /share'] / exchange_rate

        # date = filling_date1[q]
        
        single_dict['Current price'] = current_stock_price
        single_dict['Valuation'] = abs(((single_dict['Current price'] - single_dict['Estimated value /share (Local Currency)']) / single_dict['Current price'])*100)
        
        ##### Price target (USD)
        price = []
        price.append(single_dict['Estimated value /share'])
        for r in range(0,11):
            try:
                price.append(price[-1] * (1 + (cost_of_equity/100)))
            except:
                continue
        df['Price Target USD'] = price
        
        
        
        ##### Price target (Local Currency)
        pricelocal = []
        pricelocal.append(single_dict['Estimated value /share (Local Currency)'])
        for r in range(0,11):
            try:
                pricelocal.append(pricelocal[-1] * (1 + (cost_of_equity/100)))
            except:
                continue
        
        df['Price Target Local'] = pricelocal
        df = df.fillna(0)
        df_test = df

        dictt = df_test.to_dict('list')
        dictt.update(single_dict)
        
        quarter_dict[str(int(base_year)+1)] = dictt
        d1 = str(quarter_dict)
            # print(d1[7600:])
        d1 = d1.replace("'", '"')
        d1 = d1.replace("nan","0")
        d1 = d1.replace("None","0")
        d1 = d1.replace("inf","0")

    else:
        net_margin = []
        net_margin.append(request['net_year_1'])
        net_margin.append(request['net_year_2'])
        net_margin.append(request['net_year_3'])
        net_margin.append(request['net_year_4'])
        net_margin.append(request['net_year_5'])

        net_TTM = request['net_TTM']
        eps_ttm = request['eps_ttm']
        Dividends_shareTTM = request['Dividends/shareTTM']
        payout = request['current_payout']
        predicted_payout = request['predicted_payout_ratio_y5']
        roe = request['roe']

        nest = [date, revenue_growth]
            
        df = pd.DataFrame((_ for _ in itertools.zip_longest(*nest)), columns=['Date', 'revenueGrowth'])
        new_row = pd.DataFrame({'Date':int(df.loc[0,'Date'])-1, 'revenueGrowth':np.nan}, index=[0])
        df = pd.concat([new_row,df.loc[:]]).reset_index(drop=True)
        # l = []
        l = [revenue_TTM]
        
        for k in range(2,7):    
            try:  
                l.append(l[-1] * (1 +  (df.iloc[k-1]['revenueGrowth']/100)))
            except:
                break
        
        df['Revenues'] = l

        netincome_base = net_TTM
        netmargin_base = (netincome_base / revenue_TTM)*100
        net_growth_list = net_margin
        net_growth_list.insert(0, netmargin_base)
        df['netMargin'] = net_growth_list

        # df.loc[0,'operating_margin'] = (operating_TTM / (df.loc[0,'Revenues'])) * 100
        # df.loc[0,'netMargin'] = (net_TTM / (df.loc[0,'Revenues'])) * 100

        for j in range(6,11):
            revenuerest = df.iloc[j-1]['revenueGrowth'] + (rfr - df.iloc[5]['revenueGrowth']) / 5
            netrest = df.iloc[j-1]['netMargin']
            # netrest = df.iloc[j-1]['netMargin'] + (net_terminal - df.iloc[5]['netMargin']) / 5
            revenues = df.iloc[j-1]['Revenues'] * (1 +  (revenuerest/100))
            datesrest = int(int(df.iloc[j-1]['Date']) + 1)
            
            df = pd.concat([df, pd.DataFrame([{'Date':datesrest, 'revenueGrowth':revenuerest, 'netMargin':netrest, 'Revenues':revenues}])], ignore_index=True)
            
        df['Date'] = df['Date'].astype(int)
        df = pd.concat([df, pd.DataFrame([{'Date':'Terminal', 'revenueGrowth':rfr, 'netMargin':df.loc[10,'netMargin']}])], ignore_index=True)
        df.loc[11,'Revenues'] = df.iloc[-2]['Revenues'] * (1 +  (df.iloc[-1]['revenueGrowth']/100))
        
        df['netIncome'] = (df['netMargin']/100) * df['Revenues']
        # df['netIncome'] = (df['netMargin']/100) * df['Revenues']
        
        df.loc[0,"netIncome"] = netincome_base

        ##### Net Income Growth
        netgrowth = []
        # df['netGrowth'] = np.nan
        for r in range(1,12):
            try:
                netgrowth.append(((df.iloc[r]['netIncome'] - df.iloc[r-1]['netIncome']) / abs(df.iloc[r-1]['netIncome'])) * 100)
            except:
                continue
        df.loc[1:,'netGrowth'] = netgrowth
        
        
        #### Dividend Payout Ratio
        
        terminal_year = (1 - (df.iloc[-1]['netGrowth']/100) / (roe/100)) * 100
        df1 = pd.DataFrame({'Date':(int(base_year)+1)-1, 'payoutRatio':payout}, index=[0])
        print(df1)
        if payout < 0:
        #   df1 = df1.append({'Date':q[:-2], 'payoutRatio':predicted_payout}, ignore_index=True)
            df1 = pd.concat([df1, pd.DataFrame([{'Date':int(base_year)+1, 'payoutRatio':predicted_payout}])], ignore_index=True)
        else:
            pay = df1.iloc[0]['payoutRatio'] + (predicted_payout - df1.iloc[0]['payoutRatio']) / 5
        #   df1 = df1.append({'Date':q[:-2], 'payoutRatio':pay}, ignore_index=True)
            df1 = pd.concat([df1, pd.DataFrame([{'Date':int(base_year)+1, 'payoutRatio':pay}])], ignore_index=True)
        for r in range(2,5):
            if df1.iloc[0]['payoutRatio'] > 0:
                pay1 = df1.iloc[r-1]['payoutRatio'] + (predicted_payout - df1.iloc[0]['payoutRatio']) / 5
            else:
                pay1 = df1.iloc[r-1]['payoutRatio'] + (predicted_payout - df1.iloc[1]['payoutRatio']) / 5
            dates = int(int(df1.iloc[r-1]['Date']) + 1)
            #   df1 = df1.append({'Date':dates, 'payoutRatio':pay1}, ignore_index=True)
            df1 = pd.concat([df1, pd.DataFrame([{'Date':dates, 'payoutRatio':pay1}])], ignore_index=True)
        
        # df1 = df1.append({'Date':int(q[:-2])+4, 'payoutRatio':predicted_payout}, ignore_index=True)
        df1 = pd.concat([df1, pd.DataFrame([{'Date':(int(base_year)+1)+4, 'payoutRatio':predicted_payout}])], ignore_index=True)
        for r in range(6,11):
            pay1 = df1.iloc[r-1]['payoutRatio'] + (terminal_year - df1.iloc[5]['payoutRatio']) / 5
            dates = int(int(df1.iloc[r-1]['Date']) + 1)
            #   df1 = df1.append({'Date':dates, 'payoutRatio':pay1}, ignore_index=True)
            df1 = pd.concat([df1, pd.DataFrame([{'Date':dates, 'payoutRatio':pay1}])], ignore_index=True)
        
        # df1 = df1.append({'Date':'Terminal', 'payoutRatio':terminal_year}, ignore_index=True)
        df1 = pd.concat([df1, pd.DataFrame([{'Date':'Terminal', 'payoutRatio':terminal_year}])], ignore_index=True)

        df['payoutRatio'] = df1['payoutRatio']
        # print(df1)
        # try:
        equity = book_value_equity
        cost_of_equity = cost_of_equity
        return_of_equity = (net_TTM / book_value_equity) 
        payout_ratio = payout
        # except:
            # continue
        dividendpaid = df.iloc[1]['netIncome']*(df.iloc[1]['payoutRatio']/100)
        
        dictt = {'Date':[str((int(base_year)+1)-1), int(base_year)+1], 'revenueGrowth':[np.nan, df.iloc[1]['revenueGrowth']], 'revenue':[df.iloc[0]['Revenues'], df.iloc[1]['Revenues']],
            'netMargin':[df.iloc[0]['netMargin'],df.iloc[1]['netMargin']], 'netIncome':[df.iloc[0]['netIncome'], df.iloc[1]['netIncome']],
            'netGrowth':[df.iloc[0]['netGrowth'],df.iloc[1]['netGrowth']], 'bvEquity':[np.nan,equity], 'costOfEquity':[np.nan,cost_of_equity], 'returnOnEquity':[return_of_equity,
            df.iloc[1]['netIncome']/equity], 'dividendpayout':[payout_ratio, df.iloc[1]['payoutRatio']], 'dividendPaid':[np.nan,df.iloc[1]['netIncome']*(df.iloc[1]['payoutRatio']/100)],
            'retainedEarning':[np.nan, df.iloc[1]['netIncome'] - dividendpaid]}

        df2 = pd.DataFrame(dictt)
        df2['equityCost'] = df2['bvEquity'] * (df2['costOfEquity']/100)
        df2['excessEquity'] = df2['netIncome'] - df2['equityCost']
        df2['cumulatedDiscount'] = 1 + (df2['costOfEquity']/100)
        df2['presentValue'] = df2['excessEquity'] / df2['cumulatedDiscount']
        
        # if int(base_year)+1 == 'Q1':
        #     d12 = 3/4
        # elif q[-2:] == 'Q2':
        #     d12 = 2/4
        # elif q[-2:] == 'Q3':
        #     d12 = 1/4
        # else:
        #     d12 = 1
        
        for r in range(2,12):

            bvEquity = df2.iloc[r-1]['bvEquity'] + df2.iloc[r-1]['retainedEarning']
        
            costOfEquity = df2.iloc[r-1]['costOfEquity']
            returnOnEquity = df.iloc[r]['netIncome'] / bvEquity
            dividendpayout = df.iloc[r]['payoutRatio']
            dividendPaid = df.iloc[r]['netIncome'] * (dividendpayout/100)
            retainedEarning = df.iloc[r]['netIncome'] - dividendPaid
            equityCost = bvEquity * (costOfEquity/100)
            excessEquity = df.iloc[r]['netIncome'] - equityCost
            cumulatedDiscount = (1 + (costOfEquity/100) ) * df2.iloc[r-1]['cumulatedDiscount']
            presentValue = excessEquity / cumulatedDiscount
        
        #   df2 = df2.append({'Date':dates, 'revenueGrowth':df.iloc[r]['revenueGrowth'], 'revenue':df.iloc[r]['Revenues'], 'netMargin':df.iloc[r]['netMargin'], 
        #                     'netIncome':df.iloc[r]['netIncome'], 'netGrowth':df.iloc[r]['netGrowth'], 'bvEquity':bvEquity, 'costOfEquity':costOfEquity, 'returnOnEquity':returnOnEquity,
        #                     'dividendpayout':dividendpayout, 'dividendPaid':dividendPaid, 'retainedEarning':retainedEarning, 'equityCost':equityCost, 'excessEquity':excessEquity,
        #                     'cumulatedDiscount':cumulatedDiscount, 'presentValue':presentValue}, ignore_index=True)
        
            df2 = pd.concat([df2, pd.DataFrame([{'Date':dates, 'revenueGrowth':df.iloc[r]['revenueGrowth'], 'revenue':df.iloc[r]['Revenues'], 'netMargin':df.iloc[r]['netMargin'], 
                                'netIncome':df.iloc[r]['netIncome'], 'netGrowth':df.iloc[r]['netGrowth'], 'bvEquity':bvEquity, 'costOfEquity':costOfEquity, 'returnOnEquity':returnOnEquity,
                                'dividendpayout':dividendpayout, 'dividendPaid':dividendPaid, 'retainedEarning':retainedEarning, 'equityCost':equityCost, 'excessEquity':excessEquity,
                                'cumulatedDiscount':cumulatedDiscount, 'presentValue':presentValue}])], ignore_index=True)

        single_dict = {}
        single_dict['roe'] = roe
        single_dict['Equity Invested'] = df2.iloc[1]['bvEquity']
        single_dict['PV of Equity Excess Return'] = sum(df2.iloc[1:11]['presentValue'])
        single_dict['Terminal  Value of Excess Equity Return'] = (df2.iloc[-1]['excessEquity'] / ((df2.iloc[-1]['costOfEquity']/100) - (df2.iloc[-1]['revenueGrowth']/100))) / df2.iloc[-2]['cumulatedDiscount']
        single_dict['Payout Value of Equity'] = single_dict['Equity Invested'] + single_dict['PV of Equity Excess Return'] + single_dict['Terminal  Value of Excess Equity Return']
        single_dict['Payout Number of shares'] = no_of_shares_outstanding
        single_dict['Payout Estimated Value/Share'] = single_dict['Payout Value of Equity'] / single_dict['Payout Number of shares']
        single_dict['Payout Current price'] = current_stock_price
        single_dict['Payout Estimated Value/Share (Local Currency)'] = single_dict['Payout Estimated Value/Share'] / exchange_rate
        single_dict['Payout Valuation'] = abs((single_dict['Payout Current price'] - single_dict['Payout Estimated Value/Share (Local Currency)']) / single_dict['Payout Current price']) * 100
        single_dict['current_payout'] = payout
        single_dict['eps_ttm'] = eps_ttm
        #### Price target (USD)
        price_payout = []
        
        price_payout.append(single_dict['Payout Estimated Value/Share'])
        for r in range(0,11):
            try:
                price_payout.append(price_payout[-1] * (1 + (cost_of_equity/100)))
            except:
                continue
        
        df2['Payout price_payout Target USD'] = price_payout
        
        
        
        #### Price target (Local Currency)
        pricelocalpayout = []
        pricelocalpayout.append(single_dict['Payout Estimated Value/Share (Local Currency)'])
        for r in range(0,11):
            try:
                pricelocalpayout.append(pricelocalpayout[-1] * (1 + (cost_of_equity/100)))
            except:
                continue
            
        df2['Payout Price Target Local'] = pricelocalpayout

        df2 = df2.fillna(0)
        df_test = df2

        dictt = df_test.to_dict('list')
        dictt.update(single_dict)
        
        quarter_dict[str(int(base_year)+1)] = dictt
        d1 = str(quarter_dict)
            # print(d1[7600:])
        d1 = d1.replace("'", '"')
        d1 = d1.replace("nan","0")
        d1 = d1.replace("None","0")
        d1 = d1.replace("inf","0")
    # print(d1)
    jsn = json.loads(d1.replace("-inf","0"))

    return HttpResponse(json.dumps(jsn, indent=4,default=str),content_type = "application/json")


from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from django.http.response import HttpResponse
import pandas as pd
import numpy as np
import itertools
import math

from datetime import datetime, timedelta

# @api_view(['GET', 'POST'])
# def pro_version(request):
#     request = json.loads(request.body.decode('utf-8'))
#     s = request['symbol']
#     q = request['quarter']
#     curr_date = request['curr_date']  #2022-07-26
#     curr_date = str(curr_date.split('-')[0]) +str(curr_date.split('-')[1]) + str(curr_date.split('-')[2])
#     version = request['version']
#     # with open('D:/apis/mysite/dcfcalc/'+s+'.json','r') as f:
#     #     aaplinput = json.loads(f.read())
#
#     # with open('D:/apis/mysite/income_state_error/'+s+'.json', 'r') as f:
#     #     income = json.loads(f.read())
#
#     if version == 1:
#         with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/dcfcalc/'+s+'.json','r') as f:
#             aaplinput = json.loads(f.read())
#
#         with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/income_state/'+s+'.json', 'r') as f:
#             income = json.loads(f.read())
#     else:
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/wall_street_0_new/dcfcalc/'+s+'.json','r') as f:
#             aaplinput = json.loads(f.read())
#
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/wall_street_0_new/income_state_error/'+s+'.json', 'r') as f:
#             income = json.loads(f.read())
#
#     data = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv')
#     # data = pd.read_csv('profile_bulk.csv')
#     # currency_check = aaplinput['Currency check']
#     filling_date1 = aaplinput['Filling date']
#
#     if request.get("flag", False):
#         input_data = {}
#         dates = filling_date1[q]
#         input_data['symbol'] = s
#         input_data['quarter'] = q
#         # input_data['sector'] = data[data['Symbol']==s]['sector'].values[0]
#         # input_data['industry'] = data[data['Symbol']==s]['industry'].values[0]
#         # input_data['country'] = data[data['Symbol']==s]['country'].values[0]
#         input_data['sector'] = data[data['symbol']==s]['sector'].values[0]
#         input_data['industry'] = data[data['symbol']==s]['industry'].values[0]
#         input_data['country'] = data[data['symbol']==s]['country'].values[0]
#         input_data['interest_expense'] = aaplinput['Interest Expense'][q]
#         input_data['eps_ttm'] = aaplinput['Current Earnings per share'][q]
#         input_data['Dividends_shareTTM'] = aaplinput['Current Dividends per share'][q]
#         input_data['r&dY/N'] = aaplinput['RnD yes/no'][q]
#
#         if input_data['r&dY/N'] != "NO":
#             input_data['current_year_r&d_expense'] = aaplinput['Current year R&D expense'][q]
#         input_data['levered_beta'] = aaplinput['Levered Beta'][q]
#         input_data['pre_tax_cost_of_debt'] = aaplinput['Pre-tax Cost of Debt'][q]
#         input_data['equity_risk_premium'] = aaplinput['Equity Risk Premium'][dates]
#         input_data['average_maturity'] = aaplinput['Average Maturity'][q]
#         input_data['publish_date'] = filling_date1[q]
#         input_data['revenue_growth_best'] = list(aaplinput['Revenue Best'][q].values())
#         input_data['operating_margin_best'] = list(aaplinput['Operating Best'][q].values())
#         input_data['net_margin_best'] = list(aaplinput['Net Best'][q].values())
#         input_data['revenue_growth_base'] = list(aaplinput['Revenue Base'][q].values())
#         input_data['operating_margin_base'] = list(aaplinput['Operating Base'][q].values())
#         input_data['net_margin_base'] = list(aaplinput['Net Base'][q].values())
#         input_data['revenue_growth_worst'] = list(aaplinput['Revenue Worst'][q].values())
#         input_data['operating_margin_worst'] = list(aaplinput['Operating Worst'][q].values())
#         input_data['net_margin_worst'] = list(aaplinput['Net Worst'][q].values())
#         input_data['sales_to_capital'] = aaplinput['Predicted Sales to Capital'][q]
#         input_data['operating_terminal_best'] = aaplinput['Operating Best'][q].pop('Terminal')
#         input_data['net_terminal_best'] = aaplinput['Net Best'][q].pop('Terminal')
#         input_data['operating_terminal_base'] = aaplinput['Operating Base'][q].pop('Terminal')
#         input_data['net_terminal_base'] = aaplinput['Net Base'][q].pop('Terminal')
#         input_data['operating_terminal_worst'] = aaplinput['Operating Worst'][q].pop('Terminal')
#         input_data['net_terminal_worst'] = aaplinput['Net Worst'][q].pop('Terminal')
#         input_data['date'] = list(aaplinput['Revenue Best'][q].keys())
#         input_data['rfr'] = aaplinput['Riskfree Rate %'][q]
#         input_data['effective_tax_rate'] = aaplinput['Effective Tax Rate %'][q]
#         input_data['marginal_tax_rate'] = aaplinput['Marginal Tax Rate %']
#         input_data['book_value_debt'] = aaplinput['Book Value of Debt'][q]
#         input_data['book_value_equity'] = aaplinput['Book Value of Equity'][q]
#         # input_data['book_Value__equity_Previous_Year_same_quarter'] = aaplinput['Book Value of Equity(Previous Year same quarter'][q]
#         input_data['cash_marketable'] = aaplinput['Cash and Marketable Securities'][q]
#         input_data['minority_interest'] = aaplinput['Minority Interests'][q]
#         input_data['no_of_shares_outstanding'] = aaplinput['No. of Shares Outstanding'][q]
#         input_data['current_stock_price'] = aaplinput['Current Stock Price'][dates]
#         input_data['current_payout'] = aaplinput['Calculated Payout'][q]
#         input_data['predicted_payout'] = aaplinput['predicted Payout Ratio Y5'][q]
#         input_data['valuation_currency'] = aaplinput['Valuation Currency']
#         input_data['net_TTM'] = aaplinput['Net Income (TTM)'][q]
#         input_data['revenue_TTM'] = aaplinput['Revenue TTM'][q]
#         input_data['Operating_TTM'] = aaplinput['Operating Income (TTM)'][q]
#         cost_of_capital = aaplinput['Cost Of Capital'][q]
#
#         try:
#             input_data['operating_last_10k'] = aaplinput['Operating Income(last 10k)'][str(int(q[:-2])-1)+'Q4']
#         except:
#             input_data['operating_last_10k'] = 0
#         try:
#             input_data['revenue_last_10k'] = aaplinput['Last 10K Revenue'][str(int(q[:-2])-1)+'Q4']
#         except:
#             input_data['revenue_last_10k'] = 0
#         try:
#             input_data['net_last_10k'] = aaplinput['Last 10K Net Income'][str(int(q[:-2])-1)+'Q4']
#         except:
#             input_data['net_last_10k'] = 0
#
#         if input_data['valuation_currency']  != 'USD':
#             input_data['exchange_rate'] = aaplinput['Exchange rate'][dates]
#         else:
#             input_data['exchange_rate'] = aaplinput['Exchange rate']
#
#         industry = input_data['industry']
#
#         # with open('D:/apis/mysite/roe_with_us (1).json','r') as f:
#         #     roeinputusd = json.loads(f.read())
#
#         # with open('D:/apis/mysite/roe_without_us.json','r') as f:
#         #     roeinputnonusd = json.loads(f.read())
#
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/roe_with_us.json','r') as f:
#             roeinputusd = json.loads(f.read())
#
#         with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/roe_without_us.json','r') as f:
#             roeinputnonusd = json.loads(f.read())
#
#         if input_data['valuation_currency'] == 'USD':
#             if list(roeinputusd[industry].keys())[0] == '0.0':
#                 key='90.0'
#                 key2='50.0'
#             else:
#                 key='90'
#                 key2='50'
#
#             roe = roeinputusd[industry][key2]
#         else:
#             if list(roeinputnonusd[industry].keys())[0] == '0.0':
#                 key='90.0'
#                 key2='50.0'
#             else:
#                 key='90'
#                 key2='50'
#
#             roe = roeinputnonusd[industry][key2]
#
#         input_data['roe'] = roe
#
#         return HttpResponse(json.dumps(input_data, indent=4,default=str),content_type = "application/json")
#
#     else:
#         symbol = request['symbol']
#         country = data[data['symbol'] == symbol]['country'].values[0]
#         revenue_TTM = request['revenue_TTM']
#         book_value_equity = request['book_value_equity']
#         exchange_rate = request['exchange_rate']
#         book_value_debt = request['book_value_debt']
#         interest_expense = request['interest_expense']
#         valuation_currency = request['valuation_currency']
#         industry = request['industry']
#         no_of_shares_outstanding = request['no_of_shares_outstanding']
#         current_stock_price = request['current_stock_price']
#         rfr = request['risk_free_rate']
#         unlevered_beta = float(request['unlevered_beta'])
#         pre_tax_cod = float(request['pre_tax_cost_of_debt'])
#         equity_risk_premium = float(request['equity_risk_premium'])
#         average_maturity = float(request['average_maturity'])
#         quarter_dict = {}
#         mode = request['best_base_worst']
#         marginal_tax_rate = request['marginal_tax_rate']
#         quarter = request['quarter']
#         filling_date = request['publish_date']
#         base_year = request['base_year']
#         date = [base_year+1]
#         for i in range(0,4):
#             date.append(1+date[i])
#
#         # with open('currency_check_api/'+symbol+'.json', 'r') as f:
#         #     currency_check = json.loads(f.read())
#         with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/currency_check_api/'+s+'.json','r') as f:
#             currency_check = json.loads(f.read())
#
#         cur = currency_check[0]['currency']
#         # with open('exchange_rates/'+cur+'.json','r') as f:
#         #     ex = json.loads(f.read())
#         with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/exchange_rates/'+cur+'.json','r') as f:
#             ex = json.loads(f.read())
#
#         exg_rate = {}
#         exg_rate1 = {}
#         for m in ex['historical']:
#             exg_rate[m['date']] = m['adjClose']
#
#         dates = datetime.strptime(filling_date, '%Y-%m-%d').date()
#
#         q1 = math.ceil(int(str(dates)[5:7])/3)
#
#         while True:
#             if math.ceil(int(str(dates)[5:7])/3) != q1:
#                 exg_rate1[filling_date] = 0
#                 break
#             if str(dates) in list(exg_rate.keys()):
#                 exg_rate1[filling_date] = exg_rate[str(dates)]
#                 break
#             dates = dates - timedelta(days=1)
#
#         revenue_growth = []
#         revenue_growth.append(request['revenue_year_1'])
#         revenue_growth.append(request['revenue_year_2'])
#         revenue_growth.append(request['revenue_year_3'])
#         revenue_growth.append(request['revenue_year_4'])
#         revenue_growth.append(request['revenue_year_5'])
#
#         if country == 'US':
#             # with open('D:/apis/mysite/beta_with_us.json','r') as f:
#             #     beta_with_us = json.loads(f.read())
#             with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/beta_with_us.json','r') as f:
#                 beta_with_us = json.loads(f.read())
#         else:
#             # with open('D:/apis/mysite/beta_without_us.json','r') as f:
#             #     beta_with_us = json.loads(f.read())
#             with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/percentiles/revenue_sales/beta_without_us.json','r') as f:
#                 beta_with_us = json.loads(f.read())
#
#
#         EstimatedMarketValueofDebt = (book_value_debt / ((1+(pre_tax_cod/100)) ** average_maturity)) + (interest_expense * ((1-(1 / (1+(pre_tax_cod/100)) ** (average_maturity))) / (pre_tax_cod/100)))
#         # date = filling_date1
#
#         if valuation_currency == 'USD':
#             MarketValueofEquity = no_of_shares_outstanding*current_stock_price*1
#         else:
#             MarketValueofEquity = no_of_shares_outstanding*current_stock_price
#
#         if round(aaplinput['Levered Beta'][quarter],2) == unlevered_beta:
#             CalculatedBeta = unlevered_beta * (1+((1-(marginal_tax_rate)/100)*(EstimatedMarketValueofDebt/MarketValueofEquity)))
#             if CalculatedBeta > beta_with_us[industry]['65']:
#                     Levered_Beta = beta_with_us[industry]['65']
#
#             elif CalculatedBeta < beta_with_us[industry]['50']:
#                     Levered_Beta = beta_with_us[industry]['50']
#
#             else:
#                     Levered_Beta = CalculatedBeta
#         else:
#             Levered_Beta = unlevered_beta * (1+((1-(marginal_tax_rate)/100)*(EstimatedMarketValueofDebt/MarketValueofEquity)))
#
#         CostOfEquity = rfr + (Levered_Beta*equity_risk_premium)
#
#         if request['model'] == "fcff" or request['model'] == "FCFF":
#             operating_margin = []
#             operating_margin.append(request['operating_year_1'])
#             operating_margin.append(request['operating_year_2'])
#             operating_margin.append(request['operating_year_3'])
#             operating_margin.append(request['operating_year_4'])
#             operating_margin.append(request['operating_year_5'])
#             # operating_terminal = request['operating_terminal']
#             capitalized_r_d = aaplinput['Capitalized R & D'][q]
#
#             operating_TTM = request['operating_TTM']
#             sales_to_capital = request['sales_to_capital']
#             cash_marketable = request['cash_marketable']
#             cross_holdings_other_non_operating_assets = 0
#             minority_interest = request['minority_interest']
#             rdYN = request['r&dY/N']
#             effective_tax_rate = request['effective_tax_rate']
#
#
#             # pd.set_option('display.max_columns', 15)
#
#             # df = pd.DataFrame(data)
#             nest = [date, revenue_growth]
#
#             df = pd.DataFrame((_ for _ in itertools.zip_longest(*nest)), columns=['Date', 'revenueGrowth'])
#             new_row = pd.DataFrame({'Date':int(df.loc[0,'Date'])-1, 'revenueGrowth':np.nan}, index=[0])
#             df = pd.concat([new_row,df.loc[:]]).reset_index(drop=True)
#             # l = []
#             l = [revenue_TTM]
#
#             for k in range(2,7):
#                 try:
#                     l.append(l[-1] * (1 +  (df.iloc[k-1]['revenueGrowth']/100)))
#                 except:
#                     break
#
#             df['Revenues'] = l
#             operatingincome_base = operating_TTM + capitalized_r_d
#             operatingmargin_base = (operatingincome_base / revenue_TTM)*100
#             operating_growth_list = operating_margin
#             operating_growth_list.insert(0, operatingmargin_base)
#             df['operatingMargin'] = operating_growth_list
#
#             # df.loc[0,'operating_margin'] = (operating_TTM / (df.loc[0,'Revenues'])) * 100
#             # df.loc[0,'netMargin'] = (net_TTM / (df.loc[0,'Revenues'])) * 100
#
#             for j in range(6,11):
#                 revenuerest = df.iloc[j-1]['revenueGrowth'] + (rfr - df.iloc[5]['revenueGrowth']) / 5
#                 operatingrest = df.iloc[j-1]['operatingMargin']
#                 # netrest = df.iloc[j-1]['netMargin'] + (net_terminal - df.iloc[5]['netMargin']) / 5
#                 revenues = df.iloc[j-1]['Revenues'] * (1 +  (revenuerest/100))
#                 datesrest = int(int(df.iloc[j-1]['Date']) + 1)
#
#                 df = pd.concat([df, pd.DataFrame([{'Date':datesrest, 'revenueGrowth':revenuerest, 'operatingMargin':operatingrest, 'Revenues':revenues}])], ignore_index=True)
#
#             df['Date'] = df['Date'].astype(int)
#             df = pd.concat([df, pd.DataFrame([{'Date':'Terminal', 'revenueGrowth':rfr, 'operatingMargin':df.loc[10,'operatingMargin']}])], ignore_index=True)
#             # df = df.append({'Date':'Terminal', 'revenueGrowth':rfr, 'operating_margin':df.loc[10,'operatingMargin']}, ignore_index=True)
#             # df = pd.concat([df, pd.DataFrame([{'Date':'Terminal', 'revenueGrowth':rfr, 'operatingMargin':df.loc[10,'operatingMargin']}])], ignore_index=True)
#             df.loc[11,'Revenues'] = df.iloc[-2]['Revenues'] * (1 +  (df.iloc[-1]['revenueGrowth']/100))
#
#             df['OperatingIncome'] = (df['operatingMargin']/100) * df['Revenues']
#             # df['netIncome'] = (df['netMargin']/100) * df['Revenues']
#             df.loc[0,"OperatingIncome"] = operatingincome_base
#
#             # print(df)
#
#             ###### Tax rate
#             df1 = pd.DataFrame([])
#
#             for j in range(0,10):
#                     # try:
#                 if j > 4:
#                     effectiverest = df1.iloc[j-1]['effectiveTaxRate'] + (marginal_tax_rate - df1.iloc[4]['effectiveTaxRate']) / 5
#                     # df1 = df1.append({'Date':int(q[:-2])+j, 'effectiveTaxRate':effectiverest}, ignore_index=True)
#                     df1 = pd.concat([df1, pd.DataFrame([{'Date':int(q[:-2])+j, 'effectiveTaxRate':effectiverest}])], ignore_index=True)
#                 else:
#                     # df1 = df1.append({'Date':int(q[:-2])+j, 'effectiveTaxRate':effective_tax_rate}, ignore_index=True)
#                     df1 = pd.concat([df1, pd.DataFrame([{'Date':int(q[:-2])+j, 'effectiveTaxRate':effective_tax_rate}])], ignore_index=True)
#
#             new_row = pd.DataFrame({'Date':int(df.loc[0,'Date'])-1, 'effectiveTaxRate':effective_tax_rate}, index=[0])
#             df1 = pd.concat([new_row,df1.loc[:]]).reset_index(drop=True)
#             # df1 = df1.append({'Date':'Terminal', 'effectiveTaxRate':marginal_tax_rate}, ignore_index=True)
#             df1 = pd.concat([df1, pd.DataFrame([{'Date':'Terminal', 'effectiveTaxRate':marginal_tax_rate}])], ignore_index=True)
#             df['Effective_tax_rate'] = df1['effectiveTaxRate']
#
#             ##### E-bit 1-t
#             ebit = []
#             for op,ef in zip(df['OperatingIncome'],df['Effective_tax_rate']):
#                 if op > 0:
#                     ebit.append(op * (1 - (ef)/100))
#                 else:
#                     ebit.append(op)
#             df['EBIT(1-t)'] =  ebit
#
#             #####  - Reinvestment
#             if df.iloc[1]['Revenues'] > df.iloc[0]['Revenues']:
#                 df['Reinvestment'] = (df.iloc[1]['Revenues'] - df.iloc[0]['Revenues']) / sales_to_capital
#             else:
#                 df['Reinvestment'] = 0
#
#             l1 = []
#
#             for r in range(2,len(df)):
#                 l1.append((df.iloc[r]['Revenues'] - df.iloc[r-1]['Revenues']) / sales_to_capital)
#             df.loc[2:, 'Reinvestment'] = l1
#
#
#             ##### Invested capital
#             inv = []
#             inv.append(book_value_debt + book_value_equity + aaplinput['Value of Research Asset'][q] - cash_marketable)
#             for re in df['Reinvestment']:
#                 try:
#                     inv.append(inv[-1] + re)
#                 except:
#                     continue
#
#             df['Invested Capital'] = inv[:-1]
#
#
#             ##### Cost of capital
#
#             CostOfDebt = pre_tax_cod*(1-(marginal_tax_rate)/100)
#             cost_of_capital = ((CostOfEquity*MarketValueofEquity) / (EstimatedMarketValueofDebt + MarketValueofEquity)) + ((CostOfDebt*EstimatedMarketValueofDebt) / (EstimatedMarketValueofDebt+MarketValueofEquity))
#
#             df2 = pd.DataFrame([])
#
#             if mode == 'best':
#                 terminal = df.iloc[-1]['revenueGrowth'] + 4
#             elif mode == 'base':
#                 terminal = df.iloc[-1]['revenueGrowth'] + 4.5
#             else:
#                 terminal = df.iloc[-1]['revenueGrowth'] + 6
#
#             # try:
#             # df2 = df2.append({'Date':int(q[:-2]), 'cost_to_capital':aaplinput['Cost Of Capital'][q]}, ignore_index=True)
#             df2 = pd.concat([df2, pd.DataFrame([{'Date':int(q[:-2]), 'cost_to_capital':cost_of_capital}])], ignore_index=True)
#
#
#             for j in range(1,10):
#                 try:
#                     if j > 4:
#                         cost = df2.iloc[j-1]['cost_to_capital'] + (terminal - df2.iloc[4]['cost_to_capital']) / 5
#                         # df2 = df2.append({'Date':int(q[:-2])+j, 'cost_to_capital':cost}, ignore_index=True)
#                         df2 = pd.concat([df2, pd.DataFrame([{'Date':int(q[:-2])+j, 'cost_to_capital':cost}])], ignore_index=True)
#                     else:
#                         # df2 = df2.append({'Date':int(q[:-2])+j, 'cost_to_capital':aaplinput['Cost Of Capital'][q]}, ignore_index=True)
#                         df2 = pd.concat([df2, pd.DataFrame([{'Date':int(q[:-2])+j, 'cost_to_capital':cost_of_capital}])], ignore_index=True)
#                 except:
#                     print('quarter error')
#                     continue
#
#             # df2 = df2.append({'Date':'Terminal', 'cost_to_capital':terminal}, ignore_index=True)
#             df2 = pd.concat([df2, pd.DataFrame([{'Date':'Terminal', 'cost_to_capital':terminal}])], ignore_index=True)
#             new_row = pd.DataFrame({'Date':int(df2.loc[0,'Date'])-1, 'cost_to_capital':np.nan}, index=[0])
#             df2 = pd.concat([new_row,df2.loc[:]]).reset_index(drop=True)
#
#             df['cost_to_capital'] = df2['cost_to_capital']
#
#
#             ##### ROIC
#             df['ROIC'] = (df['EBIT(1-t)'] / df['Invested Capital']) * 100
#
#             if mode == 'best':
#                 terminal1 = df.iloc[-1]['cost_to_capital'] + 5
#             elif mode == 'base':
#                 terminal1 = df.iloc[-1]['cost_to_capital'] + 2.5
#             else:
#                 terminal1 = df.iloc[-1]['cost_to_capital']
#
#             df.loc[11,'ROIC'] = terminal1
#
#
#             ##### Reinvestment terminal
#             if df.iloc[-1]['revenueGrowth'] > 0:
#                 df.loc[11,'Reinvestment'] = (df.iloc[-1]['revenueGrowth'] / df.iloc[-1]['ROIC']) * df.iloc[-1]['EBIT(1-t)']
#             else:
#                 df.loc[11,'Reinvestment'] = 0
#
#
#             ##### FCFF
#             df['FCFF'] = df['EBIT(1-t)'] - df['Reinvestment']
#
#             ##### Cumulated discount factor
#             cum = []
#             cum.append(1 / (1 + (df.loc[1,'cost_to_capital']/100)))
#             for coc in df['cost_to_capital'][2:11]:
#                 try:
#                     cum.append(cum[-1] * (1 / (1 + (coc/100))))
#                 except:
#                     continue
#             cum.append(np.nan)
#             cum.insert(0,np.nan)
#             df['Cumulated discount factor'] = cum
#
#
#             ##### PV FCFF
#             df['PV FCFF'] = df['FCFF'] * df['Cumulated discount factor']
#
#             single_dict = {}
#             single_dict['Unlevered beta'] = unlevered_beta
#             single_dict['Terminal cash flow'] = df.iloc[-1]['FCFF']
#             single_dict['Terminal cost of capital'] = df.iloc[-1]['cost_to_capital']
#             single_dict['Terminal value'] = single_dict['Terminal cash flow'] / ((single_dict['Terminal cost of capital']/100) - (df.iloc[-1]['revenueGrowth']/100))
#             if np.isnan(single_dict['Terminal value']):
#                 single_dict['Terminal value'] = 0
#             single_dict['PV(Terminal value)'] = single_dict['Terminal value'] * df.iloc[-2]['Cumulated discount factor']
#             single_dict['PV (CF over next 10 years)'] = sum(df['PV FCFF'][1:11])
#             single_dict['Sum of PV'] = single_dict['PV(Terminal value)'] + single_dict['PV (CF over next 10 years)']
#             single_dict['Value of operating assets'] = single_dict['Sum of PV']
#             single_dict['Debt']  = book_value_debt
#             single_dict['Minority Interests'] = minority_interest
#             single_dict['Cash Marketable'] = cash_marketable
#             single_dict['Non-operating assets'] = 0
#             single_dict['Value of equity'] = single_dict['Value of operating assets'] - single_dict['Debt'] - single_dict['Minority Interests'] + single_dict['Cash Marketable'] + single_dict['Non-operating assets']
#             single_dict['Value of equity in common stock'] = single_dict['Value of equity']
#             single_dict['Number of shares'] = no_of_shares_outstanding
#             single_dict['Estimated value /share'] = single_dict['Value of equity in common stock'] / single_dict['Number of shares']
#             # print(single_dict)
#             ##### exchange rate
#             if cur == "USD":
#                 single_dict['Estimated value /share (Local Currency)'] = abs(single_dict['Estimated value /share'] / 1)
#             else:
#                 date1 = filling_date1[q]
#                 single_dict['Estimated value /share (Local Currency)'] = abs(single_dict['Estimated value /share'] / exg_rate1[date1])
#             # date = filling_date1[q]
#
#             single_dict['Current price'] = current_stock_price
#             single_dict['Valuation'] = abs(((single_dict['Current price'] - single_dict['Estimated value /share (Local Currency)']) / single_dict['Current price'])*100)
#
#
#             ##### Price target (USD)
#             price = []
#             price.append(single_dict['Estimated value /share'])
#             for r in range(0,11):
#                 try:
#                     price.append(price[-1] * (1 + (CostOfEquity/100)))
#                 except:
#                     continue
#             df['Price Target USD'] = price
#
#
#
#             ##### Price target (Local Currency)
#             pricelocal = []
#             pricelocal.append(single_dict['Estimated value /share (Local Currency)'])
#             for r in range(0,11):
#                 try:
#                     pricelocal.append(pricelocal[-1] * (1 + (CostOfEquity/100)))
#                 except:
#                     continue
#
#             df['Price Target Local'] = pricelocal
#             df = df.fillna(0)
#             df_test = df
#
#             dictt = df_test.to_dict('list')
#             dictt.update(single_dict)
#
#             quarter_dict[q] = dictt
#             d1 = str(quarter_dict)
#                 # print(d1[7600:])
#             d1 = d1.replace("'", '"')
#             d1 = d1.replace("nan","0")
#             d1 = d1.replace("None","0")
#             d1 = d1.replace("inf","0")
#
#         else:
#             net_margin = []
#             net_margin.append(request['net_year_1'])
#             net_margin.append(request['net_year_2'])
#             net_margin.append(request['net_year_3'])
#             net_margin.append(request['net_year_4'])
#             net_margin.append(request['net_year_5'])
#
#             net_TTM = request['net_TTM']
#             eps_ttm = request['eps_ttm']
#             Dividends_shareTTM = request['Dividends_shareTTM']
#             payout = request['current_payout']
#             predicted_payout = request['predicted_payout_ratio_y5']
#             roe = request['roe']
#
#             # operating_terminal = request['operating_target_in_year_10']
#             # net_terminal = request['net_target_in_year_10']
#
#             # with open('roe_with_us (1).json','r') as f:
#             #     roeinputusd = json.loads(f.read())
#
#             # with open('roe_without_us.json','r') as f:
#             #     roeinputnonusd = json.loads(f.read())
#             nest = [date, revenue_growth]
#
#             df = pd.DataFrame((_ for _ in itertools.zip_longest(*nest)), columns=['Date', 'revenueGrowth'])
#             new_row = pd.DataFrame({'Date':int(df.loc[0,'Date'])-1, 'revenueGrowth':np.nan}, index=[0])
#             df = pd.concat([new_row,df.loc[:]]).reset_index(drop=True)
#             # l = []
#             l = [revenue_TTM]
#
#             for k in range(2,7):
#                 try:
#                     l.append(l[-1] * (1 +  (df.iloc[k-1]['revenueGrowth']/100)))
#                 except:
#                     break
#
#             df['Revenues'] = l
#
#             netincome_base = net_TTM
#             netmargin_base = (netincome_base / revenue_TTM)*100
#             net_growth_list = net_margin
#             net_growth_list.insert(0, netmargin_base)
#             df['netMargin'] = net_growth_list
#
#             # df.loc[0,'operating_margin'] = (operating_TTM / (df.loc[0,'Revenues'])) * 100
#             # df.loc[0,'netMargin'] = (net_TTM / (df.loc[0,'Revenues'])) * 100
#
#             for j in range(6,11):
#                 revenuerest = df.iloc[j-1]['revenueGrowth'] + (rfr - df.iloc[5]['revenueGrowth']) / 5
#                 netrest = df.iloc[j-1]['netMargin']
#                 # netrest = df.iloc[j-1]['netMargin'] + (net_terminal - df.iloc[5]['netMargin']) / 5
#                 revenues = df.iloc[j-1]['Revenues'] * (1 +  (revenuerest/100))
#                 datesrest = int(int(df.iloc[j-1]['Date']) + 1)
#
#                 df = pd.concat([df, pd.DataFrame([{'Date':datesrest, 'revenueGrowth':revenuerest, 'netMargin':netrest, 'Revenues':revenues}])], ignore_index=True)
#
#             df['Date'] = df['Date'].astype(int)
#             df = pd.concat([df, pd.DataFrame([{'Date':'Terminal', 'revenueGrowth':rfr, 'netMargin':df.loc[10,'netMargin']}])], ignore_index=True)
#             df.loc[11,'Revenues'] = df.iloc[-2]['Revenues'] * (1 +  (df.iloc[-1]['revenueGrowth']/100))
#
#             df['netIncome'] = (df['netMargin']/100) * df['Revenues']
#             # df['netIncome'] = (df['netMargin']/100) * df['Revenues']
#
#             df.loc[0,"netIncome"] = netincome_base
#
#             ##### Net Income Growth
#             netgrowth = []
#             # df['netGrowth'] = np.nan
#             for r in range(1,12):
#                 try:
#                     netgrowth.append(((df.iloc[r]['netIncome'] - df.iloc[r-1]['netIncome']) / abs(df.iloc[r-1]['netIncome'])) * 100)
#                 except:
#                     continue
#             df.loc[1:,'netGrowth'] = netgrowth
#
#
#
#             #### Dividend Payout Ratio
#
#             if payout == 0:
#                 predicted_payout = 0
#             else:
#                 predicted_payout = request['predicted_payout_ratio_y5']
#
#             terminal_year = (1 - (df.iloc[-1]['netGrowth']/100) / (roe/100)) * 100
#             df1 = pd.DataFrame({'Date':int(q[:-2])-1, 'payoutRatio':payout}, index=[0])
#
#             if payout > terminal_year:
#             #   df1 = df1.append({'Date':q[:-2], 'payoutRatio':predicted_payout}, ignore_index=True)
#                 df1 = pd.concat([df1, pd.DataFrame([{'Date':q[:-2], 'payoutRatio':terminal_year}])], ignore_index=True)
#             elif payout < 0:
#                 df1 = pd.concat([df1, pd.DataFrame([{'Date':q[:-2], 'payoutRatio':predicted_payout}])], ignore_index=True)
#             else:
#                 pay = df1.iloc[0]['payoutRatio'] + (predicted_payout - df1.iloc[0]['payoutRatio']) / 5
#             #   df1 = df1.append({'Date':q[:-2], 'payoutRatio':pay}, ignore_index=True)
#                 df1 = pd.concat([df1, pd.DataFrame([{'Date':q[:-2], 'payoutRatio':pay}])], ignore_index=True)
#             for r in range(2,5):
#                 if payout > terminal_year:
#                     pay1 = terminal_year
#                 elif df1.iloc[0]['payoutRatio'] > 0:
#                     pay1 = df1.iloc[r-1]['payoutRatio'] + (predicted_payout - df1.iloc[0]['payoutRatio']) / 5
#                 else:
#                     pay1 = df1.iloc[r-1]['payoutRatio'] + (predicted_payout - df1.iloc[1]['payoutRatio']) / 5
#                 dates = int(int(df1.iloc[r-1]['Date']) + 1)
#                 #   df1 = df1.append({'Date':dates, 'payoutRatio':pay1}, ignore_index=True)
#                 df1 = pd.concat([df1, pd.DataFrame([{'Date':dates, 'payoutRatio':pay1}])], ignore_index=True)
#
#             # df1 = df1.append({'Date':int(q[:-2])+4, 'payoutRatio':predicted_payout}, ignore_index=True)
#             if payout > terminal_year:
#                 df1 = pd.concat([df1, pd.DataFrame([{'Date':int(q[:-2])+4, 'payoutRatio':terminal_year}])], ignore_index=True)
#             else:
#                 df1 = pd.concat([df1, pd.DataFrame([{'Date':int(q[:-2])+4, 'payoutRatio':predicted_payout}])], ignore_index=True)
#
#             for r in range(6,11):
#                 pay1 = df1.iloc[r-1]['payoutRatio'] + (terminal_year - df1.iloc[5]['payoutRatio']) / 5
#                 dates = int(int(df1.iloc[r-1]['Date']) + 1)
#                 #   df1 = df1.append({'Date':dates, 'payoutRatio':pay1}, ignore_index=True)
#                 df1 = pd.concat([df1, pd.DataFrame([{'Date':dates, 'payoutRatio':pay1}])], ignore_index=True)
#
#             # df1 = df1.append({'Date':'Terminal', 'payoutRatio':terminal_year}, ignore_index=True)
#             df1 = pd.concat([df1, pd.DataFrame([{'Date':'Terminal', 'payoutRatio':terminal_year}])], ignore_index=True)
#
#             df['payoutRatio'] = df1['payoutRatio']
#             # print(df1)
#             # try:
#             equity = book_value_equity
#             cost_of_equity = CostOfEquity
#             return_of_equity = (net_TTM / book_value_equity)
#             payout_ratio = payout
#             # except:
#                 # continue
#             if df.iloc[1]['netIncome'] > 0:
#                 dividendpaid = df.iloc[1]['netIncome']*(df.iloc[1]['payoutRatio']/100)
#             else:
#                 dividendpaid = 0
#
#             dictt = {'Date':[str(int(q[:-2])-1), q[:-2]], 'revenueGrowth':[np.nan, df.iloc[1]['revenueGrowth']], 'revenue':[df.iloc[0]['Revenues'], df.iloc[1]['Revenues']],
#                 'netMargin':[df.iloc[0]['netMargin'],df.iloc[1]['netMargin']], 'netIncome':[df.iloc[0]['netIncome'], df.iloc[1]['netIncome']],
#                 'netGrowth':[df.iloc[0]['netGrowth'],df.iloc[1]['netGrowth']], 'bvEquity':[np.nan,equity], 'costOfEquity':[np.nan,cost_of_equity], 'returnOnEquity':[return_of_equity,
#                 df.iloc[1]['netIncome']/equity], 'dividendpayout':[payout_ratio, df.iloc[1]['payoutRatio']], 'dividendPaid':[np.nan,dividendpaid],
#                 'retainedEarning':[np.nan, df.iloc[1]['netIncome'] - dividendpaid]}
#             df2 = pd.DataFrame(dictt)
#             df2['equityCost'] = df2['bvEquity'] * (df2['costOfEquity']/100)
#             df2['excessEquity'] = df2['netIncome'] - df2['equityCost']
#             df2['cumulatedDiscount'] = 1 + (df2['costOfEquity']/100)
#             df2['presentValue'] = df2['excessEquity'] / df2['cumulatedDiscount']
#
#             # if q[-2:] == 'Q1':
#             #     d12 = 3/4
#             # elif q[-2:] == 'Q2':
#             #     d12 = 2/4
#             # elif q[-2:] == 'Q3':
#             #     d12 = 1/4
#             # else:
#             #     d12 = 1
#
#             for r in range(2,12):
#                 dates = str(int(df.iloc[r-1]['Date'])+1)
#                 if dates == '2024':
#                     bvEquity = df2.iloc[r-1]['bvEquity'] + df2.iloc[r-1]['retainedEarning']
#                 else:
#                     bvEquity = df2.iloc[r-1]['bvEquity'] + df2.iloc[r-1]['retainedEarning']
#
#                 costOfEquity = df2.iloc[r-1]['costOfEquity']
#                 returnOnEquity = df.iloc[r]['netIncome'] / bvEquity
#                 dividendpayout = df.iloc[r]['payoutRatio']
#
#                 if df.iloc[r]['netIncome'] > 0:
#                     dividendPaid = df.iloc[r]['netIncome'] * (dividendpayout/100)
#                 else:
#                     dividendPaid = 0
#
#                 retainedEarning = df.iloc[r]['netIncome'] - dividendPaid
#                 equityCost = bvEquity * (costOfEquity/100)
#                 excessEquity = df.iloc[r]['netIncome'] - equityCost
#                 cumulatedDiscount = (1 + (costOfEquity/100) ) * df2.iloc[r-1]['cumulatedDiscount']
#                 presentValue = excessEquity / cumulatedDiscount
#
#             #   df2 = df2.append({'Date':dates, 'revenueGrowth':df.iloc[r]['revenueGrowth'], 'revenue':df.iloc[r]['Revenues'], 'netMargin':df.iloc[r]['netMargin'],
#             #                     'netIncome':df.iloc[r]['netIncome'], 'netGrowth':df.iloc[r]['netGrowth'], 'bvEquity':bvEquity, 'costOfEquity':costOfEquity, 'returnOnEquity':returnOnEquity,
#             #                     'dividendpayout':dividendpayout, 'dividendPaid':dividendPaid, 'retainedEarning':retainedEarning, 'equityCost':equityCost, 'excessEquity':excessEquity,
#             #                     'cumulatedDiscount':cumulatedDiscount, 'presentValue':presentValue}, ignore_index=True)
#
#                 df2 = pd.concat([df2, pd.DataFrame([{'Date':dates, 'revenueGrowth':df.iloc[r]['revenueGrowth'], 'revenue':df.iloc[r]['Revenues'], 'netMargin':df.iloc[r]['netMargin'],
#                                     'netIncome':df.iloc[r]['netIncome'], 'netGrowth':df.iloc[r]['netGrowth'], 'bvEquity':bvEquity, 'costOfEquity':costOfEquity, 'returnOnEquity':returnOnEquity,
#                                     'dividendpayout':dividendpayout, 'dividendPaid':dividendPaid, 'retainedEarning':retainedEarning, 'equityCost':equityCost, 'excessEquity':excessEquity,
#                                     'cumulatedDiscount':cumulatedDiscount, 'presentValue':presentValue}])], ignore_index=True)
#
#             single_dict = {}
#             single_dict['Equity Invested'] = df2.iloc[1]['bvEquity']
#             single_dict['PV of Equity Excess Return'] = sum(df2.iloc[1:11]['presentValue'])
#             single_dict['Terminal  Value of Excess Equity Return'] = (df2.iloc[-1]['excessEquity'] / ((df2.iloc[-1]['costOfEquity']/100) - (df2.iloc[-1]['revenueGrowth']/100))) / df2.iloc[-2]['cumulatedDiscount']
#             single_dict['Payout Value of Equity'] = single_dict['Equity Invested'] + single_dict['PV of Equity Excess Return'] + single_dict['Terminal  Value of Excess Equity Return']
#             single_dict['Payout Number of shares'] = no_of_shares_outstanding
#             single_dict['Payout Estimated Value/Share'] = single_dict['Payout Value of Equity'] / single_dict['Payout Number of shares']
#             single_dict['Payout Current price'] = current_stock_price
#
#             if cur == "USD":
#                 single_dict['Payout Estimated Value/Share (Local Currency)'] = abs(single_dict['Payout Estimated Value/Share'] / 1)
#             else:
#                 date1 = filling_date1[q]
#                 single_dict['Payout Estimated Value/Share (Local Currency)'] = abs(single_dict['Payout Estimated Value/Share'] / exg_rate1[date1])
#             # single_dict['Payout Estimated Value/Share (Local Currency)'] = single_dict['Payout Estimated Value/Share'] / exchange_rate
#             single_dict['Payout Valuation'] = abs((single_dict['Payout Current price'] - single_dict['Payout Estimated Value/Share (Local Currency)']) / single_dict['Payout Current price']) * 100
#             single_dict['roe'] = roe
#             # single_dict['book_value_equity_previous_year_same_quarter'] = book_value_equity_previous_year_same_quarter
#             single_dict['eps_ttm'] = eps_ttm
#             single_dict['current_payout'] = payout
#
#             #### Price target (USD)
#             price_payout = []
#
#             price_payout.append(single_dict['Payout Estimated Value/Share'])
#             for r in range(0,11):
#                 try:
#                     price_payout.append(price_payout[-1] * (1 + (aaplinput['Cost Of Equity'][q]/100)))
#                 except:
#                     continue
#
#             df2['Payout price_payout Target USD'] = price_payout
#
#             #### Price target (Local Currency)
#             pricelocalpayout = []
#             pricelocalpayout.append(single_dict['Payout Estimated Value/Share (Local Currency)'])
#             for r in range(0,11):
#                 try:
#                     pricelocalpayout.append(pricelocalpayout[-1] * (1 + (aaplinput['Cost Of Equity'][q]/100)))
#                 except:
#                     continue
#
#             df2['Payout Price Target Local'] = pricelocalpayout
#
#             df2 = df2.fillna(0)
#             df_test = df2
#
#             dictt = df_test.to_dict('list')
#             dictt.update(single_dict)
#
#             quarter_dict[q] = dictt
#             d1 = str(quarter_dict)
#
#             d1 = d1.replace("'", '"')
#             d1 = d1.replace("nan","0")
#             d1 = d1.replace("None","0")
#             d1 = d1.replace("inf","0")
# #         # print(d1)
#         jsn = json.loads(d1.replace("-inf","0"))
#
#         return HttpResponse(json.dumps(jsn, indent=4,default=str),content_type = "application/json")

@api_view(['POST'])
def read_fcff_0(request):
    res = json.loads(request.body.decode('utf-8'))
    try:
        request = res['quarter']
        symbol = res['symbol']
        model = res['valuation_model']
        case = res['case']
    
        fcf = {}
        dcfinp = {}
        er = {}
        # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/dcfcalc/'+symbol+'.json', 'r') as f:
        #     dcfinput = json.loads(f.read())
        dcf_input_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfcalc", f"{symbol}.json")
        with open(dcf_input_path, 'r') as f:
            dcfinput = json.loads(f.read()) #@danish

        # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/wall_street_0_new/current_stock_price/'+symbol+'.json', 'r') as f:
        #     dcfprice = json.loads(f.read())
        dcf_price_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "current_stock_price", f"{symbol}.json")
        with open(dcf_price_path, 'r') as f:
            dcfprice = json.loads(f.read()) #@danish

        if model == 'FCFF' or model == 'fcff' :   

            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/dcfoutputbest'+'/'+ symbol+'.json','r') as f:
            #     fcffbest = json.loads(f.read())
            fcff_best_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfoutputbest", f"{symbol}.json")
            with open(fcff_best_path, 'r') as f:
                fcffbest = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/dcfoutputbase'+'/'+ symbol+'.json','r') as f:
            #     fcffbase = json.loads(f.read())
            fcff_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfoutputbase", f"{symbol}.json")
            with open(fcff_base_path, 'r') as f:
                fcffbase = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/dcfoutputworst'+'/'+ symbol+'.json','r') as f:
            #     fcffworst = json.loads(f.read())
            fcff_worst_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfoutputworst", f"{symbol}.json")
            with open(fcff_worst_path, 'r') as f:
                fcffworst = json.loads(f.read()) #@danish

            
            # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/wall_street_0_new/fcff_quarter'+'/'+ symbol+'.json','r') as f:
            #     fcffquarter = json.loads(f.read())
            fcff_quarter_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "fcff_quarter", f"{symbol}.json")
            with open(fcff_quarter_path, 'r') as f:
                fcffquarter = json.loads(f.read()) #@danish

                    
            # publish_date = dcfinput['Publish date']
            # publish_dates = {}
            graph_data = {}
            for j in list(fcffquarter.values()):
                date = datetime.strptime(j, '%Y-%m-%d').date()
                q = math.ceil(int(str(date)[5:7])/3)
                # publish_dates[str(date)[:4]+'Q'+str(q)] = j
            
                try:
                    best = fcffbest[str(date)[:4]+'Q'+str(q)]['Estimated value /share (Local Currency)'] 
                    base = fcffbase[str(date)[:4]+'Q'+str(q)]['Estimated value /share (Local Currency)'] 
                    worst = fcffworst[str(date)[:4]+'Q'+str(q)]['Estimated value /share (Local Currency)'] 
                    if best == np.inf or best == -np.inf:
                        base=0
                        best=0
                        worst=0
                    graph_data[j] = {'Best':best, 'Base':base, 'Worst':worst, 'Current_price':dcfprice[str(date)[:4]+'Q'+str(q)]}
                except:
                    continue
        else:   
            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/ermbest'+'/'+ symbol+'.json','r') as f:
            #     fcffbest = json.loads(f.read())
            ermbest_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "ermbest", f"{symbol}.json")
            with open(ermbest_path, 'r') as f:
                fcffbest = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/ermbase'+'/'+ symbol+'.json','r') as f:
            #     fcffbase = json.loads(f.read())
            ermbase_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "ermbase", f"{symbol}.json")
            with open(ermbase_path, 'r') as f:
                fcffbase = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/ermworst'+'/'+ symbol+'.json','r') as f:
            #     fcffworst = json.loads(f.read())
            ermworst_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "ermworst", f"{symbol}.json")
            with open(ermworst_path, 'r') as f:
                fcffworst = json.loads(f.read()) #@danish

            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/erm_quarter'+'/'+ symbol+'.json','r') as f:
            #     ermquarter = json.loads(f.read())
            erm_quarter_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "erm_quarter", f"{symbol}.json")
            with open(erm_quarter_path, 'r') as f:
                ermquarter = json.loads(f.read()) #@danish

                    
            # publish_date = dcfinput['Publish date']
            # publish_dates = {}
            graph_data = {}
            for j in list(ermquarter.values()):
                date = datetime.strptime(j, '%Y-%m-%d').date()
                q = math.ceil(int(str(date)[5:7])/3)
                # publish_dates[str(date)[:4]+'Q'+str(q)] = j
            
                try:
                    best = fcffbest[str(date)[:4]+'Q'+str(q)]['Estimated Value/Share (Local Currency)'] 
                    base = fcffbase[str(date)[:4]+'Q'+str(q)]['Estimated Value/Share (Local Currency)'] 
                    worst = fcffworst[str(date)[:4]+'Q'+str(q)]['Estimated Value/Share (Local Currency)'] 
                    if best == np.inf or best == -np.inf:
                        base=0
                        best=0
                        worst=0
                    graph_data[j] = {'Best':best, 'Base':base, 'Worst':worst, 'Current_price':dcfprice[str(date)[:4]+'Q'+str(q)]}
                except:
                    continue
        
            
        if model == 'FCFF' or model == 'fcff' :
            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/dcfoutput'+case.lower()+'/'+ symbol+'.json','r') as f:
            #     fcff = json.loads(f.read())
            fcff_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", f"dcfoutput{case.lower()}", f"{symbol}.json")
            with open(fcff_path, 'r') as f:
                fcff = json.loads(f.read()) #@danish

            fcf[request] = fcff[request]
            for i in dcfinput:
                try:
                    dcfinp[i] = dcfinput[i][request]
                except:
                    continue
            dcfinp.update(fcf)
            
        else:
            # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/erm'+case.lower()+'/'+ symbol+'.json','r') as f:
            #     erm = json.loads(f.read())
            erm_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", f"erm{case.lower()}", f"{symbol}.json")
            with open(erm_path, 'r') as f:
                erm = json.loads(f.read()) #@danish

            
            er[request] = erm[request]
            for i in dcfinput:
                try:
                    dcfinp[i] = dcfinput[i][request]
                except:
                    continue
            dcfinp.update(er)
            
        dcfinp.update(dcfinp[request])
        if model == 'FCFF' or model == 'fcff':
            dcfinp["Capitalized Operating Margin"] = (dcfinp["Operating Income (TTM)"] + dcfinp["Capitalized R & D"])/dcfinp["Revenues"][0]
        else:
            dcfinp["Capitalized Operating Margin"] = (dcfinp["Operating Income (TTM)"] + dcfinp["Capitalized R & D"])/dcfinp["revenue"][0]
        
        dcfinp["Valuation Currency"] = dcfinput["Valuation Currency"]
        dcfinp["graph data"] = graph_data
        del dcfinp[request]
        dcfinp["Date"][0] = "Base"
        dcfinp["Local Currency"] = "USD"
        dcfinp["Incorporation company"] = "US"
        return HttpResponse(json.dumps(dcfinp, indent=4, default=str), content_type="application/json")
    except:
        return HttpResponse(json.dumps({"Error":"Data not found"}, indent=4, default=str), content_type="application/json")

@api_view(['POST'])
def get_quarters_0(request):
    request = json.loads(request.body.decode('utf-8'))
    symbol = request["symbol"]
    # with open('/home2/nvme2n1p1/cp5wordpress/wall_street_0_updated/fcff_quarter/'+symbol+'.json', 'r') as f:
    #     dcfinput = json.loads(f.read())
    fcff_quarter_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "fcff_quarter", f"{symbol}.json")
    with open(fcff_quarter_path, 'r') as f:
        dcfinput = json.loads(f.read()) #@danish


    keys = sorted(list(dcfinput.keys()))[::-1]
    return HttpResponse(json.dumps(keys, indent=4, default=str), content_type="application/json")

@api_view(['GET', 'POST'])
def get_symbol_quarter(request):
    request = json.loads(request.body.decode('utf-8'))
    s = request['symbol']

    # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/DCF/dcfcalc/'+s+'.json','r') as f:
    #     aaplinput = json.loads(f.read())
    dcfcalc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfcalc", f"{s}.json")
    with open(dcfcalc_path, 'r') as f:
        aaplinput = json.loads(f.read()) #@danish


    quarters = aaplinput['Base year']
    quarter = {s:list(quarters.keys())}
    return HttpResponse(json.dumps(quarter, indent=4,default=str),content_type = "application/json")

@api_view(['GET', 'POST'])
def get_symbol_quarter_0(request):
    request = json.loads(request.body.decode('utf-8'))
    s = request['symbol']

    # with open('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/wall_street_0_new/dcfcalc/'+s+'.json','r') as f:
    #     aaplinput = json.loads(f.read())
    dcfcalc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wall_street_0_updated", "dcfcalc", f"{s}.json")
    with open(dcfcalc_path, 'r') as f:
        aaplinput = json.loads(f.read()) #@danish

    quarters = aaplinput['Base year']
    quarter = {s:list(quarters.keys())}
    return HttpResponse(json.dumps(quarter, indent=4,default=str),content_type = "application/json")

@api_view(['GET', 'POST'])
def get_portfolio_symbols(request):
    # request = json.loads(request.body.decode('utf-8'))
    # portfolio_name = request['portfolio_name']

    # portfolio_data = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/PortfolioWebsite.csv')
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media")
    portfolio_file = os.path.join(base_path, "PortfolioWebsite.csv")
    portfolio_data = pd.read_csv(portfolio_file) #@danish

    portfolio_data.rename(columns={"Portfolio Name":"Portfolio_Name", "Market Cap":"Market_Cap", "Head Title":"Head_Title"}, inplace=True)
    portfolio_data.replace(np.nan, 0, inplace=True)
    data = portfolio_data[portfolio_data['Custom'] == 0]
    last_data = portfolio_data[portfolio_data['Custom'] != 0]

    today_date = date.today()
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #screener_data = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media")
            screener_path = os.path.join(base_path, "screener_data", f"screener_{curr_date}.csv")
            screener_data = pd.read_csv(screener_path) #@danish
            break
        except:
            i = i + 1
    # screener_data = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
    # screener_data = pd.read_csv('D:/apis/screener_20231205.csv')
    screener_data = screener_data[screener_data['currency'] == "USD"]

    value_invest = screener_data[(screener_data['peRatioTTM_x'] < 15.0) & (screener_data['pbRatioTTM'] < 1.5)]
    value_invest = value_invest[(value_invest['sector'] != 'Financial Services') & (value_invest['sector'] != 'Real Estate')]
    value_invest = list(value_invest[value_invest['MktCap'] > 50000000000]['symbol'])

    dividend = screener_data[screener_data['dividendYieldPercentageTTM'] < 4.0]
    dividend = list(dividend[dividend['MktCap'] > 50000000000]['symbol'])

    wallstreet = screener_data[screener_data['fcff_base'] < -50.0]
    wallstreet = wallstreet[(wallstreet['sector'] != 'Financial Services') & (wallstreet['sector'] != 'Real Estate')]
    wallstreet = list(wallstreet[wallstreet['MktCap'] > 1000000000]['symbol'])

    highly_underpriced = screener_data[screener_data['base'] < -50.0]
    highly_underpriced = list(highly_underpriced[highly_underpriced['MktCap'] > 1000000000]['symbol'])

    total_bank = screener_data[(screener_data['industry'] == "Banks") & (screener_data['erm_base'] < -25.0)]
    total_bank = list(total_bank[total_bank['MktCap'] > 20000000000]['symbol'])

    tech_giant = screener_data[screener_data['sector'] == "Technology"]
    tech_giant = list(tech_giant[tech_giant['MktCap'] > 50000000000]['symbol'])

    symbols = [value_invest,dividend,wallstreet,highly_underpriced,total_bank,tech_giant]

    data['symbol'] = symbols
    data.replace('NA', 0, inplace=True)
    slug = ['value-invest-stocks', 'high-dividend-yield-stocks', 'wallstreet-undervalued-stocks', 'highly-underpriced-stocks',
            'top-banks-stocks', 'tech-giants-stocks',  'warren-buffet-portfolio-stocks']
    
    data['slug'] = slug[:-1]
    # df = data[data['Portfolio Name'] == portfolio_name]
    dictt = data.to_dict('records')
    last_dictt = last_data.to_dict(orient='records')[0]
    last_dictt['slug'] = slug[-1]
    
    dictt.append(last_dictt)
    # dictt = data.to_dict('records')
    return HttpResponse(json.dumps(dictt, indent=4,default=str),content_type = "application/json")

@api_view(['GET', 'POST'])
def get_valuation_price(request):
    request = json.loads(request.body.decode('utf-8'))
    symbols = request['symbols']
    cols = ['symbol', 'relative_fy0_base', 'fcff_fy0_base', 'erm_fy0_base']
    
    try:
        today_date = date.today()
        curr_date = str(today_date).replace('-', '')
    
        # screener_df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')[cols]
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
        file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
        screener_df = pd.read_csv(file_path)[cols]
    except:
        today_date = date.today() - timedelta(days=1)
        curr_date = str(today_date).replace('-', '')
    
        # screener_df = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')[cols]
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
        file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
        screener_df = pd.read_csv(file_path)[cols] #@danish
    screener_df = screener_df[screener_df['symbol'].isin(symbols)][cols]
    screener_df.rename(columns={'relative_fy0_base':'pricing', 'fcff_fy0_base':'fcffValuation', 'erm_fy0_base':'ermValuation'}, inplace=True)
    
    screener_dict = screener_df.to_dict('records')

    d1 = str(screener_dict)
    # print(d1[7600:])
    d1 = d1.replace("'", '"')
    d1 = d1.replace("nan","0")
    d1 = d1.replace("None","0")
    d1 = d1.replace("inf","0")
    # print(d1)
    jsn = json.loads(d1.replace("-inf","0"))
    
    return HttpResponse(json.dumps(jsn, indent=4,default=str),content_type = "application/json")

@api_view(['GET'])
def get_sector_industry(request):
    output = {}
    today_date = date.today()
    i = 0
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            #df = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv', usecols = ["industry","sector"])
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path, usecols=["industry", "sector"]) #@danish
            # screener_data = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            break
        except:
            i = i + 1
    data = {}
    for i in df["sector"].unique():
        data[i] = list(df[df["sector"] == i]["industry"].unique())
    return HttpResponse(json.dumps(data, indent=4,default=str),content_type = "application/json")

@api_view(['POST'])
def get_industry(request):
    request = json.loads(request.body.decode('utf-8'))
    i=0
    today_date = date.today()
    while True:
        if i > 0:
            today_date = today_date - timedelta(days=1)
            # date_string = str(today_date).split(" ")[0].replace("-", "")
        try: 
            curr_date = str(today_date).replace('-', '')
            # df = pd.read_csv(f'/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_{curr_date}.csv', usecols = ["industry","sector","symbol"])
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
            file_path = os.path.join(base_path, f"screener_{curr_date}.csv")
            df = pd.read_csv(file_path, usecols=["industry", "sector", "symbol"]) #@danish
            # screener_data = pd.read_csv('/home2/nvme2n1p1/cp2invexwealth/pythonDir/stock_data/media/screener_data/screener_'+str(curr_date)+'.csv')
            break
        except:
            i = i + 1
    industry = df[df["symbol"]==request.get("symbol")]["industry"].values[0]
    return HttpResponse(json.dumps({"industry":industry, "status":True}, indent=4,default=str),content_type = "application/json")
    
    
