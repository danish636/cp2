import requests
import json
import pandas as pd
import os
import time


url_header1 = "https://financialmodelingprep.com/api/v3/stock_market/actives?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_header2_index = "https://financialmodelingprep.com/api/v3/quotes/index?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_header2_currency = "https://financialmodelingprep.com/api/v3/quote/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_header2_commodity = "https://financialmodelingprep.com/api/v3/quotes/commodity?apikey=b1360803f80dd08bdd0211c5c004ad03"


url_most_active = "https://financialmodelingprep.com/api/v3/stock_market/actives?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_gainer = "https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_losers = "https://financialmodelingprep.com/api/v3/stock_market/losers?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_stock_market = "https://financialmodelingprep.com/api/v4/stock-news-sentiments-rss-feed?page=$$$$&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_general = "https://financialmodelingprep.com/api/v4/general_news?page=$$$$&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_prices = "https://financialmodelingprep.com/api/v3/quote/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_company_profile = "https://financialmodelingprep.com/api/v4/company-outlook?symbol=$$$$&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_name = "https://financialmodelingprep.com/api/v4/stock_peers?symbol=$$$$&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_earning_more = "https://financialmodelingprep.com/api/v3/historical/earning_calendar/$$$$?limit=200&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_historical_price_stock_divident = "https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
url_etf_info = "https://financialmodelingprep.com/api/v4/etf-info?symbol=$$$$&apikey=b1360803f80dd08bdd0211c5c004ad03"

path = "./"
if not path.endswith("/"):
    path = path + "/"


def scrap_and_dump(
    urls,
    file_name,
    return_data=False,
    split_by_symbols=False,
    symbol="sam",
    call_in_500_but_save_individually=False,
    if_hist = False
):
    if symbol != "sam" and not call_in_500_but_save_individually:
        print(f"scraping for {file_name} {symbol} ......")
    else:
        print(f"scraping for {file_name} ......")

    main_list = []
    main_list_symbol = []
    for url in urls:
        print(url)
        response = requests.get(url)
        json_data = response.json()
        if if_hist:
            json_data = json_data.get("historicalStockList")
        if type(json_data) != list:
            json_data = [json_data]
        main_list += json_data
        main_list_symbol.append(json_data)
        time.sleep(0.05)

    if split_by_symbols:
        if not os.path.exists(f"{path}Jsons/{file_name}"):
            os.mkdir(f"{path}Jsons/{file_name}")
        for i in main_list_symbol:

            if call_in_500_but_save_individually == True:
                for a in i:
                    print(a)
                    try:
                        sym_name = f"{path}Jsons/{file_name}/" + a.get("symbol") + ".json"
                    except:
                        continue
                    try:
                        with open(sym_name, "w", encoding="utf-8") as f:
                            json.dump(a, f)
                    except:
                        print("symbols :", sym_name)

            else:
                if symbol == "sam":
                    sym_name = f"{path}Jsons/{file_name}/" + i.get("symbol") + ".json"
                else:
                    sym_name = f"{path}Jsons/{file_name}/" + symbol + ".json"
                try:
                    with open(sym_name, "w", encoding="utf-8") as f:
                        json.dump(i, f)
                except:
                    print("symbols :", sym_name)
    else:
        print("yes")
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(main_list, f)

    if return_data:
        return main_list


def convert_list_tostr(symlist):
    symbolstr = ""
    for j, i in enumerate(symlist):
        if j == 0:
            symbolstr += i
        else:
            symbolstr += "," + i
    return symbolstr


def import_break_symbols(break_in_5 = False,etf=False):
    if break_in_5:
        steps = 5
    else:
        steps = 500
    if etf:
        list_symbols = open("etf_symbols.txt", "r").read()
        list_symbols = list_symbols.split(",")
        return list_symbols
    else:
        list_symbols = open("Top_1000_symbols.txt", "r").read()
        list_symbols = list_symbols.split(",")
        main_list = []
        for i in range(0, len(list_symbols), steps):
            try:
                main_list.append(list_symbols[i : i + steps])
            except:
                main_list.append(list_symbols[i : len(list_symbols) - i])
        return main_list, list_symbols


