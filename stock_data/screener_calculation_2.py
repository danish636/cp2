import pandas as pd
from datetime import date, timedelta
import json
import numpy as np
import os

# curr_date = str(date.today()).replace('-', '')
# print(curr_date)
output = {}
# screener_data = pd.read_csv('media/screener_data/screener_'+str(curr_date)+'.csv')

today_date = date.today()
i = 0
while True:
    if i > 0:
        today_date = today_date - timedelta(days=1)
        # date_string = str(today_date).split(" ")[0].replace("-", "")
    try: 
        curr_date = str(today_date).replace('-', '')
        #screener_data = pd.read_csv('media/screener_data/screener_'+str(curr_date)+'.csv')
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_api_data", "Media", "screener_data")
        screener_data = pd.read_csv(os.path.join(base_path, f"screener_{curr_date}.csv")) #@danish
        break
    except:
        i = i + 1
        
percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
negative_cols = ['capexPerShareTTM', 'capexToOperatingCashFlowTTM', 'capexToRevenueTTM', 'effectiveTaxRateTTM', 'enterpriseValueTTM', 'intangiblesToTotalAssetsTTM',
 'stockBasedCompensationToRevenueTTM', 'enterpriseValueMultipleTTM', 'evToSalesTTM', 'evToOperatingCashFlowTTM', 'evToFreeCashFlowTTM', 'priceToBookRatioTTM', "priceToSalesRatioTTM_y", "priceToSalesRatioTTM_x",
 'priceEarningsRatioTTM', 'priceEarningsToGrowthRatioTTM', 'priceToFreeCashFlowsRatioTTM', 'priceToOperatingCashFlowsRatioTTM', 'priceSalesRatioTTM', 'researchAndDevelopementToRevenueTTM',
 'salesGeneralAndAdministrativeToRevenueTTM', 'debtEquityRatioTTM', 'debtToAssetsTTM', 'interestDebtPerShareTTM', 'longTermDebtToCapitalizationTTM', 'netDebtToEBITDATTM',
 'totalDebtToCapitalizationTTM', 'cashConversionCycleTTM', 'daysOfInventoryOutstandingTTM', 'daysOfSalesOutstandingTTM', 'operatingCycleTTM']
final_output = {}
final_output['industry'] = {}
final_output_us = {}
final_output_us['industry'] = {}
for per in percentiles:
    print(per)
    final_output['industry'][per] = {}
    final_output_us['industry'][per] = {}
    for column in list(screener_data.columns.values):
        if screener_data[column].dtypes == 'int64' or screener_data[column].dtypes == 'float64':
            print(column)
            all_industry = screener_data.groupby(['industry'])[[str(column),"country"]]
            final_output['industry'][per][str(column)] = {}
            final_output_us['industry'][per][str(column)] = {}
            for key, item in all_industry:
                # print(key)
                if len(item[item["country"] == "US"]) > 50:
                    if column in negative_cols:
                        
                        final_output['industry'][per][str(column)][str(key)] = item[item["country"] == "US"][str(column)].abs().quantile(1-per)
                    else:
                        if column in ["best","base","worst","relative_best","relative_base","relative_worst"]:
                            final_output['industry'][per][str(column)][str(key)] = item[item["country"] == "US"][str(column)].quantile(1-per)
                        else:
                            final_output['industry'][per][str(column)][str(key)] = item[item["country"] == "US"][str(column)].quantile(per)
                else:
                    df = all_industry.get_group(key)
                    # if 'capex' not in column.lower():
                    #     df = df[df[str(column)]>0]
                    # df.replace([np.inf, -np.inf], None, inplace=True)
                    # df.dropna(how="all", inplace=True)
                    df = df.replace([np.inf, -np.inf], None)  # Avoid inplace
                    df = df.dropna(how="all") #@danis
                    if column in negative_cols:
                        final_output['industry'][per][str(column)][str(key)] = df[str(column)].abs().quantile(1-per)
                    else:
                        if column in ["best","base","worst","relative_best","relative_base","relative_worst"]:
                            final_output['industry'][per][str(column)][str(key)] = df[str(column)].quantile(1-per)
                        else:
                            final_output['industry'][per][str(column)][str(key)] = df[str(column)].quantile(per)

final_output['sector'] = {}
for per in percentiles:
    print(per)
    final_output['sector'][per] = {}
    for column in list(screener_data.columns.values):
        if screener_data[column].dtypes == 'int64' or screener_data[column].dtypes == 'float64':
            print(column)
            all_sector = screener_data.groupby(['sector'])[[str(column)]]
            final_output['sector'][per][str(column)] = {}
            for key, item in all_sector:
                # print(key)
                df = all_sector.get_group(key)
                # if 'capex' not in column.lower():
                #     df = df[df[str(column)]>0]
                df.replace([np.inf, -np.inf], None, inplace=True)
                df.dropna(how="all", inplace=True)
                if column in negative_cols:
                    final_output['sector'][per][str(column)][str(key)] = df[str(column)].abs().quantile(1-per)
                else:
                    if column in ["best","base","worst","relative_best","relative_base","relative_worst"]:
                        final_output['sector'][per][str(column)][str(key)] = df[str(column)].quantile(1-per)
                    else:
                        final_output['sector'][per][str(column)][str(key)] = df[str(column)].quantile(per)

#industry quantiles calculations
# in_025 = screener_data.groupby(['industry']).quantile(0.25)
# in_05 = screener_data.groupby(['industry']).quantile(0.5)
# in_075 = screener_data.groupby(['industry']).quantile(0.75)
# in_09 = screener_data.groupby(['industry']).quantile(0.9)

# #sector quantiles calculaitons
# se_025 = screener_data.groupby(['sector']).quantile(0.25)
# se_05 = screener_data.groupby(['sector']).quantile(0.5)
# se_075 = screener_data.groupby(['sector']).quantile(0.75)
# se_09 = screener_data.groupby(['sector']).quantile(0.9)

# print('calculated')

# output['industry'] = {}
# output['sector'] = {}

# output['industry']['0.25'] = in_025.to_dict()
# output['industry']['0.5'] = in_05.to_dict()
# output['industry']['0.75'] = in_075.to_dict()
# output['industry']['0.9'] = in_09.to_dict()

# output['sector']['0.25'] = se_025.to_dict()
# output['sector']['0.5'] = se_05.to_dict()
# output['sector']['0.75'] = se_075.to_dict()
# output['sector']['0.9'] = se_09.to_dict()
# print(output)

# j = pd.concat([in_025, in_05, in_075, se_025, se_05, se_075])
# j = j.to_dict()

j = json.dumps(final_output, indent=4)
j_us = json.dumps(final_output_us, indent=4)

#with open(f'media/screener_data/screener_2_{curr_date}.json', 'w') as f:
with open(os.path.join(base_path, f"screener_2_{curr_date}.json"), 'w') as f: #@danish
    f.write(j)
    
# with open(f'media/screener_data/screener_2_US_{curr_date}.json', 'w') as f:
#     f.write(j_us)

# print('file saved')