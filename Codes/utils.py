import pandas as pd
import numpy as np
import datetime
from tqdm import tqdm

import matplotlib.pyplot as plt
plt.style.use('seaborn-white')

SERVICE_MAP = {
'***':'Unknown',
'Adolescent Gynecology' : 'Gynecology & Obstetrics',
'Adolescent Medicine' : 'General Pediatrics',
'Anesthesia and Pain':'Anesthesia and Pain',
'Anesthesia': 'Anesthesia and Pain',
'Audiology':'Unknown',
'Cardiac Cath': 'Cardiology',
'Cardiology':'Cardiology',
'Cardiovascular Intensive Care': 'Cardiology',
'Cardiovascular Surgery':'Cardiology',
'Cardiovascular Transplant': 'Cardiology',
'Dentistry':'Cardiology', #(almost only dental patients with heart issues get admitted after dental procedures)
'Development and Behavior':'Unknown',
'Endocrinology':'General Pediatrics',
'Gastroenterology': 'Green Team',
'Gastrointenstinal Pathology': 'Green Team',
'General': 'General Surgery', # low appearance
'General Pediatrics': 'General Pediatrics',
'General Surgery': 'General Surgery',
'Genetics': 'General Pediatrics',
'GI/Liver': 'Green Team',
'Gynecology': 'Gynecology & Obstetrics',
'Gynecology and Obstetrics': 'Gynecology & Obstetrics',
'Obstetrics/Gynecology': 'Gynecology & Obstetrics',
'Hand': 'Unknown', # [we could maybe consider this plastics]
'Hematology':'HemeOnc and StemCell',
'Hematology/Oncology': 'HemeOnc and StemCell',
'Immunology and Allergy': 'General Pediatrics',
'Immunology & Allergy' : 'General Pediatrics',
'Infectious Disease':'Unknown', #[we could maybe consider this Gen Peds]
'Interventional Radiology': 'Unknown',
'Kidney Transplant': 'Red Team',
'Liver Transplant': 'Green Team',
'Neonatology': 'General Pediatrics',
'Nephrology': 'Red Team',
'Neuro Oncology': 'HemeOnc and StemCell',
'Neurosurgery': 'Neurosurgery',
'Newborn Nursery':'Unknown', #[we could maybe consider this Gen Peds]
'Obstetrics':'Unknown',
'Oncology': 'HemeOnc and StemCell',
'Ophthalmology':'General Pediatrics',
'Oromaxilofacial Surgery':'Unknown',
'Orthopedic Surgery':'Orthopedics',
'Orthopedics':'Orthopedics',
'Otolaryngology (ENT)': 'Otolaryngology (ENT)',
'Otolaryngology': 'Otolaryngology (ENT)',
'Pain Management': 'Anesthesia and Pain',
'Plastics': 'Plastic Surgery',
'Psychiatry':'Unknown', # [we could maybe consider this Gen Peds]
'Pulmonary': 'Pulmonary',
'Pulmonary and Critical Care': 'Pulmonary',
'Radiology':'Unknown',
'Rehabilitation':'Unknown',
'Respiratory Care': 'Pulmonary',
'Rheumatology':'Red Team',
'Stem Cell Transplant': 'HemeOnc and StemCell',
'Transplant Surgery': 'Green Team',
'Transplant': 'Green Team',
'Trauma': 'General Surgery',
'Urology': 'Urology',
# added later
'Intensive Care':'Unknown',
'Aerodigestive':'Unknown', # only have 1 count
}

DEPT_MAP = {
'HOPCU' : 'PCU160',
'SCTPCU' : 'PCU160'
}

GROWTH_RATE = {
'Green Team':1.4,
'Red Team':1.4,
'Neurosurgery':0.92,
'Neurology':0.92,
'Yellow Team':0.92, # = Yellow Team = Pulmonary
'Pulmonary':0.92,
'General Pediatrics':1.06,
'General Surgery':0.83,
# 'Urology':3, # delete later
# 'Plastic Surgery':0.5 # delete later
}


