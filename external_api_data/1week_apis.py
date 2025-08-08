import requests
import json
import pandas as pd
import os
import time



# Company Financial Ratios


path = "./"
if not path.endswith("/"):
    path = path + "/"


url_ttm_cf = "https://financialmodelingprep.com/api/v3/ratios-ttm/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"

url_annual_cf_5y = "https://financialmodelingprep.com/api/v3/ratios/$$$$?limit=5&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_annual_cf_10y = "https://financialmodelingprep.com/api/v3/ratios/$$$$?limit=10&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_annual_cf_max = "https://financialmodelingprep.com/api/v3/ratios/$$$$?limit=30&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_quarter_cf_5y = "https://financialmodelingprep.com/api/v3/ratios/$$$$?period=quarter&limit=20&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_quarter_cf_10y = "https://financialmodelingprep.com/api/v3/ratios/$$$$?period=quarter&limit=40&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_quarter_cf_max = "https://financialmodelingprep.com/api/v3/ratios/$$$$?period=quarter&limit=140&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_ttm_ck = "https://financialmodelingprep.com/api/v3/key-metrics-ttm/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"

url_annual_ck_5y = "https://financialmodelingprep.com/api/v3/key-metrics/$$$$?limit=5&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_annual_ck_10y = "https://financialmodelingprep.com/api/v3/key-metrics/$$$$?limit=10&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_annual_ck_max = "https://financialmodelingprep.com/api/v3/key-metrics/$$$$?limit=30&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_quarter_ck_5y = "https://financialmodelingprep.com/api/v3/key-metrics/$$$$?period=quarter&limit=20&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_quarter_ck_10y = "https://financialmodelingprep.com/api/v3/key-metrics/$$$$?period=quarter&limit=40&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_quarter_ck_max = "https://financialmodelingprep.com/api/v3/key-metrics/$$$$?period=quarter&limit=120&apikey=b1360803f80dd08bdd0211c5c004ad03"

# Financial Statements

url_bs_annual_5y = "https://financialmodelingprep.com/api/v3/balance-sheet-statement/$$$$?period=annual&limit=5&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_bs_annual_10y = "https://financialmodelingprep.com/api/v3/balance-sheet-statement/$$$$?period=annual&limit=10&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_bs_annual_max = "https://financialmodelingprep.com/api/v3/balance-sheet-statement/$$$$?period=annual&limit=30&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_bs_quarter_5y = "https://financialmodelingprep.com/api/v3/balance-sheet-statement/$$$$?period=quarter&limit=20&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_bs_quarter_10y = "https://financialmodelingprep.com/api/v3/balance-sheet-statement/$$$$?period=quarter&limit=40&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_bs_quarter_max = "https://financialmodelingprep.com/api/v3/balance-sheet-statement/$$$$?period=quarter&limit=120&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_is_annual_5y = "https://financialmodelingprep.com/api/v3/income-statement/$$$$?period=annual&limit=5&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_is_annual_10y = "https://financialmodelingprep.com/api/v3/income-statement/$$$$?period=annual&limit=10&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_is_annual_max = "https://financialmodelingprep.com/api/v3/income-statement/$$$$?period=annual&limit=30&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_is_quarter_5y = "https://financialmodelingprep.com/api/v3/income-statement/$$$$?period=quarter&limit=20&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_is_quarter_10y = "https://financialmodelingprep.com/api/v3/income-statement/$$$$?period=quarter&limit=40&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_is_quarter_max = "https://financialmodelingprep.com/api/v3/income-statement/$$$$?period=quarter&limit=120&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_cs_annual_5y = "https://financialmodelingprep.com/api/v3/cash-flow-statement/$$$$?period=annual&limit=5&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_cs_annual_10y = "https://financialmodelingprep.com/api/v3/cash-flow-statement/$$$$?period=annual&limit=10&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_cs_annual_max = "https://financialmodelingprep.com/api/v3/cash-flow-statement/$$$$?period=annual&limit=30&apikey=b1360803f80dd08bdd0211c5c004ad03"

url_cs_quarter_5y = "https://financialmodelingprep.com/api/v3/cash-flow-statement/$$$$?period=quarter&limit=5&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_cs_quarter_10y = "https://financialmodelingprep.com/api/v3/cash-flow-statement/$$$$?period=quarter&limit=10&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_cs_quarter_max = "https://financialmodelingprep.com/api/v3/cash-flow-statement/$$$$?period=quarter&limit=30&apikey=b1360803f80dd08bdd0211c5c004ad03"


