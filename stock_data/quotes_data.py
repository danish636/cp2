# import datetime
# import vaex
# import pandas as pd
# import os
#
# now = datetime.datetime.now()
# now = now - datetime.timedelta(days=4)
# final_d = datetime.datetime(2019,9,23)
# final_date = now.strftime("%Y%m%d")
# # range_d = now - datetime.timedelta(years=3)
#
#
#
# df = pd.read_csv(f"media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_stockquotes_{str(final_date)}.csv")
# print(df)
# symbols = df["symbol"].unique()
# print(final_d.date(), now.date())
# while final_d.date() != now.date():
#     print(now.date())
#     try:
#         final_date = now.strftime("%Y%m%d")
#         df = pd.read_csv(f"media/option_data/Option Data/Historical/{str(final_date[0:4])}/{str(int(final_date[4:6]))}/L3_stockquotes_{str(final_date)}.csv")
#         print(df)
#     except:
#         now = now - datetime.timedelta(days=1)
#         print("exception")
#         continue
#     for i in symbols:
#         # print(df)
#         data = df[df["symbol"] == i]
#
#         if os.path.exists("media/closed_price/" + i + ".csv"):
#             data.to_csv("media/closed_price/" + i + ".csv", mode='a', index=False, header=False)
#         else:
#             data.to_csv("media/closed_price/" + i + ".csv")
#         # df.merge()
#     now = now - datetime.timedelta(days=1)
#
#
#     # for j in range
