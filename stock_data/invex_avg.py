# import pandas as pd
# from pandas.core import indexing
# import numpy as np
# from datetime import date
# import vaex
# import math
# import os
# import json
# from time import time
# import datetime
#
# #To get upper 10%
# def up_value(prob_data):
#   y_up = 0
#   for i_up,data in enumerate(prob_data):
#     if y_up<10:
#       y_up = y_up + data
#     else:
#       break
#   return i_up, y_up
#
# #To get lower 10%
# def down_value(prob_data):
#   y_down = 0
#   for i_down, data in reversed(list(enumerate(prob_data))):
#     if y_down < 10:
#       y_down = y_down + data
#     else:
#       break
#   return i_down+1, y_down
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
# #reading data from stored csv files
# def calculation(symbol,df_value, df_quotes, call_min, call_max, put_min, put_max, cp_min, cp_max, startdate, enddate):
#   step_size = 0.25
#   df_value["rolling"] = (df_value['Expiration'] - df_value[' DataDate']).dt.days
#   data = pd.read_csv("stock_data/media/hist data/" + symbol + ".csv",parse_dates=["date"])
#   data = data[(data["date"].dt.date >= startdate.date()) & (data["date"].dt.date <= enddate.date())]
#   real_rolling = df_value["rolling"].unique()   #[6, 24, 59, 142]
#   expirations = df_value["Expiration"].dt.strftime('%Y-%m-%d').unique()
#   rolling = list(filter(lambda day: day <= (len(data) - 10), real_rolling))
#   rolling.sort()
#   sym_data = df_quotes[df_quotes["symbol"] == symbol]
#   current_price=sym_data["close"].iloc[0]
#   invex = pd.DataFrame([current_price])
#   send_data = np.append(current_price, real_rolling)
#   expirations = np.append(expirations,0)
#   #print(expirations)
#   inv = pd.DataFrame(send_data)
#   inv["Expiration"] = expirations
#   inv_dict = {}
#
#
#   for j,rolling_value in enumerate(real_rolling):
#     new_data = pd.DataFrame([])
#     df_value_1 = df_value[df_value["rolling"] == rolling_value]
#     expiration_date = str(df_value_1["Expiration"].iloc[0].date())
#
#     if rolling_value in rolling:
#       df_1 = pd.DataFrame([])
#       data['date'] = pd.to_datetime(data['date'])
#       data = data.sort_values(by='date',ascending=False)
#       data['high_value_'+ str(rolling_value)] = data['high'].rolling(rolling_value).max()
#       data['low_value_'+ str(rolling_value)] = data['low'].rolling(rolling_value).min()
#       data['change_mid_'+ str(rolling_value)] = ((data['high_value_'+ str(rolling_value)].astype('float') - data['low_value_'+ str(rolling_value)].astype('float')) / data['open'].astype('float'))*100.0
#       least_value = int(data['change_mid_'+ str(rolling_value)].min())
#       high_value = math.ceil(data['change_mid_'+ str(rolling_value)].max()) + 1.0
#       if (high_value - least_value) >= 2000:
#           break
#       bins_array = np.arange(least_value, high_value, step_size)
#       frequency = data['change_mid_'+ str(rolling_value)].value_counts(bins=bins_array).sort_index(axis=0).values
#       freq_total = frequency.sum()
#       bins_array = bins_array[1:]
#       prob_data = np.array((frequency/freq_total)*100.0)
#       i_up, y_up = up_value(prob_data)
#       i_down, y_down = down_value(prob_data)
#       cumulative_prob = np.cumsum(prob_data)
#       prob_data_required = prob_data[i_up:i_down]
#       required_prob = prob_data_required
#       prob_require_total = (sum(prob_data_required)+y_up+y_down-20)/100
#       prob_data_required[0] = prob_data_required[0] + y_up - 10
#       prob_data_required[-1] = prob_data_required[-1] + y_down - 10
#       normal_prob = prob_data_required/prob_require_total
#       bins_array_required = bins_array[i_up+1:i_down+1]
#       weighted_avg = (normal_prob*bins_array_required)/100.0
#       weighted_avg_sum = weighted_avg.sum()
#       rol = rolling_value
#       required_prob = np.append(required_prob, required_prob.sum())
#       normal_prob = np.append(normal_prob, normal_prob.sum())
#       weighted_avg = np.append(weighted_avg, weighted_avg.sum())
#       data["space_" + str(2*j + 1)] = [""] * len(data.index)
#       df_1["bins_"+ str(rolling_value)] = bins_array
#       df_1["Frequency_" + str(rolling_value)] = frequency
#       df_1["Probability_" + str(rolling_value)] = prob_data
#       df_1["Cumulative_" + str(rolling_value)] = cumulative_prob
#
#       call_value = df_value_1[df_value_1["Type"] == "call"]
#       put_value = df_value_1[df_value_1["Type"] == "put"]
#       new_data["Bid_call_" + str(rolling_value)] = call_value["Bid"].values
#       new_data["Ask_call_" + str(rolling_value)] = call_value["Ask"].values
#       new_data["Mid_call_"+str(rolling_value)] = (call_value["Bid"].values + call_value["Ask"].values) /2.0
#       time_value_call = time_value_call_cal(np.array(call_value["Strike"]), current_price, np.array(new_data["Mid_call_"+str(rolling_value)]), np.array(new_data["Ask_call_"+str(rolling_value)]))
#       new_data["Time_value_call_"+str(rolling_value)] = time_value_call
#       new_data["Strike_" + str(rolling_value)] = call_value["Strike"].values
#       new_data["Bid_put_" + str(rolling_value)] = put_value["Bid"].values
#       new_data["Ask_put_" + str(rolling_value)] = put_value["Ask"].values
#       new_data["Mid_put_"+str(rolling_value)] = (put_value["Bid"].values + put_value["Ask"].values) /2.0
#       time_value_put = time_value_put_cal(np.array(put_value["Strike"]), current_price, np.array(new_data["Mid_put_"+str(rolling_value)]), np.array(new_data["Ask_put_"+str(rolling_value)]))
#       new_data["Time_value_put_"+str(rolling_value)] = time_value_put
#       new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#       new_data["%_change_call_"+str(rolling_value)] = np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#       last_len = len(new_data.index)
#       #Calculate if the rolling value is in rolling array
#       prob_strike_ls = np.zeros(shape=(len(new_data["%_change_call_"+str(rolling_value)])))
#       for index,k in enumerate(new_data["%_change_call_"+str(rolling_value)]):
#         n = math.ceil(k/step_size) * step_size
#         if n<=least_value:
#           prob_strike_ls[index] = 0.0
#         elif n>=high_value:
#           prob_strike_ls[index] = cumulative_prob[-1]
#         elif n in bins_array:
#           d = df_1[df_1["bins_"+ str(rolling_value)] == n]
#           if d["Cumulative_" + str(rolling_value)].values:
#             prob_strike_ls[index] = d["Cumulative_" + str(rolling_value)].values
#           else:
#             prob_strike_ls[index] = prob_strike_ls[index-1]
#         else:
#           print("else part for prob strike")
#           prob_strike_ls[index] = 0.0
#
#       new_data["Prob_Strike_call_" + str(rolling_value)] = 100.0 - prob_strike_ls
#       new_data["HVTF_call_" + str(rolling_value)] = [weighted_avg_sum] * len(new_data.index)
#       new_data["Invex_ratio_call_" + str(rolling_value)] = (new_data["HVTF_call_"+str(rolling_value)].values * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#
#       new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#       new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#       new_data["Invex_ratio_put_" + str(rolling_value)] = (new_data["HVTF_put_"+str(rolling_value)].values * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#
#       new_data["CP_ratio_" + str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#     else:
#       new_data["Bid_call_" + str(rolling_value)] = invex["Bid_call_" + str(rol)].values#call_value["Bid"].values
#       new_data["Ask_call_" + str(rolling_value)] = invex["Ask_call_" + str(rol)].values#call_value["Ask"].values
#       new_data["Mid_call_"+str(rolling_value)] = invex["Mid_call_" + str(rol)].values#(call_value["Bid"].values + call_value["Ask"].values) /2.0
#       new_data["Time_value_call_"+str(rolling_value)] = invex["Time_value_call_"+str(rol)].values#time_value_call
#       new_data["Strike_" + str(rolling_value)] = invex["Strike_"+str(rol)].values
#       new_data["Bid_put_" + str(rolling_value)] = invex["Bid_put_"+str(rol)].values #put_value["Bid"].values
#       new_data["Ask_put_" + str(rolling_value)] = invex["Ask_put_"+str(rol)] #put_value["Ask"].values
#       new_data["Mid_put_"+str(rolling_value)] = invex["Mid_put_"+str(rol)] #(put_value["Bid"].values + put_value["Ask"].values) /2.0
#       new_data["Time_value_put_"+str(rolling_value)] = invex["Time_value_put_"+str(rol)] #time_value_put
#       new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#       new_data["%_change_call_"+str(rolling_value)] = invex["%_change_call_"+str(rol)] #np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#       new_data["Prob_Strike_call_" + str(rolling_value)] = invex["Prob_Strike_call_" + str(rol)]
#       w_a_s = (((1 + float(weighted_avg_sum / 100)) ** (float(rolling_value / rol))) - 1) * 100.0
#       hvtf_arr = np.array([w_a_s]*last_len)
#       new_data["HVTF_call_" + str(rolling_value)] = np.append(hvtf_arr, [" "]*(len(new_data.index) - last_len))   #last_len#
#       new_data["Invex_ratio_call_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#       new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#       new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#       new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#       new_data["Invex_ratio_put_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#       new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#       new_data["CP_ratio_"+ str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#
#     invex = pd.concat([invex, new_data], axis=1)
#     inv = pd.concat([inv, new_data[["Strike_" + str(rolling_value),"Invex_ratio_call_" + str(rolling_value),"Invex_ratio_put_" + str(rolling_value),"CP_ratio_"+ str(rolling_value),"HVTF_put_" + str(rolling_value)]]], axis=1)
#     inv_filter = inv[((inv["Invex_ratio_call_" + str(rolling_value)] >= call_min) & (inv["Invex_ratio_call_" + str(rolling_value)] <= call_max)) & ((inv["Invex_ratio_put_" + str(rolling_value)] <= put_max) & (inv["Invex_ratio_put_" + str(rolling_value)] >= put_min)) & ((inv["CP_ratio_"+ str(rolling_value)] >= cp_min) & (inv["CP_ratio_"+ str(rolling_value)] <= cp_max))]
#
#     inv_dict[expiration_date] = [inv_filter["Invex_ratio_call_" + str(rolling_value)].mean(), inv_filter["Invex_ratio_put_" + str(rolling_value)].mean(), inv_filter["CP_ratio_"+ str(rolling_value)].mean(), inv_filter["HVTF_put_" + str(rolling_value)].mean()]
#
#   return inv_dict
#
#
# #some value is not calculating due to error in data
#
#
#
# # symbollist = ["CAKE", "BBSI","BKNG"]
# #df = vaex.open("C:/Users/home/OneDrive/Desktop/PROJECT/abdullabhai/data/L3_options_20211123.hdf5") , '20211213'
# def cal(datadate,startdate,enddate,call_min,call_max,put_min,put_max,cp_min,cp_max):
#   final = {}
#   df = vaex.open('stock_data/media/option_data/L3_options_'+datadate+'.hdf5')
#   #df = pd.read_csv('media/option_data/L3_options_'+datadate+'.csv',parse_dates=[" DataDate","Expiration"])
#   df_quotes = pd.read_csv('stock_data/media/option_data/L3_stockquotes_'+datadate+'.csv')
#   #print(df_quotes) stock_project/stock_data/media/option_data
#   #instead of files we can go for symbol name list stored in json file
#   file = open('stock_data/media/symbols_name.json', 'r')
#   files = json.load(file)
#   for num,symbol in enumerate(files[:50]):
#       #symbol = filename.split('.')[0]
#       df_value = df[df["UnderlyingSymbol"] == symbol]
#       df_value = df_value.to_pandas_df()
#       df_value[" DataDate"] = pd.to_datetime(df_value[" DataDate"])
#       df_value["Expiration"] = pd.to_datetime(df_value["Expiration"])
#       try:
#         inv = calculation(symbol,df_value, df_quotes, call_min, call_max, put_min, put_max, cp_min, cp_max, startdate, enddate)
#         final[symbol] = inv
#       except:
#         print("Except")
#         continue
#   print('data calculated...')
#   return final
#
#
#
