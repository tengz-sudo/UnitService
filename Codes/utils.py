

def convert_datatimes(df):
    # convert the datetime columns into datatime in panda
    cols = ['Hospital Admission Dt/Tm', 'Hospital Discharge Dt/Tm',
           'Effective Date/Time', 'Originally_Scheduled_For', 'Originally_Scheduled_On',
           'Patient in Facility', 'Patient in Room', 'Patient out of Room',
       'Ready for Discharge from Recovery', 'Patient out of Recovery']
    for col in cols:
        df.loc[:, col] = pd.to_datetime(df[col])
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


print('utils are imported! yeah!')
