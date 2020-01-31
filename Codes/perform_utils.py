import pandas as pd
import numpy as np
from utils import *

def cal_cap_diff(allocation, service_count_daily, units_to_consider, services_to_consider):
    allocation_temp = allocation.copy()
#     allocation_temp = allocation_orig.copy()

    off_capacity_daily = pd.DataFrame()
    off_capacity_daily['Date'] = service_count_daily['Date']
    for unit in units_to_consider:
        off_capacity_daily[unit] = unit_cap_dict[unit]

    service_count_copy = service_count_daily.copy().set_index('Date')
    off_capacity_daily = off_capacity_daily.set_index('Date')
    for day in off_capacity_daily.index:
        for unit in units_to_consider:
            total_cap_day = 0
            for service in services_to_consider:
                total_cap_day += service_count_copy.loc[day, service]*allocation_temp.loc[service, unit]
            off_capacity_daily.loc[day, unit] -= total_cap_day

    return off_capacity_daily

def cal_daily_census(allocation, service_count_daily, units_to_consider, services_to_consider):
    allocation_temp = allocation.copy()
#     allocation_temp = allocation_orig.copy()

    off_capacity_daily = pd.DataFrame()
    off_capacity_daily['Date'] = service_count_daily['Date']
    for unit in units_to_consider:
        off_capacity_daily[unit] = 0

    service_count_copy = service_count_daily.copy().set_index('Date')
    off_capacity_daily = off_capacity_daily.set_index('Date')
    for day in off_capacity_daily.index:
        for unit in units_to_consider:
            total_cap_day = 0
            for service in services_to_consider:
                total_cap_day += service_count_copy.loc[day, service]*allocation_temp.loc[service, unit]
            off_capacity_daily.loc[day, unit] = total_cap_day

    return off_capacity_daily

def cal_off_cap(df, unit, unit_cap_dict, thresh = 0.9, method = 'floor'):
    cap_unit = np.round(df[unit])

    off_cap_days = len(df.loc[cap_unit >= unit_cap_dict[unit]])
    if method == 'floor':
        off_thresh_days = len(df.loc[cap_unit >= np.floor(unit_cap_dict[unit]*thresh)])
    elif method == 'round':
        off_thresh_days = len(df.loc[cap_unit >= np.round(unit_cap_dict[unit]*thresh)])
    elif method == 'ceil':
        off_thresh_days = len(df.loc[cap_unit >= np.ceil(unit_cap_dict[unit]*thresh)])
    return [off_thresh_days, off_cap_days]


def present_performance(allocation_dict, service_count_daily,
                        unit_cap_dict,
                        units_to_consider = ['PCU200', 'PCU300', 'PCU360', 'PCU400', 'PCU500', 'PCU380'],
                        cap_thresh = 0.9,
                        over_cap_transfer = 'floor'):

    allocation = allocation_dict_to_dataframe(allocation_dict)
    services_to_consider = [item for l in allocation_dict.values() for item in l]
    result = cal_daily_census(allocation, service_count_daily, units_to_consider, services_to_consider)

    # plot the performance for each unit

    f = plt.figure(figsize=(20,16))
    off_unit_days = {}
    for i in range(len(units_to_consider)):
        unit = units_to_consider[i]
        ax = f.add_subplot(3, 2, i+1)
        ax.plot(result[unit])
        ax.axhline(y=int(unit_cap_dict[unit]), color='r', linestyle='-')
        ax.axhline(y=int(unit_cap_dict[unit]*0.9), color='g', linestyle='-')
        off_unit_days[unit] = cal_off_cap(result, unit, unit_cap_dict, cap_thresh, over_cap_transfer)
        ax.title.set_text(unit)
        ax.grid()

    print('----off-service-stats----')
    print('[over_90%_cap_days, over_full_cap_days]')
    over_cap_count = 0
    over_90_count = 0
    for key in off_unit_days:
        aa, bb = off_unit_days[key]
        over_cap_count += aa
        over_90_count += bb
        print(key, off_unit_days[key])
    print('----in-total----')
    print(over_cap_count, over_90_count)

# dsd
