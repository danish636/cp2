import json
import pandas as pd
import os
from datetime import datetime


#file = open('media/symbols_name.json', 'r')

base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, "..", "external_api_data", "Media", "symbols_name.json")
file_path = os.path.normpath(file_path)
with open(file_path, "r") as file:
    symbols = json.load(file)


    
for index, symbol in enumerate(symbols):
    try:
        print(index)
        #df = pd.read_csv('media/hist data2/'+ symbol + '.csv',usecols=['date', 'open', 'high', 'low', 'close','adjClose', 'volume', 'unadjustedVolume', 'change', 'changePercent','vwap', 'label', 'changeOverTime'])
        base_path = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.normpath(os.path.join(base_path, "..", "external_api_data", "Media", "hist data2", f"{symbol}.csv"))

        if os.path.exists(csv_path): #@danish
            df = pd.read_csv(csv_path, usecols=['date', 'open', 'high', 'low', 'close', 'adjClose', 'volume', 'unadjustedVolume', 'change', 'changePercent', 'vwap', 'label', 'changeOverTime'])
        else:
            df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'adjClose', 'volume', 'unadjustedVolume', 'change', 'changePercent', 'vwap', 'label', 'changeOverTime'])

        if "2023-02-13" not in df["date"]:
            url = "https://financialmodelingprep.com/api/v3/historical-price-full/" + symbol + "?timeseries=140&apikey=b1360803f80dd08bdd0211c5c004ad03"
                    
            data = pd.read_json(url)
            data = pd.DataFrame.from_records(data["historical"])
            df = pd.concat([df,data], ignore_index=True)
            # df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'adjClose', 'volume', 'unadjustedVolume', 'change', 'changePercent', 'vwap', 'label', 'changeOverTime']) #@dansih
            # for i, symbol in enumerate(symbols):
            #     # ... load data logic ...
            #     if not data.empty:
            #         df = pd.concat([df, data], ignore_index=True)
            #     print(i)

            df = df.drop_duplicates(subset=["date"])
            df = df.sort_values(by='date')
        
            #df.to_csv("media/hist data2/" + symbol + ".csv")
            df.to_csv(csv_path, index=False) #@danish
    
    # except:
    #     print("Exception")
    #     continue

    except Exception as e:
        print(f"Exception occurred for {symbol}: {e}")
        continue #@danish
    