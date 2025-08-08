# from datetime import datetime, date
# from django.http.response import HttpResponse,JsonResponse
# from django.shortcuts import render
# import json
# from stock_data import test_api
# import vaex
# import numpy as np
# import pandas as pd
# from pandas.core.arrays import integer
# from pandas.core.frame import DataFrame
# import os
# from . import run_api,final_api, invex_avg
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# import glob
# import os
# import os.path
# from datetime import date, timedelta
# import math
# from collections import defaultdict
# from bisect import bisect_left
# import collections
# from urllib.request import urlopen
# import mimetypes
# from pathlib import Path
# from django.core.files.storage import FileSystemStorage
# import statistics
#
# # Create your views here.
# def home(request):
#     return render(request, "home.html")
#
# def daily(request):
#     return render(request, "daily.html")
#
# def load_data(path, ticker, in_date):
#     data = pd.read_csv(path + ticker + ".csv", usecols=["date","open","high","low", "close"], parse_dates=["date"])
#     data = data[data['date'] <= in_date]
#     return data
#
# def rolling_finder(data, filter_days, rolling_value, in_date):
#     # data["date"] = pd.to_datetime(data["date"])
#     # print(len(data))
#     print(in_date)
#     data = data[data["date"] >= (in_date - timedelta(days=filter_days))]
#     # print(len(data))
#     high_v = []
#     open_v = []
#     low_v = []
#     for i in range(0,len(data)):
#         # print(data.iloc[i+rolling_value-1])
#         try:
#             # print('try')
#             df = data.iloc[i+rolling_value-1]
#             print(df)
#         except:
#             print('except---------')
#             break
#         open_val = data.iloc[i]["open"]
#
#         high_col = data.iloc[i:i+rolling_value]['high'].max()
#         print(high_col)
#
#         low_col = data.iloc[i:i+rolling_value]['low'].min()
#         high_v.append(((high_col - open_val)/ open_val)*100)
#         open_v.append(((df["open"] - open_val)/ open_val)*100)
#         low_v.append(((low_col - open_val)/ open_val)*100)
#     print(high_v)
#     return high_v,open_v,low_v
#
# #Order will be in 'high', 'low', 'open'
# def get_median(d):
#     return [d['high'].describe()['50%']/100, d['low'].describe()['50%']/100, d['open'].describe()['50%']/100]
#
# #Order will be in 'high', 'low', 'open'
# def get_mean(d):
#     return [d['high'].describe()['mean']/100, d['low'].describe()['mean']/100, d['open'].describe()['mean']/100]
#
# def get_std(d):
#     return [d['high'].describe()['std']/100, d['low'].describe()['std']/100, d['open'].describe()['std']/100]
#
# def bins_and_frequency(data, value):
#     # print('bins frequency')
#     # print(data)
#     # print(value)
#     least_value = int(data[value].min())
#     high_value = math.ceil(data[value].max()) + 1.0
#     bins_array = np.arange(least_value, high_value, 0.05)
#     count = defaultdict(int)
#     bins_array.sort()
#     for item in data[value]:
#         pos = bisect_left(bins_array, item)
#         if pos == len(bins_array):
#             count[None] += 1
#         else:
#             count[bins_array[pos]] += 1
#     od = collections.OrderedDict(sorted(count.items()))
#     frequency = []
#     probability=[]
#     bins = []
#     for k, v in od.items():
#         bins.append(k)
#         frequency.append(v)
#     for i in frequency:
#             probability.append((i/sum(frequency))*100)
#     if value == "low":
#         cumulative = np.cumsum(probability[::-1])
#     else:
#         cumulative = np.cumsum(probability)
#     return frequency,bins,probability,cumulative
#
# def get_cumsum(cum, prob):
#     for i,c in enumerate(cum):
#         if c>=prob:
#             return i, c
#
# def get_last_col(d, day):
#     data = d[-day:]
#     low_min_idx = data['low'].idxmin()
#     high_max_idx = data['high'].idxmax()
#     return (low_min_idx, high_max_idx)
#
# def get_high_close_eod(d, day, close_val, h_bin):
#     data = d[-day:]
#     low_min_idx = data.low.sort_values().index[0] #low nu minimum
#     predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
#     count_i = 0
#     while predicted_high<close_val:
#         #data = data.drop(data.index[low_min_idx])
#         # low_min_idx = data['low'].idxmin()
#         low_min_idx = data.low.sort_values().index[count_i]
#         predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
#         count_i += 1
#         if count_i==day:
#             break
#     if count_i == day:
#         return (float(close_val + ((close_val*h_bin)/100.0)), close_val, "close_val")
#     else:
#         return (float(d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)), low_min_idx, "high_idx_val")
#
# def get_low_close_eod(d, day, close_val, l_bin):
#     data = d[-day:]
#     high_max_idx = data.high.sort_values().index[-1] # high nu maximum
#     predicted_close = d['open'].iloc[high_max_idx] + (d['open'].iloc[high_max_idx]*l_bin)/100.0
#     count_i = 0
#     while predicted_close>=close_val:
#         # print(data.index)
#         # data = data.drop(data.index[high_max_idx-len(d)+day])
#         high_max_idx = data.high.sort_values().index[-(count_i+1)]
#         predicted_close = d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)
#         count_i += 1
#         if count_i==day:
#             break
#     if count_i == day:
#         return (float(close_val + ((close_val*l_bin)/100.0)), close_val, "close_val")
#     else:
#         return (float(d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)), high_max_idx, "low_idx_val")
#
# def get_last_col_api(d, day, latest_api_data):
#     data = d[-(day - 1):]
#     high_ls = []
#     low_ls = []
#     for lad in latest_api_data:
#         # try:
#         if (lad['high'] != None) and (lad['low'] != None):
#             #print(lad['high'])
#             high_ls.append(float(lad['high']))
#             low_ls.append(float(lad['low']))
#
#     # print(high_ls)
#     high_val = float(max(high_ls))
#     low_val = float(min(low_ls))
#     if latest_api_data[0]['open'] != None:
#         open_val = float(latest_api_data[0]['open'])
#     elif latest_api_data[1]['open'] != None:
#         open_val = float(latest_api_data[1]['open'])
#     else:
#         open_val = float(latest_api_data[-1]['open'])
#     data.append([high_val, open_val, low_val])
#     low_min_idx = data['low'].idxmin()
#     high_max_idx = data['high'].idxmax()
#     return (low_min_idx, high_max_idx)
#
# def get_high_close_api(d, day, latest_api_data, close_val, h_bin):
#     data = d[-(day - 1):]
#     high_ls = []
#     low_ls = []
#     for lad in latest_api_data:
#         if (lad['high'] != None) and (lad['low'] != None):
#             high_ls.append(float(lad['high']))
#             low_ls.append(float(lad['low']))
#     high_val = float(max(high_ls))
#     low_val = float(min(low_ls))
#     if latest_api_data[0]['open'] != None:
#         open_val = float(latest_api_data[0]['open'])
#     elif latest_api_data[1]['open'] != None:
#         open_val = float(latest_api_data[1]['open'])
#     else:
#         open_val = float(latest_api_data[-1]['open'])
#     data.append([close_val, high_val, low_val, open_val])
#     low_min_idx = data.low.sort_values().index[0]   ## [4,5,6,3,8,9,10] => [3,8,9,10]
#     # high_max_idx = data['high'].idxmax()
#     predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
#     count_i = 0
#     while predicted_high<close_val:
#         if count_i==day:
#             break
#         # data = data.drop(data.index[low_min_idx-len(d)+day])
#         # low_min_idx = data['low'].idxmin()
#         low_min_idx = data.low.sort_values().index[count_i]
#         predicted_high = d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)
#         count_i += 1
#
#     if count_i == day:
#         return (float(close_val + ((close_val*h_bin)/100.0)), close_val, "close_val")
#     else:
#         return (float(d['open'].iloc[low_min_idx] + ((d['open'].iloc[low_min_idx]*h_bin)/100.0)), low_min_idx, "high_idx_val")
#
# def get_low_close_api(d, day, latest_api_data, close_val, l_bin):
#     data = d[-(day - 1):]
#     high_ls = []
#     low_ls = []
#     for lad in latest_api_data:
#         if (lad['high'] != None) and (lad['low'] != None):
#             high_ls.append(float(lad['high']))
#             low_ls.append(float(lad['low']))
#     high_val = float(max(high_ls))
#     low_val = float(min(low_ls))
#     if latest_api_data[0]['open'] != None:
#         open_val = float(latest_api_data[0]['open'])
#     elif latest_api_data[1]['open'] != None:
#         open_val = float(latest_api_data[1]['open'])
#     else:
#         open_val = float(latest_api_data[-1]['open'])
#     data.append([close_val, high_val, low_val, open_val])
#     # low_min_idx = data['low'].idxmin()
#     high_max_idx = data.high.sort_values().index[-1]
#     predicted_close = d['open'].iloc[high_max_idx] + (d['open'].iloc[high_max_idx]*l_bin)/100.0
#     count_i = 0
#     while predicted_close>=close_val:
#         # data = data.drop(data.index[high_max_idx-len(d)+day])
#         # high_max_idx = data['high'].idxmax()
#         high_max_idx = data.high.sort_values().index[-(count_i+1)]
#         predicted_close = d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)
#         count_i += 1
#         if count_i==day:
#             break
#     if count_i == day:
#         return (float(close_val + ((close_val*l_bin)/100.0)), close_val, "close_val")
#     else:
#         return (float(d['open'].iloc[high_max_idx] + ((d['open'].iloc[high_max_idx]*l_bin)/100.0)), high_max_idx, "low_idx_val")
#
#
# @api_view(['GET', 'POST'])
# def predict_price(request):
#     request = json.loads(request.body.decode('utf-8'))
#     path = "stock_data/media/hist data/"
#     ticker = request['ticker']
#     filter_days = int(request['filter_days'])   #180
#     in_date = datetime.strptime(request['in_date'], "%Y-%m-%d")
#     rolling_value = [5, 10, 20, 60]#5
#     percentage = int(request['percentage'])#65
#     percentages = [90,80,70,60,50,40,30,20]
#     percentages.append(percentage)
#     final_dict = {}
#
#     data = load_data(path, ticker, in_date)
#     url_latest_api = f"https://cloud.iexapis.com/stable/stock/{ticker.lower()}/intraday-prices?token=pk_55e019e9e4db4baaa9493d29a095bf63"
#     response = urlopen(url_latest_api)
#     latest_api_data = json.loads(response.read())
#
#     d_date = datetime.utcnow() - timedelta(hours=4)
#     nw = datetime.now()
#     hrs = nw.hour
#     mins = nw.minute
#     secs = nw.second
#     zero = timedelta(seconds = secs+mins*60+hrs*3600)
#     st = nw - zero # this take me to 0 hours.
#     time1 = st + timedelta(seconds=9*3600+30*60) # this gives 09:30 AM
#     time2 = st + timedelta(seconds=16*3600+1*60) # 04:00 PM
#
#     if d_date.time()>=time1.time() and d_date.time()<=time2.time():
#         # If market is Open
#         for rolling in rolling_value:
#             pred_open_high = []
#             pred_open_low = []
#             h_bins_array = []
#             l_bins_array = []
#             pred_final_open_high = []
#             pred_final_open_low = []
#             month_fixed_high = []
#             month_fixed_low = []
#
#             low_min_idx, high_max_idx = get_last_col_api(data, rolling, latest_api_data)
#             data_last = data[-rolling:]
#             if rolling != 5:
#                 half_roll = int(rolling/2)
#                 open_final_val = data_last['open'].iloc[half_roll+1]
#
#             for idx,percentage in enumerate(percentages):
#                 if idx==0:
#                     #For 90% only calculate the value
#                     d = pd.DataFrame([])
#                     d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#                     high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#                     index, cum_cal = get_cumsum(high_cum, percentage)
#                     h_bin = high_bins[index]
#
#                     low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#                     index, cum_cal = get_cumsum(low_cum, percentage)
#                     l_bin = low_bins[len(low_bins) - index]
#
#                     open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#                     index, cum_cal = get_cumsum(open_cum, percentage)
#                     o_bin = open_bins[index]
#
#                     predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
#                     predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
#                     close_val = float(data.tail(1)['close'])
#
#                     if rolling != 5:
#                         pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
#                         pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
#
#                     if predicted_high>=close_val:
#                         pred_open_high.append(predicted_high)
#                         r_type_high = "high_idx_val"
#                         val_id_high = low_min_idx
#                     else:
#                         p_high, val_id_high, r_type_high = get_high_close_api(data, rolling, latest_api_data, close_val, h_bin)
#                         pred_open_high.append(p_high)
#
#                     if predicted_low<close_val:
#                         pred_open_low.append(predicted_low)
#                         r_type_low = "low_idx_val"
#                         val_id_low = high_max_idx
#                     else:
#                         p_low, val_id_low, r_type_low = get_low_close_api(data, rolling, latest_api_data, close_val, l_bin)
#                         pred_open_low.append(p_low)
#                 else:
#                     #For every other percentage
#                     d = pd.DataFrame([])
#                     d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#                     high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#                     index, cum_cal = get_cumsum(high_cum, percentage)
#                     h_bin = high_bins[index]
#
#                     low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#                     index, cum_cal = get_cumsum(low_cum, percentage)
#                     l_bin = low_bins[len(low_bins) - index]
#
#                     open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#                     index, cum_cal = get_cumsum(open_cum, percentage)
#                     o_bin = open_bins[index]
#                     close_val = float(data.tail(1)['close'])
#
#                     if rolling != 5:
#                         pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
#                         pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
#
#                     if r_type_high == "high_idx_val":
#                         predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
#                         val_l = data['open'].iloc[val_id_high]
#
#                     else:
#                         predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
#                         val_l = val_id_high
#
#                     if r_type_low == "low_idx_val":
#                         predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
#                         val_h = data['open'].iloc[val_id_low]
#                     else:
#                         predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
#                         val_h = val_id_low
#                     pred_open_high.append(predicted_high)
#                     pred_open_low.append(predicted_low)
#
#                 if rolling == 20:
#                     open_val_cal = float(data.tail(1)['close'])
#                     month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
#                     month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
#
#                 h_bins_array.append(h_bin)
#                 l_bins_array.append(l_bin)
#
#             median = get_median(d)[2]
#             standard_deviation = get_std(d)[2]
#
#             first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
#             second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
#             third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
#
#             first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
#             second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
#             third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
#             if rolling != 5:
#                 pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
#                 pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
#                 pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
#
#             if rolling == 20:
#                 open_val_cal = float(data.tail(1)['close'])
#                 month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
#                 month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
#                 month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
#
#             if rolling == 5:
#                 final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":[], "fixed_predicted_low":[], "fixed_predicted_first_std":[], "fixed_predicted_second_std":[], "fixed_predicted_third_std":[]}
#             elif rolling == 20:
#                 final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS, "month_fixed_high":month_fixed_low[::-1], "month_fixed_low":month_fixed_high[::-1], "month_pred_final_FS":month_pred_final_FS, "month_pred_final_SS":month_pred_final_SS, "month_pred_final_TS":month_pred_final_TS}
#             else:
#                 final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS}
#
#     else:
#         #If market is Close
#         for rolling in rolling_value:
#             #print(rolling)
#             pred_open_high = []
#             pred_open_low = []
#             h_bins_array = []
#             l_bins_array = []
#             pred_final_open_high = []
#             pred_final_open_low = []
#             month_fixed_high = []
#             month_fixed_low = []
#             low_min_idx, high_max_idx = get_last_col(data, rolling)
#             data_last = data[-rolling:]
#             if rolling != 5:
#                 half_roll = int(rolling/2)
#                 open_final_val = data_last['open'].iloc[half_roll+1]
#
#             for idx,percentage in enumerate(percentages):
#                 if idx==0:
#                     #For 90% only calculate the value
#                     d = pd.DataFrame([])
#                     d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#                     high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#                     index, cum_cal = get_cumsum(high_cum, percentage)
#                     h_bin = high_bins[index]
#
#                     low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#                     index, cum_cal = get_cumsum(low_cum, percentage)
#                     l_bin = low_bins[len(low_bins) - index]
#
#                     open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#                     index, cum_cal = get_cumsum(open_cum, percentage)
#                     o_bin = open_bins[index]
#
#                     predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
#                     predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
#                     print(data.tail(1))
#                     close_val = float(data.tail(1)['close'])
#
#                     if rolling != 5:
#                         pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
#                         pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
#
#                     if predicted_high>=close_val:
#                         pred_open_high.append(predicted_high)
#                         r_type_high = "high_idx_val"
#                         val_id_high = low_min_idx
#                     else:
#                         p_high, val_id_high, r_type_high = get_high_close_eod(data, rolling, close_val, h_bin)
#                         pred_open_high.append(p_high)
#
#                     if predicted_low<close_val:
#                         pred_open_low.append(predicted_low)
#                         r_type_low = "low_idx_val"
#                         val_id_low = high_max_idx
#                     else:
#                         p_low, val_id_low, r_type_low = get_low_close_eod(data, rolling, close_val, l_bin)
#                         pred_open_low.append(p_low)
#
#
#                 else:
#                     #For every other percentage
#                     d = pd.DataFrame([])
#                     d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#                     high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#                     index, cum_cal = get_cumsum(high_cum, percentage)
#                     h_bin = high_bins[index]
#
#                     low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#                     index, cum_cal = get_cumsum(low_cum, percentage)
#                     l_bin = low_bins[len(low_bins) - index]
#
#                     open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#                     index, cum_cal = get_cumsum(open_cum, percentage)
#                     o_bin = open_bins[index]
#                     close_val = float(data.tail(1)['close'])
#
#                     if rolling != 5:
#                         pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
#                         pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
#
#                     if r_type_high == "high_idx_val":
#                         predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
#                         val_l = data['open'].iloc[val_id_high]
#                     else:
#                         predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
#                         val_l = val_id_high
#
#                     if r_type_low == "low_idx_val":
#                         predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
#                         val_h = data['open'].iloc[val_id_low]
#                     else:
#                         predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
#                         val_h = val_id_low
#                     pred_open_high.append(predicted_high)
#                     pred_open_low.append(predicted_low)
#
#                 if rolling == 20:
#                     open_val_cal = float(data.tail(1)['close'])
#                     month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
#                     month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
#
#                 h_bins_array.append(h_bin)
#                 l_bins_array.append(l_bin)
#
#             median = get_median(d)[2]
#             standard_deviation = get_std(d)[2]
#
#             first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
#             second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
#             third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
#
#             first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
#             second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
#             third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
#
#             if rolling != 5:
#                 pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
#                 pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
#                 pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
#
#             if rolling == 20:
#                 open_val_cal = float(data.tail(1)['close'])
#                 month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
#                 month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
#                 month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
#
#             if rolling == 5:
#                 final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":[], "fixed_predicted_low":[], "fixed_predicted_first_std":[], "fixed_predicted_second_std":[], "fixed_predicted_third_std":[]}
#             elif rolling == 20:
#                 final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS, "month_fixed_high":month_fixed_low[::-1], "month_fixed_low":month_fixed_high[::-1], "month_pred_final_FS":month_pred_final_FS, "month_pred_final_SS":month_pred_final_SS, "month_pred_final_TS":month_pred_final_TS}
#             else:
#                 final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS}
#
#     return HttpResponse(json.dumps(final_dict, indent=4,default=str),content_type = "application/json")
#
#
# #=============================================================---------++++++------------+++++++-----------++++++---------=========================================================================================
#
# def predict_price_csv(data, filter_days, percentage):
#     filter_days = int(filter_days)  #180
#     rolling_value = [5, 10, 20, 60]#5
#     percentage = int(percentage)#65
#     percentages = [90,80,70,60,50,40,30,20]
#     percentages.append(percentage)
#     final_dict = {}
#     today = date.today()
#     in_date = today.strftime("%Y-%m-%d")
#     in_date = datetime.strptime(in_date, "%Y-%m-%d")
#     data = data
#     d_date = datetime.utcnow() - timedelta(hours=4)
#     for rolling in rolling_value:
#         print(f"===================================={rolling}")
#         pred_open_high = []
#         pred_open_low = []
#         h_bins_array = []
#         l_bins_array = []
#         pred_final_open_high = []
#         pred_final_open_low = []
#         month_fixed_high = []
#         month_fixed_low = []
#
#         low_min_idx, high_max_idx = get_last_col(data, rolling)
#         data_last = data[-rolling:]
#
#         if rolling != 5:
#             half_roll = int(rolling/2)
#             open_final_val = data_last['open'].iloc[half_roll+1]
#
#         for idx,percentage in enumerate(percentages):
#             if idx==0:
#                 #For 90% only calculate the value
#                 d = pd.DataFrame([])
#                 d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#                 print(d)
#                 high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#                 index, cum_cal = get_cumsum(high_cum, percentage)
#                 h_bin = high_bins[index]
#
#                 low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#                 index, cum_cal = get_cumsum(low_cum, percentage)
#                 l_bin = low_bins[len(low_bins) - index]
#
#                 open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#                 index, cum_cal = get_cumsum(open_cum, percentage)
#                 o_bin = open_bins[index]
#
#                 predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
#                 predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
#                 # print(data.tail(1))
#                 close_val = float(data.tail(1)['close'])
#
#                 if rolling != 5:
#                     pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
#                     pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
#
#                 if predicted_high>=close_val:
#                     pred_open_high.append(predicted_high)
#                     r_type_high = "high_idx_val"
#                     val_id_high = low_min_idx
#                 else:
#                     p_high, val_id_high, r_type_high = get_high_close_eod(data, rolling, close_val, h_bin)
#                     pred_open_high.append(p_high)
#
#                 if predicted_low<close_val:
#                     pred_open_low.append(predicted_low)
#                     r_type_low = "low_idx_val"
#                     val_id_low = high_max_idx
#                 else:
#                     p_low, val_id_low, r_type_low = get_low_close_eod(data, rolling, close_val, l_bin)
#                     pred_open_low.append(p_low)
#
#
#             else:
#                 #For every other percentage
#                 d = pd.DataFrame([])
#                 d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#                 high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#                 index, cum_cal = get_cumsum(high_cum, percentage)
#                 h_bin = high_bins[index]
#
#                 low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#                 index, cum_cal = get_cumsum(low_cum, percentage)
#                 l_bin = low_bins[len(low_bins) - index]
#
#                 open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#                 index, cum_cal = get_cumsum(open_cum, percentage)
#                 o_bin = open_bins[index]
#                 close_val = float(data.tail(1)['close'])
#
#                 if rolling != 5:
#                     pred_final_open_high.append(open_final_val + ((open_final_val*h_bin)/100.0))
#                     pred_final_open_low.append(open_final_val + ((open_final_val*l_bin)/100.0))
#
#                 if r_type_high == "high_idx_val":
#                     predicted_high = data['open'].iloc[val_id_high] + ((data['open'].iloc[val_id_high]*h_bin)/100.0)
#                     val_l = data['open'].iloc[val_id_high]
#                 else:
#                     predicted_high = val_id_high + ((val_id_high*h_bin)/100.0)
#                     val_l = val_id_high
#
#                 if r_type_low == "low_idx_val":
#                     predicted_low = data['open'].iloc[val_id_low] + (data['open'].iloc[val_id_low]*l_bin)/100.0
#                     val_h = data['open'].iloc[val_id_low]
#                 else:
#                     predicted_low = val_id_low + ((val_id_low*l_bin)/100.0)
#                     val_h = val_id_low
#                 pred_open_high.append(predicted_high)
#                 pred_open_low.append(predicted_low)
#
#             if rolling == 20:
#                 open_val_cal = float(data.tail(1)['close'])
#                 month_fixed_high.append(open_val_cal + ((open_val_cal*l_bin)/100.0))
#                 month_fixed_low.append(open_val_cal + ((open_val_cal*h_bin)/100.0))
#
#             h_bins_array.append(h_bin)
#             l_bins_array.append(l_bin)
#
#         median = get_median(d)[2]
#         standard_deviation = get_std(d)[2]
#
#         first_std = [(median + standard_deviation)*100, (median - standard_deviation)*100]
#         second_std = [(median + 2*standard_deviation)*100, (median - 2*standard_deviation)*100]
#         third_std = [(median + 3*standard_deviation)*100, (median - 3*standard_deviation)*100]
#
#         first_SD = [val_l + (val_l*first_std[0])/100.0, val_h + (val_h*first_std[1])/100.0]
#         second_SD = [val_l + (val_l*second_std[0])/100.0, val_h + (val_h*second_std[1])/100.0]
#         third_SD = [val_l + (val_l*third_std[0])/100.0, val_h + (val_h*third_std[1])/100.0]
#
#         if rolling != 5:
#             pred_final_FS = [open_final_val + (open_final_val*first_std[0])/100.0, open_final_val + (open_final_val*first_std[1])/100.0]
#             pred_final_SS = [open_final_val + (open_final_val*second_std[0])/100.0, open_final_val + (open_final_val*second_std[1])/100.0]
#             pred_final_TS = [open_final_val + (open_final_val*third_std[0])/100.0, open_final_val + (open_final_val*third_std[1])/100.0]
#
#         if rolling == 20:
#             open_val_cal = float(data.tail(1)['close'])
#             month_pred_final_FS = [open_val_cal + (open_val_cal*first_std[0])/100.0, open_val_cal + (open_val_cal*first_std[1])/100.0]
#             month_pred_final_SS = [open_val_cal + (open_val_cal*second_std[0])/100.0, open_val_cal + (open_val_cal*second_std[1])/100.0]
#             month_pred_final_TS = [open_val_cal + (open_val_cal*third_std[0])/100.0, open_val_cal + (open_val_cal*third_std[1])/100.0]
#
#         if rolling == 5:
#             final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":[], "fixed_predicted_low":[], "fixed_predicted_first_std":[], "fixed_predicted_second_std":[], "fixed_predicted_third_std":[]}
#         elif rolling == 20:
#             final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS, "month_fixed_high":month_fixed_low[::-1], "month_fixed_low":month_fixed_high[::-1], "month_pred_final_FS":month_pred_final_FS, "month_pred_final_SS":month_pred_final_SS, "month_pred_final_TS":month_pred_final_TS}
#         else:
#             final_dict[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1], "first_percent":first_std, "second_percent":second_std, "third_percent":third_std, "first":first_SD, "second":second_SD, "third":third_SD,"percentage":percentages[::-1], "OtoHpercent":h_bins_array[::-1], "OtoLpercent":l_bins_array[::-1], "fixed_predicteed_high":pred_final_open_high[::-1], "fixed_predicted_low":pred_final_open_low[::-1], "fixed_predicted_first_std":pred_final_FS, "fixed_predicted_second_std":pred_final_SS, "fixed_predicted_third_std":pred_final_TS}
#     return final_dict
#
#
# @api_view(['GET', 'POST'])
# def upload_csv(request):
#     if request.method == 'POST':
#         option = request.FILES['option']
#         if os.path.isfile(f"stock_data/media/uploaded_prediction_file/{option.name}"):
#             os.remove(f"stock_data/media/uploaded_prediction_file/{option.name}")
#         fs1 = FileSystemStorage(location=f"stock_data/media/uploaded_prediction_file/")
#         fs1.save(option.name, option)
#
#         filter_days = int(request.POST.get('filter_days'))
#         percentage = int(request.POST.get('percentage'))
#
#         data = pd.read_csv(f'stock_data/media/uploaded_prediction_file/{option.name}', parse_dates=['date'])
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
#         month = int(request["month"])
#         strike_perc = int(request["strike_percent"])
#         date = request["date"]
#
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
#         filter_days = str(request["filter_days"])
#
#         formated_date = date.split("-")
#         #datadate = datetime(int(formated_date[0]), int(formated_date[1]), int(formated_date[2]))
#         final_date = formated_date[0] + formated_date[1] + formated_date[2]
#         if filter_days == "180" or filter_days == "720":
#             path = "stock_data/media/invex_ratio_daily/invex_"+ filter_days + "_" +str(final_date) + ".json"
#         else:
#             path = "stock_data/media/invex_ratio_daily/invex_max_" +str(final_date) + ".json"
#
#         df_quote = pd.read_csv(f'stock_data/media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_stockquotes_{str(final_date)}.csv')
#
#         file = open(path,"r")
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
#                 #print(rolling)
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
#                     if r <= month:
#
#                         filter_s = s[(s["Strike_"+str(r)]>=lower_value) & (s["Strike_"+str(r)]<=higher_value)]
#                         strike = filter_s["Strike_"+str(r)].values
#                         call_ir = filter_s["Invex_ratio_call_"+str(r)].mean()
#                         put_ir = filter_s["Invex_ratio_put_"+str(r)].mean()
#                         cp_ratio = filter_s["CP_ratio_"+str(r)].mean()
#                         cp_ratio_median = filter_s['CP_ratio_'+str(r)].median()
#                         hvtf = filter_s["HVTF_put_" + str(r)].iloc[0]
#                         # com["Expiration"] = filter_s["Expiration"]
#
#                         call_array += call_ir
#                         put_array += put_ir
#                         cp += (call_ir/put_ir)
#                         hvtf_array += hvtf
#                         cp_median.append(call_ir/put_ir)
#
#                         com[e[0]]=[call_ir, put_ir, call_ir/put_ir, call_ir/put_ir, hvtf]
#                         len_roll += 1
#             except:
#                 continue
#             try:
#                 call_array = call_array/len_roll
#                 put_array = put_array/len_roll
#                 cp = cp/len_roll
#                 hvtf_array = hvtf_array/len_roll
#                 cp_m = statistics.median(cp_median)
#             except:
#                 continue
#
#             if (call_array>call_min and call_array<call_max) and (put_array>put_min and put_array<put_max) and (cp_m>cp_min and cp_m<cp_max):
#                 close_val = df_quote[df_quote['symbol']=='AAPL']['adjustedclose'].values[0]
#                 com["total"] = [call_array, put_array, cp, cp_m, hvtf_array, close_val]
#                 final_data[symbol] = com
#
#         file.close()
#         return HttpResponse(json.dumps(final_data, indent=4,default=str),content_type = "application/json")
#
#
# @api_view(['GET', 'POST'])
# def graph(request):
#     path = "stock_data/media/graph_data/final_graph_2.json"
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
#         fs = FileSystemStorage(location=f"stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/")
#         fs.save(option.name, option)
#         dir_path = f"stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/"
#         df_chunk = vaex.open(dir_path + option.name)
#
#         fs1 = FileSystemStorage(location=f"stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/")
#         fs1.save(optionstat.name, optionstat)
#
#         fs2 = FileSystemStorage(location=f"stock_data/media/option_data/Option Data/Historical/{file_year}/{str(file_month)}/")
#         fs2.save(optionquotes.name, optionquotes)
#
#         return HttpResponse("File uploaded successfully")
#     else:
#         curr_month = datetime.now().month
#         curr_year = str(int(datetime.now().year))
#         dirpath = f'stock_data/media/option_data/Option Data/Historical/{curr_year}/'
#         input_path = Path("stock_data/media/option_data/Option Data/Historical/")
#         dirls = list(input_path.rglob("*.csv"))
#         # dirpath = f'{dirpath}{str(curr_month)}'
#         options_ls = []
#         stockquotes_ls = []
#         optionstats_ls = []
#         for r, d, f in os.walk(dirpath):
#             for filename in f:
#                 if filename.split('.')[1] == 'csv':
#                     print(str(filename))
#                     filepath = os.path.join(dirpath + str(int(filename.split('_')[2][4:6])) +"/", filename)
#                     dirls.append(filepath)
#                     # print(filename.split('.'))
#                     if filename.split('_')[1] == 'options' and filename.split('.')[-1] == 'csv':
#                         options_ls.append(filename)
#                     elif filename.split('_')[1] == 'stockquotes':
#                         stockquotes_ls.append(filename)
#                     elif filename.split("_")[1] == 'optionstats':
#                         optionstats_ls.append(filename)
#                     else:
#                         continue
#         print(f'=========================           {options_ls}       {stockquotes_ls}     {stockquotes_ls}')
#
#         if not dirls:
#             print('not')
#             return render(request, 'upload.html', {"data":"No Files till now", "options_ls":options_ls[::-1], "optionstats_ls":optionstats_ls[::-1], "stockquotes_ls":stockquotes_ls[::-1], "file_names":zip(options_ls[::-1], optionstats_ls[::-1], stockquotes_ls[::-1])})
#         else:
#             latest_file = max(dirls, key=os.path.getctime)
#             l_f = str(latest_file).split("/")[-1]
#             options_ls.sort()
#             optionstats_ls.sort()
#             stockquotes_ls.sort()
#             return render(request, 'upload.html', {"data":l_f, "options_ls":options_ls[::-1], "optionstats_ls":optionstats_ls[::-1], "stockquotes_ls":stockquotes_ls[::-1], "file_names":zip(options_ls[::-1], optionstats_ls[::-1], stockquotes_ls[::-1])})
#
#
# def download_file(request):
#     if request.method == "POST":
#         file_year = str(request.POST.get('year'))
#         file_month = str(request.POST.get('month')).zfill(2)
#         file_day = str(request.POST.get('day')).zfill(2)
#         file_type = str(request.POST.get('file_type')) #options / optionstats / stockquotes (create dropdown)
#         #L3_optionstats_20211006
#         filename = 'L3_'+file_type+'_'+file_year+file_month+file_day+'.csv'
#         filepath =  f'/home/cp2invexwealth/pythonDir/stock_data/media/option_data/Option Data/Historical/{file_year}/{int(file_month)}/{filename}'
#         if os.path.isfile(filepath):
#             path = open(filepath, 'rb')
#             mime_type, _ = mimetypes.guess_type(filepath)
#             response = HttpResponse(path, content_type=mime_type)
#             response['Content-Disposition'] = "attachment; filename=%s" % filename
#             return response
#         else:
#             return HttpResponse('Sorry File does not Exists!!!')
#     else:
#         return render(request, 'download_file.html')
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
# @api_view(['GET', 'POST'])
# def website_quote(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     ticker = request["ticker"]
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     data = {}
#     df = pd.read_csv(f"stock_data/media/option_data/Option Data/Historical/{date_string[0:4]}/{str(int(date_string[4:6]))}/L3_optionstats_{date_string}.csv")
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
#             week = pd.read_csv(f"stock_data/media/option_data/Option Data/Historical/{week_ago[0:4]}/{str(int(week_ago[4:6]))}/L3_optionstats_{week_ago}.csv")
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
#             a_month = pd.read_csv(f"stock_data/media/option_data/Option Data/Historical/{a_month_ago[0:4]}/{str(int(a_month_ago[4:6]))}/L3_optionstats_{a_month_ago}.csv")
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
#             three_month = pd.read_csv(f"stock_data/media/option_data/Option Data/Historical/{three_month_ago[0:4]}/{str(int(three_month_ago[4:6]))}/L3_optionstats_{three_month_ago}.csv")
#             three_month = three_month[three_month["symbol"] == ticker]
#             break
#         except:
#             i = i+1
#             three_month_ago = str(date_time - timedelta(days=90-i))          ### if any change in days then Put same value as used in three_month_ago (90)
#             three_month_ago = three_month_ago.split(" ")[0].replace("-", "")
#             print(three_month_ago)
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
#     #         temp = pd.read_csv(f"stock_data/media/option_data/Option Data/Historical/{y[0:4]}/{str(int(y[4:6]))}/L3_optionstats_{y}.csv")
#     #         temp = temp[temp["symbol"] == ticker]
#     #         one_year = pd.concat([one_year, temp])
#     #     except:
#     #         pass
#     # #
#     # one_year = one_year.reset_index(drop=True)
#     # one_year["quotedate"] = pd.to_datetime(one_year["quotedate"], format="%m/%d/%Y")
#     # one_year.to_csv(f'stock_data/media/website/quote/{ticker}.csv')
#
#     one_year = pd.read_csv(f"stock_data/media/website/quote/{ticker}.csv")
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
#     df2 = pd.read_csv(f"stock_data/media/hist data/{ticker}.csv")
#     df2["date"] = pd.to_datetime(df2["date"], format="%Y-%m-%d")
#
#     ## For Current HV
#     days = [30,60,90,120,150,180,360]
#     start_date = date.replace("/", "-")
#     current_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(date_time - timedelta(x)).split(" ")[0]) & (df2["date"] <= start_date)].reset_index(drop=True)
#         current_hv = round(((current_hv_df["high"].max() - current_hv_df["low"].min()) / current_hv_df["open"][len(current_hv_df)-1])*100, 2)
#         current_hv_dict[f"{x}_Days"] = current_hv
#     #     print(current_hv_df)
#
#     ## For one Week Ago HV
#     modify_date = date_time - timedelta(7)
#     one_week_ago_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((current_hv_df["high"].max() - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         one_week_ago_hv_dict[f"{x}_Days"] = current_hv
#
#
#     ## For one Month Ago HV
#     modify_date = date_time - timedelta(30)
#     one_month_ago_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((current_hv_df["high"].max() - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         one_month_ago_hv_dict[f"{x}_Days"] = current_hv
#
#
#     ## For Three Month Ago HV
#     modify_date = date_time - timedelta(90)
#     three_month_ago_hv_dict = {}
#     for x in days:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((current_hv_df["high"].max() - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
#         three_month_ago_hv_dict[f"{x}_Days"] = current_hv
#
#     data["Historical_Volatility"] = {
#         "Current_HV" : current_hv_dict,
#         "1_Week_Ago" : one_week_ago_hv_dict,
#         "1_Month_Ago" : one_month_ago_hv_dict,
#         "3_Month_Ago" : three_month_ago_hv_dict,
#     }
#
#
#
#     ## For Historical Volatility
#     ## For 365 days of IV
#     d = str(date_time - timedelta(28)).split(" ")[0]                 ## For one year used 365
#     y = d.replace("-", "")
#     temp = pd.read_csv(f"stock_data/media/option_data/Option Data/Historical/{y[0:4]}/{str(int(y[4:6]))}/L3_optionstats_{y}.csv")
#     temp = temp[temp["symbol"] == ticker]
#
#     ## For 365 days of HV
#     modify_date = date_time - timedelta(365)
#     one_year_ago_hv_dict = {}
#     for x in days[:1]:
#         current_hv_df = df2[(df2["date"] >= str(modify_date - timedelta(x)).split(" ")[0]) & (df2["date"] <= modify_date)].reset_index(drop=True)
#         current_hv = round(((current_hv_df["high"].max() - current_hv_df["low"].min()) / df2[df2["date"] == start_date]["open"].values[0])*100, 2)
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
#     return HttpResponse(json.dumps(data, indent=4, cls=NpEncoder), content_type="application/json")
#     # return data
#
#
# # def website_quote(request):
# #     datadate = '20220103'
# #     ticker = 'AAPL'
# #     filename = f'media/option_data/Option Data/Historical/{datadate[0:4]}/str(int(datadate[4:6]))/L3_optionstats_{datadate}.csv'
# #     final_out = {}
#
# #     #filter symbol data only
# #     optionstats_data = pd.read_csv(filename)
# #     optionstats_data = optionstats_data[optionstats_data['symbol']==ticker]
#
# #     # iv = 30,60,90
# #     final_out['volatility'] = {'iv': [optionstats_data['iv30mean'], optionstats_data['iv60mean'], optionstats_data['iv90mean']], 'hv': []}
# #     # total = volume => call,put,total
# #     # total = OI => call,put,total
# #     final_out['total'] = {'volume': [optionstats_data['callvol'], optionstats_data['putvol'], optionstats_data['totalvol']], 'oi': [optionstats_data['calloi'], optionstats_data['putoi'], optionstats_data['totaloi']]}
#
#
#
# # website market
# @api_view(['GET', 'POST'])
# def most_active_options(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     df = main_df.sort_values(by='totalvol', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     symbol = list(df["symbol"])
#     most_active_options= pd.DataFrame()
#
#      ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#             except:
#                 pass
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#             except:
#                 pass
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#             except:
#                 pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     most_active_options["Symbol"] = symbol
#     most_active_options["Last"] = last
#     most_active_options["volume"] = df["totalvol"]
#     most_active_options["1_day_change"] = day_change
#     most_active_options["Weekly_change"] = week_change
#     most_active_options["Monthly_change"] = month_change
#     most_active_options["Quarterly_change"] = quarter_change
#
#     return HttpResponse(json.dumps(most_active_options, indent=4, cls=NpEncoder), content_type="application/json")
#
#
# @api_view(['GET', 'POST'])
# def highest_implied_volatility(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     day_list = request['day_list']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     column = f"iv{day_list}mean"
#     df = main_df.sort_values(by=column, ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     symbol = list(df["symbol"])
#     highest_implied_volatility = pd.DataFrame()
#
#      ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
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
#     highest_implied_volatility["1_day_change"] = day_change
#     highest_implied_volatility["Weekly_change"] = week_change
#     highest_implied_volatility["Monthly_change"] = month_change
#     highest_implied_volatility["Quarterly_change"] = quarter_change
#
#     return HttpResponse(json.dumps(highest_implied_volatility, indent=4, cls=NpEncoder), content_type="application/json")
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
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     column = f"iv{day_list}mean"
#     df = main_df.sort_values(by=column, ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     exploding_IV = pd.DataFrame()
#     symbol = list(df["symbol"])
#
#      ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
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
#     exploding_IV["1_day_change"] = day_change
#     exploding_IV["Weekly_change"] = week_change
#     exploding_IV["Monthly_change"] = month_change
#     exploding_IV["Quarterly_change"] = quarter_change
#     exploding_IV = exploding_IV.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#
#     return HttpResponse(json.dumps(exploding_IV, indent=4, cls=NpEncoder), content_type="application/json")
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
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     column = f"iv{day_list}mean"
#     df = main_df.sort_values(by=column, ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     imploding_IV = pd.DataFrame()
#     symbol = list(df["symbol"])
#
#      ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
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
#     imploding_IV["1_day_change"] = day_change
#     imploding_IV["Weekly_change"] = week_change
#     imploding_IV["Monthly_change"] = month_change
#     imploding_IV["Quarterly_change"] = quarter_change
#     imploding_IV = imploding_IV.sort_values(by=order_data, ascending=True).reset_index(drop=True)
#
#     return HttpResponse(json.dumps(imploding_IV, indent=4, cls=NpEncoder), content_type="application/json")
#
#
#
#
# @api_view(['GET', 'POST'])
# def option_volume_gainers(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     df = main_df.sort_values(by='totalvol', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     symbol = list(df["symbol"])
#     option_volume_gainers= pd.DataFrame()
#
#      ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#             except:
#                 pass
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#             except:
#                 pass
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#             except:
#                 pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_volume_gainers["Symbol"] = symbol
#     option_volume_gainers["Last"] = last
#     option_volume_gainers["volume"] = df["totalvol"]
#     option_volume_gainers["1_day_change"] = day_change
#     option_volume_gainers["Weekly_change"] = week_change
#     option_volume_gainers["Monthly_change"] = month_change
#     option_volume_gainers["Quarterly_change"] = quarter_change
#
#     option_volume_gainers = option_volume_gainers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#     return HttpResponse(json.dumps(option_volume_gainers, indent=4, cls=NpEncoder), content_type="application/json")
#
#
# @api_view(['GET', 'POST'])
# def option_volume_losers(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     df = main_df.sort_values(by='totalvol', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     symbol = list(df["symbol"])
#     option_volume_losers= pd.DataFrame()
#
#      ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = day[day["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = week[week["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#             except:
#                 pass
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = month[month["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#             except:
#                 pass
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = quarter[quarter["symbol"] == y]["totalvol"].values[0]
#                     new = df[df["symbol"] == y]["totalvol"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#             except:
#                 pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_volume_losers["Symbol"] = symbol
#     option_volume_losers["Last"] = last
#     option_volume_losers["volume"] = df["totalvol"]
#     option_volume_losers["1_day_change"] = day_change
#     option_volume_losers["Weekly_change"] = week_change
#     option_volume_losers["Monthly_change"] = month_change
#     option_volume_losers["Quarterly_change"] = quarter_change
#
#     option_volume_losers = option_volume_losers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#     return HttpResponse(json.dumps(option_volume_losers, indent=4, cls=NpEncoder), content_type="application/json")
#
# @api_view(['GET', 'POST'])
# def option_open_interest_gainers(request):
#     request = json.loads(request.body.decode('utf-8'))
#     date = request["date"]
#     order_data = request['order_data']
#     date_time = pd.to_datetime(date,format='%Y/%m/%d')
#     date_string = date.replace("/", "")
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     df = main_df.sort_values(by='totaloi', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     symbol = list(df["symbol"])
#     option_open_interest_gainers= pd.DataFrame()
#
#      ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = week[week["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#             except:
#                 pass
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = month[month["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#             except:
#                 pass
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = quarter[quarter["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#             except:
#                 pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_open_interest_gainers["Symbol"] = symbol
#     option_open_interest_gainers["Last"] = last
#     option_open_interest_gainers["volume"] = df["totaloi"]
#     option_open_interest_gainers["1_day_change"] = day_change
#     option_open_interest_gainers["Weekly_change"] = week_change
#     option_open_interest_gainers["Monthly_change"] = month_change
#     option_open_interest_gainers["Quarterly_change"] = quarter_change
#
#     option_open_interest_gainers = option_open_interest_gainers.sort_values(by=order_data, ascending=False).reset_index(drop=True)
#
#     return HttpResponse(json.dumps(option_open_interest_gainers, indent=4, cls=NpEncoder), content_type="application/json")
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
#     main_df = pd.read_csv(f"all/L3_optionstats_{date_string}.csv")
#     df = main_df.sort_values(by='totaloi', ascending=False)
#     df = df.reset_index(drop=True)
#     df = df.head(10)
#     symbol = list(df["symbol"])
#     option_open_interest_losers= pd.DataFrame()
#
#     ## Last
#     last = []
#     for x in symbol:
#         try:
#             default = pd.read_json(f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{x.lower()}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             last.append(default["close"].loc[len(default)-1])
#         except:
#             last.append(np.NaN)
#
#     ## Daily Change
#     day_change = []
#     day_ago = str(date_time - timedelta(days=1)).split(" ")[0].replace("-", "")
#     i = 0
#     while True:
#         try:
#             day = pd.read_csv(f"all/L3_optionstats_{day_ago}.csv")
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
#             week = pd.read_csv(f"all/L3_optionstats_{week_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = week[week["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     week_change.append(difference)
#             except:
#                 pass
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
#             month = pd.read_csv(f"all/L3_optionstats_{month_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = month[month["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     month_change.append(difference)
#             except:
#                 pass
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
#             quarter = pd.read_csv(f"all/L3_optionstats_{quarter_ago}.csv")
#             try:
#                 for y in symbol:
#                     old = quarter[quarter["symbol"] == y]["totaloi"].values[0]
#                     new = df[df["symbol"] == y]["totaloi"].values[0]
#                     difference = round(((new - old)/new)*100, 2)
#                     quarter_change.append(difference)
#             except:
#                 pass
#             break
#         except:
#             i = i+1
#             quarter_ago = str(date_time - timedelta(days=90+i)).split(" ")[0].replace("-", "")         ### if any change in days then Put same value as used in a_quarter_ago (30)
#             pass
#     option_open_interest_losers["Symbol"] = symbol
#     option_open_interest_losers["Last"] = last
#     option_open_interest_losers["volume"] = df["totaloi"]
#     option_open_interest_losers["1_day_change"] = day_change
#     option_open_interest_losers["Weekly_change"] = week_change
#     option_open_interest_losers["Monthly_change"] = month_change
#     option_open_interest_losers["Quarterly_change"] = quarter_change
#
#     option_open_interest_losers = option_open_interest_losers.sort_values(by=order_data, ascending=True).reset_index(drop=True)
#
#     return HttpResponse(json.dumps(option_open_interest_losers, indent=4, cls=NpEncoder), content_type="application/json")
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# # OLD total function working completely
# # def total(request):
# #     if request.method == "POST":
# #         request = json.loads(request.body.decode('utf-8'))
# #         month = int(request["month"])
# #         strike_perc = int(request["strike_percent"])
# #         date = request["date"]
#
# #         calls = request["call_value"]
# #         call_min = float(calls.split('_')[0])
# #         call_max = float(calls.split('_')[1])
#
# #         puts = request["put_value"]
# #         put_min = float(puts.split('_')[0])
# #         put_max = float(puts.split('_')[1])
#
# #         cps = request["cp_value"]
# #         cp_min = float(cps.split('_')[0])
# #         cp_max = float(cps.split('_')[1])
#
# #         formated_date = date.split("-")
# #         final_date = formated_date[0] + formated_date[1] + formated_date[2]
# #         file = open("stock_data/media/invex_ratio_daily/final_invex_avg_"+str(final_date) + ".json","r")
# #         data = json.load(file)
#
# #         final_data = {}
# #         #strike_perc = 30
# #         #month = 200
# #         symbols = data.keys()
#
# #         for symbol in symbols:
# #             try:
# #                 arr = []
# #                 s = pd.DataFrame(data[symbol])
# #                 current_price = float(s.iloc[0,0])
# #                 rol_value = s["0"]
# #                 arr = pd.DataFrame(rol_value)
# #                 rolling = arr.dropna()
# #                 rolling = pd.to_numeric(rolling["0"])
# #                 rolling = rolling[1:].astype(int)
# #                 #print(rolling)
#
# #                 exp_value = s["Expiration"]
# #                 arr2 = pd.DataFrame(exp_value)
# #                 expiration = arr2.dropna()
# #                 expiration = expiration[:-1]
#
# #                 lower_value = float(current_price - ((current_price*(strike_perc / 10))/10.0))
# #                 higher_value = float(current_price + ((current_price*(strike_perc / 10))/10.0))
#
# #                 call_array = 0.0
# #                 put_array = 0.0
# #                 cp = 0.0
# #                 hvtf_array = 0.0
# #                 len_roll = 0
# #                 com = {}
# #                 for r,e in zip(rolling,expiration.values):
# #                     if r <= month:
#
# #                         filter_s = s[(s["Strike_"+str(r)]>=lower_value) & (s["Strike_"+str(r)]<=higher_value)]
# #                         strike = filter_s["Strike_"+str(r)].values
# #                         call_ir = filter_s["Invex_ratio_call_"+str(r)].mean()
# #                         put_ir = filter_s["Invex_ratio_put_"+str(r)].mean()
# #                         cp_ratio = filter_s["CP_ratio_"+str(r)].mean()
# #                         hvtf = filter_s["HVTF_put_" + str(r)].iloc[0]
# #                         # com["Expiration"] = filter_s["Expiration"]
#
# #                         call_array += call_ir
# #                         put_array += put_ir
# #                         cp += cp_ratio
# #                         hvtf_array += hvtf
#
# #                         com[e[0]]=[call_ir, put_ir, cp_ratio, hvtf]
# #                         len_roll += 1
# #             except:
# #                 continue
# #             try:
# #                 call_array = call_array/len_roll
# #                 put_array = put_array/len_roll
# #                 cp = cp/len_roll
# #                 hvtf_array = hvtf_array/len_roll
# #             except:
# #                 continue
#
# #             if (call_array>call_min and call_array<call_max) and (put_array>put_min and put_array<put_max) and (cp>cp_min and cp<cp_max):
# #                 com["total"] = [call_array, put_array, cp,hvtf_array]
# #                 final_data[symbol] = com
#
# #         file.close()
# #         return HttpResponse(json.dumps(final_data, indent=4,default=str),content_type = "application/json")
# #         #return JsonResponse(final_data, safe=False)