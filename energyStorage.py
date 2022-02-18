import numpy as np
from asset import asset
from Utils import timer_func

class energyStorage(asset):
    
    def __init__(self, name, capacity, charge_rate, discharge_rate, year, NumBus, BASEYEAR):

        self.name = name
        self.timesteps = 8760

        self.BASEYEAR = BASEYEAR
        self.year = year
        self.busbar = NumBus

        #Economic parameters
        self.discount_rate = 0
        self.ROI = 0
        self.NPV = 0.0

        #Technical parameters
        self.capacity = capacity # kWh
        self.current_capacity = 0.0 # kWh 
        self.charge_rate = charge_rate # kW
        self.discharge_rate = discharge_rate # kW
        self.hourly_storage = np.array(8760) # real-time SoC kWh
        self.hourly_energy_exchange = np.array(8760) # kW
        self.lifetime = 15
        self.actualCapFac = (self.capacity/self.charge_rate)/24 # number of hours per cycle / 24
        self.yearly_energy_stored = 0
        self.availability_factor = 0
        self.construction_time = 0
        self.ghg_emissions_per_kWh = 0 # kg of CO2 emitted per kWh generated
        self.start_year = 0
        self.end_year = 0


        #Economic parameters
        self.yearly_income = 0.0
        self.yearly_cost = 0.0
        self.yearly_profit =0.0
        self.hourly_profit = np.zeros(self.timesteps)
        self.hourly_income = np.zeros(self.timesteps)
        self.hourly_cost = np.zeros(self.timesteps)
        self.marginal_cost = np.zeros(self.timesteps)
        self.yearly_emissions = 0.0


        self.yearly_profit_list = list() # keep track of the past profit of a plant to see if it is profitable

        self.fuel_cost = 0.0 #£/kWh_electricity
        self.current_CO2_price = 0.0 #£/tCO2
        self.fixed_OM_cost = 0.0 #£/kW
        self.variable_OM_Cost = 0.0 #£/kWh_electricity
        self.capital_cost = 0.0 #£/kW
        self.waste_cost = 0.0
        self.cost_of_generating_electricity = 0  #£/kWh_electricity

        self.connection_fee = 0 # to be defined
        self.capacity_market_sub = 0.0 # no subsidies for capital unless specified £ / kW cap per year
        self.discount_rate = 0
        self.CFDPrice = 0 # GBP
        self.TNUoS_charge = 0 #£/kW

    # @timer_func # to get the execution time
    def chargingDischargingBattery(self, arr_chargeRate, arr_dischargeRate, netDemand):
        arr_charge = arr_chargeRate*self.capacity # how much we want to charge by
        arr_charge = arr_charge.clip(max=self.charge_rate) #cap it to the max charge_rate (should not be useful)

        arr_discharge = arr_dischargeRate*self.capacity # how much we want to charge by
        arr_discharge = arr_discharge.clip(max=self.discharge_rate) #cap it to the max discharge_rate (should not be useful)
        arr_discharge = np.min([arr_discharge, netDemand], axis=0)  # we should not discharge more than the demand 
        
        current_capacity = 0
        list_energyStored = []
        list_curCapacity = []
        for val in np.subtract(arr_charge, arr_discharge):
            energyStored = val
            if val > 0: #charging
                if current_capacity+val >= self.capacity: # battery is full
                    energyStored = self.capacity-self.current_capacity
                    current_capacity = self.capacity
                else:
                    current_capacity = current_capacity + energyStored
            else: #discharging
                if current_capacity-val <= 0: # battery is empty
                    energyStored = -current_capacity
                    current_capacity = 0
                else:
                    current_capacity = current_capacity + energyStored
            list_energyStored.append(energyStored)
            list_curCapacity.append(current_capacity)

        self.hourly_energy_exchange = np.array(list_energyStored) #+charging, -discharging
        self.hourly_storage = np.array(list_curCapacity)
        self.yearly_energy_stored = np.sum(self.hourly_energy_exchange.clip(min=0))
         
        #return the netDemand minus what was stored in the battery and what was released from the battery
        return np.subtract(netDemand, -self.hourly_energy_exchange)

    def calc_revenue(self, hourly_wholesale_price):
        hourly_variable_OM = np.absolute(self.hourly_energy_exchange) * self.variable_OM_Cost

        hourly_income = self.hourly_energy_exchange.copy() # Income occurs when discharging the battery
        hourly_income = -hourly_income.clip(max=0) #remove the values when the battery is charging
        hourly_income = np.multiply(hourly_income, hourly_wholesale_price) + ((self.capacity_market_sub*self.discharge_rate)/(365*24))

        hourly_cost = self.hourly_energy_exchange.copy() # Charging cost occurs when charging the battery
        hourly_cost = hourly_cost.clip(min=0) #remove the values when the battery is discharging
        hourly_cost = np.multiply(hourly_cost, hourly_wholesale_price)

        hourly_cost = np.add(hourly_cost, hourly_variable_OM) + self.fixed_OM_cost*self.capacity/8760
        hourly_profit = np.subtract(hourly_income, hourly_cost)

        self.marginal_cost = np.zeros(8760)
        self.marginal_cost[np.where(self.hourly_energy_exchange < 0)] = self.variable_OM_Cost #hourly_energy_exchange: +charging, -discharging
        self.hourly_profit = hourly_profit
        self.hourly_income = hourly_income
        self.yearly_cost = np.sum(hourly_cost)
        self.yearly_profit = np.sum(hourly_profit)
        self.yearly_income = np.sum(hourly_income)

        total_initial_investment = self.capital_cost*self.capacity + self.connection_fee
        self.ROI = (self.yearly_profit*(1-(1+self.discount_rate)**-self.lifetime)/self.discount_rate - total_initial_investment)/total_initial_investment
        self.NPV = self.yearly_profit*(1-(1+self.discount_rate)**-self.lifetime)/self.discount_rate - total_initial_investment

    # update date for next year
    def increment_year(self):
        self.yearly_profit_list.append(self.yearly_profit)
        age = self.year - self.start_year
        if(age >= 15):
            self.CFDPrice = 0.0
        self.year = self.year + 1

        self.current_CO2_price = 0
        self.yearly_energy_stored = 0
        self.yearly_income = 0.0
        self.yearly_cost = 0.0
        self.yearly_profit=0.0
        self.hourly_profit = np.zeros(self.timesteps)
        self.hourly_income = np.zeros(self.timesteps)
        self.hourly_cost = np.zeros(self.timesteps)
        self.marginal_cost = np.zeros(self.timesteps)
        self.yearly_emissions = 0.0

        return True


        
    def getActCapFactor(self):
        # to be updated
        self.actualCapFac = (self.capacity/self.charge_rate)/24
        return self.actualCapFac
    




    
    









        
        
