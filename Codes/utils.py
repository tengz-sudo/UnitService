import pandas as pd
import numpy as np

SERVICE_MAP = {
'***':'Unknown',
'Adolescent Gynecology' : 'Gynecology',
'Adolescent Medicine' : 'General Pediatrics',
'Anesthesia and Pain':'Pain',
'Audiology':'Unknown',
'Cardiac Cath': 'Cardiology',
'Cardiology':'Cardiology',
'Cardiovascular Intensive Care': 'Cardiology',
'Cardiovascular Surgery':'Cardiology',
'Dentistry':'Cardiology', #(almost only dental patients with heart issues get admitted after dental procedures)
'Development and Behavior':'Unknown',
'Endocrinology':'General Pediatrics',
'Gastroenterology': 'Green Team',
'Gastrointenstinal Pathology': 'Green Team',
'General Pediatrics': 'General Pediatrics',
'General Surgery': 'General Surgery',
'Genetics': 'General Pediatrics',
'GI/Liver': 'Green Team',
'Gynecology': 'Gynecology',
'Gynecology and Obstetrics': 'Gynecology',
'Hand': 'Unknown', # [we could maybe consider this plastics]
'Hematology':'HemeOnc/SCT',
'Hematology/Oncology': 'HemeOnc/SCT',
'Immunology and Allergy': 'General Pediatrics',
'Infectious Disease':'Unknown', #[we could maybe consider this Gen Peds]
'Neonatology': 'General Pediatrics',
'Nephrology': 'Red Team',
'Neuro Oncology': 'HemeOnc/SCT',
'Neurosurgery': 'Neurosurgery',
'Newborn Nursery':'Unknown', #[we could maybe consider this Gen Peds]
'Obstetrics':'Unknown',
'Oncology': 'HemeOnc/SCT',
'Ophthalmology':'General Pediatrics',
'Oromaxilofacial Surgery':'Unknown',
'Orthopedic Surgery':'Orthopedics',
'Orthopedics':'Orthopedics',
'Otolaryngology (ENT)': 'ENT',
'Pain Management': 'Pain',
'Psychiatry':'Unknown', # [we could maybe consider this Gen Peds]
'Pulmonary': 'Pulmonary',
'Pulmonary and Critical Care': 'Pulmonary',
'Radiology':'Unknown',
'Rehabilitation':'Unknown',
'Respiratory Care': 'Pulmonary',
'Rheumatology':'Red Team',
'Stem Cell Transplant': 'HemeOnc and StemCell',
'Transplant Surgery': 'Transplant',
'Trauma': 'General Surgery',
'Urology': 'Urology',
# added later
'Intensive Care':'Unknown'
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
'Pulmonary':0.92,
'General Pediatrics':1.06,
'General Surgery':0.83,
'Urology':3,
'Plastic Surgery':0.5
}

def convert_datatimes(df):
    # convert the datetime columns into datatime in panda
    cols = ['Hospital Admission Dt/Tm', 'Hospital Discharge Dt/Tm',
           'Effective Date/Time', 'Originally_Scheduled_For', 'Originally_Scheduled_On',
           'Patient in Facility', 'Patient in Room', 'Patient out of Room',
       'Ready for Discharge from Recovery', 'Patient out of Recovery']
    for col in cols:
        df.loc[:, col] = pd.to_datetime(df[col])
    return df

def convert_service_name(df):
    # convert the datetime columns into datatime in panda
    def converter(s):
        if s in SERVICE_MAP.keys():
            return SERVICE_MAP[s]
        else:
            return s
    df['Service New'] = df['Service.x'].apply(converter)
    df = df.rename(columns = {'Service.x':'Service Original', 'Service New':'Service.x'})
    return df

def convert_dept_name(df):
    # convert the datetime columns into datatime in panda
    def converter(d):
        if d in DEPT_MAP.keys():
            return DEPT_MAP[d]
        else:
            return d
    df['Dept Abbrev'] = df['Dept Abbrev'].apply(converter)
    # df = df.rename(columns = {'Service.x':'Service Original', 'Service New':'Service.x'})
    return df

def print_services_in_units(df):
    # print top 10 services  in each unit
    major_units = df['Dept Abbrev'].value_counts().index
    for dept in major_units:
        temp = df.loc[df['Dept Abbrev'] == dept]
        print('Major Services in [', dept, '] :::::::')
        print(temp['Service.x'].value_counts()[:10])
        print('\n')

def print_units_of_services(df, col = 'Service.x'):
    services_set = df[col].value_counts().index
    for service in services_set:
        temp = df.loc[df[col] == service]
        print('Major Units of Service [', service, '] :::::::')
        print(temp['Dept Abbrev'].value_counts()[:10])
        print('\n')

def service_daily_stats(df, services_set, percentiles = [0.25, 0.5, 0.75, 0.95, 0.97]):
    temp = pd.DataFrame()
    for service in services_set:
        temp[service] = df[service].describe(percentiles = percentiles)
    return temp

def daily_census_adjust(df):
    def converter(c):
        return np.round(c)
    for service in GROWTH_RATE:
        df[service] = df[service]*GROWTH_RATE[service]
        df[service] = df[service].apply(converter)
    return df


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
