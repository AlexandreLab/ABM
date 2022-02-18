import numpy as np
from asset import asset

class electricityGenerator(asset):
    
    
    def __init__(self, genName, capacity, numBus, BASEYEAR):

        self.name = genName
        self.timesteps = 8760
        
        self.busbar = numBus

        #Technical parameters
        self.ghg_emissions_per_kWh = 0.0 # kg of CO2 emitted per kWh generated
        self.lifetime = 0
        self.efficiency = 0
        self.capacity = capacity #kW
        self.renewable_flag = False
        self.yearly_emissions = 0.0
        self.yearly_energy_generated = 0.0
        self.hourly_energy_generated = np.zeros(self.timesteps)
        self.hourly_emissions = np.zeros(self.timesteps)
        self.capacity_factor = 0
        self.availability_factor = 0

        # Construction parameters
        self.pre_dev_time = 0 # years
        self.construction_time = 0 # years
        self.total_construction_time = 0 # years

        self.start_year = 0
        self.end_year = 0
        self.BASEYEAR = BASEYEAR
        self.year = self.BASEYEAR

        #Economic parameters
        self.yearly_income = 0.0
        self.yearly_cost = 0.0
        self.yearly_profit =0.0
        self.hourly_profit = np.zeros(self.timesteps)
        self.hourly_income = np.zeros(self.timesteps)
        self.hourly_cost = np.zeros(self.timesteps)
        self.marginal_cost = np.zeros(self.timesteps)
        self.future_fuel_cost = list() # list of projected fuel costs

        self.yearly_profit_list = list() # keep track of the past profit of a plant to see if it is profitable

        self.fuel_cost = 0.0 #£/kWh_electricity
        self.currrent_CO2_price = 0.0 #£/tCO2
        self.fixed_OM_cost = 0.0 #£/kW
        self.variable_OM_cost = 0.0 #£/kWh_electricity
        self.capital_cost = 0.0 #£/kW
        self.waste_cost = 0.0
        self.cost_of_generating_electricity = 0  #£/kWh_electricity

        self.TNUoS_charge = 0 #£/kW
        self.connection_fee = 0 # to be defined
        self.capacity_market_sub = 0.0 # no subsidies for capital unless specified £ / kW cap per year
        self.discount_rate = 0
        self.CfD_price = 0 # GBP/kWh

        self.yearly_solar_FiT = np.array([]) # initialize as an empty array

    def calculateHourlyData(self):
        temp_arr_emissions = self.hourly_energy_generated*self.ghg_emissions_per_kWh #kgCO2
        temp_arr_fuelCost = self.hourly_energy_generated*self.fuel_cost
        temp_arr_variableOM = self.hourly_energy_generated*self.variable_OM_cost
        temp_arr_carbonCost = temp_arr_emissions/1000.0*self.currrent_CO2_price
        temp_arr_waste = self.hourly_energy_generated*self.waste_cost
        

        # margin cost is 0 if the current generation is 0
        temp_arr_marginal_cost = np.sum([temp_arr_fuelCost, temp_arr_waste, temp_arr_variableOM, temp_arr_carbonCost], axis=0)
        temp_arr_marginal_cost = np.divide(temp_arr_marginal_cost, self.hourly_energy_generated, out=np.zeros_like(temp_arr_marginal_cost), where=self.hourly_energy_generated != 0)
        # if self.yearly_energy_generated > 0:
        #     TNUoS_charges_per_hour = (self.TNUoS_charge*self.capacity*self.availability_factor)/self.yearly_energy_generated
        # else:
        #     TNUoS_charges_per_hour = 0
        # temp_arr_marginal_cost = temp_arr_marginal_cost + TNUoS_charges_per_hour

        temp_arr_hourly_cost = np.sum([temp_arr_fuelCost, temp_arr_waste, temp_arr_variableOM, temp_arr_carbonCost], axis=0)
        temp_arr_hourly_cost = temp_arr_hourly_cost + (self.fixed_OM_cost+self.TNUoS_charge*self.availability_factor)*self.capacity/8760
        
        self.yearly_carbon_cost = np.sum(temp_arr_carbonCost)
        self.hourly_cost = temp_arr_hourly_cost
        self.marginal_cost = temp_arr_marginal_cost
        self.hourly_emissions = temp_arr_emissions
        self.yearly_cost = np.sum(temp_arr_hourly_cost)
        self.yearly_emissions = np.sum(temp_arr_emissions)
        return True

    def calc_revenue(self, hourly_wholesale_price):
        if(self.CfD_price>0):
            temp_arr_hourly_income = self.hourly_energy_generated * self.CfD_price
        else:
            if(self.name=='Solar'):
                y = self.year- self.BASEYEAR
                if(y<len(self.yearly_solar_FiT)):
                    temp_arr_hourly_income = self.hourly_energy_generated * self.yearly_solar_FiT[y]
                else:
                    temp_arr_hourly_income = np.multiply(self.hourly_energy_generated, hourly_wholesale_price) + ((self.capacity_market_sub*self.capacity)/(365*24))
            else:
                temp_arr_hourly_income = np.multiply(self.hourly_energy_generated, hourly_wholesale_price) + ((self.capacity_market_sub*self.capacity)/(365*24))

        temp_arr_hourly_profit = np.subtract(temp_arr_hourly_income, self.hourly_cost)
            
        self.hourly_profit = temp_arr_hourly_profit
        self.hourly_income = temp_arr_hourly_income
        self.yearly_profit = np.sum(temp_arr_hourly_profit)
        self.yearly_income = np.sum(temp_arr_hourly_income)

        total_initial_investment = self.capital_cost*self.capacity + self.connection_fee
        self.ROI = (self.yearly_profit*(1-(1+self.discount_rate)**-self.lifetime)/self.discount_rate - total_initial_investment)/total_initial_investment
        self.NPV = self.yearly_profit*(1-(1+self.discount_rate)**-self.lifetime)/self.discount_rate - total_initial_investment

        #calculate the cost of producing 1 kWh of electricity for this plant used to calculate the merit order for the next year
        self.cost_of_generating_electricity = self.fuel_cost+self.variable_OM_cost+self.ghg_emissions_per_kWh/1000.0*self.currrent_CO2_price+self.waste_cost

    # update date for next year
    def increment_year(self, CO2Price):
        self.yearly_profit_list.append(self.yearly_profit)
        age = self.year - self.start_year
        if(age >= 15):
            self.CfD_price = 0.0
        self.year = self.year + 1
        y = self.year - self.BASEYEAR
        
        self.currrent_CO2_price = CO2Price
        if not self.renewable_flag:
            self.fuel_cost = self.future_fuel_cost[y]/self.efficiency
            self.hourly_energy_generated = np.zeros(self.timesteps)
            self.hourly_emissions = np.zeros(self.timesteps)
        self.resetYearValueRecord()
        return True

    # reset values for next year
    def resetYearValueRecord(self):

        if not self.renewable_flag:
            self.yearly_energy_generated=0.0
        self.yearly_cost = 0.0
        self.yearly_profit = 0
        self.yearly_income = 0
        self.yearly_emissions = 0
        self.yearly_carbon_cost = 0
        
        self.hourly_cost = np.zeros(self.timesteps)
        self.marginal_cost = np.zeros(self.timesteps)
        self.hourly_profit = np.zeros(self.timesteps)
        self.NPV = 0
        
    def getActCapFactor(self):
        maxEnergyGen = self.capacity*24*365
        self.actualCapFac = self.yearly_energy_generated/maxEnergyGen
        return self.actualCapFac

    def estimateCfDSubsidy(self):
        estCfD = 0
        return estCfD
































        
        
