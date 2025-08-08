# #!/usr/local/bin/python3.9
# import pandas as pd
# from pandas.core import indexing
# import numpy as np
# from datetime import date, timedelta, datetime
# import vaex
# import math
# import os
# import json
# import random
# from time import time
# import warnings
# warnings.filterwarnings('ignore')
#
#
# print('start')
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
# def calculation_max(symbol,df_value, df_quotes):
#   step_size = 0.25
# #   df_value = df_value.to_pandas_df()
# #   df_value[" DataDate"] = pd.to_datetime(df_value[" DataDate"])
# #   df_value["Expiration"] = pd.to_datetime(df_value["Expiration"])
#   df_value["rolling"] = (df_value['Expiration'] - df_value[' DataDate']).dt.days
#   #df_quotes = pd.read_csv("L3_stockquotes_20211123.csv")
#   #data = pd.read_json('C:/Users/home/OneDrive/Desktop/PROJECT/abdullabhai/data/Daily_data/'+symbol+'.csv')
#   if os.path.isfile("media/hist data/" + symbol + ".csv"):
#     data = pd.read_csv("media/hist data/" + symbol + ".csv",parse_dates=["date"])
#   else:
#     data = pd.read_json("https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/" + symbol + "?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=20y")
#     data['date'] =  pd.to_datetime(data['date'])
#
# #   data["date"] = pd.to_datetime(data["date"])
#   real_rolling = df_value["rolling"].unique() #[6, 24, 59, 142]
#   expirations = df_value["Expiration"].dt.strftime('%Y-%m-%d').unique()
# #   expirations.sort()
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
#
#
#   for j,rolling_value in enumerate(real_rolling):
#     new_data = pd.DataFrame([])
#     df_value_1 = df_value[df_value["rolling"] == rolling_value]
#     # expiration_date = str(df_value_1["Expiration"].iloc[0].date())
#     if rolling_value!=0:
#         if rolling_value in rolling:
#           df_1 = pd.DataFrame([])
#         #   df_2 = pd.DataFrame([])
#           data['date'] = pd.to_datetime(data['date'])
#           data = data.sort_values(by='date',ascending=False)
#         #   print(data['high'].rolling(rolling_value).max())
#           data['high_value_'+ str(rolling_value)] = data['high'].rolling(rolling_value).max()
#           data['low_value_'+ str(rolling_value)] = data['low'].rolling(rolling_value).min()
#         #   print(data)
#           data['change_mid_'+ str(rolling_value)] = ((data['high_value_'+ str(rolling_value)].astype('float') - data['low_value_'+ str(rolling_value)].astype('float')) / data['open'].astype('float'))*100.0
#         #   print(data['change_mid_'+ str(rolling_value)])
#           least_value = int(data['change_mid_'+ str(rolling_value)].min())
#           high_value = math.ceil(data['change_mid_'+ str(rolling_value)].max()) + 1.0
#           if (high_value - least_value) >= 2000:
#               break
#           bins_array = np.arange(least_value, high_value, step_size)
#           frequency = data['change_mid_'+ str(rolling_value)].value_counts(bins=bins_array).sort_index(axis=0).values
#           freq_total = frequency.sum()
#           bins_array = bins_array[1:]
#           prob_data = np.array((frequency/freq_total)*100.0)
#           i_up, y_up = up_value(prob_data)
#           i_down, y_down = down_value(prob_data)
#           cumulative_prob = np.cumsum(prob_data)
#           prob_data_required = prob_data[i_up:i_down]
#           required_prob = prob_data_required
#           prob_require_total = (sum(prob_data_required)+y_up+y_down-20)/100
#           prob_data_required[0] = prob_data_required[0] + y_up - 10
#           prob_data_required[-1] = prob_data_required[-1] + y_down - 10
#           normal_prob = prob_data_required/prob_require_total
#           bins_array_required = bins_array[i_up+1:i_down+1]
#           weighted_avg = (normal_prob*bins_array_required)/100.0
#           weighted_avg_sum = weighted_avg.sum()
#           rol = rolling_value
#           required_prob = np.append(required_prob, required_prob.sum())
#           normal_prob = np.append(normal_prob, normal_prob.sum())
#           weighted_avg = np.append(weighted_avg, weighted_avg.sum())
#           data["space_" + str(2*j + 1)] = [""] * len(data.index)
#           df_1["bins_"+ str(rolling_value)] = bins_array
#           df_1["Frequency_" + str(rolling_value)] = frequency
#           df_1["Probability_" + str(rolling_value)] = prob_data
#           df_1["Cumulative_" + str(rolling_value)] = cumulative_prob
#
#           call_value = df_value_1[df_value_1["Type"] == "call"]
#           put_value = df_value_1[df_value_1["Type"] == "put"]
#           new_data["Bid_call_" + str(rolling_value)] = call_value["Bid"].values
#           new_data["Ask_call_" + str(rolling_value)] = call_value["Ask"].values
#           new_data["Mid_call_"+str(rolling_value)] = (call_value["Bid"].values + call_value["Ask"].values) /2.0
#           time_value_call = time_value_call_cal(np.array(call_value["Strike"]), current_price, np.array(new_data["Mid_call_"+str(rolling_value)]), np.array(new_data["Ask_call_"+str(rolling_value)]))
#           new_data["Time_value_call_"+str(rolling_value)] = time_value_call
#           new_data["Strike_" + str(rolling_value)] = call_value["Strike"].values
#           new_data["Bid_put_" + str(rolling_value)] = put_value["Bid"].values
#           new_data["Ask_put_" + str(rolling_value)] = put_value["Ask"].values
#           new_data["Mid_put_"+str(rolling_value)] = (put_value["Bid"].values + put_value["Ask"].values) /2.0
#           time_value_put = time_value_put_cal(np.array(put_value["Strike"]), current_price, np.array(new_data["Mid_put_"+str(rolling_value)]), np.array(new_data["Ask_put_"+str(rolling_value)]))
#           new_data["Time_value_put_"+str(rolling_value)] = time_value_put
#           new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#           new_data["%_change_call_"+str(rolling_value)] = np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#           last_len = len(new_data.index)
#           #Calculate if the rolling value is in rolling array
#           prob_strike_ls = np.zeros(shape=(len(new_data["%_change_call_"+str(rolling_value)])))
#           for index,k in enumerate(new_data["%_change_call_"+str(rolling_value)]):
#             n = math.ceil(k/step_size) * step_size
#             if n<=least_value:
#               prob_strike_ls[index] = 0.0
#             elif n>=high_value:
#               prob_strike_ls[index] = cumulative_prob[-1]
#             elif n in bins_array:
#               d = df_1[df_1["bins_"+ str(rolling_value)] == n]
#               if d["Cumulative_" + str(rolling_value)].values:
#                 prob_strike_ls[index] = d["Cumulative_" + str(rolling_value)].values
#               else:
#                 prob_strike_ls[index] = prob_strike_ls[index-1]
#             else:
#               print("else part for prob strike")
#               prob_strike_ls[index] = 0.0
#
#           new_data["Prob_Strike_call_" + str(rolling_value)] = 100.0 - prob_strike_ls
#           new_data["HVTF_call_" + str(rolling_value)] = [weighted_avg_sum] * len(new_data.index)
#           new_data["Invex_ratio_call_" + str(rolling_value)] = (new_data["HVTF_call_"+str(rolling_value)].values * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#           #new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#           new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#           new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#           new_data["Invex_ratio_put_" + str(rolling_value)] = (new_data["HVTF_put_"+str(rolling_value)].values * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#           #new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#           new_data["CP_ratio_" + str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#         else:
#
#           new_data["Bid_call_" + str(rolling_value)] = invex["Bid_call_" + str(rol)].values#call_value["Bid"].values
#           new_data["Ask_call_" + str(rolling_value)] = invex["Ask_call_" + str(rol)].values#call_value["Ask"].values
#           new_data["Mid_call_"+str(rolling_value)] = invex["Mid_call_" + str(rol)].values#(call_value["Bid"].values + call_value["Ask"].values) /2.0
#           new_data["Time_value_call_"+str(rolling_value)] = invex["Time_value_call_"+str(rol)].values#time_value_call
#           new_data["Strike_" + str(rolling_value)] = invex["Strike_"+str(rol)].values
#           new_data["Bid_put_" + str(rolling_value)] = invex["Bid_put_"+str(rol)].values #put_value["Bid"].values
#           new_data["Ask_put_" + str(rolling_value)] = invex["Ask_put_"+str(rol)] #put_value["Ask"].values
#           new_data["Mid_put_"+str(rolling_value)] = invex["Mid_put_"+str(rol)] #(put_value["Bid"].values + put_value["Ask"].values) /2.0
#           new_data["Time_value_put_"+str(rolling_value)] = invex["Time_value_put_"+str(rol)] #time_value_put
#           new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#           new_data["%_change_call_"+str(rolling_value)] = invex["%_change_call_"+str(rol)] #np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#           new_data["Prob_Strike_call_" + str(rolling_value)] = invex["Prob_Strike_call_" + str(rol)]
#           w_a_s = (((1 + float(weighted_avg_sum / 100)) ** (float(rolling_value / rol))) - 1) * 100.0
#           hvtf_arr = np.array([w_a_s]*last_len)
#           new_data["HVTF_call_" + str(rolling_value)] = np.append(hvtf_arr, [" "]*(len(new_data.index) - last_len))   #last_len#
#           new_data["Invex_ratio_call_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#           new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#           new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#           new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#           new_data["Invex_ratio_put_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#           new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#           new_data["CP_ratio_"+ str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#
#         invex = pd.concat([invex, new_data], axis=1)
#         inv = pd.concat([inv, new_data[["Strike_" + str(rolling_value),"Invex_ratio_call_" + str(rolling_value),"Invex_ratio_put_" + str(rolling_value),"CP_ratio_"+ str(rolling_value),"HVTF_put_" + str(rolling_value)]]], axis=1)
#   return inv
#
#
# #Calculation for 6months ::
# def calculation_180(symbol,df_value, df_quotes):
#   step_size = 0.25
#   df_value["rolling"] = (df_value['Expiration'] - df_value['DataDate']).dt.days
#
#   enddate = df_value['DataDate'].dt.date.iloc[0]
#   startdate = enddate - timedelta(days=180)
# #   print(f'End-date:     {(enddate)}')
# #   print(f'Start-date:   {(startdate)}')
#
#   if os.path.isfile("media/hist data/" + symbol + ".csv"):
#     data = pd.read_csv("media/hist data/" + symbol + ".csv",parse_dates=["date"])
#   else:
#     data = pd.read_json("https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/" + symbol + "?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=20y")
#     data['date'] =  pd.to_datetime(data['date'])
#
#   data["date"] = pd.to_datetime(data["date"])
#   data = data[(data["date"].dt.date >= startdate) & (data["date"].dt.date <= enddate)]
#
#   real_rolling = df_value["rolling"].unique() #[6, 24, 59, 142]
#   expirations = df_value["Expiration"].dt.strftime('%Y-%m-%d').unique()
#
#   rolling = list(filter(lambda day: day <= (len(data) - 10), real_rolling))
#   rolling.sort()
#   sym_data = df_quotes[df_quotes["symbol"] == symbol]
#   current_price=sym_data["close"].iloc[0]
#   invex = pd.DataFrame([current_price])
#   send_data = np.append(current_price, real_rolling)
#   expirations = np.append(expirations,0)
#
#   inv = pd.DataFrame(send_data)
#   inv["Expiration"] = expirations
#
#
#   for j,rolling_value in enumerate(real_rolling):
#     new_data = pd.DataFrame([])
#     df_value_1 = df_value[df_value["rolling"] == rolling_value]
#
#     if rolling_value<=180 and rolling_value!=0:
#         if rolling_value in rolling:
#           df_1 = pd.DataFrame([])
#         #   df_2 = pd.DataFrame([])
#           data['date'] = pd.to_datetime(data['date'])
#           data = data.sort_values(by='date',ascending=False)
#           data['high_value_'+ str(rolling_value)] = data['high'].rolling(rolling_value).max()
#           data['low_value_'+ str(rolling_value)] = data['low'].rolling(rolling_value).min()
#           data['change_mid_'+ str(rolling_value)] = ((data['high_value_'+ str(rolling_value)].astype('float') - data['low_value_'+ str(rolling_value)].astype('float')) / data['open'].astype('float'))*100.0
#           least_value = int(data['change_mid_'+ str(rolling_value)].min())
#           high_value = math.ceil(data['change_mid_'+ str(rolling_value)].max()) + 1.0
#           if (high_value - least_value) >= 2000:
#               break
#           bins_array = np.arange(least_value, high_value, step_size)
#           frequency = data['change_mid_'+ str(rolling_value)].value_counts(bins=bins_array).sort_index(axis=0).values
#           freq_total = frequency.sum()
#           bins_array = bins_array[1:]
#           prob_data = np.array((frequency/freq_total)*100.0)
#           i_up, y_up = up_value(prob_data)
#           i_down, y_down = down_value(prob_data)
#           cumulative_prob = np.cumsum(prob_data)
#           prob_data_required = prob_data[i_up:i_down]
#           required_prob = prob_data_required
#           prob_require_total = (sum(prob_data_required)+y_up+y_down-20)/100
#           prob_data_required[0] = prob_data_required[0] + y_up - 10
#           prob_data_required[-1] = prob_data_required[-1] + y_down - 10
#           normal_prob = prob_data_required/prob_require_total
#           bins_array_required = bins_array[i_up+1:i_down+1]
#           weighted_avg = (normal_prob*bins_array_required)/100.0
#           weighted_avg_sum = weighted_avg.sum()
#           rol = rolling_value
#           required_prob = np.append(required_prob, required_prob.sum())
#           normal_prob = np.append(normal_prob, normal_prob.sum())
#           weighted_avg = np.append(weighted_avg, weighted_avg.sum())
#           data["space_" + str(2*j + 1)] = [""] * len(data.index)
#           df_1["bins_"+ str(rolling_value)] = bins_array
#           df_1["Frequency_" + str(rolling_value)] = frequency
#           df_1["Probability_" + str(rolling_value)] = prob_data
#           df_1["Cumulative_" + str(rolling_value)] = cumulative_prob
#
#           call_value = df_value_1[df_value_1["Type"] == "call"]
#           put_value = df_value_1[df_value_1["Type"] == "put"]
#           new_data["Bid_call_" + str(rolling_value)] = call_value["Bid"].values
#           new_data["Ask_call_" + str(rolling_value)] = call_value["Ask"].values
#           new_data["Mid_call_"+str(rolling_value)] = (call_value["Bid"].values + call_value["Ask"].values) /2.0
#           time_value_call = time_value_call_cal(np.array(call_value["Strike"]), current_price, np.array(new_data["Mid_call_"+str(rolling_value)]), np.array(new_data["Ask_call_"+str(rolling_value)]))
#           new_data["Time_value_call_"+str(rolling_value)] = time_value_call
#           new_data["Strike_" + str(rolling_value)] = call_value["Strike"].values
#           new_data["Bid_put_" + str(rolling_value)] = put_value["Bid"].values
#           new_data["Ask_put_" + str(rolling_value)] = put_value["Ask"].values
#           new_data["Mid_put_"+str(rolling_value)] = (put_value["Bid"].values + put_value["Ask"].values) /2.0
#           time_value_put = time_value_put_cal(np.array(put_value["Strike"]), current_price, np.array(new_data["Mid_put_"+str(rolling_value)]), np.array(new_data["Ask_put_"+str(rolling_value)]))
#           new_data["Time_value_put_"+str(rolling_value)] = time_value_put
#           new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#           new_data["%_change_call_"+str(rolling_value)] = np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#           last_len = len(new_data.index)
#           #Calculate if the rolling value is in rolling array
#           prob_strike_ls = np.zeros(shape=(len(new_data["%_change_call_"+str(rolling_value)])))
#           for index,k in enumerate(new_data["%_change_call_"+str(rolling_value)]):
#             n = math.ceil(k/step_size) * step_size
#             if n<=least_value:
#               prob_strike_ls[index] = 0.0
#             elif n>=high_value:
#               prob_strike_ls[index] = cumulative_prob[-1]
#             elif n in bins_array:
#               d = df_1[df_1["bins_"+ str(rolling_value)] == n]
#               if d["Cumulative_" + str(rolling_value)].values:
#                 prob_strike_ls[index] = d["Cumulative_" + str(rolling_value)].values
#               else:
#                 prob_strike_ls[index] = prob_strike_ls[index-1]
#             else:
#               print("else part for prob strike")
#               prob_strike_ls[index] = 0.0
#
#           new_data["Prob_Strike_call_" + str(rolling_value)] = 100.0 - prob_strike_ls
#           new_data["HVTF_call_" + str(rolling_value)] = [weighted_avg_sum] * len(new_data.index)
#           new_data["Invex_ratio_call_" + str(rolling_value)] = (new_data["HVTF_call_"+str(rolling_value)].values * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#           #new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#           new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#           new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#           new_data["Invex_ratio_put_" + str(rolling_value)] = (new_data["HVTF_put_"+str(rolling_value)].values * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#           #new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#           new_data["CP_ratio_" + str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#         else:
#
#           new_data["Bid_call_" + str(rolling_value)] = invex["Bid_call_" + str(rol)].values#call_value["Bid"].values
#           new_data["Ask_call_" + str(rolling_value)] = invex["Ask_call_" + str(rol)].values#call_value["Ask"].values
#           new_data["Mid_call_"+str(rolling_value)] = invex["Mid_call_" + str(rol)].values#(call_value["Bid"].values + call_value["Ask"].values) /2.0
#           new_data["Time_value_call_"+str(rolling_value)] = invex["Time_value_call_"+str(rol)].values#time_value_call
#           new_data["Strike_" + str(rolling_value)] = invex["Strike_"+str(rol)].values
#           new_data["Bid_put_" + str(rolling_value)] = invex["Bid_put_"+str(rol)].values #put_value["Bid"].values
#           new_data["Ask_put_" + str(rolling_value)] = invex["Ask_put_"+str(rol)] #put_value["Ask"].values
#           new_data["Mid_put_"+str(rolling_value)] = invex["Mid_put_"+str(rol)] #(put_value["Bid"].values + put_value["Ask"].values) /2.0
#           new_data["Time_value_put_"+str(rolling_value)] = invex["Time_value_put_"+str(rol)] #time_value_put
#           new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#           new_data["%_change_call_"+str(rolling_value)] = invex["%_change_call_"+str(rol)] #np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#           new_data["Prob_Strike_call_" + str(rolling_value)] = invex["Prob_Strike_call_" + str(rol)]
#           w_a_s = (((1 + float(weighted_avg_sum / 100)) ** (float(rolling_value / rol))) - 1) * 100.0
#           hvtf_arr = np.array([w_a_s]*last_len)
#           new_data["HVTF_call_" + str(rolling_value)] = np.append(hvtf_arr, [" "]*(len(new_data.index) - last_len))   #last_len#
#           new_data["Invex_ratio_call_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#           new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#           new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#           new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#           new_data["Invex_ratio_put_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#           new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#           new_data["CP_ratio_"+ str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#
#         invex = pd.concat([invex, new_data], axis=1)
#         inv = pd.concat([inv, new_data[["Strike_" + str(rolling_value),"Invex_ratio_call_" + str(rolling_value),"Invex_ratio_put_" + str(rolling_value),"CP_ratio_"+ str(rolling_value),"HVTF_put_" + str(rolling_value)]]], axis=1)
#   return inv
#
#
# #Calculation for 2years ::
# def calculation_720(symbol,df_value, df_quotes):
#   step_size = 0.25
#   df_value["rolling"] = (df_value['Expiration'] - df_value[' DataDate']).dt.days
#
#   enddate = df_value[' DataDate'].dt.date.iloc[0]
#   startdate = enddate - timedelta(days = 720)
#
#   if os.path.isfile("media/hist data/" + symbol + ".csv"):
#     data = pd.read_csv("media/hist data/" + symbol + ".csv",parse_dates=["date"])
#   else:
#     data = pd.read_json("https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/" + symbol + "?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=20y")
#     data['date'] =  pd.to_datetime(data['date'])
#
#   data = data[(data["date"].dt.date >= startdate) & (data["date"].dt.date <= enddate)]
#
#   real_rolling = df_value["rolling"].unique() #[6, 24, 59, 142]
#   expirations = df_value["Expiration"].dt.strftime('%Y-%m-%d').unique()
#
#   rolling = list(filter(lambda day: day <= (len(data) - 10), real_rolling))
#   rolling.sort()
#   sym_data = df_quotes[df_quotes["symbol"] == symbol]
#   current_price=sym_data["close"].iloc[0]
#   invex = pd.DataFrame([current_price])
#   send_data = np.append(current_price, real_rolling)
#   expirations = np.append(expirations,0)
#
#   inv = pd.DataFrame(send_data)
#   inv["Expiration"] = expirations
#
#
#   for j,rolling_value in enumerate(real_rolling):
#     new_data = pd.DataFrame([])
#     df_value_1 = df_value[df_value["rolling"] == rolling_value]
#
#     if rolling_value<=720 and rolling_value!=0:
#         if rolling_value in rolling:
#           df_1 = pd.DataFrame([])
#         #   df_2 = pd.DataFrame([])
#           data['date'] = pd.to_datetime(data['date'])
#           data = data.sort_values(by='date',ascending=False)
#           data['high_value_'+ str(rolling_value)] = data['high'].rolling(rolling_value).max()
#           data['low_value_'+ str(rolling_value)] = data['low'].rolling(rolling_value).min()
#           data['change_mid_'+ str(rolling_value)] = ((data['high_value_'+ str(rolling_value)].astype('float') - data['low_value_'+ str(rolling_value)].astype('float')) / data['open'].astype('float'))*100.0
#           least_value = int(data['change_mid_'+ str(rolling_value)].min())
#           high_value = math.ceil(data['change_mid_'+ str(rolling_value)].max()) + 1.0
#           if (high_value - least_value) >= 2000:
#               break
#           bins_array = np.arange(least_value, high_value, step_size)
#           frequency = data['change_mid_'+ str(rolling_value)].value_counts(bins=bins_array).sort_index(axis=0).values
#           freq_total = frequency.sum()
#           bins_array = bins_array[1:]
#           prob_data = np.array((frequency/freq_total)*100.0)
#           i_up, y_up = up_value(prob_data)
#           i_down, y_down = down_value(prob_data)
#           cumulative_prob = np.cumsum(prob_data)
#           prob_data_required = prob_data[i_up:i_down]
#           required_prob = prob_data_required
#           prob_require_total = (sum(prob_data_required)+y_up+y_down-20)/100
#           prob_data_required[0] = prob_data_required[0] + y_up - 10
#           prob_data_required[-1] = prob_data_required[-1] + y_down - 10
#           normal_prob = prob_data_required/prob_require_total
#           bins_array_required = bins_array[i_up+1:i_down+1]
#           weighted_avg = (normal_prob*bins_array_required)/100.0
#           weighted_avg_sum = weighted_avg.sum()
#           rol = rolling_value
#           required_prob = np.append(required_prob, required_prob.sum())
#           normal_prob = np.append(normal_prob, normal_prob.sum())
#           weighted_avg = np.append(weighted_avg, weighted_avg.sum())
#           data["space_" + str(2*j + 1)] = [""] * len(data.index)
#           df_1["bins_"+ str(rolling_value)] = bins_array
#           df_1["Frequency_" + str(rolling_value)] = frequency
#           df_1["Probability_" + str(rolling_value)] = prob_data
#           df_1["Cumulative_" + str(rolling_value)] = cumulative_prob
#
#           call_value = df_value_1[df_value_1["Type"] == "call"]
#           put_value = df_value_1[df_value_1["Type"] == "put"]
#           new_data["Bid_call_" + str(rolling_value)] = call_value["Bid"].values
#           new_data["Ask_call_" + str(rolling_value)] = call_value["Ask"].values
#           new_data["Mid_call_"+str(rolling_value)] = (call_value["Bid"].values + call_value["Ask"].values) /2.0
#           time_value_call = time_value_call_cal(np.array(call_value["Strike"]), current_price, np.array(new_data["Mid_call_"+str(rolling_value)]), np.array(new_data["Ask_call_"+str(rolling_value)]))
#           new_data["Time_value_call_"+str(rolling_value)] = time_value_call
#           new_data["Strike_" + str(rolling_value)] = call_value["Strike"].values
#           new_data["Bid_put_" + str(rolling_value)] = put_value["Bid"].values
#           new_data["Ask_put_" + str(rolling_value)] = put_value["Ask"].values
#           new_data["Mid_put_"+str(rolling_value)] = (put_value["Bid"].values + put_value["Ask"].values) /2.0
#           time_value_put = time_value_put_cal(np.array(put_value["Strike"]), current_price, np.array(new_data["Mid_put_"+str(rolling_value)]), np.array(new_data["Ask_put_"+str(rolling_value)]))
#           new_data["Time_value_put_"+str(rolling_value)] = time_value_put
#           new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#           new_data["%_change_call_"+str(rolling_value)] = np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#           last_len = len(new_data.index)
#           #Calculate if the rolling value is in rolling array
#           prob_strike_ls = np.zeros(shape=(len(new_data["%_change_call_"+str(rolling_value)])))
#           for index,k in enumerate(new_data["%_change_call_"+str(rolling_value)]):
#             n = math.ceil(k/step_size) * step_size
#             if n<=least_value:
#               prob_strike_ls[index] = 0.0
#             elif n>=high_value:
#               prob_strike_ls[index] = cumulative_prob[-1]
#             elif n in bins_array:
#               d = df_1[df_1["bins_"+ str(rolling_value)] == n]
#               if d["Cumulative_" + str(rolling_value)].values:
#                 prob_strike_ls[index] = d["Cumulative_" + str(rolling_value)].values
#               else:
#                 prob_strike_ls[index] = prob_strike_ls[index-1]
#             else:
#               print("else part for prob strike")
#               prob_strike_ls[index] = 0.0
#
#           new_data["Prob_Strike_call_" + str(rolling_value)] = 100.0 - prob_strike_ls
#           new_data["HVTF_call_" + str(rolling_value)] = [weighted_avg_sum] * len(new_data.index)
#           new_data["Invex_ratio_call_" + str(rolling_value)] = (new_data["HVTF_call_"+str(rolling_value)].values * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#           #new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#           new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#           new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#           new_data["Invex_ratio_put_" + str(rolling_value)] = (new_data["HVTF_put_"+str(rolling_value)].values * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#           #new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#           new_data["CP_ratio_" + str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#         else:
#
#           new_data["Bid_call_" + str(rolling_value)] = invex["Bid_call_" + str(rol)].values#call_value["Bid"].values
#           new_data["Ask_call_" + str(rolling_value)] = invex["Ask_call_" + str(rol)].values#call_value["Ask"].values
#           new_data["Mid_call_"+str(rolling_value)] = invex["Mid_call_" + str(rol)].values#(call_value["Bid"].values + call_value["Ask"].values) /2.0
#           new_data["Time_value_call_"+str(rolling_value)] = invex["Time_value_call_"+str(rol)].values#time_value_call
#           new_data["Strike_" + str(rolling_value)] = invex["Strike_"+str(rol)].values
#           new_data["Bid_put_" + str(rolling_value)] = invex["Bid_put_"+str(rol)].values #put_value["Bid"].values
#           new_data["Ask_put_" + str(rolling_value)] = invex["Ask_put_"+str(rol)] #put_value["Ask"].values
#           new_data["Mid_put_"+str(rolling_value)] = invex["Mid_put_"+str(rol)] #(put_value["Bid"].values + put_value["Ask"].values) /2.0
#           new_data["Time_value_put_"+str(rolling_value)] = invex["Time_value_put_"+str(rol)] #time_value_put
#           new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#           new_data["%_change_call_"+str(rolling_value)] = invex["%_change_call_"+str(rol)] #np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#           new_data["Prob_Strike_call_" + str(rolling_value)] = invex["Prob_Strike_call_" + str(rol)]
#           w_a_s = (((1 + float(weighted_avg_sum / 100)) ** (float(rolling_value / rol))) - 1) * 100.0
#           hvtf_arr = np.array([w_a_s]*last_len)
#           new_data["HVTF_call_" + str(rolling_value)] = np.append(hvtf_arr, [" "]*(len(new_data.index) - last_len))   #last_len#
#           new_data["Invex_ratio_call_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#           new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#           new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#           new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#           new_data["Invex_ratio_put_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#           new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#           new_data["CP_ratio_"+ str(rolling_value)] = new_data["Invex_ratio_call_" + str(rolling_value)].astype("float") / new_data["Invex_ratio_put_" + str(rolling_value)].astype("float")
#
#         invex = pd.concat([invex, new_data], axis=1)
#         inv = pd.concat([inv, new_data[["Strike_" + str(rolling_value),"Invex_ratio_call_" + str(rolling_value),"Invex_ratio_put_" + str(rolling_value),"CP_ratio_"+ str(rolling_value),"HVTF_put_" + str(rolling_value)]]], axis=1)
#   return inv
#
# # '20220103', '20220104', '20220105', '20220106', '20220107', '20220110', '20220111', '20220112', '20220113', '20220114', '20220118', '20220119', '20220120', '20220121', '20220124', '20220125', '20220126', '20220127', '20220128', '20220131'
#
# '''
# '20211201', '20211202', '20211203', '20211206', '20211207', '20211208', '20211209', '20211210', '20211213', '20211214', '20211215', '20211216', '20211217', '20211220', '20211221', '20211222', '20211223', '20211227', '20211228', '20211229', '20211230', '20211231',
#              '20220103', '20220104', '20220105', '20220106', '20220107', '20220110', '20220111', '20220112', '20220113', '20220114', '20220118', '20220119', '20220120', '20220121', '20220124', '20220125', '20220126', '20220127', '20220128', '20220131',
#              '20220301', '20220302', '20220303', '20220304', '20220307', '20220308', '20220309', '20220310', '20220311', '20220314', '20220315', '20220316', '20220317', '20220318', '20220321', '20220322', '20220323', '20220324', '20220325', '20220328', '20220329', '20220330', '20220331'
#              '20220401', '20220404', '20220405', '20220406', '20220407', '20220408', '20220411', '20220412', '20220413', '20220414', '20220418', '20220419', '20220420', '20220421', '20220422', '20220425', '20220426', '20220427', '20220428',
# '''
#
# today = datetime.today().strftime('%Y%m%d')
# datadates = []
# datadates.append(today)
# for datadate in datadates:
#   final_max = {}
#   final_180 = {}
#   final_720 = {}
#   df = pd.read_csv('media/option_data/Option Data/Historical/'+datadate[0:4]+'/'+str(int(datadate[4:6]))+'/L3_options_'+datadate+'.csv')
#   df_quotes = pd.read_csv('media/option_data/Option Data/Historical/'+datadate[0:4]+'/'+str(int(datadate[4:6]))+'/L3_stockquotes_'+datadate+'.csv')
#   files = df_quotes['symbol'].unique()
# #   file = open('media/symbol.json', 'r')
# #   files = json.load(file)
#   print(datadate)
# #   print(files)
#   numbers = random.sample(range(1,5000), 350)
#   for num,symbol in enumerate(files):
#         print(num, symbol)
#         df_value = df[df["UnderlyingSymbol"] == symbol]
#         # df_value = df_value.to_pandas_df()
#         try:
#             df_value[" DataDate"] = pd.to_datetime(df_value[" DataDate"])
#             df_value["DataDate"] = pd.to_datetime(df_value[" DataDate"])
#         except:
#             df_value[" DataDate"] = pd.to_datetime(df_value["DataDate"])
#             df_value["DataDate"] = pd.to_datetime(df_value["DataDate"])
#         df_value["Expiration"] = pd.to_datetime(df_value["Expiration"])
#         try:
#             inv_max = calculation_max(symbol,df_value, df_quotes)
#             final_max[symbol] = inv_max.to_dict()
#         except:
#             print("Except_max")
#             continue
#         try:
#             inv_180 = calculation_180(symbol,df_value, df_quotes)
#             final_180[symbol] = inv_180.to_dict()
#         except:
#             print("Except_180")
#             continue
#         try:
#             inv_720 = calculation_720(symbol,df_value, df_quotes)
#             final_720[symbol] = inv_720.to_dict()
#         except:
#             print("Except_720")
#             continue
#   print('data calculated...')
#   with open("media/invex_ratio_daily/invex_max_"+datadate+".json", "w") as f:
#     json.dump(final_max, f)
#
#   with open("media/invex_ratio_daily/invex_180_"+datadate+".json", "w") as f:
#     json.dump(final_180, f)
#
#   with open("media/invex_ratio_daily/invex_720_"+datadate+".json", "w") as f:
#     json.dump(final_720, f)
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
