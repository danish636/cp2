# import pandas as pd
# from datetime import date, timedelta
# import os.path
#
#
# date = "2022/04/28"
# start_date = date.replace("/", "-")
# date_time = pd.to_datetime(date,format='%Y/%m/%d')
# end_date = str(date_time - timedelta(days=30)).split(" ")[0]                                                    ## For year used 365
# year_dates = pd.bdate_range(start=end_date, end=start_date)
# columns = ['symbol', 'quotedate', 'iv30call', 'iv30put', 'iv30mean', 'iv60call',
#        'iv60put', 'iv60mean', 'iv90call', 'iv90put', 'iv90mean', 'iv120call',
#        'iv120put', 'iv120mean', 'iv150call', 'iv150put', 'iv150mean',
#        'iv180call', 'iv180put', 'iv180mean', 'iv360call', 'iv360put',
#        'iv360mean', 'callvol', 'putvol', 'totalvol', 'calloi', 'putoi',
#        'totaloi']
#
#
# str_date = '20220428'
# df = pd.read_csv(f"media/option_data/Option Data/Historical/{str_date[0:4]}/{str(int(str_date[4:6]))}/L3_optionstats_{str_date}.csv")
# symbols = df['symbol'].unique()
#
#
# #To create the data
# # for ticker in symbols:
# #     if os.path.isfile(f'media/website/quote/{ticker}.csv'):
# #         print(f'Done........{ticker}')
# #     else:
# #         print(ticker)
# #         one_year = pd.DataFrame(columns=columns)
# #         for x in year_dates:
# #             try:
# #                 y = str(x.date()).replace("-", "")
# #                 temp = pd.read_csv(f"media/option_data/Option Data/Historical/{y[0:4]}/{str(int(y[4:6]))}/L3_optionstats_{y}.csv")
# #                 temp = temp[temp["symbol"] == ticker]
# #                 one_year = pd.concat([one_year, temp])
# #             except:
# #                 pass
# #         #
# #         one_year = one_year.reset_index(drop=True)
# #         one_year["quotedate"] = pd.to_datetime(one_year["quotedate"], format="%m/%d/%Y")
# #         temp_file = pd.read_csv(f'media/website/quote/{ticker}.csv')
# #         one_year.to_csv(f'media/website/quote/{ticker}.csv')
#
# #         # final_d = pd.concat([temp_file,one_year],axis=0).drop_duplicates(subset=['quotedate']).reset_index(drop=True)
# #         # final_d['date'] = pd.to_datetime(final_d['quotedate'])
# #         # final_d = final_d.sort_values(by="quotedate")
# #         # final_d.to_csv(f'media/website/quote/{ticker}.csv',index=False)
#
#
#
#
# #To update the data
# for ticker in symbols:
#     print(ticker)
#     one_year = pd.DataFrame(columns=columns)
#     for x in year_dates:
#         try:
#             y = str(x.date()).replace("-", "")
#             temp = pd.read_csv(f"media/option_data/Option Data/Historical/{y[0:4]}/{str(int(y[4:6]))}/L3_optionstats_{y}.csv")
#             temp = temp[temp["symbol"] == ticker]
#             one_year = pd.concat([one_year, temp])
#         except:
#             pass
#     one_year = one_year.reset_index(drop=True)
#     one_year["quotedate"] = pd.to_datetime(one_year["quotedate"], format="%m/%d/%Y")
#
#     if os.path.isfile(f'media/website/quote/{ticker}.csv'):
#         temp_file = pd.read_csv(f'media/website/quote/{ticker}.csv')
#         final_d = pd.concat([temp_file,one_year],axis=0).drop_duplicates(subset=['quotedate']).reset_index(drop=True)
#         final_d['quotedate'] = pd.to_datetime(final_d['quotedate'])
#         final_d = final_d.sort_values(by="quotedate")
#         final_d.to_csv(f'media/website/quote/{ticker}.csv',index=False)
#     else:
#         one_year.to_csv(f'media/website/quote/{ticker}.csv')
#
#
#
#
#