url_earning_calendar = "https://financialmodelingprep.com/api/v4/earning-calendar-confirmed?from=2022-08-29&to=2022-09-02&apikey=b1360803f80dd08bdd0211c5c004ad03"
url_macro_eco = "https://financialmodelingprep.com/api/v4/economic?name=$$$$&from=1900-10-10&to=2030-11-10&apikey=b1360803f80dd08bdd0211c5c004ad03"


# 5year , 10year, max = 30
# 20 q   , 40q  , max = 120


def scrap_and_dump(urls, file_name, return_data=False, split_by_symbols=False, symbol="sam",if_hist=False):
    print(f"scraping for {file_name} ......")
    main_list = []
    main_list_symbol = []
    for url in urls:
        print(url)
        response = requests.get(url)
        json_data = response.json()
        main_list += json_data
        if if_hist:
            json_data = json_data.get("historicalStockList")
        if type(json_data) != list:
            json_data = [json_data]
        main_list_symbol.append(json_data)
        time.sleep(0.05)

    if split_by_symbols:
        if not os.path.exists(f"{path}Jsons/{file_name}"):
            os.mkdir(f"{path}Jsons/{file_name}")
        for i in main_list_symbol:
            if not if_hist:
                sym_name = f"{path}Jsons/{file_name}/" + symbol + ".json"
                try:
                    with open(sym_name, "w", encoding="utf-8") as f:
                        json.dump(i, f)
                except:
                    print(sym_name)
            else:
                for a in i:
                    sym_name = f"{path}Jsons/{file_name}/" + a.get("symbol") + ".json"
                    try:
                        with open(sym_name, "w", encoding="utf-8") as f:
                            json.dump(a, f)
                    except:
                        print(sym_name)
    else:
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


def import_break_symbols(etf= False,top1000 = False):
    if etf:
        list_symbols = open("etf_symbols.txt", "r").read()
        list_symbols = list_symbols.split(",")
    elif top1000:
        list_symbols = open("Top_1000_symbols.txt", "r").read()
        list_symbols = list_symbols.split(",")
        return list_symbols
    else:
        list_symbols = open("symbols.txt", "r").read()
        list_symbols = list_symbols.split(",")
    return list_symbols[:1000]



def break_symbol(list_symbols,steps=500,convert_str=False):
    main_list = []
    for i in range(0,len(list_symbols),steps):
    	try:
    		main_list.append(list_symbols[i:i+steps])
    	except:
    		main_list.append(list_symbols[i:len(list_symbols)-i])

    if convert_str:
        final_main_list = []
        for i in main_list:
            final_main_list.append(convert_list_tostr(i))
        return final_main_list

    return main_list


# def symbols_wise_scrap_and_dump(url, file_name,list_of_symbols):
# 	url_prices_final = []
# 	for i in list_of_symbols:
# 		# url_prices = url.replace("$$$$",convert_list_tostr(i))
# 		url_prices = url.replace("$$$$",str(i))
# 		# url_prices_final.append(url_prices)
# 		scrap_and_dump([url_prices],file_name,split_by_symbols=True,symbol = i)
# 	print(f"Scraped {file_name}")


def symbols_wise_scrap_and_dump(url, file_name, list_of_symbols, flag=False,if_hist=False):
    url_prices_final = []
    for i in list_of_symbols:
        url_prices = url.replace("$$$$", i)
        scrap_and_dump([url_prices], file_name, split_by_symbols=True, symbol=i,if_hist=if_hist)


if __name__ == "__main__":
    if not os.path.exists(f"{path}/Jsons"):
        os.mkdir(f"{path}/Jsons")

#####################################################################################
    list_of_symbols = import_break_symbols()
    etf_list_of_symbols = import_break_symbols(etf=True)
    top1000_list_of_symbols = import_break_symbols(top1000 = True)
#####################################################################################





