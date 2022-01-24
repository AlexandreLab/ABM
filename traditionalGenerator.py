import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils
from electricityGenerator import electricityGenerator

class traditionalGenerator(electricityGenerator):
    
    def __init__(self, genName, genTypeID, capacity, lifetime, numBus, headroom, BASEYEAR):
        super().__init__(genName, genTypeID, capacity, lifetime, numBus, headroom, BASEYEAR)
        self.renewableBool = False
        self.availabilityFactor = 0.9
    
    # load fuel cost method
    def loadFuelCost(self,FILEPATH): 
        self.yearlyFuelCost = Utils.loadFuelCostFile(self.name, FILEPATH)
        self.FuelCost = self.yearlyFuelCost[0]

    # get generation for demand profile
    def getGeneration(self, demand):
        # to update to use arrays instead of list
        newDemand = np.zeros(8760)
        arr_demand = np.array(demand)
        temp_arr_excess = np.zeros(8760)
        energyGenerated = np.zeros(8760) + self.genCapacity*self.availabilityFactor #init with maximum energy generation kWh
        if(self.name == 'Nuclear'):
            # to add change of capacity factor during summer
            minNuclearOpCap = self.genCapacity*0.65

            # excess generation only for nuclear power plant
            temp_arr_excess = arr_demand - minNuclearOpCap  #find indices where demand is lower than the minimum nuclear generation
            temp_arr_excess[np.where(temp_arr_excess>0)] = 0 #remove values where energy generated is lower than demand
            temp_arr_excess = -temp_arr_excess 
            energyGenerated[np.where(temp_arr_excess > 0)] = minNuclearOpCap

        else:
            energyGenerated = np.min([energyGenerated, arr_demand], axis=0) # get the minimum between the maximum energy generation from the unit and the demand

        newDemand = np.subtract(arr_demand, energyGenerated).clip(min=0)

        self.yearlyEnergyGen = np.sum(energyGenerated)
        self.energyGenerated = energyGenerated

        return self.energyGenerated, newDemand, temp_arr_excess

            



    
    









        
        
