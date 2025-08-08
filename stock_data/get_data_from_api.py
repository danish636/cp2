# import pandas as pd
# import json
#
# def get_data(symbols):
#     for index, symbol in enumerate(symbols[3748:]):
#         try:
#     	    print(index+3748, symbol)
#     	    data = pd.read_json("https://cloud.iexapis.com/stable/stock/" + symbol + "/chart/max?token=pk_55e019e9e4db4baaa9493d29a095bf63")
#     	    data.to_csv('media/hist data/'+symbol+'.csv', index=False)
#         except:
#             print("Exception")
#             continue
#
# def append_data(symbols):
#     for index, symbol in enumerate(symbols):
#         try:
#             print(index, symbol)
#             data = pd.read_json("https://cloud.iexapis.com/stable/stoc/" + symbol + "/chart/max?token=pk_55e019e9e4db4baaa9493d29a095bf63")
#             new_data = pd.read_json("https://cloud.iexapis.com/stable/stoc/" + symbol + "/chart/1w?token=pk_55e019e9e4db4baaa9493d29a095bf63")
#             data.append(new_data)
#             data.to_csv('media/hist data/' + symbol +'.csv', index=False)
#         except:
#             print('Exception')
#             continue
#
#
# if __name__ == '__main__':
# 	file = open('media/symbols_name.json', 'r')
# 	symbols = json.load(file)
# 	get_data(symbols)