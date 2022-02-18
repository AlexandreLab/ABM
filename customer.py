from random import randint
from collections import namedtuple
import numpy as np
import Utils


class Customer():
    def __init__(self, timesteps, BASEYEAR):
        self.timesteps = timesteps
        self.busbar = 0
        self.year = BASEYEAR
        self.baseyear = BASEYEAR
        self.load_file_path = 'Generation/TotalElectricityGeneration_hourly_2018_kWh.txt'
        self.fes_yearly_peak = Utils.loadTextFile(
            'Generation/NationalGrid_FES_TwoDeg_PeakDemandChange.txt')
        self.fes_yearly_total = Utils.loadTextFile(
            'Generation/NationalGrid_FES_TwoDeg_TotalDemandChange.txt')
        self.consumer_perc_list = [1]
        self.yearly_elec_price = []
        self.cur_elec_price = 0
        self.baseyear_load_profile = self.get_load_profile()*self.consumer_perc_list[(self.busbar-1)]
        self.load_profile = np.zeros(timesteps)
        self.name = 'Customer ' + str(self.busbar)

    def get_load_profile(self):
        if self.baseyear == 2018:
            load_profile = Utils.loadTextFile(self.load_file_path)
        elif self.baseyear == 2010:
            temp_list = Utils.loadTextFile(self.load_file_path)
            load_profile = temp_list*(1+9.32)
        else:
            input('Baseyear not 2010 or 2018, do you want to continue with 2018 demand data?')
        return load_profile

    # loops through each hour
    def run_sim(self):
        net_load = self.load_profile
        return net_load

    def load_price(self):
        filepath = 'RetailElectricityPrices/ResidentialElectricityPrice'+str(self.baseyear)+'_2050_GBPperkWh.txt'
        self.yearly_elec_price = Utils.loadTextFile(filepath)
        self.cur_elec_price = self.yearly_elec_price[0]
        return True

    def update_load_profile(self):
        y = self.year-self.baseyear
        org_peak = np.max(self.baseyear_load_profile)/1000000 #peak in GW
        current_peak = self.fes_yearly_peak[y]*self.consumer_perc_list[(self.busbar-1)]
        self.load_profile = self.baseyear_load_profile*current_peak/org_peak
        return True

    # update values for next year (demand elasticity)
    def increment_year(self): # reads in pc change in wholesale elec price, e.g. + 2% or -1%
        self.year = self.year + 1
        self.update_load_profile()
        return True

    