def symbols_wise_scrap_and_dump(url, file_name, list_of_symbols, flag=False, call_in_500_but_save_individually=False,if_hist=False):
    url_prices_final = []
    for i in list_of_symbols:
        if not flag:
            url_prices = url.replace("$$$$", convert_list_tostr(i))
            url_prices_final.append(url_prices)
        else:
            url_prices = url.replace("$$$$", i)
            scrap_and_dump([url_prices], file_name, split_by_symbols=True, symbol=i)

    if not flag:
        scrap_and_dump(url_prices_final, file_name, split_by_symbols=True, symbol=convert_list_tostr(i), call_in_500_but_save_individually=call_in_500_but_save_individually,if_hist=if_hist)


if __name__ == "__main__":
    if not os.path.exists(f"{path}Jsons"):
        os.mkdir(f"{path}Jsons")
    
    ################################################################################
    
    scrap_and_dump([url_header1],f"{path}Jsons/header1.json") #same api as most active
    scrap_and_dump([url_header2_index],f"{path}Jsons/header2_index.json")
    
    symbols_wise_scrap_and_dump(url_header2_currency,"header2_currency",["JPYUSD","EURUSD","GBPUSD","USDJPY","USDCHF","AUDUSD","NZDUSD","USDCAD","USDINR"],flag=True)
    scrap_and_dump([url_header2_commodity],f"{path}Jsons/header2_commodity.json")
    scrap_and_dump([url_gainer],f"{path}Jsons/gainer.json")
    scrap_and_dump([url_losers],f"{path}Jsons/losers.json")
    
    scrap_and_dump([url_stock_market.replace("$$$$",str(i)) for i in range(0,10)],f"{path}Jsons/stock_market.json")
    scrap_and_dump([url_general.replace("$$$$",str(i)) for i in range(0,10)],f"{path}Jsons/general.json")
    
    ###############################################################################
    
    json_active = scrap_and_dump([url_most_active],f"{path}Jsons/most_active.json",return_data = True)
    try:
        df_ = pd.json_normalize(json_active)
        symbols = list(df_["symbol"])
        symbolstr = convert_list_tostr(symbols)
    except:
        pass
    
    url_values = f"https://financialmodelingprep.com/api/v3/profile/{symbolstr}?apikey=b1360803f80dd08bdd0211c5c004ad03"
    url_related_News = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={symbolstr}&apikey=b1360803f80dd08bdd0211c5c004ad03"
    
    ##################################################################################
    
    scrap_and_dump([url_values],f"{path}Jsons/values.json")
    scrap_and_dump([url_related_News],f"{path}Jsons/relates_News.json")
    
    list_of_symbols, list_symbols = import_break_symbols()
    list_of_symbols_5, list_symbols_5 = import_break_symbols(break_in_5 = True)
    etf_list_of_symbols = import_break_symbols(etf=True)
# #####################################################################################


    symbols_wise_scrap_and_dump(url_prices,"Price",list_of_symbols,call_in_500_but_save_individually=True)
    symbols_wise_scrap_and_dump(url_company_profile,"Company Profile",list_symbols,flag = True)
    symbols_wise_scrap_and_dump(url_name,"Name",list_of_symbols)
    symbols_wise_scrap_and_dump(url_earning_more,"Earning More",list_symbols,flag = True)
    
    
    symbols_wise_scrap_and_dump(url_stock_market,"Stock_market",[str(i) for i in range(0,10)],flag=True)
    symbols_wise_scrap_and_dump(url_general,"General",[str(i) for i in range(0,10)],flag=True)
    
    scrap_and_dump([url_stock_market.replace("$$$$",str(i)) for i in range(0,10)],f"{path}Jsons/stock_market.json")
    scrap_and_dump([url_general.replace("$$$$",str(i)) for i in range(0,10)],f"{path}Jsons/general.json")


################################################## New Apis ########################################################################



    symbols_wise_scrap_and_dump(
        url_historical_price_stock_divident,
        "HP Stock Divident",
        list_of_symbols_5,
        call_in_500_but_save_individually=True,
        if_hist = True
    )


    symbols_wise_scrap_and_dump(url_etf_info,"ETF Info",etf_list_of_symbols,flag=True)
    url_stock_price_change = "https://financialmodelingprep.com/api/v3/stock-price-change/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
    symbols_wise_scrap_and_dump(url_stock_price_change,"Stock Price Change",list_of_symbols,call_in_500_but_save_individually=True)

