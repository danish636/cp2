# import pandas as pd
# from pandas.core import indexing
# import numpy as np
# from datetime import date
# import vaex
# import math
#
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
# def calculation(symbol,step_size,month_filter,strike_perc,startdate,enddate,data_date):
#   #df = vaex.open("stock_data/media/L3_options_20211123.hdf5")
#   df = vaex.open("stock_data/media/option_data/L3_options_" + data_date + ".hdf5")
#   df_value = df[df["UnderlyingSymbol"] == symbol]
#   df_value = df_value.to_pandas_df()
#   df_value[" DataDate"] = pd.to_datetime(df_value[" DataDate"])
#   df_value["Expiration"] = pd.to_datetime(df_value["Expiration"])
#
#   datadate = df_value[' DataDate'].dt.date.iloc[0]
#
#
#   df_value["rolling"] = (df_value['Expiration'] - df_value[' DataDate']).dt.days
#
#   #df_quotes = pd.read_csv("stock_data/media/L3_stockquotes_20211123.csv")
#   df_quotes = pd.read_csv("stock_data/media/option_data/Option Data/Historical/"+data_date[0:4]+"/"+str(int(data_date[4:6]))+"/L3_stockquotes_" + data_date + ".csv")
#   # data = pd.read_csv("/content/Daily_data/" + symbol + ".csv",parse_dates=["date"])
#   data = pd.read_json("https://cloud.iexapis.com/stable/stock/" + symbol + "/chart/max?token=pk_55e019e9e4db4baaa9493d29a095bf63")
#
#   data["date"] = pd.to_datetime(data["date"])
#   data = data[data["date"].dt.date <= datadate]
#   data = data[(data["date"].dt.date >= startdate.date()) & (data["date"].dt.date <= enddate.date())]
#   rolling_df = df_value[df_value["rolling"]<=month_filter]
#   real_rolling = rolling_df["rolling"].unique() #[6, 24, 59, 142]
#   expirations = rolling_df["Expiration"].dt.date.unique()
#   expirations.sort()
#   rolling = list(filter(lambda day: day <= (len(data) - 10), real_rolling))
#   rolling.sort()
#   datadate = df_value[" DataDate"].iloc[0].date()
#   sym_data = df_quotes[df_quotes["symbol"] == symbol]
#   current_price=sym_data["close"].iloc[0]
#   invex = pd.DataFrame([])
#
#
#   #loop over each rolling value
#   for j,rolling_value in enumerate(real_rolling):
#     #print(rolling_value)
#     #if rolling value is in rolling array than work with normal calculations
#     #if rolling_value in rolling:
#     new_data = pd.DataFrame([])
#     df_value_1 = df_value[df_value["rolling"] == rolling_value]
#     expiration_date = str(df_value_1["Expiration"].iloc[0].date())
#     if rolling_value in rolling:
#       df_1 = pd.DataFrame([])
#       df_2 = pd.DataFrame([])
#       data['date'] = pd.to_datetime(data['date'])
#       data = data.sort_values(by='date',ascending=False)
#       data['high_value_'+ str(rolling_value)] = data['high'].rolling(rolling_value).max()
#       data['low_value_'+ str(rolling_value)] = data['low'].rolling(rolling_value).min()
#       data['change_mid_'+ str(rolling_value)] = ((data['high_value_'+ str(rolling_value)].astype('float') - data['low_value_'+ str(rolling_value)].astype('float')) / data['open'].astype('float'))*100.0
#       least_value = int(data['change_mid_'+ str(rolling_value)].min())
#       high_value = math.ceil(data['change_mid_'+ str(rolling_value)].max()) + 1.0
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
#       df_1["space_" + str(2*j + 2)] = [""] * len(df_1.index)
#       df_2["Actual_bins_" + str(rolling_value)] = np.append(bins_array[i_up:i_down],[""])
#       df_2["Actual_probability_" + str(rolling_value)] = required_prob
#       df_2["Normalized_probability_" + str(rolling_value)] = normal_prob
#       df_2["Weighted_Average_" + str(rolling_value)] = weighted_avg
#       data = pd.concat([data.reset_index(drop=True),df_1.reset_index(drop=True),df_2.reset_index(drop=True)], axis=1)
#
#
#       #Invex ratio calculation:
#       lower_price = float(current_price - ((current_price*(strike_perc / 10))/10.0))
#       higher_price = float(current_price + ((current_price*(strike_perc / 10))/10.0))
#       #print(lower_price, higher_price)
#       call_value = df_value_1[(df_value_1["Strike"].gt(lower_price)) & (df_value_1["Strike"].lt(higher_price)) & (df_value_1["Type"]=="call")]
#       put_value = df_value_1[(df_value_1["Strike"].gt(lower_price)) & (df_value_1["Strike"].lt(higher_price)) & (df_value_1["Type"]=="put")]
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
#       new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#       new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#       new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#       new_data["Invex_ratio_put_" + str(rolling_value)] = (new_data["HVTF_put_"+str(rolling_value)].values * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#       new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#     else:
#
#       new_data["Bid_call_" + str(rolling_value)] = invex["Bid_call_" + str(rol)].values#call_value["Bid"].values
#       new_data["Ask_call_" + str(rolling_value)] = invex["Ask_call_" + str(rol)].values#call_value["Ask"].values
#       new_data["Mid_call_"+str(rolling_value)] = invex["Mid_call_" + str(rol)].values#(call_value["Bid"].values + call_value["Ask"].values) /2.0
#       #time_value_call = time_value_call_cal(np.array(call_value["Strike"]), current_price, np.array(new_data["Mid_call_"+str(rolling_value)]), np.array(new_data["Ask_call_"+str(rolling_value)]))
#       new_data["Time_value_call_"+str(rolling_value)] = invex["Time_value_call_"+str(rol)].values#time_value_call
#       new_data["Strike_" + str(rolling_value)] = invex["Strike_"+str(rol)].values
#       new_data["Bid_put_" + str(rolling_value)] = invex["Bid_put_"+str(rol)].values #put_value["Bid"].values
#       new_data["Ask_put_" + str(rolling_value)] = invex["Ask_put_"+str(rol)] #put_value["Ask"].values
#       new_data["Mid_put_"+str(rolling_value)] = invex["Mid_put_"+str(rol)] #(put_value["Bid"].values + put_value["Ask"].values) /2.0
#       #time_value_put = time_value_put_cal(np.array(put_value["Strike"]), current_price, np.array(new_data["Mid_put_"+str(rolling_value)]), np.array(new_data["Ask_put_"+str(rolling_value)]))
#       new_data["Time_value_put_"+str(rolling_value)] = invex["Time_value_put_"+str(rol)] #time_value_put
#       new_data["space_" + str(3*j+ 1)] = [""] * len(new_data.index)
#       new_data["%_change_call_"+str(rolling_value)] = invex["%_change_call_"+str(rol)] #np.array((abs((new_data['Strike_'+str(rolling_value)].values)-current_price)/current_price)*100.0)
#
#       new_data["Prob_Strike_call_" + str(rolling_value)] = invex["Prob_Strike_call_" + str(rol)]
#       w_a_s = (((1 + float(weighted_avg_sum / 100)) ** (float(rolling_value / rol))) - 1) * 100.0
#       #print(len(new_data["Bid_call_" + str(rolling_value)].difference(['NaN'])))
#       #print(len(set(new_data["Bid_call_"+str(rolling_value)]) - set(new_data["Bid_call_"+str(rolling_value)].notnull())))
#       hvtf_arr = np.array([w_a_s]*last_len)
#       new_data["HVTF_call_" + str(rolling_value)] = np.append(hvtf_arr, [" "]*(len(new_data.index) - last_len))   #last_len#
#       new_data["Invex_ratio_call_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_call_" + str(rolling_value)].values * current_price) / (new_data["Time_value_call_"+str(rolling_value)].values * 10000.0)
#       new_data["space_" + str(3*j + 2)] = [""] * len(new_data.index)
#       new_data["Prob_Strike_put_" + str(rolling_value)] = new_data["Prob_Strike_call_" + str(rolling_value)]
#       new_data["HVTF_put_" + str(rolling_value)] = new_data["HVTF_call_" + str(rolling_value)]
#       new_data["Invex_ratio_put_" + str(rolling_value)] = (w_a_s * new_data["Prob_Strike_put_" + str(rolling_value)].values * current_price) / (new_data["Time_value_put_"+str(rolling_value)].values * 10000.0)
#       new_data["space_" + str(3*j+3)] = [""] * len(new_data.index)
#
#     invex = pd.concat([invex, new_data], axis=1)
#     #new_data.to_csv('/content/newdata'+str(rolling_value)+'.csv')
#   return invex,current_price,datadate,list(real_rolling),list(expirations)
#   #data = data.sort_values(by='date',ascending=False)
#   # data.to_csv('/content/testdata'+symbol+".csv")
#   # invex.to_csv('/content/invexdata'+symbol+'.csv')