symbols_wise_scrap_and_dump(url_ttm_cf, "Ttm cf", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_annual_cf_5y, "Annual cf 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_annual_cf_10y, "Annual cf 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_annual_cf_max, "Annual cf max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_quarter_cf_5y, "Quarter cf 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_quarter_cf_10y, "Quarter cf 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_quarter_cf_max, "Quarter cf max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_ttm_ck, "Ttm ck", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_annual_ck_5y, "Annual ck 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_annual_ck_10y, "Annual ck 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_annual_ck_max, "Annual ck max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_quarter_ck_5y, "Quarter ck 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_quarter_ck_10y, "Quarter ck 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_quarter_ck_max, "Quarter ck max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_bs_annual_5y, "Bs annual 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_bs_annual_10y, "Bs annual 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_bs_annual_max, "Bs annual max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_bs_quarter_5y, "Bs quarter 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_bs_quarter_10y, "Bs quarter 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_bs_quarter_max, "Bs quarter max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_is_annual_5y, "Is annual 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_is_annual_10y, "Is annual 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_is_annual_max, "Is annual max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_is_quarter_5y, "Is quarter 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_is_quarter_10y, "Is quarter 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_is_quarter_max, "Is quarter max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_cs_annual_5y, "Cs annual 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_cs_annual_10y, "Cs annual 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_cs_annual_max, "Cs annual max", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_cs_quarter_5y, "Cs quarter 5y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_cs_quarter_10y, "Cs quarter 10y", top1000_list_of_symbols)
symbols_wise_scrap_and_dump(url_cs_quarter_max, "Cs quarter max", top1000_list_of_symbols)



scrap_and_dump([url_earning_calendar], f"{path}Jsons/Earning_calendar.json")
symbols_wise_scrap_and_dump(
    url_macro_eco,
    "Macro Economics",
    [
        "GDP",
        "realGDP",
        "nominalPotentialGDP",
        "realGDPPerCapita",
        "federalFunds",
        "CPI",
        "inflationRate",
        "inflation",
        "retailSales",
        "consumerSentiment",
        "durableGoods",
        "unemploymentRate",
        "totalNonfarmPayroll",
        "initialClaims",
        "industrialProductionTotalIndex",
        "newPrivatelyOwnedHousingUnitsStartedTotalUnits",
        "totalVehicleSales",
        "retailMoneyFunds",
        "smoothedUSRecessionProbabilities",
        "3MonthOr90DayRatesAndYieldsCertificatesOfDeposit",
        "commercialBankInterestRateOnCreditCardPlansAllAccounts",
        "30YearFixedRateMortgageAverage",
        "15YearFixedRateMortgageAverage",
    ],
    flag=True,
)




################################################## New Apis ########################################################################


url_earning_surprise = "https://financialmodelingprep.com/api/v3/earnings-surprises/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
symbols_wise_scrap_and_dump(url_earning_surprise,"Earning Surprise",top1000_list_of_symbols)

url_etf_stock_exposure = "https://financialmodelingprep.com/api/v3/etf-stock-exposure/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
symbols_wise_scrap_and_dump(url_etf_stock_exposure,"Etf Stock Exposure",etf_list_of_symbols)

url_etf_sector_weightage = "https://financialmodelingprep.com/api/v3/etf-sector-weightings/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
symbols_wise_scrap_and_dump(url_etf_sector_weightage,"Etf Sector weightage",etf_list_of_symbols)

url_etf_holders = "https://financialmodelingprep.com/api/v3/etf-holder/$$$$?apikey=b1360803f80dd08bdd0211c5c004ad03"
symbols_wise_scrap_and_dump(url_etf_holders,"Etf Holders",etf_list_of_symbols)  

url_historical_price_full = "https://financialmodelingprep.com/api/v3/historical-price-full/$$$$?serietype=line&apikey=b1360803f80dd08bdd0211c5c004ad03"
symbols_wise_scrap_and_dump(url_historical_price_full,"Historical Price Full",break_symbol(top1000_list_of_symbols,steps=5,convert_str = True),if_hist=True)
macro_commodity = "https://financialmodelingprep.com/api/v3/historical-chart/1day/$$$$?from=1900-10-10&to=2030-08-10&apikey=b1360803f80dd08bdd0211c5c004ad03"
symbols_wise_scrap_and_dump(
    macro_commodity,
    "Macro Economics",
    [x.lower() for x in ["PLUSD","CTUSX","NGUSD","CLUSD","HOUSD","ZGUSD","HGUSD","CCUSD","SIUSD","KCUSX","LBUSD"]],
    flag=True,
)


url_sec_filing = "https://financialmodelingprep.com/api/v3/sec_filings/$$$$?page=0&apikey=b1360803f80dd08bdd0211c5c004ad03"
symbols_wise_scrap_and_dump(url_sec_filing,"SEC Filing",top1000_list_of_symbols)