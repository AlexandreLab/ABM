import random
import numpy as np
import Utils
from renewableGenerator import renewableGenerator
from traditionalGenerator import traditionalGenerator
from energyStorage import energyStorage
import pandas as pd
import os

class generationCompany():
    def __init__(self, name, timesteps, params, currentCarbonPrice,BASEYEAR):
        self.params = params

        self.timesteps = timesteps

        self.name = name
        self.discount_rate = 0.1 # 10%

        self.traditional_gen = list()
        self.renewable_gen = list() # list of renewable_generator objects
        self.list_technology_portfolio = list() # list of technology names owned by this company

        self.hourly_gen_per_type = dict() # store the hourly generation profile for each technology type
        columns = ["name", "capacity_kW", "start_year", "end_year", "capacity_market_sub_GBP/kW", "CfD_price_GBP/kWh", "busbar"]
        self.construction_queue = pd.DataFrame(columns=columns)

        self.gen_cap_per_type_per_bus = pd.DataFrame() #generation capacity per type and by bus
        self.storage_cap_per_type_per_bus = pd.DataFrame() #storage capacity per type and by bus
        self.BASEYEAR = BASEYEAR
        self.year = BASEYEAR

        self.energy_stores = list()

        self.current_CO2_price = currentCarbonPrice

    #function that looks at the profitability of plants and choose what will be the next investment of company
    def nextInvestment(self, sorted_TNUoS_charges):

        priority_busbars = sorted_TNUoS_charges.columns
        genROIandNPV = pd.DataFrame(columns=["object_ID", "generation_company", "busbar", "capacity_kW", "start_year", "end_year", "ROI", "NPV"])
        genROIandNPV.index.name = "Technology"
        for gen in self.traditional_gen+self.renewable_gen+self.energy_stores:
            genID = id(gen)
            if gen.ROI > 0:
                unit_name = gen.name
                busbar = self.get_busbar(unit_name, priority_busbars)
                capacity = int(self.params["technical_parameters"].loc[unit_name, "Typical_Capacity_kW"]) # years #capacity to be installed of the technology
                construction_time = int(self.params["technical_parameters"].loc[unit_name, "Construction_Time_Years"]) # years
                start_year = construction_time + self.year
                lifetime = int(self.params["technical_parameters"].loc[unit_name, "Lifetime_Years"]) # years
                end_year = start_year + lifetime
                genROIandNPV.loc[unit_name, :] = [genID, self.name, busbar, capacity, start_year, end_year, gen.ROI, gen.NPV]

        # Keep investment with a positive ROI (if ROI>0 NPV will also be >0)
        return genROIandNPV

    def calc_revenue(self, wholesaleProf): # method to recalculate profit for all plants
        for gen in self.traditional_gen+self.renewable_gen+self.energy_stores:
            gen.calc_revenue(wholesaleProf)
        return True

    def calcEmissions(self): # method to recalculate profit for all plants
        totalGenCoEmissions = 0
        for gen in self.traditional_gen+self.renewable_gen+self.energy_stores:
            totalGenCoEmissions += gen.yearly_emissions
        return totalGenCoEmissions

    # The batteries are controlled at the level of the generation company
    # method to charge/ discharge battery and return net demand - battery usage
    def chargeDischargeBatteryTime(self, netDemand, battery_cat):
        # if netDemand>dailyAverage => battery discharge
        # else: battery charge

        #Difference between hourly demand of a day and the mean demand for the same day
        arr_discharging24Hr = np.array([arr_day-np.mean(arr_day) for arr_day in np.split(netDemand, 8760/24)])
        arr_discharging24Hr = arr_discharging24Hr.flatten()
        arr_charging24Hr = -arr_discharging24Hr.copy()
        arr_discharging24Hr = arr_discharging24Hr.clip(min=0)
        arr_charging24Hr = arr_charging24Hr.clip(min=0)
        arr_charging24Hr = np.array([arr_dayCharging/np.sum(arr_dayCharging) for arr_dayCharging in np.split(arr_charging24Hr, 8760/24)]) #charging rate
        arr_discharging24Hr = np.array([arr_dayDischarging/np.sum(arr_dayDischarging) for arr_dayDischarging in np.split(arr_discharging24Hr, 8760/24)]) #discharging rate

        arr_charging24Hr = arr_charging24Hr.flatten()
        arr_discharging24Hr = arr_discharging24Hr.flatten()
        tempNetDemand = netDemand.copy()
        pd.DataFrame([arr_charging24Hr, arr_discharging24Hr, tempNetDemand]).to_csv("battery.csv")
        for eStore in self.energy_stores:
            if eStore.name == battery_cat:
                tempNetDemand = eStore.chargingDischargingBattery(arr_charging24Hr, arr_discharging24Hr, tempNetDemand)
        return tempNetDemand
            
    # get generation from specific technology type ,e.g. Wind, solar, etc.
    def getRenewableGenerationByType(self, unit_name):
        arr_curGen = np.zeros(self.timesteps)
        for rgen in self.renewable_gen:
            # print(genTypeID, tgen.genTypeID)
            if rgen.name == unit_name:
                curGen = rgen.hourly_energy_generated
                arr_curGen = np.add(arr_curGen, curGen)
        self.hourly_gen_per_type[unit_name] = arr_curGen
        return arr_curGen

    # get generation from specific technology type ,e.g. CCGT
    def getTraditionalGenerationByType(self, unit_name, curNetD):
        tempNetD = curNetD.copy()
        arr_curGen = np.zeros(self.timesteps)
        arr_currExcessGen = np.zeros(self.timesteps)
        for tgen in self.traditional_gen:
            # print(genTypeID, tgen.genTypeID)
            if tgen.name == unit_name:
                curGen, newNetD, curExcessGen = tgen.dispatch(tempNetD)
                # print(np.sum(curGen))
                tempNetD = newNetD
                arr_curGen = np.add(arr_curGen, curGen)
                arr_currExcessGen = np.add(arr_currExcessGen, curExcessGen)
        self.hourly_gen_per_type[unit_name] = arr_curGen
        return arr_curGen, arr_currExcessGen, tempNetD

    # get capacity of all battery storage in kW
    def getBatteryPowerKw(self):
        totalPowerKW = 0.0
        for eStore in self.energy_stores:
            totalPowerKW = totalPowerKW + eStore.discharge_rate
        return totalPowerKW

    # make decision to invest in new generation plants
    def increment_year(self, newCO2Price):
        self.removeOldCapacity()
        self.removeUnprofitableCapacity()
        self.year = self.year + 1
        self.current_CO2_price = newCO2Price
        
        for gen in self.traditional_gen + self.renewable_gen:
            gen.increment_year(newCO2Price)
        # add any new plants that are in the construction queue and are meant to come online
        self.checkConstructionQueue()

        self.hourly_gen_per_type = {}
        return True
        
    # method to add plants to construction queue so that they come online after build time has completed
    def addToConstructionQueue(self, unit_name, capacity, start_year, end_year, capacity_market_sub, CfD_price, busbar):

        print("Adding {0} to the construction queue of the company {1}".format(unit_name, self.name))
        if len(self.construction_queue.index) == 0:
            new_idx = 1
        else:
            new_idx = self.construction_queue.index[-1]+1
        # ["name", "capacity_kW", "start_year", "end_year", "capacity_market_sub_GBP/kW", "CfD_price_GBP/kWh", "busbar"]
        self.construction_queue.loc[new_idx, :] = [unit_name, capacity, start_year, end_year, capacity_market_sub, CfD_price, busbar]
        return True

    # check plants that are in construction queue to see if ready to come online
    def checkConstructionQueue(self):
        units_to_build = self.construction_queue.loc[self.construction_queue["start_year"] == self.year, :]
        self.construction_queue = self.construction_queue.loc[self.construction_queue["start_year"] > self.year, :]
        if len(units_to_build) > 0:
            for idx, row in units_to_build.iterrows():
                unit_name = row["name"]
                capacity = row["capacity_kW"]
                start_year = row["start_year"]
                end_year = row["end_year"]
                capacity_market_sub = row["capacity_market_sub_GBP/kW"]
                CfD_price = row["CfD_price_GBP/kWh"]
                busbar = row["busbar"]
                self.add_unit(unit_name, capacity, start_year, end_year, capacity_market_sub, CfD_price, busbar)
        return True

    # method to remove old capacity whos age>lifetime
    def removeOldCapacity(self):
        for gen in self.traditional_gen + self.renewable_gen + self.energy_stores:
            if gen.end_year <= self.year:
                if gen in self.traditional_gen:
                    self.traditional_gen.remove(gen)
                elif gen in self.renewable_gen:
                    self.renewable_gen.remove(gen)
                else:
                    self.energy_stores.remove(gen)
        return True
        
    # method to remove unprofitable generation plants
    def removeUnprofitableCapacity(self):
        # remove at most 1 plant (renewable or non renewable) that is not profitable
        removed = False
        yearsWait = 8 # number of years allowed to make a loss for before removed
        shuffled_list = [x for x in range(len(self.traditional_gen+self.renewable_gen+self.energy_stores))]
        random.shuffle(shuffled_list)

        for idx in shuffled_list:
            count = 0
            if not removed:
                gen = (self.traditional_gen+self.renewable_gen+self.energy_stores)[idx]
                for yProfit in reversed(gen.yearly_profit_list): # loop through yearly profits from most recent
                    if yProfit < 0:
                        count += 1
                    # if not profitable for x years and no plant has been removed yet
                    if count == yearsWait:
                        if gen in self.traditional_gen:
                            self.traditional_gen.remove(gen)
                        elif gen in self.renewable_gen:
                            self.renewable_gen.remove(gen)
                        else:
                            self.energy_stores.remove(gen)
                        removed = True
                        break
        return True

    def calculateStrikePrice(self, unit_name, capacity, TNUoS_charge, totalGen):

        #add a try/catch to raise error
        # load parameters to calculate the strike price for this technology
        economic_param_df = self.params["economic_parameters"]
        renewableFlag = int(self.params["technical_parameters"].loc[unit_name, 'Renewable_Flag'])
        availability_factor = float(self.params["technical_parameters"].loc[unit_name, 'Availability_Factor'])
        lifetime = int(self.params["technical_parameters"].loc[unit_name, "Lifetime_Years"]) # years
        capital_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="CAPEX"), self.year].values[0]/1000*capacity
        fixed_OM_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="OPEX"), self.year].values[0]/1000*capacity
        variable_OM_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="Variable Other Work Costs"), self.year].values[0]/1000
        # capitalCostAnnualised = (capital_cost*self.discount_rate)/(1-(1+self.discount_rate)**-lifetime)  # EAC GBP/year
        wasteCost = 0 #GBP/kWh
        # capacity_factor = float(self.params["technical_parameters"].loc[unit_name, "Capacity_Factor"])
        ghg_emissions_per_kWh = float(self.params["technical_parameters"].loc[unit_name, "GHG_Emissions_kgCO2/kWh"]) # kgCO2/kWh

        fuelCost = 0
        if not renewableFlag:
            path_wholesale_price = self.params["path_wholesale_fuel_price"]
            targetFuel = self.params["technical_parameters"].loc[unit_name, "Primary_Fuel"]
            fuelPricePath = Utils.getPathWholesalePriceOfFuel(path_wholesale_price, targetFuel, self.BASEYEAR)
            fuelCost = Utils.loadFuelCostFile(unit_name, fuelPricePath)[self.year-self.BASEYEAR]

        totalVariableOandMCost = (variable_OM_cost+ghg_emissions_per_kWh/1000*self.current_CO2_price+ wasteCost+fuelCost)*totalGen #GBP/kWh

        NPV_total_cost = (fixed_OM_cost + TNUoS_charge*availability_factor+ totalVariableOandMCost)*(1-(1+self.discount_rate)**-lifetime)/self.discount_rate + capital_cost
        NPV_electricity_generated = (totalGen)*(1-(1+self.discount_rate)**-lifetime)/self.discount_rate
        strikePrice = NPV_total_cost/NPV_electricity_generated #GBP/kWh
        return strikePrice

    def get_busbar(self, unit_name, priority_busbars): #get the busbar where to install new capacity 
       
        busbarConstraints = self.params["busbar_constraints"]
        if unit_name not in busbarConstraints.columns:
            eligible_busbars = priority_busbars
        else:
            eligible_busbars = list(busbarConstraints[busbarConstraints[unit_name] > 0].index)
            eligible_busbars = [b for b in priority_busbars if b in eligible_busbars]
        busbar = random.choice(eligible_busbars[:3]) # choose a busbar in the top 3 eligible busbars

        return busbar

    # method to get bid for CFD auction
    def getCFDAuctionBid(self, timeHorizon, sorted_TNUoS_charges):
        priority_busbars = sorted_TNUoS_charges.columns
        dfStrikePrices = pd.DataFrame(index=self.list_technology_portfolio, columns=["strike_price_GBP/kWh", "busbar", "capacity_kW", "start_Year", "end_year", "generation_company"]) #store the strike prices of the technologies 
        dfStrikePrices.fillna(0, inplace=True)

        # Calculating the bid for each technology
        for unit_name in self.list_technology_portfolio:
            market_readiness = int(self.params["technical_parameters"].loc[unit_name, "Expected_Market_Ready_Time"]) # when is the technology market ready
            
            if int(self.params["technical_parameters"].loc[unit_name, "CfD_eligible"]): #the technology is CfD eligible
                if market_readiness<=self.year: #the technology is ready for market
                    #Select a busbar where the technology can be built

                    busbar = self.get_busbar(unit_name, priority_busbars)
                    TNUoS_charge = sorted_TNUoS_charges.loc["TNUoS_charges_GBP/kW", busbar]
                    construction_time = int(self.params["technical_parameters"].loc[unit_name, "Construction_Time_Years"]) # years
                    lifetime = int(self.params["technical_parameters"].loc[unit_name, "Lifetime_Years"]) # years
                    start_year = construction_time + self.year
                    capacityBid = int(self.params["technical_parameters"].loc[unit_name, "Typical_Capacity_kW"]) # years #capacity to be installed of the technology
                    if capacityBid > 0:
                        totalCapacityInstalled = self.gen_cap_per_type_per_bus[unit_name+'_Capacity_kW'].sum() # capacity installed of this technology in the company
                        if totalCapacityInstalled > 0:
                            hourlyGen = self.hourly_gen_per_type[unit_name].copy() #estimate hourly generation of this technology and this capacity
                            
                            hourlyGen = hourlyGen/totalCapacityInstalled*capacityBid #scale the hourly gen
                            totalGen = np.sum(hourlyGen)
                        else:
                            capacity_factor = float(self.params["technical_parameters"].loc[unit_name, "Capacity_Factor"])
                            totalGen = capacity_factor * capacityBid

                        if construction_time<=timeHorizon: # The construction time is equal or below the construction time required by the CfD auction
                            strikePrice = self.calculateStrikePrice(unit_name, capacityBid, TNUoS_charge, totalGen)
                            dfStrikePrices.loc[unit_name, "strike_price_GBP/kWh"] = strikePrice
                            dfStrikePrices.loc[unit_name, "busbar"] = busbar
                            dfStrikePrices.loc[unit_name, "capacity_kW"] = capacityBid
                            dfStrikePrices.loc[unit_name, "start_year"] = start_year
                            dfStrikePrices.loc[unit_name, "end_year"] = start_year + lifetime
                            dfStrikePrices.loc[unit_name, "generation_company"] = self.name
        
        return dfStrikePrices

    # method to get cap auction bid
    def getCapAuctionBid(self, timeHorizon, sorted_TNUoS_charges):
        priority_busbars = sorted_TNUoS_charges.columns
        dfCapacityAuctionBids = pd.DataFrame(columns=["bid_price_GBP/kW", "busbar", "capacity_kW", "derated_capacity_kW", "start_year", "end_year", "generation_company"])
        for unit in self.traditional_gen+self.energy_stores:
            unit_name = unit.name
            start_year = unit.construction_time + self.year
            lifetime = int(self.params["technical_parameters"].loc[unit_name, "Lifetime_Years"]) # years
            end_year = start_year + lifetime
            #  can technology be built in time horizon, e.g. 4 years and is it already in the list of bids (only one unit of each tech can be submitted by each eC)
            if unit.construction_time <= timeHorizon and (not unit_name in dfCapacityAuctionBids.index):
                #Select a busbar where the technology can be built (not based on headroom at the moment)
                busbar = self.get_busbar(unit_name, priority_busbars)
                capacityBid = int(self.params["technical_parameters"].loc[unit_name , "Typical_Capacity_kW"]) #capacity to be installed of the technology
                deRCap = capacityBid*unit.availability_factor
                if deRCap > 0:
                    if(unit.NPV > 0): # no need to go through the capacity market
                        bidPrice = 0
                    else:
                        lossPerKW = (-unit.NPV / unit.capacity)/lifetime
                        bidPrice = lossPerKW
                        dfCapacityAuctionBids.loc[unit_name, :] = [bidPrice, busbar, capacityBid, deRCap, start_year, end_year, self.name]
                else:
                    print(capacityBid, unit.availability_factor)

        return dfCapacityAuctionBids
    

    # method to get (derated) capacity in a specific year in the future, this is used for the capacity market auction
    #construction queue indices : tGenName #0,  tCapacityKW #1, tStartYear #2, tcapSub #3, cfdBool #4, capMarketBool #5, busbar#6
    def getCapYear(self, capYear, deratedBool):
        runCap = 0.0
        for gen in self.traditional_gen+self.renewable_gen+self.energy_stores:
            if gen.end_year > capYear and gen.start_year <= capYear:
                if deratedBool:
                    runCap = runCap + gen.capacity*gen.availability_factor
                else:
                    runCap = runCap + gen.capacity

        to_be_built = self.construction_queue.loc[self.construction_queue["start_year"]<=capYear, :]
        for i, row in to_be_built.iterrows():
            unit_name = row["name"]
            capacity = row["capacity_kW"]
            if deratedBool:
                tempAvailabilityF = float(self.params["technical_parameters"].loc[unit_name, 'Availability_Factor'])
                runCap = runCap + capacity * tempAvailabilityF
            else:
                runCap = runCap + capacity
            
        return  runCap

    # method to get capacity by generation type, e.g. all solar plants, etc.
    def calculateCapacityByType(self, list_gen_tech, list_storage_tech, listBusBars):
        temp_cols = [x+'_Derated_Capacity_kW' for x in list_gen_tech] + [x+'_Capacity_kW' for x in list_gen_tech]
        gen_cap_per_type_per_bus = pd.DataFrame(index=listBusBars, columns=temp_cols)
        gen_cap_per_type_per_bus.index.name = "Busbars"
        gen_cap_per_type_per_bus.fillna(0, inplace=True)

        temp_cols = [x+'_Capacity_kWh' for x in list_storage_tech]
        storage_cap_per_type_per_bus = pd.DataFrame(index=listBusBars, columns=temp_cols)
        storage_cap_per_type_per_bus.index.name = "Busbars"
        storage_cap_per_type_per_bus.fillna(0, inplace=True)
        storage_cap_per_type_per_bus

        for gen in self.traditional_gen + self.renewable_gen:
            name = gen.name
            capacity = gen.capacity
            bus = gen.busbar

            curDeRCap = capacity*gen.availability_factor
            curCap = capacity
            gen_cap_per_type_per_bus.loc[bus, name+'_Derated_Capacity_kW'] += curDeRCap
            gen_cap_per_type_per_bus.loc[bus, name+'_Capacity_kW'] += curCap

        for st in self.energy_stores:
            capacity = st.capacity
            bus = st.busbar
            name = st.name
            curDeRCap = st.charge_rate*st.availability_factor
            curCap = st.charge_rate
            gen_cap_per_type_per_bus.loc[bus, name+'_Capacity_kW'] += curCap #kW
            gen_cap_per_type_per_bus.loc[bus, name+'_Derated_Capacity_kW'] += curDeRCap #kW
            storage_cap_per_type_per_bus.loc[bus, name+'_Capacity_kWh'] += capacity # kWh

        self.storage_cap_per_type_per_bus = storage_cap_per_type_per_bus
        self.gen_cap_per_type_per_bus = gen_cap_per_type_per_bus
        return True

    def add_unit(self, unit_name, capacity, start_year, end_year, capacity_market_sub, CfD_price, busbar):
        renewable_flag = int(self.params["technical_parameters"].loc[unit_name, "Renewable_Flag"])
        storage_flag = int(self.params["technical_parameters"].loc[unit_name, "Storage_Flag"])

        if start_year > self.year: # not built yet
            print('Add to construction queue')
            self.addToConstructionQueue(unit_name, capacity, start_year, capacity_market_sub, CfD_price, busbar)
        elif end_year < self.year:
            print('Plant already decommissioned, not adding to capacity!')

        if(capacity_market_sub > 0 and CfD_price > 0):
            raise ValueError('****** Problem, both capacity market bool and cfd bool are true......')
        else:
            if storage_flag:
                battery_duration = float(self.params["technical_parameters"].loc[unit_name, "Storage_duration_hour"])
                capkWh = capacity*battery_duration # kWh
                charge_rate = capacity # kW
                discharge_rate = capacity # kW
                
                unit = energyStorage(unit_name, capkWh, charge_rate, discharge_rate, self.year, busbar, self.BASEYEAR)
                unit.degradation_rate = float(self.params["technical_parameters"].loc[unit_name, "Degradation_rate_perc"])
                self.energy_stores.append(unit)
            else:
                if renewable_flag:
                    unit = renewableGenerator(unit_name, capacity, busbar, self.BASEYEAR) # offshore
                    path_profiles = r'D:\OneDrive - Cardiff University\04 - Projects\18 - ABM\01 - Code\ABM code - Jan 2022 saved\Code_WH'
                    gen_profile_name = self.params["technical_parameters"].loc[unit_name, "Profile"]
                    unit.loadScaleGenProfile(path_profiles+os.path.sep+gen_profile_name)

                    self.renewable_gen.append(unit)
                else:
                    unit = traditionalGenerator(unit_name, capacity, busbar, self.BASEYEAR)
                    unit.efficiency = float(self.params["technical_parameters"].loc[unit_name, "Efficiency"]) 
                    # print("Add wholesale prices for primary fuel")
                    path_wholesale_price = self.params["path_wholesale_fuel_price"]
                    targetFuel = self.params["technical_parameters"].loc[unit_name, "Primary_Fuel"]
                    fuelPricePath = Utils.getPathWholesalePriceOfFuel(path_wholesale_price, targetFuel, self.BASEYEAR)
                    unit.loadFuelCost(fuelPricePath)
                    self.traditional_gen.append(unit)
                        
            economic_param_df = self.params["economic_parameters"]
            unit.start_year = start_year
            unit.end_year = end_year
            unit.CfD_price = CfD_price
            unit.capacity_market_sub = capacity_market_sub
            unit.capacity_factor = float(self.params["technical_parameters"].loc[unit_name, "Capacity_Factor"])
            unit.capital_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="CAPEX"), self.year].values[0]/1000
            unit.fixed_OM_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="OPEX"), self.year].values[0]/1000
            unit.variable_OM_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="Variable Other Work Costs"), self.year].values[0]/1000
            unit.construction_time = int(self.params["technical_parameters"].loc[unit_name, "Construction_Time_Years"]) # years
            unit.availability_factor = float(self.params["technical_parameters"].loc[unit_name, "Availability_Factor"]) 
            unit.ghg_emissions_per_kWh = float(self.params["technical_parameters"].loc[unit_name, "GHG_Emissions_kgCO2/kWh"]) # kgCO2/kWh
            unit.current_CO2_price = self.current_CO2_price
            unit.discount_rate = self.discount_rate

            # add the technology name to the list of plants that can be built by this company
            if unit_name not in self.list_technology_portfolio:
                self.list_technology_portfolio.append(unit_name)

            return True

    # # add a new battery
    # def addBattery(self, name, batteryPower, capacity_market_sub, CfD_price, busbar):

    #     return battery

    # # method to add new generation plants to the generation company
    # def addGeneration(self, unit_name, capacityKW, lifetime, start_year, end_year, age, capacity_market_sub, CfD_price, busbar):
    #     renewableFlag = int(self.params["technical_parameters"].loc[unit_name, "Renewable_Flag"])
    #     # print("Name: {0}, RenewableFlag: {1}, CapKW: {2}, startY: {3}, endY: {4}".format(unit_name, str(renewableFlag), str(capacityKW), str(start_year), str(end_year)))
    #     if(capacity_market_sub > 0 and CfD_price > 0):
    #         raise ValueError('****** Problem, both capacity market bool and cfd bool are true......')
    #     if start_year > self.year: # not built yet
    #         print('Add to construction queue')
    #         self.addToConstructionQueue(unit_name, capacityKW, start_year, capacity_market_sub, CfD_price, busbar)
    #     elif end_year < self.year:
    #         print('Plant already decommissioned, not adding to capacity!')

    #     else:
    #         if unit_name in self.params["gen_tech_list"]: #check if the unit_name is recognised
    #             if renewableFlag:
    #                 unit = renewable_generator(unit_name, capacityKW, lifetime, CfD_price, busbar, self.BASEYEAR) # offshore
    #                 self.renewable_gen.append(unit)
    #             else:
    #                 unit = traditionalGenerator(unit_name, capacityKW, lifetime, busbar, self.BASEYEAR)
    #                 self.traditional_gen.append(unit)
                    
    #         economic_param_df = self.params["economic_parameters"]
    #         unit.start_year = start_year
    #         unit.end_year = end_year
    #         unit.age = age
    #         unit.CfD_price = CfD_price
    #         unit.capacity_market_sub = capacity_market_sub
             
    #         unit.capital_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="CAPEX"), self.year].values[0]/1000
    #         unit.fixed_OM_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="OPEX"), self.year].values[0]/1000
    #         unit.variable_OM_cost = economic_param_df.loc[(economic_param_df["Key"]==unit_name) & (economic_param_df["Cost Type"]=="Variable Other Work Costs"), self.year].values[0]/1000
    #         unit.preDevTime = int(self.params["technical_parameters"].loc[unit_name, "PrevDevTime_Years"]) # years (not used)
    #         unit.construction_time = int(self.params["technical_parameters"].loc[unit_name, "Construction_Time_Years"]) # years
    #         unit.totConstructionTime = unit.preDevTime + unit.construction_time# years (not used)
    #         unit.capacity_factor = float(self.params["technical_parameters"].loc[unit_name, "Capacity_Factor"]) 
    #         unit.availability_factor = float(self.params["technical_parameters"].loc[unit_name, "Availability_Factor"]) 
    #         unit.ghg_emissions_per_kWh = float(self.params["technical_parameters"].loc[unit_name, "GHG_Emissions_kgCO2/kWh"]) # kgCO2/kWh
    #         unit.current_CO2_price = self.current_CO2_price
    #         unit.discount_rate = self.discount_rate

    #         if renewableFlag:
    #             # print("Add Profile")
    #             path_profiles = r'D:\OneDrive - Cardiff University\04 - Projects\18 - ABM\01 - Code\ABM code - Jan 2022 saved\Code_WH'
    #             gen_profile_name = self.params["technical_parameters"].loc[unit_name, "Profile"]
    #             unit.loadScaleGenProfile(path_profiles+os.path.sep+gen_profile_name)
    #         else:
    #             unit.efficiency = float(self.params["technical_parameters"].loc[unit_name, "Efficiency"]) 
    #             # print("Add wholesale prices for primary fuel")
    #             path_wholesale_price = self.params["path_wholesale_fuel_price"]
    #             targetFuel = self.params["technical_parameters"].loc[unit_name, "Primary_Fuel"]
    #             fuelPricePath = Utils.getPathWholesalePriceOfFuel(path_wholesale_price, targetFuel, self.BASEYEAR)
    #             unit.loadFuelCost(fuelPricePath)

    #         # add the technology name to the list of plants that can be built by this company
    #         if unit_name not in self.list_technology_portfolio:
    #             self.list_technology_portfolio.append(unit_name)
    #     return True
    




































        
        
