import random
import numpy as np
from electricityGenerator import electricityGenerator
import Utils
from timeit import default_timer as timer

class renewableGenerator(electricityGenerator):
    
    
    def __init__(self,genName, capacity, numBus, BASEYEAR): # kW
        super().__init__(genName, capacity, numBus, BASEYEAR)
        self.renewable_flag = True
        solar_FiT_filePath = 'WholesaleEnergyPrices/Solar_FiT_2010_2019_GBPPerkWh.txt'
        self.yearly_solar_FiT = Utils.loadTextFile(solar_FiT_filePath) # GBP per kWh

        # load generation profile and scale to match desired capacity
    def loadScaleGenProfile(self, FILEPATH):
        # start = timer()
        self.hourly_energy_generated = np.array(Utils.loadTextFile(FILEPATH))

        if(self.name == 'Solar'): # solar
            fileGenCapacity = 13000000        
        elif(self.name == 'Hydro'): # Hydro
            fileGenCapacity = 1000000
        elif(self.name == 'Wind Onshore'): # Onshore wind
            fileGenCapacity = 9500000
        elif(self.name == 'Wind Offshore'): # Offshore wind
            fileGenCapacity = 4000000

        self.hourly_energy_generated = self.hourly_energy_generated*1000*self.capacity/fileGenCapacity
        self.yearly_energy_generated = np.sum(self.hourly_energy_generated)
        # print("end loadScale function: {0}".format(timer()-start))
    
    # used for testing
    def loadGenRandomProfile(self, timesteps, minV, maxV):
        # For now, just generating random numbers to check if works*
        self.hourly_energy_generated = list()
        for i in range(timesteps): #8760 hours in year
            self.hourly_energy_generated.append(random.uniform(minV, maxV)) #kW
            self.yearly_energy_generated = self.yearly_energy_generated + self.hourly_energy_generated[i]
        
    