# #!/usr/local/bin/python3.9
#
# import json
# import pandas as pd
# import os
#
# def get_data(symbols):
#     for index, symbol in enumerate(symbols):
#         symbol = symbol.split(".")[0]
#         try:
#             print(index, symbol)
#             d = pd.read_json("https://financialmodelingprep.com/api/v3/historical-price-full/"+ symbol + "?timeseries=10&apikey=b1360803f80dd08bdd0211c5c004ad03")
#             data = pd.DataFrame.from_records(d["historical"])
#             # data["fHigh"] = data["fhigh"]
#             # data["fLow"] = data["flow"]
#             # data["fClose"] = data["fclose"]
#             # data["uHigh"] = data["uhigh"]
#             # data["uLow"] = data["ulow"]
#             # data["uClose"] = data["uclose"]
#             # data["fVolume"] = data["fvolume"]
#             # data["fOpen"] = data["fopen"]
#             # data["uVolume"] = data["uvolume"]
#             # data["uOpen"] = data["uopen"]
#
#             # data.drop(["fhigh", "flow", "fclose", "uhigh", "ulow", "uclose", "fvolume", "uvolume", "uopen", "fopen"], axis=1, inplace=True)
#             df = pd.read_csv('media/hist data2/'+symbol+'.csv',error_bad_lines=False, engine="python",usecols=['date', 'open', 'high', 'low', 'close','adjClose', 'volume', 'unadjustedVolume', 'change', 'changePercent','vwap', 'label', 'changeOverTime'])
#             df = df.append(data)
#             df = df.reset_index(drop=True)
#             df.to_csv('media/hist data2/'+symbol+'.csv')
#             # data.to_csv('media/hist data/'+symbol+'.csv', mode="a", header=None, index=False)
#         except:
#             print("Exception")
#             continue
#
# def drop_dupli(symbols):
#     for id,symbol in enumerate(symbols):
#         print(id)
#         try:
#             symbol = symbol.split(".")[0]
#             df = pd.read_csv('media/hist data2/'+symbol+'.csv',error_bad_lines=False, engine="python",usecols=['date', 'open', 'high', 'low', 'close','adjClose', 'volume', 'unadjustedVolume', 'change', 'changePercent','vwap', 'label', 'changeOverTime'])
#             df = df.drop_duplicates(subset=["date"])
#             df.to_csv('media/hist data2/'+symbol+'.csv',index=False)
#         except:
#             continue
#
#
# if __name__ == '__main__':
# 	path = "media/hist data2"
# 	symbols = os.listdir(path)
#
# 	get_data(symbols)
# 	drop_dupli(symbols)

#########################################################################################################################
#NEW CODE
#!/usr/local/bin/python3.9

import json
import pandas as pd
import os

def get_data(symbols, base_path):
    for index, symbol in enumerate(symbols):
        symbol = symbol.split(".")[0]
        try:
            print(index, symbol)
            d = pd.read_json(
                f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?timeseries=10&apikey=b1360803f80dd08bdd0211c5c004ad03"
            )
            data = pd.DataFrame.from_records(d["historical"])

            file_path = os.path.join(base_path, f"{symbol}.csv")
            df = pd.read_csv(file_path, error_bad_lines=False, engine="python", usecols=[
                'date', 'open', 'high', 'low', 'close', 'adjClose', 'volume',
                'unadjustedVolume', 'change', 'changePercent', 'vwap', 'label', 'changeOverTime'
            ])
            df = pd.concat([df, data], ignore_index=True)
            df.to_csv(file_path, index=False)
        except:
            print("Exception")
            continue

def drop_dupli(symbols, base_path):
    for idx, symbol in enumerate(symbols):
        print(idx)
        try:
            symbol = symbol.split(".")[0]
            file_path = os.path.join(base_path, f"{symbol}.csv")
            df = pd.read_csv(file_path, error_bad_lines=False, engine="python", usecols=[
                'date', 'open', 'high', 'low', 'close', 'adjClose', 'volume',
                'unadjustedVolume', 'change', 'changePercent', 'vwap', 'label', 'changeOverTime'
            ])
            df = df.drop_duplicates(subset=["date"])
            df.to_csv(file_path, index=False)
        except:
            continue

if __name__ == '__main__':
    base_path = os.path.join(os.path.dirname(__file__), "..", "external_api_data", "Media", "hist data2")
    symbols = os.listdir(base_path)

    get_data(symbols, base_path)
    drop_dupli(symbols, base_path)
