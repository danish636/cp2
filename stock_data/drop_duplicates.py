# import pandas as pd
# import os
# import datetime
# if __name__ == '__main__':
#     path = "media/hist data"
#     symbols = os.listdir(path)
#
#     for id,symbol in enumerate(os.listdir(path)):
#         print(id)
#         try:
#             # symbol = symbol.split(".")[0]
#             df = pd.read_csv('media/hist data/'+symbol)
#             # if df.iloc[-1]["high"] == "2022-07-11":
#             #     print(symbol)
#             #     df = df.head(-1)
#             #     df.to_csv('media/hist data/'+symbol,index=False)
#
#             # df = df.drop_duplicates(subset=["date"])
#             l = df.iloc[-1].to_list()
#
#             date = l[1]
#             l.remove(date)
#             l.insert(9, date)
#             d = pd.DataFrame([],columns=df.columns)
#             d.loc[0] = l
#             #####################################################
#
#             df = df.head(-1)
#             df.to_csv('media/hist data/'+symbol,index=False)
#             ######################################################
#             d.to_csv('media/hist data/'+symbol, mode="a", header=None, index=False)
#         except:
#             print("Exception")
#             continue

##################################################################################################

#NEW CODE

import pandas as pd
import os
import datetime

if __name__ == '__main__':
    base_path = os.path.join(os.path.dirname(__file__), "..", "external_api_data", "Media", "hist data2")
    symbols = os.listdir(base_path)

    for idx, symbol in enumerate(symbols):
        print(idx)
        try:
            file_path = os.path.join(base_path, symbol)
            df = pd.read_csv(file_path)

            # Extract last row, move date from index 1 to index 9
            last_row = df.iloc[-1].to_list()
            date_value = last_row[1]
            last_row.pop(1)
            last_row.insert(9, date_value)

            # Create a single-row DataFrame for the modified row
            modified_row = pd.DataFrame([last_row], columns=df.columns)

            # Remove last row from original DataFrame
            df = df.iloc[:-1]
            df.to_csv(file_path, index=False)

            # Append modified row back
            modified_row.to_csv(file_path, mode="a", header=False, index=False)

        except Exception as e:
            print("Exception:", e)
            continue
