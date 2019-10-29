import pandas as pd

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

def cal_off_cap(df, unit, unit_cap_dict, thresh = 0.9):
    off_cap_days = len(df.loc[df[unit] >= unit_cap_dict[unit]])
    off_thresh_days = len(df.loc[df[unit] >= int(unit_cap_dict[unit]*thresh)])
    return [off_cap_days, off_thresh_days]
