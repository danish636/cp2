# import pandas as pd
# from datetime import date, timedelta, datetime
# import math
# import numpy as np
# from collections import defaultdict
# from bisect import bisect_left
# import collections
# import urllib
# from urllib.request import urlopen
# import json
# import os, zipfile
#
# np.set_printoptions(suppress=True)
#
#
# def load_data(path, ticker, in_date):
#     data = pd.read_csv(path + ticker + ".csv", usecols=["date","open","high","low", "close"], parse_dates=["date"])
#     data = data[data['date'] <= in_date]
#     return data
#
# def rolling_finder(data, filter_days, rolling_value, in_date):
#     # data["date"] = pd.to_datetime(data["date"])
#     data = data[data["date"] >= (in_date - timedelta(days=filter_days))]
#     high_v = []
#     open_v = []
#     low_v = []
#     for i in range(0,len(data)):
#         try:
#             df = data.iloc[i+rolling_value-1]
#         except:
#             break
#         open_val = data.iloc[i]["open"]
#
#         high_col = data.iloc[i:i+rolling_value]['high'].max()
#
#         low_col = data.iloc[i:i+rolling_value]['low'].min()
#         high_v.append(((high_col - open_val)/ open_val)*100)
#         open_v.append(((df["open"] - open_val)/ open_val)*100)
#         low_v.append(((low_col - open_val)/ open_val)*100)
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
#     open_val = float(latest_api_data[0]['open'])
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
#     open_val = float(latest_api_data[0]['open'])
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
#     open_val = float(latest_api_data[0]['open'])
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
# def predict_price(ticker, filter_days, in_date, percentage):
#     path = "media/hist data/"
#     in_date = datetime.strptime(in_date, "%Y-%m-%d")
#     rolling_value = [5, 10, 20, 60]#5
#     percentages = [90]
#     percentages.append(percentage)
#     final_dict = {}
#
#     data = load_data(path, ticker, in_date)
#
#     for rolling in rolling_value:
#         #print(rolling)
#         pred_open_high = []
#         pred_open_low = []
#         h_bins_array = []
#         l_bins_array = []
#         pred_final_open_high = []
#         pred_final_open_low = []
#         month_fixed_high = []
#         month_fixed_low = []
#         low_min_idx, high_max_idx = get_last_col(data, rolling)
#         data_last = data[-rolling:]
#         if rolling != 5:
#             half_roll = int(rolling/2)
#             open_final_val = data_last['open'].iloc[half_roll+1]
#
#         for idx,percentage in enumerate(percentages):
#             if idx==0:
#                 #For 90% only calculate the value
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
#
#                 predicted_high = data['open'].iloc[low_min_idx] + ((data['open'].iloc[low_min_idx]*h_bin)/100.0)
#                 predicted_low = data['open'].iloc[high_max_idx] + (data['open'].iloc[high_max_idx]*l_bin)/100.0
#                 print(data.tail(1))
#                 close_val = float(data.tail(1)['close'])
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
#             h_bins_array.append(h_bin)
#             l_bins_array.append(l_bin)
#
#
#         final_dict[rolling] = {"predicted_high":pred_open_high[::-1], "predicted_low":pred_open_low[::-1]}
#
#     return final_dict
#
# #set constant variables
# in_date = "2021-11-01"
# out_date = "2021-11-23"
# ticker = "A"
# percentage = 65
# filter_days = 180
#
# output = predict_price(ticker, filter_days, in_date, percentage)
#
# p_high = float(output[20]["predicted_high"][0])
#
# upper_h = p_high + float(p_high * 0.05)
# lower_h = p_high - float(p_high * 0.05)
#
# process_date = datetime(int(in_date.split("-")[0]), int(in_date.split("-")[1]), int(in_date.split("-")[2]))
#
# files = []
# dir_name = 'media/option_data/Option Data/Historical/2021/11/'
# extension = ".csv"
# for f in os.listdir(dir_name):
#     if f.endswith(extension) and f.split('_')[1] == "options" and int(f.split('_')[2][4:6]) == 10:
#         file_name = os.path.abspath(f)
#         files.append(file_name)
# df = pd.read_csv(dir_name + "L3_options_" + in_date.replace("-","") + ".csv", parse_dates=["Expiration"])
# df = df[(df["UnderlyingSymbol"] == ticker) & (df["Expiration"] <= (datetime(int(in_date.split("-")[0]), int(in_date.split("-")[1]), int(in_date.split("-")[2])) + timedelta(days=30))) & (df["Strike"] >= lower_h) & (df["Strike"] <= upper_h) & (df["Type"] == "call")]
# # df = df.reset_index().to_csv("demo.csv")
#
# optionsymbols = list(df.OptionSymbol.values)
# expiration = list(df.Expiration.values)
# print(optionsymbols)
# dates = []
# for i in range(0,31):
#     print(i)
#     d = (process_date + timedelta(days=i)).strftime("%Y%m%d")
#     dates.append(d)
#
# print(dates)
#
#
