# import pandas as pd
# import os
# if __name__ == '__main__':
#     path = "media/h_data"
#     symbols = os.listdir(path)
#
#     for idx,symbol in enumerate(symbols):
#         print(idx)
#         symbol = symbol.split(".")[0]
#         data = pd.read_csv('media/h_data/'+symbol+'.csv')
#         print(symbol)
#         try:
#
#             data.drop(["Unnamed: 0.1"], axis=1,inplace=True)
#         except:
#             print('Except')
#             continue
#
#
#         data.to_csv("media/h_data/"+symbol+".csv", index=False)

###################################################################################################

#NEW CODE

import pandas as pd
import os

if __name__ == '__main__':
    base_path = os.path.join(os.path.dirname(__file__), "..", "external_api_data", "Media", "hist data2")
    symbols = os.listdir(base_path)

    for idx, symbol in enumerate(symbols):
        print(idx)
        symbol_name = symbol.split(".")[0]
        file_path = os.path.join(base_path, symbol)

        try:
            data = pd.read_csv(file_path)
            print(symbol_name)

            if "Unnamed: 0.1" in data.columns:
                data.drop(["Unnamed: 0.1"], axis=1, inplace=True)
                data.to_csv(file_path, index=False)

        except Exception as e:
            print("Except:", e)
            continue
