# import pandas as pd
# from pandas.core import indexing
# import numpy as np
# from datetime import date,timedelta
# import statistics as st
# import vaex
# import math
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
#
# def calculation(symbol,step_size,month_filter,strike_perc,filter_days,minimum_days):
#   df = vaex.open("C:/Users/Raj/Desktop/stock_data/stock_project/stock_project/media/L3_options_20211123.hdf5")
#   df_value = df[df["UnderlyingSymbol"] == symbol]
#   df_value = df_value.to_pandas_df()
#   df_value[" DataDate"] = pd.to_datetime(df_value[" DataDate"])
#   df_value["Expiration"] = pd.to_datetime(df_value["Expiration"])
#
#   df_value["rolling"] = (df_value['Expiration'] - df_value[' DataDate']).dt.days
#   df_quotes = pd.read_csv("C:/Users/Raj/Desktop/stock_data/stock_project/stock_project/media/L3_stockquotes_20211123.csv")
#
#   # for symbol in symbol_list:
#   filter_date = df_value[" DataDate"].iloc[0].date() - timedelta(days=filter_days)
#
#   data = pd.read_json("https://cloud.iexapis.com/stable/stock/" + symbol + "/chart/max?token=pk_55e019e9e4db4baaa9493d29a095bf63")
#   data["date"] = pd.to_datetime(data["date"])
#   data = data[data["date"].dt.date > filter_date]
#
#   # data = pd.read_csv("C:/Users/Raj/Desktop/stock_data/stock_project/stock_project/media/Daily_data/" + symbol + ".csv",parse_dates=["date"])
#   # month_filter = 180
#   rolling_df = df_value[df_value["rolling"]<=month_filter]
#   rolling = rolling_df["rolling"].unique()
#   # real_rolling = rolling_df["rolling"].unique()
#   # rolling = list(filter(lambda day: day <= (len(data) - 10), real_rolling))
#   # rolling.append(minimum_days)
#   rolling.sort()
#   # differences = list((set(real_rolling) - set(rolling)).union(set(real_rolling) - set(rolling)))
#
#   #invex = pd.DataFrame([])
#   invex = pd.DataFrame([], columns=["DataDate", "Expiration" , "Rolling_value", "UnderlyingPrice","Bid_call_", "Ask_call_", "Mid_call_", "Time_value_call_",
#                                   "Strike_", "Bid_put_", "Ask_put_", "Mid_put_", "Time_value_put_",
#                                   "space_1", "%_change_call_", "prob_strike_call_", "HVTF_call_",
#                                   "Invex_ratio_call_", "space_2", "%_change_put_", "prob_strike_put_",
#                                   "HVTF_put_", "Invex_ratio_put_", "CP_ratio"])
#   #rolling = [3]
#
#
#   invex_avg_call = []
#   invex_avg_put = []
#   for j,rolling_value in enumerate(rolling):
#     new_data = pd.DataFrame([])
#     #print(rolling_value)
#     data['date'] = pd.to_datetime(data['date'])
#     df_value_1 = df_value[df_value["rolling"] == rolling_value]
#     #print(df_value)
#     data = data.sort_values(by='date',ascending=False)
#
#     data['high_value_'+ str(rolling_value)] = data['high'].rolling(rolling_value).max()
#     data['low_value_'+ str(rolling_value)] = data['low'].rolling(rolling_value).min()
#     data['change_mid_'+ str(rolling_value)] = ((data['high_value_'+ str(rolling_value)] - data['low_value_'+ str(rolling_value)]) / data['open'].astype('float'))*100.0
#     #print(data.head(30))
#     #print("data1")c
#
#     least_value = int(data['change_mid_'+ str(rolling_value)].min())
#     high_value = math.ceil(data['change_mid_'+ str(rolling_value)].max()) + 1.0   #math.ceil(data['change_mid_'+ str(rolling_value)].iloc[data['change_mid_'+ str(rolling_value)].idxmax()]) + 1
#     #print(least_value, high_value)
#     bins_array = np.round(np.arange(least_value, high_value, step_size), 2)
#     frequency = data['change_mid_'+ str(rolling_value)].value_counts(bins=bins_array).sort_index(axis=0)
#     freq_total = frequency.sum()
#     temp_arr = bins_array[1:]
#     bins_array = np.append(temp_arr, 0)
#     #print(f"frequency: {freq_total}")
#
#     prob_data = np.array((frequency/freq_total)*100.0)
#     i_up, y_up = up_value(prob_data)
#     i_down, y_down = down_value(prob_data)
#     #print(y_up, y_down)
#
#     cumulative_prob = np.cumsum(prob_data)
#     #print(cumulative_prob)
#
#     prob_data_required = prob_data[i_up:i_down]
#     required_prob = prob_data_required
#     prob_require_total = (sum(prob_data_required)+y_up+y_down-20)/100
#     prob_data_required[0] = prob_data_required[0] + y_up - 10
#     prob_data_required[-1] = prob_data_required[-1] + y_down - 10
#
#     normal_prob = prob_data_required/prob_require_total
#     #print("normal_prob")
#
#     bins_array_required = bins_array[i_up:i_down]
#     weighted_avg = (normal_prob*bins_array_required)/100.0
#     weighted_avg_sum = weighted_avg.sum()
#
#     required_prob = np.append(required_prob, required_prob.sum())
#     normal_prob = np.append(normal_prob, normal_prob.sum())
#     weighted_avg = np.append(weighted_avg, weighted_avg.sum())
#     if len(data.index)>=len(bins_array):
#       #print("IF")
#       data["space_" + str(2*j + 1)] = [""] * len(data.index)
#       data["bins_"+ str(rolling_value)] = np.append(bins_array, [0.0]*(len(data.index)-len(bins_array))).astype('float32')
#       data["Frequency_" + str(rolling_value)] = np.append(frequency, [""]*(len(data.index)-len(frequency)))
#       data["Probability_" + str(rolling_value)] = np.append(prob_data, [""]*(len(data.index)-len(prob_data)))
#       data["Cumulative_" + str(rolling_value)] = np.append(cumulative_prob, [""]*(len(data.index)-len(cumulative_prob)))
#       data["space_" + str(2*j + 2)] = [""] * len(data.index)
#
#       data["Actual_bins_" + str(rolling_value)] = np.append(bins_array[i_up:i_down], [""]*(len(data.index)-len(bins_array[i_up:i_down])))
#       data["Actual_probability_" + str(rolling_value)] = np.append(required_prob, [""]*(len(data.index)-len(required_prob)))
#       data["Normalized_probability_" + str(rolling_value)] = np.append(normal_prob, [""]*(len(data.index)-len(normal_prob)))
#       data["Weighted_Average_" + str(rolling_value)] = np.append(weighted_avg, [""]*(len(data.index)-len(weighted_avg)))
#     else:
#       loop = len(bins_array) - len(data.index) +1
#
#       data = data.reindex(list(range(0, len(bins_array[:-1])))).reset_index(drop=True)
#       data["space_"+str(2*j + 1)] = [""]*len(bins_array[:-1])
#       data["bins_"+str(rolling_value)] = np.array(bins_array[:-1]).astype("float")
#
#       data["Frequency_" + str(rolling_value)] = np.array(frequency)
#       data["Probability_" + str(rolling_value)] = np.array(prob_data)
#       data["Cumulative_" + str(rolling_value)] = np.array(cumulative_prob)
#       data["space_" + str(2*j + 2)] = [""] * len(data.index)
#
#       data["Actual_bins_" + str(rolling_value)] = np.append(bins_array[i_up:i_down], [""]*(len(data.index)-len(bins_array[i_up:i_down])))
#       data["Actual_probability_" + str(rolling_value)] = np.append(required_prob, [""]*(len(data.index)-len(required_prob)))
#       data["Normalized_probability_" + str(rolling_value)] = np.append(normal_prob, [""]*(len(data.index)-len(normal_prob)))
#       data["Weighted_Average_" + str(rolling_value)] = np.append(weighted_avg, [""]*(len(data.index)-len(weighted_avg)))
#     # data.to_csv("/content/temp_"+symbol+".csv")
#     sym_data = df_quotes[df_quotes["symbol"] == symbol]
#     current_price=sym_data["close"].iloc[0]
#
#     lower_price = float(current_price - ((current_price*strike_perc)/100.0))
#     higher_price = float(current_price + ((current_price*strike_perc)/100.0))
#     call_value = df_value_1[(df_value_1["Strike"] > lower_price) & (df_value_1["Strike"] < higher_price) & (df_value_1["Type"]=="call")]
#     put_value = df_value_1[(df_value_1["Strike"] > lower_price) & (df_value_1["Strike"] < higher_price) & (df_value_1["Type"]=="put")]
#
#     # call_value.to_csv("call_value.csv")
#     # put_value.to_csv("put_value.csv")
#
#     new_data["Bid_call_"] = call_value["Bid"].values
#     new_data["Ask_call_"] = call_value["Ask"].values
#     new_data["Mid_call_"] = (call_value["Bid"].values + call_value["Ask"].values)/2.0
#     time_value_call = time_value_call_cal(np.array(call_value["Strike"]), current_price, np.array(new_data["Mid_call_"].astype("float")), np.array(new_data["Ask_call_"].astype("float")))
#     new_data["Time_value_call_"] = time_value_call
#
#     new_data['Strike_'] = call_value["Strike"].values
#
#     new_data["Bid_put_"] = put_value["Bid"].values
#     new_data["Ask_put_"] = put_value["Ask"].values
#     new_data["Mid_put_"] = (put_value["Bid"].values + put_value["Ask"].values)/2.0
#     time_value_put = time_value_put_cal(np.array(call_value["Strike"]), current_price, np.array(new_data["Mid_put_"]), np.array(new_data["Ask_put_"]))
#     new_data["Time_value_put_"] = time_value_put
#
#     new_data["%_change_call_"] = abs(np.array((((new_data['Strike_'])-current_price)/current_price)*100.0))
#
#     prob_strike_ls_call = np.empty(len(new_data["%_change_call_"]))
#     for t,k in enumerate(np.array(new_data["%_change_call_"])):
#       l_value = round(float(math.ceil(k/step_size) * step_size), 2)
#
#
#       if l_value<=least_value:
#         prob_strike_ls_call[t] = 0.0
#
#       elif l_value>=high_value:
#         prob_strike_ls_call[t] = cumulative_prob[-1]
#
#       else:
#         if data["bins_"+str(rolling_value)].dtypes == 'object':
#           l_value = str(l_value)
#         d = data[data["bins_"+str(rolling_value)] == l_value]
#
#         prob_strike_ls_call[t] = d["Cumulative_"+str(rolling_value)].values
#
#     new_data["prob_strike_call_"] = 100.0 - np.array(prob_strike_ls_call, dtype='float32')
#
#     a = np.empty(len(new_data.index))
#     a.fill(weighted_avg_sum)
#     new_data["HVTF_call_"] = a
#     new_data["Invex_ratio_call_"] = ((new_data["prob_strike_call_"].astype("float")/100.0) * (new_data["HVTF_call_"].astype("float")/100.0) * current_price) / new_data["Time_value_call_"].astype("float")
#
#     new_data["%_change_put_"] = new_data["%_change_call_"].values
#     new_data["prob_strike_put_"] = new_data["prob_strike_call_"].values
#     # new_data["%_change_put_"] = abs(np.array((((new_data['Strike_'])-current_price)/current_price)*100.0))
#     # prob_strike_ls_put = np.empty(len(new_data["%_change_put_"]))
#     # for t,k in enumerate(np.array(new_data["%_change_put_"])):
#     #   l_value = float(math.ceil(k/step_size) * step_size)
#     #   if l_value<=least_value or l_value>=high_value:
#     #     if data["bins_"+str(rolling_value)].dtypes == 'object':
#     #       l_value = str(l_value)
#     #     prob_strike_ls_put[t] = 0.0
#     #   else:
#     #     if data["bins_"+str(rolling_value)].dtypes == 'object':
#     #       l_value = str(l_value)
#     #     d = data[data["bins_"+ str(rolling_value)] == round(l_value,2)]
#
#     #     prob_strike_ls_put[t] = d["Cumulative_" + str(rolling_value)]
#
#     # new_data["prob_strike_put_"] = 100.0 - prob_strike_ls_put
#
#     new_data["HVTF_put_"] = new_data["HVTF_call_"].values
#     new_data["Invex_ratio_put_"] = ((new_data["prob_strike_put_"].astype('float')/100.0) * (new_data["HVTF_put_"].astype("float")/100.0) * current_price) / new_data["Time_value_put_"].astype("float")
#     new_data["CP_ratio"] = new_data["Invex_ratio_call_"].astype("float") / new_data["Invex_ratio_put_"].astype("float")
#     invex_avg_call.append(new_data["Invex_ratio_call_"].mean())
#     invex_avg_put.append(new_data["Invex_ratio_put_"].mean())
#     exp_date = rolling_df[rolling_df["rolling"] == rolling_value]
#     exp_date = str(exp_date["Expiration"].iloc[0].date())
#     #new_data.at[len(new_data), 'Bid_call_'] = rolling_value
#     #new_data = new_data.shift()
#     new_data.at[0, 'Rolling_value'] = rolling_value
#     new_data.at[0, 'Expiration'] = exp_date
#     new_data.at[0, "DataDate"] = str(rolling_df[" DataDate"].iloc[0].date())
#     new_data.at[0, 'UnderlyingPrice'] = current_price
#
#     new_data.loc[len(new_data)] = " "
#
#     invex = pd.concat([invex, new_data], axis=0)
#     invex = invex.fillna("")
#   print(st.mean(invex_avg_call))
#   print(st.mean(invex_avg_put))
#
#   return invex
#
#
#
#
