import pandas as pd
import numpy as np
import datetime
from utils import *
from qpmodel import *
from perform_utils import *
from tqdm import tqdm

import matplotlib.pyplot as plt
plt.style.use('seaborn-white')
# import numpy as np


class Experiment(object):
    '''
    Object to do experiment
    '''
    def __init__(self,  census_file,
                    fyear = 2019,
                    nogrowth = True,
                    units_to_consider = ['PCU160', 'PCU200', 'PCU300', 'PCU360', 'PCU380', 'PCU400', 'PCU500', 'PCU520'],
                    services_to_consider = ['HemeOnc and StemCell', 'General Surgery', 'Cardiology', 'Green Team',
                                             'Red Team',
                                             'Urology', 'Orthopedics', 'Pulmonary',
                                              'Neurosurgery',
                                              'Neurology',
                                              'Otolaryngology (ENT)',
                                              'Plastic Surgery', 'HemeOnc and StemCell']
                 ):

        start_date = datetime.datetime(year = fyear-1, month = 9, day = 1)
        end_date = datetime.datetime(year = 2019, month = 9, day = 1)
        data = CensusData(fyear=fyear, units_to_consider = units_to_consider,
                              services_to_consider = services_to_consider)
        data.read_census_from_file(census_file)
        data.data_preprocess(start_date = start_date, end_date = end_date)
        data.filter_units_services()
        data.cal_daily_census()
        data.daily_census_adjust(nogrowth = nogrowth)
        data.divide_gen_peds() # divide the gen peds into two teams equally

        self.allocation = None
        self.units_to_consider = data.get_units_to_consider()
        self.services_to_consider = data.get_services_to_consider()
        self.service_count_daily = data.get_adjusted_daily_census()
        self.unit_cap_dict = data.get_dict_unit_cap()
        print('Units:', self.units_to_consider)
        print('Services:', self.services_to_consider)



    def run_model(self, cap_thresh = 0.90):
        self.allocation = constrained_qp(self.services_to_consider,
                                        self.units_to_consider,
                                        self.service_count_daily,
                                        self.unit_cap_dict,
                                        cap_thresh = cap_thresh)
        temp = allocation_to_dict(self.allocation, self.units_to_consider, self.services_to_consider)
        print('\n********Optmial Allocation*******')
        for unit in temp:
            print(unit, temp[unit])

    def plot_results(self):
        allocation_dict = allocation_to_dict(self.allocation, self.units_to_consider, self.services_to_consider)
        present_performance(allocation_dict, self.service_count_daily,
                                self.unit_cap_dict,
                                units_to_consider = ['PCU200', 'PCU300', 'PCU360', 'PCU400', 'PCU500'],
                                cap_thresh = 0.9,
                                over_cap_transfer = 'floor')





# end
