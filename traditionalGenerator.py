import numpy as np
import Utils
from electricityGenerator import electricityGenerator

class traditionalGenerator(electricityGenerator):
    
    def __init__(self, genName, capacity, numBus, BASEYEAR):
        super().__init__(genName, capacity, numBus, BASEYEAR)
        self.renewable_flag = False
        self.availability_factor = 0.9
    
    # load fuel cost method
    def loadFuelCost(self, FILEPATH): 
        self.future_fuel_cost = Utils.loadFuelCostFile(self.name, FILEPATH)
        self.fuel_cost = self.future_fuel_cost[0]/self.efficiency

    # get generation for demand profile
    def dispatch(self, demand):
        # to update to use arrays instead of list
        newDemand = np.zeros(8760)
        arr_demand = np.array(demand)
        temp_arr_excess = np.zeros(8760)
        hourly_energy_generated = np.zeros(8760) + self.capacity*self.availability_factor #init with maximum energy generation kWh

        hourly_energy_generated = np.min([hourly_energy_generated, arr_demand], axis=0) # get the minimum between the maximum energy generation from the unit and the demand

        if(self.name == 'Nuclear'):
            # Minimum power capacity is 50% during summer months (June, July, August) day>151 and day<243 and 65% during the rest of the year
            arr_minNuclearOp = np.zeros(8760)+self.capacity*0.65
            arr_minNuclearOp[151*24:243*24] = self.capacity*0.5

            #Cap the minimum generation of nuclear
            hourly_energy_generated = np.max([hourly_energy_generated, arr_minNuclearOp], axis=0)

            # excess generation only for nuclear power plant
            temp_arr_excess = np.subtract(arr_demand, hourly_energy_generated)  #find indices where demand is lower than the minimum nuclear generation
            temp_arr_excess[np.where(temp_arr_excess>0)] = 0 #remove values where energy generated is lower than demand
            temp_arr_excess = -temp_arr_excess 

        newDemand = np.subtract(arr_demand, hourly_energy_generated).clip(min=0)

        self.yearly_energy_generated = np.sum(hourly_energy_generated)
        self.hourly_energy_generated = hourly_energy_generated

        return self.hourly_energy_generated, newDemand, temp_arr_excess

            



    
    









        
        
