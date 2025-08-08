# import pandas as pd
# from datetime import date
# import json
# import statistics
# import numpy as np
# import math
# import os
# # dates = ['2022-08-31']
#
# curr_date = str(date.today()).replace('-', '')
# #get first csv file
# # for curr_date in dates:
# #     curr_date = str(curr_date).replace('-', '')
# #     print(curr_date)
# #     try:
# print('read data-1')
# data = pd.read_csv('https://financialmodelingprep.com/api/v4/profile/all?apikey=b1360803f80dd08bdd0211c5c004ad03')
# data["symbol"] = data["Symbol"]
# data.drop('Symbol', axis=1, inplace=True)
#
# #currency filter --> USD
# # data = data.loc[data['currency'] == 'USD']
#
# #exchange filter --> 'AMEX', 'NASDAQ', 'NYSE', 'BATS', 'OTC'
# # data = data.loc[data['exchangeShortName'].isin(['AMEX', 'NASDAQ', 'NYSE', 'BATS', 'OTC'])]
#
# #isETF filter --> False
# data = data[data['isEtf'] == False]
#
# #isFund filter --> False
# data = data[data['isFund'] == False]
#
# #isAdr filter --> False
# # data = data[data['isAdr'] == False]
#
# #isActivelyTrading filter --> True
# data = data[data['isActivelyTrading'] == True]
#
# print('read data-2')
# #get second csv file
# data2 = pd.read_csv('https://financialmodelingprep.com/api/v4/key-metrics-ttm-bulk?apikey=b1360803f80dd08bdd0211c5c004ad03')
#
# print('read data-3')
# #get third csv file
# data3 = pd.read_csv('https://financialmodelingprep.com/api/v4/ratios-ttm-bulk?apikey=b1360803f80dd08bdd0211c5c004ad03')
# final = pd.merge(pd.merge(data,data2, how="left", on='symbol'),data3,how="left", on='symbol')
# final['Revenue'] = [final['MktCap'][i]/final['priceToSalesRatioTTM_x'][i] for i in range(len(final))]
#
#
# final.drop(final[final['sector'] == 'Financial'].index, inplace = True)
# final.drop(final[final['sector'] == 'Conglomerates'].index, inplace = True)
# final.drop(final[(final['sector'] == 'Financial') & (final['industry'] == 'Gold')].index, inplace = True)
#
# # print(final)
# # final.to_csv('media/screener_data/screener_'+str(curr_date)+'.csv', index=False)
#
#
#
#
# # df = pd.read_csv("final.csv")
# df = final
#
#
# # print(pd.merge(df_1.fillna(0),df,on="symbol",how="outer"))
# # print(len(df))
# # print(len(df_1))
# cols = ['Price','enterpriseValueMultipleTTM','evToFreeCashFlowTTM','evToOperatingCashFlowTTM','evToSalesTTM', 'grahamNumberTTM','priceEarningsRatioTTM','priceEarningsToGrowthRatioTTM','priceToBookRatioTTM','priceToFreeCashFlowsRatioTTM','priceToOperatingCashFlowsRatioTTM','priceToSalesRatioTTM_x','Revenue','MktCap']
#
# best = []
# base = []
# worst = []
# relative_best = []
# relative_base = []
# relative_worst = []
#
# symbol = []
#
#
# for i in df["industry"].unique():
#     print(i)
#     in_05 = {}
#     in_05_us = {}
#     d = df[df["industry"] == i]
#     d.replace([np.inf, -np.inf], np.nan, inplace=True)
#     d.dropna(subset=["Revenue"], how="all", inplace=True)
#     d = d[d['Revenue']>=0]
#     flag=False
#     if len(d[(d["country"] == "US") & (d['industry'] == i)]) > 50:
#         flag = True
#         dc = d[d["country"] == "US"]
#     for j in cols:
#         in_05[j] = {}
#         in_05[j] = d[d[j]>0][j].median()
#         if flag:
#             in_05_us[j] = {}
#             in_05_us[j] = dc[dc[j]>0][j].median()
#
#     for s in d["symbol"].dropna().unique():
#
#         t = d[d['symbol'] == s].reset_index()
#
#
#         if t.loc[0,'country'] == "US" and flag:
#             in_data = [in_05_us['enterpriseValueMultipleTTM'], in_05_us['evToFreeCashFlowTTM'], in_05_us['evToOperatingCashFlowTTM'], in_05_us['evToSalesTTM'],
#                         in_05_us['priceEarningsRatioTTM'], in_05_us['priceToBookRatioTTM'],
#                     in_05_us['priceToFreeCashFlowsRatioTTM'], in_05_us['priceToOperatingCashFlowsRatioTTM'], in_05_us['priceToSalesRatioTTM_x']]
#         else:
#             in_data = [in_05['enterpriseValueMultipleTTM'], in_05['evToFreeCashFlowTTM'], in_05['evToOperatingCashFlowTTM'], in_05['evToSalesTTM'],
#                         in_05['priceEarningsRatioTTM'], in_05['priceToBookRatioTTM'],
#                     in_05['priceToFreeCashFlowsRatioTTM'], in_05['priceToOperatingCashFlowsRatioTTM'], in_05['priceToSalesRatioTTM_x']]
#
#         symbol.append(s)
#         t_data = [t.loc[0,'enterpriseValueMultipleTTM'], t.loc[0,'evToFreeCashFlowTTM'], t.loc[0,'evToOperatingCashFlowTTM'], t.loc[0,'evToSalesTTM'],
#                         t.loc[0,'priceEarningsRatioTTM'], t.loc[0,'priceToBookRatioTTM'],
#                     t.loc[0,'priceToFreeCashFlowsRatioTTM'], t.loc[0,'priceToOperatingCashFlowsRatioTTM'], t.loc[0,'priceToSalesRatioTTM_x']]
#
#         average_1 = [i / j for i, j in zip(in_data, t_data) if j != 0]
#         average = [i*t["Price"][0] for i in average_1]
#         # average.pop(4)
#         average = [i for i in average if i >0.05]
#         average = sorted(average)[::-1]
#         if len(average) == 0:
#             best.append(0)
#             relative_best.append(0)
#
#             # average.append(t.loc[0,'grahamNumberTTM'])
#
#             base.append(0)
#             relative_base.append(0)
#
#             # average_2 = [i for i in average if i>0]
#             worst.append(0)
#             relative_worst.append(0)
#
#         else:
#             best.append(statistics.mean(average[:math.ceil(len(average)/2)]))
#             relative_best.append(((t["Price"][0] - statistics.mean(average[:math.ceil(len(average)/2)])) / t["Price"][0]) * 100)
#
#             base.append(statistics.mean(average))
#             relative_base.append(((t["Price"][0] - statistics.mean(average)) / t["Price"][0]) * 100)
#
#             worst.append(statistics.mean(average[-math.ceil(len(average)/2):]))
#             relative_worst.append(((t["Price"][0] - statistics.mean(average[-math.ceil(len(average)/2):])) / t["Price"][0]) * 100)
#
# fin = pd.DataFrame({})
# fin["symbol"]= symbol
# fin["best"]= best
# fin["base"]= base
# fin["worst"]= worst
# fin["relative_best"]= relative_best
# fin["relative_base"]= relative_base
# fin["relative_worst"]= relative_worst
#
#
#
# df = pd.merge(final,fin,on="symbol",how="outer")
#
# # df.to_csv('screener1.csv')
#
# # df = pd.read_csv('screener1.csv')
# # df = df.iloc[:20]
#
# # pd.set_option('display.max_columns', 100)
# relative_best_fy2 = []
# relative_best_fy5 = []
# relative_best_fy10 = []
#
# relative_base_fy2 = []
# relative_base_fy5 = []
# relative_base_fy10 = []
#
# relative_worst_fy2 = []
# relative_worst_fy5 = []
# relative_worst_fy10 = []
#
# revenue_best_fy1 = []
# revenue_best_fy2 = []
# revenue_best_fy5 = []
# revenue_best_fy10 = []
#
# revenue_base_fy1 = []
# revenue_base_fy2 = []
# revenue_base_fy5 = []
# revenue_base_fy10 = []
#
# revenue_worst_fy1 = []
# revenue_worst_fy2 = []
# revenue_worst_fy5 = []
# revenue_worst_fy10 = []
#
# erm_best_fy1 = []
# erm_best_fy2 = []
# erm_best_fy5 = []
# erm_best_fy10 = []
#
# erm_base_fy1 = []
# erm_base_fy2 = []
# erm_base_fy5 = []
# erm_base_fy10 = []
#
# erm_worst_fy1 = []
# erm_worst_fy2 = []
# erm_worst_fy5 = []
# erm_worst_fy10 = []
#
# symbol1 = []
# symbol2 = []
#
# # sym = ['AAPL']
#
# for s in df["symbol"].dropna().unique():
#     try:
#         t = df[df['symbol'] == s].reset_index()
#
#         with open('media/DCF/dcfoutputbest/'+s+'.json','r') as f:
#             best = json.loads(f.read())
#
#         with open('media/DCF/dcfoutputbase/'+s+'.json','r') as f:
#             base = json.loads(f.read())
#
#         with open('media/DCF/dcfoutputworst/'+s+'.json','r') as f:
#             worst = json.loads(f.read())
#
#         with open('media/DCF/ermbest/'+s+'.json','r') as f:
#             ermbest = json.loads(f.read())
#
#         with open('media/DCF/ermbase/'+s+'.json','r') as f:
#             ermbase = json.loads(f.read())
#
#         with open('media/DCF/ermworst/'+s+'.json','r') as f:
#             ermworst = json.loads(f.read())
#
#         fcffl = list(best.keys())
#         fcffl1 = [i[:-2] for i in fcffl]
#
#         if max(fcffl1)+'Q4' in fcffl:
#             quarter = max(fcffl1)+'Q4'
#         elif max(fcffl1)+'Q3' in fcffl:
#             quarter = max(fcffl1)+'Q3'
#         elif max(fcffl1)+'Q2' in fcffl:
#             quarter = max(fcffl1)+'Q2'
#         else:
#             quarter = max(fcffl1)+'Q1'
#
#         erml = list(ermbest.keys())
#         erml1 = [i[:-2] for i in erml]
#
#         if max(erml1)+'Q4' in erml:
#             quarter1 = max(erml1)+'Q4'
#         elif max(erml1)+'Q3' in erml:
#             quarter1 = max(erml1)+'Q3'
#         elif max(erml1)+'Q2' in erml:
#             quarter1 = max(erml1)+'Q2'
#         else:
#             quarter1 = max(erml1)+'Q1'
#
#         revenue_best_fy1.append(((t["Price"][0] - best[quarter]['Price Target Local'][0]) / t["Price"][0]) * 100)
#         revenue_base_fy1.append(((t["Price"][0] - base[quarter]['Price Target Local'][0]) / t["Price"][0]) * 100)
#         revenue_worst_fy1.append(((t["Price"][0] - worst[quarter]['Price Target Local'][0]) / t["Price"][0]) * 100)
#
#         erm_best_fy1.append(((t["Price"][0] - ermbest[quarter1]['Price Target Local'][0]) / t["Price"][0]) * 100)
#         erm_base_fy1.append(((t["Price"][0] - ermbase[quarter1]['Price Target Local'][0]) / t["Price"][0]) * 100)
#         erm_worst_fy1.append(((t["Price"][0] - ermworst[quarter1]['Price Target Local'][0]) / t["Price"][0]) * 100)
#
#         symbol1.append(str(s))
#
#     except:
#         continue
#
# df1 = pd.DataFrame([])
# df1['symbol'] = symbol1
# df1['fcff_fy1_best'] = revenue_best_fy1
# df1['fcff_fy1_base'] = revenue_base_fy1
# df1['fcff_fy1_worst'] = revenue_worst_fy1
# df1['erm_fy1_best'] = erm_best_fy1
# df1['erm_fy1_base'] = erm_base_fy1
# df1['erm_fy1_worst'] = erm_worst_fy1
#
#
# df = pd.merge(df,df1,on="symbol",how="outer")
#
#
# for s in df["symbol"].dropna().unique():
#     try:
#         relative_best_1 = []
#         relative_base_1 = []
#         relative_worst_1 = []
#         t = df[df['symbol'] == s].reset_index()
#         print(s)
#
#         with open('media/DCF/dcfoutputbest/'+s+'.json','r') as f:
#             best = json.loads(f.read())
#
#         with open('media/DCF/dcfoutputbase/'+s+'.json','r') as f:
#             base = json.loads(f.read())
#
#         with open('media/DCF/dcfoutputworst/'+s+'.json','r') as f:
#             worst = json.loads(f.read())
#
#
#         with open('media/DCF/ermbest/'+s+'.json','r') as f:
#             ermbest = json.loads(f.read())
#
#         with open('media/DCF/ermbase/'+s+'.json','r') as f:
#             ermbase = json.loads(f.read())
#
#         with open('media/DCF/ermworst/'+s+'.json','r') as f:
#             ermworst = json.loads(f.read())
#
#         fcffl = list(best.keys())
#         fcffl1 = [i[:-2] for i in fcffl]
#
#         if max(fcffl1)+'Q4' in fcffl:
#             quarter = max(fcffl1)+'Q4'
#         elif max(fcffl1)+'Q3' in fcffl:
#             quarter = max(fcffl1)+'Q3'
#         elif max(fcffl1)+'Q2' in fcffl:
#             quarter = max(fcffl1)+'Q2'
#         else:
#             quarter = max(fcffl1)+'Q1'
#
#         erml = list(ermbest.keys())
#         erml1 = [i[:-2] for i in erml]
#
#         if max(erml1)+'Q4' in erml:
#             quarter1 = max(erml1)+'Q4'
#         elif max(erml1)+'Q3' in erml:
#             quarter1 = max(erml1)+'Q3'
#         elif max(erml1)+'Q2' in erml:
#             quarter1 = max(erml1)+'Q2'
#         else:
#             quarter1 = max(erml1)+'Q1'
#
#
#         with open('media/DCF/dcfcalc/'+s+'.json','r') as f:
#             input = json.loads(f.read())
#
#         cost_of_equity = input['Cost Of Equity']
#
#         fcffl1 = list(cost_of_equity.keys())
#         fcffl11 = [i[:-2] for i in fcffl1]
#
#         if max(fcffl11)+'Q4' in fcffl1:
#             quarter2 = max(fcffl11)+'Q4'
#         elif max(fcffl11)+'Q3' in fcffl1:
#             quarter2 = max(fcffl11)+'Q3'
#         elif max(fcffl11)+'Q2' in fcffl1:
#             quarter2 = max(fcffl11)+'Q2'
#         else:
#             quarter2 = max(fcffl11)+'Q1'
#
#         relative_best_fy2.append((t['Price'].values[0] - t['best'].values[0] * (1 + cost_of_equity[quarter2]) ** 2) / t['Price'].values[0])
#         relative_best_fy5.append((t['Price'].values[0] - t['best'].values[0] * (1 + cost_of_equity[quarter2]) ** 5) / t['Price'].values[0])
#         relative_best_fy10.append((t['Price'].values[0] - t['best'].values[0] * (1 + cost_of_equity[quarter2]) ** 10) / t['Price'].values[0])
#
#         relative_base_fy2.append((t['Price'].values[0] - t['base'].values[0] * (1 + cost_of_equity[quarter2]) ** 2) / t['Price'].values[0])
#         relative_base_fy5.append((t['Price'].values[0] - t['base'].values[0] * (1 + cost_of_equity[quarter2]) ** 5) / t['Price'].values[0])
#         relative_base_fy10.append((t['Price'].values[0] - t['base'].values[0] * (1 + cost_of_equity[quarter2]) ** 10) / t['Price'].values[0])
#
#         relative_worst_fy2.append((t['Price'].values[0] - t['worst'].values[0] * (1 + cost_of_equity[quarter2]) ** 2) / t['Price'].values[0])
#         relative_worst_fy5.append((t['Price'].values[0] - t['worst'].values[0] * (1 + cost_of_equity[quarter2]) ** 5) / t['Price'].values[0])
#         relative_worst_fy10.append((t['Price'].values[0] - t['worst'].values[0] * (1 + cost_of_equity[quarter2]) ** 10) / t['Price'].values[0])
#
#         revenue_best_fy2.append((t['Price'].values[0] - t['fcff_fy1_best'].values[0] * (1 + cost_of_equity[quarter]) ** 2) / t['Price'].values[0])
#         revenue_best_fy5.append((t['Price'].values[0] - t['fcff_fy1_best'].values[0] * (1 + cost_of_equity[quarter]) ** 5) / t['Price'].values[0])
#         revenue_best_fy10.append((t['Price'].values[0] - t['fcff_fy1_best'].values[0] * (1 + cost_of_equity[quarter]) ** 10) / t['Price'].values[0])
#
#         revenue_base_fy2.append((t['Price'].values[0] - t['fcff_fy1_base'].values[0] * (1 + cost_of_equity[quarter]) ** 2) / t['Price'].values[0])
#         revenue_base_fy5.append((t['Price'].values[0] - t['fcff_fy1_base'].values[0] * (1 + cost_of_equity[quarter]) ** 5) / t['Price'].values[0])
#         revenue_base_fy10.append((t['Price'].values[0] - t['fcff_fy1_base'].values[0] * (1 + cost_of_equity[quarter]) ** 10) / t['Price'].values[0])
#
#         revenue_worst_fy2.append((t['Price'].values[0] - t['fcff_fy1_worst'].values[0] * (1 + cost_of_equity[quarter]) ** 2) / t['Price'].values[0])
#         revenue_worst_fy5.append((t['Price'].values[0] - t['fcff_fy1_worst'].values[0] * (1 + cost_of_equity[quarter]) ** 5) / t['Price'].values[0])
#         revenue_worst_fy10.append((t['Price'].values[0] - t['fcff_fy1_worst'].values[0] * (1 + cost_of_equity[quarter]) ** 10) / t['Price'].values[0])
#
#
#         erm_best_fy2.append((t['Price'].values[0] - t['erm_fy1_best'].values[0] * (1 + cost_of_equity[quarter1]) ** 2) / t['Price'].values[0])
#         erm_best_fy5.append((t['Price'].values[0] - t['erm_fy1_best'].values[0] * (1 + cost_of_equity[quarter1]) ** 5) / t['Price'].values[0])
#         erm_best_fy10.append((t['Price'].values[0] - t['erm_fy1_best'].values[0] * (1 + cost_of_equity[quarter1]) ** 10) / t['Price'].values[0])
#
#         erm_base_fy2.append((t['Price'].values[0] - t['erm_fy1_base'].values[0] * (1 + cost_of_equity[quarter1]) ** 2) / t['Price'].values[0])
#         erm_base_fy5.append((t['Price'].values[0] - t['erm_fy1_base'].values[0] * (1 + cost_of_equity[quarter1]) ** 5) / t['Price'].values[0])
#         erm_base_fy10.append((t['Price'].values[0] - t['erm_fy1_base'].values[0] * (1 + cost_of_equity[quarter1]) ** 10) / t['Price'].values[0])
#
#         erm_worst_fy2.append((t['Price'].values[0] - t['erm_fy1_worst'].values[0] * (1 + cost_of_equity[quarter1]) ** 2) / t['Price'].values[0])
#         erm_worst_fy5.append((t['Price'].values[0] - t['erm_fy1_worst'].values[0] * (1 + cost_of_equity[quarter1]) ** 5) / t['Price'].values[0])
#         erm_worst_fy10.append((t['Price'].values[0] - t['erm_fy1_worst'].values[0] * (1 + cost_of_equity[quarter1]) ** 10) / t['Price'].values[0])
#
#         symbol2.append(s)
#
#     except:
#         continue
#
# df2 = pd.DataFrame([])
# df2['symbol'] = symbol2
# df2['relative_best_1'] = relative_best_fy2
# df2['relative_best_fy5'] = relative_best_fy5
# df2['relative_best_fy10'] = relative_best_fy10
#
# df2['relative_base_fy2'] = relative_base_fy2
# df2['relative_base_fy5'] = relative_base_fy5
# df2['relative_base_fy10'] = relative_base_fy10
#
# df2['relative_worst_fy2'] = relative_worst_fy2
# df2['relative_worst_fy5'] = relative_worst_fy5
# df2['relative_worst_fy10'] = relative_worst_fy10
#
# df2['fcff_fy2_best'] = revenue_best_fy2
# df2['fcff_fy5_best'] = revenue_best_fy5
# df2['fcfffy10_best'] = revenue_best_fy10
#
# df2['fcff_fy2_base'] = revenue_base_fy2
# df2['fcff_fy5_base'] = revenue_base_fy5
# df2['fcff_fy10_base'] = revenue_base_fy10
#
# df2['fcff_fy2_worst'] = revenue_worst_fy2
# df2['fcff_fy5_worst'] = revenue_worst_fy5
# df2['fcff_fy10_worst'] = revenue_worst_fy10
#
# df2['erm_fy2_best'] = erm_best_fy2
# df2['erm_fy5_best'] = erm_best_fy5
# df2['erm_fy10_best'] = erm_best_fy10
#
# df2['erm_fy2_base'] = erm_base_fy2
# df2['erm_fy5_base'] = erm_base_fy5
# df2['erm_fy10_base'] = erm_base_fy10
#
# df2['erm_fy2_worst'] = erm_worst_fy2
# df2['erm_fy5_worst'] = erm_worst_fy5
# df2['erm_fy10_worst'] = erm_worst_fy10
#
# df = pd.merge(df,df2,on="symbol",how="outer")
#
# ##################################################################################################
# df.to_csv('media/screener_data/screener_'+str(curr_date)+'.csv', index=False)
#
# def number_to_string(number):
#     suffixes = ["", "K", "M", "B", "T", "Qua", "Qui"]
#     number = round(number,2)
#     # Turn the int number into a string and format with ,'s
#     number = str("{:,}".format(number))
#     # For loop to find the amount of commas in the newly made string
#     commas = 0
#     x = 0
#     while x < len(number):
#         if number[x] == ',':
#             commas += 1
#         x += 1
#     # Use the amount of commas to decide the element in the array that will be used as a suffix
#     # for example, if there are 2 commas it will use million.
#     return number.split(',')[0]+ suffixes[commas]
#
# numerical_features = [feature for feature in df.columns if df[feature].dtypes != 'O' and df[feature].dtypes != 'bool']
# df1 = df[numerical_features].copy()
# data_limit = {}
# percentage_columns = ["returnOnTangibleAssetsTTM","returnOnAssetsTTM","returnOnEquityTTM","returnOnCapitalEmployedTTM","ebtPerEbitTTM","grossProfitMarginTTM","netIncomePerEBTTTM","netProfitMarginTTM","operatingProfitMarginTTM","pretaxProfitMarginTTM","researchAndDevelopementToRevenueTTM","salesGeneralAndAdministrativeToRevenueTTM","dividendPaidAndCapexCoverageRatioTTM","dividendYieldTTM_y","earningsYieldTTM","freeCashFlowYieldTTM"]
# for x in df1.columns:
#     minimum = df1[x].min()
#     maximum = df1[x].max()
#     data_limit[x] = {}
#     data_limit[x]['Any'] = str(minimum)+'_'+str(maximum)+"_0"
#     try:
#         if "capex" in x:
#             limits = np.array([minimum,np.percentile(df[x].dropna(),20), np.percentile(df[x].dropna(),40), np.percentile(df[x].dropna(),60), np.percentile(df[x].dropna(),80),maximum])
#             limits = limits[::-1]
#         else:
#             limits = np.array([0,np.percentile(df[df[x] > 0][x].dropna(),20), np.percentile(df[df[x] > 0][x].dropna(),40), np.percentile(df[df[x] > 0][x].dropna(),60), np.percentile(df[df[x] > 0][x].dropna(),80),maximum])
#     except:
#         limits = np.linspace(0, maximum, 6)
#     if minimum < 0 and "capex" not in x:
#         # limits = np.linspace(0, maximum, 6)
#         data_limit[x]['Negative (Below 0)'] = str(minimum)+'_'+str(0)
#     # else:
#         # limits = np.linspace(minimum, maximum, 6)
#     limits = np.around(limits, decimals=2)
#     if x in percentage_columns:
#         data_limit[x]['Very Low ('+number_to_string(limits[0]*100)+'% to '+number_to_string(limits[1]*100) + '%)'] = str(limits[0])+'_'+str(limits[1])
#         data_limit[x]['Low ('+number_to_string(limits[1]*100)+'% to '+number_to_string(limits[2]*100) + '%)'] = str(limits[1])+'_'+str(limits[2])
#         data_limit[x]['Medium ('+number_to_string(limits[2]*100)+'% to '+number_to_string(limits[3]*100) + '%)'] = str(limits[2])+'_'+str(limits[3])
#         data_limit[x]['High ('+number_to_string(limits[3]*100)+ '% to '+number_to_string(limits[4]*100) + '%)'] = str(limits[3])+'_'+str(limits[4])
#         data_limit[x]['Very High ('+number_to_string(limits[4]*100)+'% and above' + ' )'] = str(limits[4])+'_'+str(limits[5])
#
#     else:
#         data_limit[x]['Very Low ('+number_to_string(limits[0])+' to '+number_to_string(limits[1]) + ')'] = str(limits[0])+'_'+str(limits[1])
#         data_limit[x]['Low ('+number_to_string(limits[1])+' to '+number_to_string(limits[2]) + ')'] = str(limits[1])+'_'+str(limits[2])
#         data_limit[x]['Medium ('+number_to_string(limits[2])+' to '+number_to_string(limits[3]) + ')'] = str(limits[2])+'_'+str(limits[3])
#         data_limit[x]['High ('+number_to_string(limits[3])+ ' to '+number_to_string(limits[4]) + ')'] = str(limits[3])+'_'+str(limits[4])
#         data_limit[x]['Very High ('+number_to_string(limits[4])+' and above' + ')'] = str(limits[4])+'_'+str(limits[5])
#
# with open('media/screener_percentiles_data/screener_'+str(curr_date)+'.json', 'w') as f:
#     f.write(json.dumps(data_limit))
# # final.to_csv('media/screener_data/screener_'+str(curr_date)+'.csv', index=False)
# # j = final.to_dict()
# # j = json.dumps(j)
# # with open(f'media/screener_data/screener_{curr_date}.json', 'w') as f:
# #     f.write(j)
# print('complete')
#     # except:
#     #     print('Except')