class CensusData(object):
    '''
    Object to store the census data, transfer the data, calculate the daily counts
    '''
    def __init__(self,  fyear = 2019,
                        units_to_consider = ['PCU160', 'PCU200', 'PCU300', 'PCU360', 'PCU380', 'PCU400', 'PCU500'],
                        services_to_consider = None,
                        dict_unit_cap = {'PCU200': 26,
                                         'PCU300': 26,
                                         'PCU360': 14,
                                         'PCU380': 0,
                                         'PCU400': 24,
                                         'PCU500': 49,
                                         'PCU520': 0}
                 ):
        self.df_census = None
        self.df_census_year = None
        self.df_to_work = None
        self.df_daily_census = None
        self.df_daily_census_adjusted = None
        self.dict_unit_cap = dict_unit_cap

        self.fyear = fyear
        self.units_to_consider = units_to_consider
        self.services_to_consider = services_to_consider

    def read_census_from_file(self, census_file):
        # census_file = "../Data/2019-09-13Census and Surgical Admits and Scheduled 2.csv"
        self.df_census = pd.read_csv(census_file, index_col = 0)
        self.convert_datatimes()
        print('Read Census Data Size:', self.df_census.shape)

    def convert_datatimes(self):
        # convert the datetime columns into datatime in panda
        cols = ['Hospital Admission Dt/Tm', 'Hospital Discharge Dt/Tm',
               'Effective Date/Time', 'Originally_Scheduled_For', 'Originally_Scheduled_On',
               'Patient in Facility', 'Patient in Room', 'Patient out of Room',
           'Ready for Discharge from Recovery', 'Patient out of Recovery']
        for col in cols:
            self.df_census.loc[:, col] = pd.to_datetime(self.df_census[col])

    def data_preprocess(self, start_date = None, end_date = None):
        # filter out the data by time
        if not start_date:
            start_date = datetime.datetime(year = self.fyear-1, month = 9, day = 1)
        if not end_date:
            end_date = datetime.datetime(year = 2019, month = 9, day = 1)
        self.df_census_year = self.df_census.loc[(self.df_census['Effective Date/Time'] >= start_date) &
                                                (self.df_census['Effective Date/Time'] < end_date)]
        # convert the service and dept names
        self.convert_intensive_care()
        self.convert_service_name()
        self.convert_dept_name()
        # add some columns
        self.df_census_year.loc[:,'Date']  = self.df_census_year['Effective Date/Time'].dt.date
        return None

    def convert_intensive_care(self):
        # df_census is the main census file
        # rule: 1. if service.x is intensive care and service.y is not null, then service.x = service.y
        #       2. use the last unit as their unit
        def fill_x_use_y(row):
            service_y = row['Service.y']
            service_x = row['Service.x']
            if service_x == 'Intensive Care' and not pd.isna(service_y):
                return service_y
            else:
                return service_x

        def fill_x_use_first(row, df_census_part):
            service_x = row['Service.x']
            if service_x == 'Intensive Care':
                csn = row['Primary CSN']
        #         print(csn)
                temp = df_census_part.loc[df_census_part['Primary CSN'] == csn].sort_values('Effective Date/Time').iloc[-1]
        #         temp = temp.loc[~temp['Service.x'].isna()].iloc[-1]
                return temp['Service.x']
            else:
                return service_x

        # first, fill the service.x using service.y
        self.df_census_year['Service.x'] = self.df_census_year.apply(fill_x_use_y, axis = 1)

        # then use the last room to fill in the service
        tqdm.pandas()
        intensice_csn = self.df_census.loc[(self.df_census['Service.x'] == 'Intensive Care')]['Primary CSN'].unique()
        df_census_part = self.df_census.loc[(self.df_census['Primary CSN'].isin(intensice_csn))&
                                      (self.df_census['Service.y'].isna())]
        fill_func = lambda row: fill_x_use_first(row, df_census_part)
        self.df_census_year['Service.x'] = self.df_census_year.progress_apply(fill_func, axis = 1)
        # there might be some rows left still with service.x == Intensive Care, which will be later categorized into Unknown by convert_service_name
        return None

    def convert_service_name(self, service_col = 'Service.x'):
        # convert the datetime columns into datatime in panda
        def converter(s):
            if s in SERVICE_MAP.keys():
                return SERVICE_MAP[s]
            else:
                return s
        self.df_census_year['Service New'] = self.df_census_year[service_col].apply(converter)
        self.df_census_year = self.df_census_year.rename(columns = {service_col:'Service Original', 'Service New':service_col})
        return None

    def convert_dept_name(self, dept_col = 'Dept Abbrev'):
        # convert the datetime columns into datatime in panda
        def converter(d):
            if d in DEPT_MAP.keys():
                return DEPT_MAP[d]
            else:
                return d
        self.df_census_year[dept_col] = self.df_census_year[dept_col].apply(converter)
        # df = df.rename(columns = {'Service.x':'Service Original', 'Service New':'Service.x'})
        return None

    def filter_units(self):
        self.df_to_work = self.df_census_year.loc[self.df_census_year['Dept Abbrev'].isin(self.units_to_consider)]
        self.services_to_consider = list(self.df_to_work['Service.x'].value_counts().index)
        print('In total', len(self.services_to_consider), 'services')

        # rename the 160 to 500
        def switch_160_to_500(d):
            if d == 'PCU160':
                return 'PCU500'
            else:
                return d
        self.df_to_work['Dept Abbrev'] = self.df_to_work['Dept Abbrev'].apply(switch_160_to_500)
        if 'PCU160' in self.units_to_consider:
            self.units_to_consider.remove('PCU160')
        if 'PCU500' not in self.units_to_consider:
            self.units_to_consider += ['PCU500']
        return None

    def filter_units_services(self):
        self.df_to_work = self.df_census_year.loc[self.df_census_year['Dept Abbrev'].isin(self.units_to_consider)]
        if self.services_to_consider:
            self.df_to_work = self.df_to_work.loc[self.df_to_work['Service.x'].isin(self.services_to_consider)]

        self.services_to_consider = list(self.df_to_work['Service.x'].value_counts().index)
        print('In total', len(self.services_to_consider), 'services')

        # rename the 160 to 500
        def switch_160_to_500(d):
            if d == 'PCU160':
                return 'PCU500'
            else:
                return d
        self.df_to_work['Dept Abbrev'] = self.df_to_work['Dept Abbrev'].apply(switch_160_to_500)
        if 'PCU160' in self.units_to_consider:
            self.units_to_consider.remove('PCU160')
        if 'PCU500' not in self.units_to_consider:
            self.units_to_consider += ['PCU500']
        return None


    def cal_daily_census(self):
        df_service_range = self.df_to_work.copy()
        service = self.services_to_consider[0]
        temp = df_service_range.loc[df_service_range['Service.x'] == service]
        temp = temp.groupby('Date')['Service.x'].size().reset_index()
        service_count_daily = temp.rename(columns = {'Service.x':service})
        for service in self.services_to_consider[1:]:
            temp = df_service_range.loc[df_service_range['Service.x'] == service]
            temp = temp.groupby('Date')['Service.x'].size().reset_index()
            service_count_daily = service_count_daily.merge(temp.rename(columns = {'Service.x':service}),
                                                            on = 'Date', how = 'left')
        service_count_daily = service_count_daily.fillna(0)
        # sanity check: if we missed some days
        days_range = (service_count_daily['Date'].max() - service_count_daily['Date'].min()) / datetime.timedelta(days = 1)
        assert (days_range+1 == service_count_daily.shape[0]), "Range not match!"
        self.df_daily_census = service_count_daily
        return None

    def daily_census_adjust(self, converter = None, nogrowth = False):
        # covnerter can be none
        # def converter(c):
        #     return np.round(c)
        self.df_daily_census_adjusted = self.df_daily_census.copy()
        if not nogrowth:
            for service in GROWTH_RATE:
                if service in self.services_to_consider:
                    self.df_daily_census_adjusted[service] = self.df_daily_census_adjusted[service]*GROWTH_RATE[service]
                    if converter:
                        self.df_daily_census_adjusted[service] = self.df_daily_census_adjusted[service].apply(converter)
        return None

    def divide_gen_peds(self, portion = 0.5):
        if  "General Pediatrics" in self.services_to_consider:
            self.df_daily_census_adjusted['General Pediatrics 1'] = self.df_daily_census_adjusted['General Pediatrics'] * portion
            self.df_daily_census_adjusted['General Pediatrics 2'] = self.df_daily_census_adjusted['General Pediatrics'] - self.df_daily_census_adjusted['General Pediatrics 1']
            self.df_daily_census_adjusted = self.df_daily_census_adjusted.drop(columns = ['General Pediatrics'])
            # update service to consider
            self.services_to_consider.remove('General Pediatrics')
            self.services_to_consider += ['General Pediatrics 1', 'General Pediatrics 2']
            print('In total', len(self.services_to_consider), 'units')
        return None

    def get_adjusted_daily_census(self):
        return self.df_daily_census_adjusted

    def get_dict_unit_cap(self):
        return self.dict_unit_cap

    def get_units_to_consider(self):
        return self.units_to_consider

    def get_services_to_consider(self):
        return self.services_to_consider


