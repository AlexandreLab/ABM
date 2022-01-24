import random
from random import randint
from collections import namedtuple
import numpy as np
import math
from electricityGenerator import electricityGenerator
import Utils
from timeit import default_timer as timer


class renewableGenerator(electricityGenerator):
    
    
    def __init__(self,genName, genTypeID, capacity,lifetime, CFDPrice, numBus, headroom, BASEYEAR): # kW
        super().__init__(genName, genTypeID, capacity,lifetime, numBus, headroom, BASEYEAR)

        self.CFDPrice = CFDPrice # GBP
        self.renewableBool = True
        solarFiTFilePath = 'WholesaleEnergyPrices/Solar_FiT_2010_2019_GBPPerkWh.txt'
        self.yearlySolarFiT = Utils.loadTextFile(solarFiTFilePath) # GBP per kWh

        # load generation profile and scale to match desired capacity
    def loadScaleGenProfile(self,FILEPATH):
        # start = timer()
        self.energyGenerated = np.array(Utils.loadTextFile(FILEPATH))

        if(self.name == 'Solar'): # solar
            fileGenCapacity = 13000000        
        elif(self.name == 'Hydro'): # Hydro
            fileGenCapacity = 1000000
        elif(self.name == 'Wind Onshore'): # Onshore wind
            fileGenCapacity = 9500000
        elif(self.name == 'Wind Offshore'): # Offshore wind
            fileGenCapacity = 4000000

        self.energyGenerated = self.energyGenerated*1000*self.genCapacity/fileGenCapacity
        # print("end loadScale function: {0}".format(timer()-start))
  
    # used for testing
    def loadGenRandomProfile(self,timeSteps,minV, maxV):
        # For now, just generating random numbers to check if works*
        self.energyGenerated = list()
        for i in range(timeSteps): #8760 hours in year
            self.energyGenerated.append(random.uniform(minV, maxV)) #kW
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
        
    