# import pandas as pd
# from datetime import datetime,timedelta
# import math
# import numpy as np
# from collections import defaultdict
# from bisect import bisect_left
# import collections
#
# def load_data(path, ticker, in_date):
#     data = pd.read_csv(path + ticker + ".csv", usecols=["date","open","high","low", "close"], parse_dates=["date"])
#     data = data[data['date'] <= in_date]
#     return data
#
# def rolling_finder(data, filter_days, rolling_value, in_date):
#     # data["date"] = pd.to_datetime(data["date"])
#     # #print(len(data))
#     #print(in_date)
#     data = data[data["date"] >= (in_date - timedelta(days=filter_days))]
#     print(len(data))
#     # #print(len(data))
#     high_v = []
#     open_v = []
#     low_v = []
#     for i in range(0,len(data)):
#         # #print(data.iloc[i+rolling_value-1])
#         try:
#             # #print('try')
#             df = data.iloc[i+rolling_value-1]
#             #print(df)
#         except:
#             #print('except---------')
#             break
#         open_val = data.iloc[i]["open"]
#
#         high_col = data.iloc[i:i+rolling_value]['high'].max()
#         #print(high_col)
#
#         low_col = data.iloc[i:i+rolling_value]['low'].min()
#         high_v.append(((high_col - open_val)/ open_val)*100)
#         open_v.append(((df["open"] - open_val)/ open_val)*100)
#         low_v.append(((low_col - open_val)/ open_val)*100)
#     #print(high_v)
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
#     # #print('bins frequency')
#     # #print(data)
#     # #print(value)
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
# def predict_price_graph(request):
#     path = "media/hist data2/"
#     date = request['date']
#     date_range = request['date_range']
#     ticker = request['ticker']
#     filter_days = int(request['filter_days'])
#     rollings = [22, 44, 65, 86, 108, 130, 259]
#     date_time = pd.to_datetime(date, format='%Y-%m-%d')
#     in_date = datetime.strptime(date, "%Y-%m-%d")
#
#     #commone for both
#     percentage = 65
#     new_data = {}
#
#     data = load_data(path, ticker, in_date)
#     # f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?serietype=line&apikey=b1360803f80dd08bdd0211c5c004ad03"
#     # f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
#     # url_latest_api = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker.lower()}?apikey=b1360803f80dd08bdd0211c5c004ad03"
#     latest_api_data = {}
#     latest_api_data["historical"] = pd.read_csv("media/hist data2/" + ticker + ".csv").to_dict('records')
#     #old API
#     #f"https://cloud.iexapis.com/stable/stock/{ticker.lower()}/intraday-prices?token=pk_55e019e9e4db4baaa9493d29a095bf63"
#
#     # response = urlopen(url_latest_api)
#     # latest_api_data = json.loads(response.read())
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
#
#         pred_open_high = []
#         pred_open_low = []
#         h_bins_array = []
#         l_bins_array = []
#         pred_final_open_high = []
#         pred_final_open_low = []
#         month_fixed_high = []
#         month_fixed_low = []
#
#         for idx,rolling in enumerate(rollings):
#             low_min_idx, high_max_idx = get_last_col_api(data, rolling, latest_api_data)
#             data_last = data[-rolling:]
#             if rolling != 5:
#                 half_roll = int(rolling/2)
#                 open_final_val = data_last['open'].iloc[half_roll+1]
#             else:
#                 half_roll = int((rolling-1)/2)
#                 open_final_val = data_last['open'].iloc[half_roll+1]
#
#
#             #For 90% only calculate the value
#             d = pd.DataFrame([])
#             d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#             high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#             index, cum_cal = get_cumsum(high_cum, percentage)
#             h_bin = high_bins[index]
#
#             low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#             index, cum_cal = get_cumsum(low_cum, percentage)
#             l_bin = low_bins[len(low_bins) - index]
#
#             open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#             index, cum_cal = get_cumsum(open_cum, percentage)
#             o_bin = open_bins[index]
#             close_val = float(data.tail(1)['close'])
#
#             predicted_high = close_val + ((close_val*h_bin)/100.0)
#             predicted_low = close_val + ((close_val*l_bin)/100.0)
#             pred_open_high.append(predicted_high)
#             pred_open_low.append(predicted_low)
#             h_bins_array.append(h_bin)
#             l_bins_array.append(-1*(l_bin))
#         new_data[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high, "predicted_low":pred_open_low}
#
#     else:
#         #If market is Close
#         pred_open_high = []
#         pred_open_low = []
#         h_bins_array = []
#         l_bins_array = []
#         pred_final_open_high = []
#         pred_final_open_low = []
#         month_fixed_high = []
#         month_fixed_low = []
#
#         for idx,rolling in enumerate(rollings):
#             low_min_idx, high_max_idx = get_last_col(data, rolling)
#             data_last = data[-rolling:]
#             if rolling != 5:
#                 half_roll = int(rolling/2)
#                 open_final_val = data_last['open'].iloc[half_roll+1]
#             else:
#                 half_roll = int((rolling-1)/2)
#                 open_final_val = data_last['open'].iloc[half_roll+1]
#
#
#             #For 90% only calculate the value
#             d = pd.DataFrame([])
#
#             d["high"], d["open"], d["low"] = rolling_finder(data, filter_days, rolling, in_date)
#             high_freq,high_bins,high_prob,high_cum = bins_and_frequency(d,"high")
#             index, cum_cal = get_cumsum(high_cum, percentage)
#             h_bin = high_bins[index]
#
#             low_freq,low_bins,low_prob,low_cum = bins_and_frequency(d,"low")
#             index, cum_cal = get_cumsum(low_cum, percentage)
#             l_bin = low_bins[len(low_bins) - index]
#
#             open_freq,open_bins,open_prob,open_cum = bins_and_frequency(d,"open")
#             index, cum_cal = get_cumsum(open_cum, percentage)
#             o_bin = open_bins[index]
#             close_val = float(data.tail(1)['close'])
#
#             predicted_high = close_val + ((close_val*h_bin)/100.0)
#             predicted_low = close_val + ((close_val*l_bin)/100.0)
#             pred_open_high.append(predicted_high)
#             pred_open_low.append(predicted_low)
#
#             h_bins_array.append(h_bin)
#             l_bins_array.append(-1*(l_bin))
#         new_data[rolling] = {"O to H":h_bin, "O to L":l_bin, "predicted_high":pred_open_high, "predicted_low":pred_open_low}
#
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
#
#     # start_date = str(date_time).split(" ")[0]
#     # end_date = str(date_range_date).split(" ")[0]
#     # d = requests.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={end_date}&to={start_date}&apikey=b1360803f80dd08bdd0211c5c004ad03')
#     # data = d.json()
#     # df = pd.DataFrame(data['historical'])
#     df = pd.read_csv('media/hist data2/'+ticker+'.csv',parse_dates=['date'])
#     df = df[(df["date"] >= date_range_date) & (df["date"] <= date_time)]
#     df2 = df[::-1]
#     temp_date = date_time
#     while True:
#         try:
#             next_day = str(temp_date).split(" ")[0]
#             next_day = next_day.split("-")[::-1]
#             next_day = "-".join(next_day)
#             new_pred_high = new_data[rolling]['predicted_high']
#             new_pred_low = new_data[rolling]["predicted_low"]
#             rollings = rollings[::-1]
#             break
#         except:
#             temp_date = temp_date + timedelta(days=1)
#
#     y_values_high = new_pred_high
#     y_values_low = new_pred_low
#
#     final_dict = {}
#
#     final_dict['rollings'] = [30, 60, 90, 120, 150, 180, 360]
#     final_dict['pred_high'] = y_values_high
#     final_dict['pred_low'] = y_values_low
#     final_dict['pred_high_percentage'] = h_bins_array
#     final_dict['pred_low_percentage'] = l_bins_array
#
#     return final_dict
#
# request = {
#     "date": "2023-03-09",
#     "date_range":"1m",
#     "ticker":"AAPL",
#     "filter_days":"390",
# }
#
# print(predict_price_graph(request))