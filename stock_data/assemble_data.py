# import datetime
# import vaex
# import pandas as pd
# import os
#
# now = datetime.datetime.now()
# now = now - datetime.timedelta(days=3)
# final_d = datetime.datetime(2019,9,23)
# final_date = now.strftime("%Y%m%d")
# # range_d = now - datetime.timedelta(years=3)
#
#
#
# df = pd.read_csv(f"media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_options_{str(final_date)}.csv")
# symbols = df["UnderlyingSymbol"].unique()
# option_symbols = df["OptionSymbol"].unique()
# print(final_d.date(), now.date())
# while final_d.date() != now.date():
#     print(now.date())
#     try:
#         final_date = now.strftime("%Y%m%d")
#         df = pd.read_csv(f"media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_options_{str(final_date)}.csv")
#         for i in symbols:
#         # symbol_d = df[df["UnderlyingSymbol"] == i].to_pandas_df()
#         # print(symbol_d)
#         data = df[(df["UnderlyingSymbol"] == i) & (df["OptionSymbol"].isin(option_symbols))]
#         if os.path.exists("media/company_data/" + i + ".csv"):
#             data.to_csv("media/company_data/" + i + ".csv", mode='a', index=False, header=False)
#         else:
#             data.to_csv("media/company_data/" + i + ".csv")
#     except:
#         now = now - datetime.timedelta(days=1)
#         print("exception")
#         continue
#
#         # df.merge()
#     now = now - datetime.timedelta(days=1)
#
#
#     # for j in range
