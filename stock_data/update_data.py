# import json
# import pandas as pd
#
# def get_data(symbols):
#     for index, symbol in enumerate(symbols):
#         try:
#             print(index, symbol)
#             data = pd.read_json("https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/" + symbol + "?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m")
#             data["fHigh"] = data["fhigh"]
#             data["fLow"] = data["flow"]
#             data["fClose"] = data["fclose"]
#             data["uHigh"] = data["uhigh"]
#             data["uLow"] = data["ulow"]
#             data["uClose"] = data["uclose"]
#             data["fVolume"] = data["fvolume"]
#             data["fOpen"] = data["fopen"]
#             data["uVolume"] = data["uvolume"]
#             data["uOpen"] = data["uopen"]
#
#             data.drop(["fhigh", "flow", "fclose", "uhigh", "ulow", "uclose", "fvolume", "uvolume", "uopen", "fopen"], axis=1, inplace=True)
#
#
#             data2 = pd.read_csv('media/hist data/'+symbol+'.csv', usecols=data.columns)
#             final_d = pd.concat([data,data2],axis=0).drop_duplicates(subset=['date']).reset_index(drop=True)
#             final_d['date'] = pd.to_datetime(final_d['date'])
#             final_d = final_d.sort_values(by="date")
#
#             final_d.to_csv('media/hist data/'+symbol+'.csv',index=False)
#
#         except:
#             print("Exception")
#             continue
#
#
# if __name__ == '__main__':
# 	file = open('media/symbols_name.json', 'r')
# 	symbols = json.load(file)
# 	get_data(symbols)

############################################################################################################################

#NEW CODE

# import os
# import json
# import pandas as pd
#
# def get_data(symbols):
#     base_dir = os.path.dirname(os.path.dirname(__file__))  # Goes to project root (backend)
#     hist_data_path = os.path.join(base_dir, "external_api_data", "Media", "hist data")
#
#     for index, symbol in enumerate(symbols):
#         try:
#             print(index, symbol)
#             data = pd.read_json(
#                 f"https://cloud.iexapis.com/stable/time-series/HISTORICAL_PRICES/{symbol}?token=pk_55e019e9e4db4baaa9493d29a095bf63&range=3m"
#             )
#             data["fHigh"] = data["fhigh"]
#             data["fLow"] = data["flow"]
#             data["fClose"] = data["fclose"]
#             data["uHigh"] = data["uhigh"]
#             data["uLow"] = data["ulow"]
#             data["uClose"] = data["uclose"]
#             data["fVolume"] = data["fvolume"]
#             data["fOpen"] = data["fopen"]
#             data["uVolume"] = data["uvolume"]
#             data["uOpen"] = data["uopen"]
#
#             data.drop(
#                 ["fhigh", "flow", "fclose", "uhigh", "ulow", "uclose", "fvolume", "uvolume", "uopen", "fopen"],
#                 axis=1,
#                 inplace=True,
#             )
#
#             file_path = os.path.join(hist_data_path, f"{symbol}.csv")
#             data2 = pd.read_csv(file_path, usecols=data.columns)
#             final_d = pd.concat([data, data2], axis=0).drop_duplicates(subset=["date"]).reset_index(drop=True)
#             final_d["date"] = pd.to_datetime(final_d["date"])
#             final_d = final_d.sort_values(by="date")
#
#             final_d.to_csv(file_path, index=False)
#
#         except Exception as e:
#             print("Exception:", e)
#             continue
#
# if __name__ == "__main__":
#     base_dir = os.path.dirname(os.path.dirname(__file__))
#     symbols_file_path = os.path.join(base_dir, "external_api_data", "Media", "symbols_name.json")
#     with open(symbols_file_path, "r") as file:
#         symbols = json.load(file)
#
#     get_data(symbols)
