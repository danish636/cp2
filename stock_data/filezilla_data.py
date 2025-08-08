# import ftplib
# import zipfile
# import shutil
# from datetime import datetime, date, timedelta
# import pandas as pd
# import os.path
# import os
# import vaex
# # date_list = ['20230101', '20230102', '20230103', '20230104', '20230105', '20230106', '20230107', '20230108', '20230109', '20230110', '20230111', '20230112', '20230113', '20230114', '20230115', '20230116', '20230117', '20230118', '20230119', '20230120', '20230121', '20230122', '20230123', '20230124', '20230125', '20230126']
# date_list = ['20231201', '20231204', '20231205', '20231206', '20231207', '20231208', '20231211']
# # for today in date_list:
# # today = '20220519'
#
#
# today = datetime.today().strftime('%Y%m%d')
# # today = "20231130"
# path = 'media/option_data/Option Data/Historical/'
# filename = f'L3_{today}.zip'
# # filename = "L3_20231130.zip"
# print(filename)
#
# ftp = ftplib.FTP("L3.deltaneutral.net")
# ftp.login("abbyiluck", "Pazzword24$")
# try:
#     ftp.retrbinary("RETR " + filename, open(filename, 'wb').write)
#
#     shutil.move(f'L3_{today}.zip', f'/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/L3_{today}.zip')
#     print('file moved...')
#
#     with zipfile.ZipFile(f'/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/L3_{today}.zip', 'r') as zip_ref:
#         zip_ref.extractall(f'/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/')
#     print('files extracted...')
#
#     columns = ['symbol', 'quotedate', 'iv30call', 'iv30put', 'iv30mean', 'iv60call',
#        'iv60put', 'iv60mean', 'iv90call', 'iv90put', 'iv90mean', 'iv120call',
#        'iv120put', 'iv120mean', 'iv150call', 'iv150put', 'iv150mean',
#        'iv180call', 'iv180put', 'iv180mean', 'iv360call', 'iv360put',
#        'iv360mean', 'callvol', 'putvol', 'totalvol', 'calloi', 'putoi',
#        'totaloi']
#
#     df = pd.read_csv(f"/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/L3_optionstats_{today}.csv")
#     symbols = df['symbol'].unique()
#     options = vaex.from_csv(f"/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/L3_options_{today}.csv")
#     options.export_hdf5(f"/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/L3_options_{today}.csv.hdf5")
#
#     for ticker in symbols:
#         print(ticker)
#         one_year = pd.DataFrame(columns=columns)
#
#         temp = pd.read_csv(f"/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/L3_optionstats_{today}.csv")
#         temp = temp[temp["symbol"] == ticker]
#         one_year = pd.concat([one_year, temp])
#         one_year = one_year.reset_index(drop=True)
#         one_year["quotedate"] = pd.to_datetime(one_year["quotedate"], format="%m/%d/%Y")
#
#         if os.path.isfile(f'media/website/quote/{ticker}.csv'):
#             temp_file = pd.read_csv(f'media/website/quote/{ticker}.csv')
#             final_d = pd.concat([temp_file,one_year],axis=0).drop_duplicates(subset=['quotedate']).reset_index(drop=True)
#             final_d['quotedate'] = pd.to_datetime(final_d['quotedate'])
#             final_d = final_d.sort_values(by="quotedate")
#             final_d.to_csv(f'media/website/quote/{ticker}.csv',index=False)
#         else:
#             one_year.to_csv(f'media/website/quote/{ticker}.csv')
#     os.remove(f'/home/pytestinvexaitec/Amassinginvestment-DS/stock_data/media/option_data/Option Data/Historical/{today[0:4]}/{str(int(today[4:6]))}/L3_{today}.zip')
# except:
#
#     try:
#         os.remove(filename)
#         print('Except')
#     except:
#         print('Except')
#
# # ftp.quit()
#
#
#