def print_services_in_units(df, service_col = 'Service.x', dept_col = 'Dept Abbrev'):
    # print top 10 services  in each unit
    major_units = df[dept_col].value_counts().index
    for dept in major_units:
        temp = df.loc[df[dept_col] == dept]
        print('Major Services in [', dept, '] :::::::')
        print(temp[service_col].value_counts()[:10])
        print('\n')

def print_units_of_services(df, service_col = 'Service.x', dept_col = 'Dept Abbrev'):
    services_set = df[service_col].value_counts().index
    for service in services_set:
        temp = df.loc[df[service_col] == service]
        print('Major Units of Service [', service, '] :::::::')
        print(temp[dept_col].value_counts()[:10])
        print('\n')

def service_daily_stats(df, services_set, percentiles = [0.25, 0.5, 0.75, 0.95, 0.97]):
    temp = pd.DataFrame()
    for service in services_set:
        temp[service] = df[service].describe(percentiles = percentiles)
    return temp


def allocation_to_dict(allocation, units_to_consider, services_to_consider):
    # turn 0/1 allocation table into allocation dictionary
    allocation_dict = {}
    for unit in units_to_consider:
        for service in services_to_consider:
            if allocation.loc[service, unit] == 1:
                if unit in allocation_dict:
                    allocation_dict[unit] += [service]
                else:
                    allocation_dict[unit] = [service]
    return allocation_dict


def allocation_dict_to_dataframe(all_dict):
    # turn a unit:[list of service] dict to a 0/1 allocation table
    service_set = [item for l in all_dict.values() for item in l ]
    unit_set = list(all_dict.keys())
    all_df = pd.DataFrame()
    all_df['Service'] = service_set
    for unit in unit_set:
        all_df[unit] = 0
    all_df = all_df.set_index('Service')
    for unit in unit_set:
        for service in all_dict[unit]:
            all_df.loc[service, unit] = 1
    return all_df


print('utils are imported! yeah!')
