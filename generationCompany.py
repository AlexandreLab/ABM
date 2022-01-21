import random
from collections import namedtuple
import numpy as np
import math
import statistics
import Utils
from renewableGenerator import renewableGenerator
from traditionalGenerator import traditionalGenerator
from energyStorage import energyStorage
from random import choice
from scipy import (dot, eye, randn, asarray, array, trace, log, exp, sqrt, mean, sum, argsort, square, arange)
import pandas as pd
import os

class generationCompany():
    
    
    def __init__(self,timeSteps, companyType, companyID, params, BASEYEAR):

        self.initialise(timeSteps, companyType, companyID, params, BASEYEAR)

    def __init__(self,timeSteps, params, BASEYEAR):

        self.initialise(timeSteps, 1, 1, params, BASEYEAR)


    def initialise(self,timeSteps, companyType, companyID, params, BASEYEAR):

        self.params = params

        self.timeSteps = timeSteps
        self.companyID = companyID #useless, to be removed
        self.companyType = companyType

        self.heatGenerated = list()
        self.genCapacity = 1E11
        self.hourlyCost = np.zeros(timeSteps)
        self.hourlyEmissions = np.zeros(timeSteps)
        self.yearlyCost=0.0
        self.yearlyEmissions=0.0
        self.totalEmissionsYear = 0.0 # total emissions of all technologies for cur year
        self.name = 'Generation Company '+ str(self.companyID)+': '
        self.elecLoss = 0.0 #0.1
        self.CFDPrice = 0.0 #0.12
        self.discountR = 0.1 # 10%

        self.traditionalGen = list()
        self.renewableGen = list() # list of renewableGenerator objects
        self.listTechnologyNames = list() # list of technology names owned by this company
        self.hourlyGenPerType = dict() # store the hourly generation profile for each technology type

        self.curYearBatteryBuild = 0.0

        self.batteryDuration = 3 #7 #3 # hours

        self.constructionQueue = list()
        self.yearlyCapPerBus = list()
        self.yearlyCapPerTech = list()
        self.yearlyDerateCapPerTech = list()
        self.yearlyProfitPerTech = list()
        self.yearlyRevenuePerTech = list()
        self.yearlyCostPerTech = list()
        self.yearlyEmissionsPerTech = list()
        self.yearlyGenerationPerTech = list()
        self.yearlyBatterySubsNeeded = list()

        self.yearlyStorageCapKW = list()
        self.yearlyStorageGenKWh = list()
        self.yearlyStorageCost = list()
        self.yearlyStorageCapSubs = list()
        self.techNames = list()

        self.capacityPerType = pd.DataFrame() #capacity per type for each year
        self.capacityPerTypePerBus = pd.DataFrame() #capacity per type and by bus

        # Allocate technologies and its capacity for each bus
        self.windoncap = 1000000
        self.windoffcap = 500000
        self.pvcap = 2000000
        self.hydrocap = 500000
        self.biomasscap = 500000
        self.coalcap = 5000000
        self.CCGTcap = 5000000
        self.nuclearcap = 1500000
        self.OCGTcap = 200000
        self.BECCScap = 10
        self.Hydrogencap = 10

        self.yearlyTotalCapacity = list()
        self.yearlyDeRatedCapacity = list()
        self.getTotalCapacity()

        self.yearlyPeakDemand = list()
        self.yearlyCapacityMargin = list()
        self.yearlyDeRatedCapacityMargin = list()

        self.BASEYEAR = BASEYEAR
        self.year = BASEYEAR
        self.years = list()

        self.energyStores = list()
        # battery = energyStorage(10000,1000,500,self.year, random.randint(1,30)) # need to give values
        # self.energyStores.append(battery)
        carbonFilePath = 'CarbonPrice/carbonPrice'+str(self.BASEYEAR)+'_2050.txt'
        self.yearlyCarbonCost = Utils.loadTextFile(carbonFilePath)
        self.carbonCost = self.yearlyCarbonCost[0]

    def calcRevenue(self, wholesaleProf): # method to recalculate profit for all plants
        for gen in self.traditionalGen+self.renewableGen+self.energyStores:
            gen.wholesaleEPrice = wholesaleProf
            gen.calculateProfit()
        return True

    def calcEmissions(self): # method to recalculate profit for all plants
        totalGenCoEmissions = 0
        for gen in self.traditionalGen+self.renewableGen+self.energyStores:
            totalGenCoEmissions += gen.yearlyEmissions
            gen.calculateProfit()
        return totalGenCoEmissions

    # The batteries are controlled at the level of the generation company
    # method to charge/ discharge battery and return net demand - battery
    def chargeDischargeBatteryTime(self, netDemand):
        # if netDemand>dailyAverage => battery discharge
        # else: battery charge
        arr_discharging24Hr = np.array([arr_day-np.mean(arr_day) for arr_day in np.split(netDemand, 8760/24)])
        arr_discharging24Hr = arr_discharging24Hr.flatten()
        arr_charging24Hr = -arr_discharging24Hr.copy()
        arr_discharging24Hr = arr_discharging24Hr.clip(min=0)
        arr_charging24Hr = arr_charging24Hr.clip(min=0)
        arr_charging24Hr = np.array([arr_dayCharging/np.sum(arr_dayCharging) for arr_dayCharging in np.split(arr_charging24Hr, 8760/24)])
        arr_discharging24Hr = np.array([arr_dayDischarging/np.sum(arr_dayDischarging) for arr_dayDischarging in np.split(arr_discharging24Hr, 8760/24)])

        arr_charging24Hr = arr_charging24Hr.flatten()
        arr_discharging24Hr = arr_discharging24Hr.flatten()
        tempNetDemand = netDemand.copy()
        pd.DataFrame([arr_charging24Hr, arr_discharging24Hr, tempNetDemand]).to_csv("battery.csv")
        for eStore in self.energyStores:
            tempNetDemand = eStore.chargingDischargingBattery(arr_charging24Hr, arr_discharging24Hr, tempNetDemand)
            eStore.updateProfit()

        return tempNetDemand

    # reset values at the end of a year
    def resetYearlyValues(self):
        for i in range(len(self.energyStores)):
            self.energyStores[i].resetYearValueRecord()

        for i in range(len(self.traditionalGen)):
            self.traditionalGen[i].resetYearValueRecord()

        for i in range(len(self.renewableGen)):
            self.renewableGen[i].resetYearValueRecord()
            
    # get generation from specific technology type ,e.g. Wind, solar, etc.
    def getRenewableGenerationByType(self, genName):
        arr_curGen = np.zeros(self.timeSteps)
        for rgen in self.renewableGen:
            # print(genTypeID, tgen.genTypeID)
            if rgen.name==genName:
                curGen = rgen.energyGenerated
                arr_curGen = np.add(arr_curGen, curGen)
        self.hourlyGenPerType[genName] = arr_curGen
        return arr_curGen

    # get generation from specific technology type ,e.g. CCGT
    def getTraditionalGenerationByType(self, genName, curNetD):
        tempNetD = curNetD.copy()
        arr_curGen = np.zeros(self.timeSteps)
        arr_currExcessGen = np.zeros(self.timeSteps)
        for tgen in self.traditionalGen:
            # print(genTypeID, tgen.genTypeID)
            if(tgen.name==genName):
                curGen,newNetD, curExcessGen = tgen.getGeneration(tempNetD)
                # print(np.sum(curGen))
                tempNetD = newNetD
                arr_curGen = np.add(arr_curGen, curGen)
                arr_currExcessGen = np.add(arr_currExcessGen, curExcessGen)
        self.hourlyGenPerType[genName] = arr_curGen
        return arr_curGen, arr_currExcessGen, tempNetD

    # get capacity of all battery storage in kW
    def getBatteryPowerKW(self):
        totalPowerKW = 0.0
        for eStore in self.energyStores:
            totalPowerKW = totalPowerKW + eStore.dischargeRate
        return totalPowerKW

    # make decision to invest in new generation plants 
    def updateYear(self, OneYearHeadroom, newCO2Price, ):
        self.removeOldCapacity()
        self.removeUnprofitableCapacity()
        self.year = self.year + 1
        for gen in self.traditionalGen + self.renewableGen:
            gen.updateYear(newCO2Price)  
        # add any new plants that are in the construction queue and are meant to come online
        self.checkConstructionQueue(OneYearHeadroom)
        return True
        
    # method to add plants to construction queue so that they come online after build time has completed
    def addToConstructionQueue(self, tGenName, tCapacityKW, tStartYear, tcapSub, cfdBool, capMarketBool, BusNum):
        print("Adding {0} to the construction queue of the company {1}".format(tGenName, self.name))
        queuePlant = list()
        queuePlant.append(tGenName) #0
        queuePlant.append(tCapacityKW)#1
        queuePlant.append(tStartYear)#2
        queuePlant.append(tcapSub)#3
        queuePlant.append(cfdBool)#4
        queuePlant.append(capMarketBool)#5
        queuePlant.append(BusNum)#6
        self.constructionQueue.append(queuePlant)

    # check plants that are in construction queue to see if ready to come online
    def checkConstructionQueue(self,OneYearHeadroom):
        newConstructionQueue = []
        for genRow in self.constructionQueue:
            startYear = genRow[2]
            if startYear == self.year:  # start year is now
                genName = genRow[0]
                capacityKW = genRow[1]
                capitalSub = genRow[3]
                cfdBool = genRow[4]
                capMarketBool = genRow[5]
                BusNum = genRow[6]
                renewableFlag = int(self.params["technical_parameters"].loc[genName, 'Renewable_Flag'])
                lifetime = lifetime = int(self.params["technical_parameters"].loc[genName, "Lifetime_Years"]) # years
                endYear = startYear + lifetime
                age = 0
                self.addGeneration(genName, renewableFlag, capacityKW, lifetime, startYear, endYear, age, capitalSub, cfdBool, capMarketBool, BusNum, OneYearHeadroom[BusNum-1])
            else:
                newConstructionQueue.append(genRow)
        self.constructionQueue = newConstructionQueue

    # method to remove old capacity whos age>lifetime
    def removeOldCapacity(self):
        for gen in self.traditionalGen + self.renewableGen:
            if gen.endYear <= self.year:
                print('Removing Old Capacity')
                print('type ',gen.name)
                print('capacity ',gen.genCapacity)
                print('Cur Year: %s,   End Year: %s'%(str(self.year), str(gen.endYear)))
                if gen in self.traditionalGen:
                    self.traditionalGen.remove(gen)
                else:
                    self.renewableGen.remove(gen)
        return True
        
    # method to remove unprofitable generation plants
    def removeUnprofitableCapacity(self):
        # remove at most 1 plant (renewable or non renewable) that is not profitable
        removed = False
        yearsWait = 8 # number of years allowed to make a loss for before removed
        shuffled_list = [x for x in range(len(self.traditionalGen+self.renewableGen))]
        random.shuffle(shuffled_list)

        for idx in shuffled_list:
            count=0
            if not removed:
                gen = (self.traditionalGen+self.renewableGen)[idx]
                for yProfit in reversed (gen.yearlyProfitList): # loop through yearly profits from most recent
                    if yProfit < 0:
                        count +=1
                    # if not profitable for x years and no plant has been removed yet
                    if count== yearsWait : 
                        print('Removing Unprofitable Capacity')
                        print('Profit ',gen.yearlyProfitList)
                        print('type ',gen.name)
                        print('capacity ',gen.genCapacity)
                        if gen in self.traditionalGen:
                            self.traditionalGen.remove(gen)
                        else:
                            self.renewableGen.remove(gen)
                        removed = True
                        break
        return True

    def calculateStrikePrice(self, genName, capacity, totalGen):
        # load parameters to calculate the strike price for this technology
        economic_param_df = self.params["economic_parameters"]
        renewableFlag = int(self.params["technical_parameters"].loc[genName, 'Renewable_Flag'])
        lifetime = int(self.params["technical_parameters"].loc[genName, "Lifetime_Years"]) # years
        capitalCost = economic_param_df.loc[(economic_param_df["Key"]==genName) & (economic_param_df["Cost Type"]=="CAPEX"), self.year].values[0]/1000*capacity
        fixedOandMCost = economic_param_df.loc[(economic_param_df["Key"]==genName) & (economic_param_df["Cost Type"]=="OPEX"), self.year].values[0]/1000*capacity
        variableOandMCost = economic_param_df.loc[(economic_param_df["Key"]==genName) & (economic_param_df["Cost Type"]=="Variable Other Work Costs"), self.year].values[0]/1000
        capitalCostAnnualised = (capitalCost*self.discountR)/(1-(1+self.discountR)**-lifetime)  # EAC GBP/year
        wasteCost = 0 #GBP/kWh
        capacityFactor = float(self.params["technical_parameters"].loc[genName, "Capacity_Factor"])
        opEmissionsPkW = float(self.params["technical_parameters"].loc[genName, "GHG_Emissions_kgCO2/kWh"]) # kgCO2/kWh

        fuelCost = 0
        if not renewableFlag:
            path_wholesale_price = self.params["path_wholesale_fuel_price"]
            targetFuel = self.params["technical_parameters"].loc[genName, "Primary_Fuel"]
            fuelPricePath = Utils.getPathWholesalePriceOfFuel(path_wholesale_price, targetFuel, self.BASEYEAR)
            fuelCost = Utils.loadFuelCostFile(genName, fuelPricePath)[self.year-self.BASEYEAR]

        totalVariableOandMCost = (variableOandMCost+opEmissionsPkW/1000*self.carbonCost+ wasteCost+fuelCost)*totalGen #GBP/kWh
        strikePrice = (capitalCostAnnualised + fixedOandMCost + totalVariableOandMCost)/totalGen #GBP/kWh
        return strikePrice


    # method to get bid for CFD auction
    def getCFDAuctionBid(self, timeHorizon, busheadroom):

        dfStrikePrices = pd.DataFrame(index= self.listTechnologyNames, columns=["Strike_Price_GBP/kWh","Busbar", "Capacity_kW",  "Start_Year", "Generation_Company"]) #store the strike prices of the technologies 
        dfStrikePrices.fillna(0, inplace=True)
        # Calculating the bid for each technology 
        for genName in self.listTechnologyNames:
            if int(self.params["technical_parameters"].loc[genName, "CfD_eligible"]): #the technology is CfD eligible
                #Select a busbar where the technology can be built (not based on headroom at the moment)
                busbarConstraints = self.params["busbar_constraints"]
                busbar = random.choice(list(busbarConstraints[busbarConstraints[genName]>0].index))
                constructionTime = int(self.params["technical_parameters"].loc[genName, "Construction_Time_Years"]) # years
                startYear = constructionTime + self.year
                capacityBid = int(self.params["technical_parameters"].loc[genName, "Typical_Capacity_kW"]) # years #capacity to be installed of the technology
                if capacityBid>0:
                    totalCapacityInstalled = self.capacityPerTypePerBus[genName+'_Capacity_kW'].sum() # capacity installed of this technology in the company
                    hourlyGen = self.hourlyGenPerType[genName].copy() #estimate hourly generation of this technology and this capacity
                    capacityFactor = np.sum(hourlyGen)/(self.timeSteps*totalCapacityInstalled)
                    hourlyGen = hourlyGen/totalCapacityInstalled*capacityBid #scale the hourly gen
                    totalGen = np.sum(hourlyGen)

                    if constructionTime<=timeHorizon: # The construction time is equal or below the construction time required by the CfD auction
                        strikePrice = self.calculateStrikePrice(genName, capacityBid, totalGen)
                        dfStrikePrices.loc[genName, "Strike_Price_GBP/kWh"] = strikePrice
                        dfStrikePrices.loc[genName, "Busbar"] = busbar
                        dfStrikePrices.loc[genName, "Capacity_kW"] = capacityBid
                        dfStrikePrices.loc[genName, "Start_Year"] = startYear
                        dfStrikePrices.loc[genName, "Generation_Company"] = self.name
        
        return dfStrikePrices



    # method to get cap auction bid
    def getCapAuctionBid(self, timeHorizon, busheadroom):
        dfCapacityAuctionBids = pd.DataFrame(columns=["Bid_Price_GBP/kW", "Busbar","Capacity_kW", "DeRated_Capacity_kW", "Start_Year", "Battery_Flag", "Generation_Company"])
        for gen in self.traditionalGen:
            genName = gen.name
            startYear = gen.constructionTime + self.year
            #  can technology be built in time horizon, e.g. 4 years
            if gen.constructionTime <= timeHorizon and (not genName in dfCapacityAuctionBids.index):
                #Select a busbar where the technology can be built (not based on headroom at the moment)
                busbarConstraints = self.params["busbar_constraints"]
                busbar = random.choice(list(busbarConstraints[busbarConstraints[genName]>0].index))
                capacityBid = int(self.params["technical_parameters"].loc[genName, "Typical_Capacity_kW"]) #capacity to be installed of the technology
                deRCap = capacityBid*gen.availabilityFactor
                if deRCap>0:
                    if(gen.NPV>0):
                        bidPrice = 0
                    else:
                        lossPerKW = -gen.NPV / gen.genCapacity
                        bidPrice = lossPerKW
                    dfCapacityAuctionBids.loc[genName, :] = [bidPrice, busbar, capacityBid, deRCap, startYear, False, self.name]
                else:
                    print(capacityBid,gen.availabilityFactor)

        return dfCapacityAuctionBids
    

    # method to get (derated) capacity in a specific year in the future, this is used for the capacity market auction
    #construction queue indices : tGenName #0,  tCapacityKW #1, tStartYear #2, tcapSub #3, cfdBool #4, capMarketBool #5, BusNum#6
    def getCapYear(self, capYear, deratedBool):
        runCap = 0.0
        for gen in self.traditionalGen+self.renewableGen:
            if gen.endYear>capYear and gen.startYear<=capYear:
                if deratedBool:
                    runCap = runCap + gen.genCapacity*gen.availabilityFactor
                else:
                    runCap = runCap + gen.genCapacity

        for i in range(len(self.constructionQueue)):
            constructSYear = self.constructionQueue[i][2]
            if constructSYear<=capYear:
                if deratedBool:
                    genName = self.constructionQueue[i][0]
                    tempAvailabilityF = float(self.params["technical_parameters"].loc[genName, 'Availability_Factor']) 
                    runCap = runCap + (self.constructionQueue[i][1] * tempAvailabilityF)
                else:
                    runCap = runCap + self.constructionQueue[i][1]

        return  runCap

        
    # method to return capacity margin
    def getCapacityMargin(self, peakDemand):
        self.getTotalCapacity()

        self.capacityMargin = (self.totalCapacity - peakDemand)/peakDemand
        self.deRatedCapacityMargin = (self.deRatedCapacity - peakDemand)/peakDemand
        
        self.yearlyPeakDemand.append(peakDemand)
        self.yearlyCapacityMargin.append(self.capacityMargin)
        self.yearlyDeRatedCapacityMargin.append(self.deRatedCapacityMargin)
        return True

    # get total capacity
    def getTotalCapacity(self):
        totalCapacity = 0.0
        deRatedCapacity = 0.0
        for gen in self.traditionalGen+self.renewableGen:
            totalCapacity = totalCapacity + gen.genCapacity
            deRatedCapacity = deRatedCapacity + gen.genCapacity*gen.availabilityFactor

        self.totalCapacity = totalCapacity
        self.deRatedCapacity = deRatedCapacity
        return True

    # method to get capacity by generation type, e.g. all solar plants, etc.
    def calculateCapacityByType(self, listTechnologies, listBusBars):
        temp_cols = [x+'_Derated_Capacity_kW' for x in listTechnologies] + [x+'_Capacity_kW' for x in listTechnologies]
        capacityPerTypePerBus = pd.DataFrame(index=listBusBars, columns=temp_cols)
        capacityPerTypePerBus.index.name = "Busbars"
        capacityPerTypePerBus.fillna(0, inplace=True)

        for gen in self.traditionalGen + self.renewableGen:
            name = gen.name
            capacity = gen.genCapacity
            bus = gen.busbar
            availabilityFactor = gen.availabilityFactor
            curDeRCap = capacity*availabilityFactor
            curCap = capacity
            capacityPerTypePerBus.loc[bus, name+'_Derated_Capacity_kW'] += curDeRCap 
            capacityPerTypePerBus.loc[bus, name+'_Capacity_kW'] += curCap 

        for store in self.energyStores:
            capacity = store.maxCapacity
            bus = store.busbar
            name = 'Battery'
            capacityPerTypePerBus.loc[bus, name+'_Derated_Capacity_kW'] += capacity 
            capacityPerTypePerBus.loc[bus, name+'_Capacity_kW'] += capacity

        self.capacityPerTypePerBus = capacityPerTypePerBus
        return True
                
    # update CO2 price
    def setNewPolicyValues(self, newCO2Price,newCFDPrice):
        self.carbonCost = newCO2Price
        self.CFDPrice = newCFDPrice # this can be ignored**



    # add a new battery
    def addBattery(self, batteryPower, busbar): 
        capkWh = batteryPower*self.batteryDuration # kWh
        chargeRate = batteryPower # kW
        dischargeRate = batteryPower # kW
        battery = energyStorage(capkWh,chargeRate,dischargeRate,self.year, busbar, self.BASEYEAR)
        self.energyStores.append(battery)
        return battery

    # method to add new generation plants to the generation company
    def addGeneration(self, genName, renewableFlag, capacityKW, lifetime, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom):
        print("Name: {0}, RenewableFlag: {1}, CapKW: {2}, startY: {3}, endY: {4}".format(genName, str(renewableFlag), str(capacityKW), str(startYear), str(endYear)))
        if(cfdBool and capMarketBool):
            input('****** Problem, both capacity market bool and cfd bool are true......')
        elif(cfdBool):
            cfdSub = subsidy # GBP/kWh
            capitalSub = 0.0 # GBP/ kW Cap /year
            print('**** CfD ', cfdSub)
            print("Name: {0}, RenewableFlag: {1}, CapKW: {2}, startY: {3}, endY: {4}".format(genName, str(renewableFlag), str(capacityKW), str(startYear), str(endYear)))
        elif(capMarketBool):
            cfdSub = 0.0 # GBP/kWh
            capitalSub = subsidy # GBP/ kW Cap /year
            print('**** Capactiy Market ', capitalSub)
            print("Name: {0}, RenewableFlag: {1}, CapKW: {2}, startY: {3}, endY: {4}".format(genName, str(renewableFlag), str(capacityKW), str(startYear), str(endYear)))
        else:
            capitalSub = 0.0 # GBP/ kW Cap /year
            cfdSub = 0.0 # GBP/kWh
            
        if(startYear> self.year): # not built yet
            print('Add to construction queue')
            self.addToConstructionQueue(genName, capacityKW, startYear, subsidy, cfdBool, capMarketBool, BusNum)

        elif(endYear<self.year):
            print('Plant already decommissioned, not adding to capacity!')

        else:
            list_plants = list(self.params["technical_parameters"].index)
            if genName in list_plants: #check if the genName is recognised
 
                genTypeID = int(self.params["technical_parameters"].loc[genName, "TypeID"])
                if renewableFlag:
                    newGen = renewableGenerator(genName, genTypeID,capacityKW, lifetime, cfdSub, BusNum, Headroom, self.BASEYEAR) # offshore
                    self.renewableGen.append(newGen)
                else:
                    newGen = traditionalGenerator(genName, genTypeID,capacityKW, lifetime, BusNum, Headroom, self.BASEYEAR)
                    self.traditionalGen.append(newGen)
                    
            economic_param_df = self.params["economic_parameters"]
            newGen.startYear = startYear
            newGen.endYear = endYear
            newGen.age = age
            newGen.CFDPrice = cfdSub
            newGen.capitalSub = capitalSub
            newGen.capitalCost = economic_param_df.loc[(economic_param_df["Key"]==genName) & (economic_param_df["Cost Type"]=="CAPEX"), self.year].values[0]/1000
            newGen.fixedOandMCost = economic_param_df.loc[(economic_param_df["Key"]==genName) & (economic_param_df["Cost Type"]=="OPEX"), self.year].values[0]/1000
            newGen.variableOandMCost = economic_param_df.loc[(economic_param_df["Key"]==genName) & (economic_param_df["Cost Type"]=="Variable Other Work Costs"), self.year].values[0]/1000
            newGen.preDevTime = int(self.params["technical_parameters"].loc[genName, "PrevDevTime_Years"]) # years (not used)
            newGen.constructionTime = int(self.params["technical_parameters"].loc[genName, "Construction_Time_Years"]) # years
            newGen.totConstructionTime = newGen.preDevTime + newGen.constructionTime# years (not used)
            newGen.capacityFactor = float(self.params["technical_parameters"].loc[genName, "Capacity_Factor"]) 
            newGen.availabilityFactor = float(self.params["technical_parameters"].loc[genName, "Availability_Factor"]) 
            newGen.opEmissionsPkW = float(self.params["technical_parameters"].loc[genName, "GHG_Emissions_kgCO2/kWh"]) # kgCO2/kWh
            newGen.carbonCost = self.carbonCost
            newGen.discountR = self.discountR
            if renewableFlag:
                print("Add Profile")
                path_profiles = r'D:\OneDrive - Cardiff University\04 - Projects\18 - ABM\01 - Code\ABM code - Jan 2022 saved\Code_WH'
                gen_profile_name = self.params["technical_parameters"].loc[genName, "Profile"]
                newGen.loadScaleGenProfile(path_profiles+os.path.sep+gen_profile_name)
            else:
                print("Add wholesale prices for primary fuel")
                path_wholesale_price = self.params["path_wholesale_fuel_price"]
                targetFuel = self.params["technical_parameters"].loc[genName, "Primary_Fuel"]
                fuelPricePath = Utils.getPathWholesalePriceOfFuel(path_wholesale_price, targetFuel, self.BASEYEAR)
                newGen.loadFuelCost(fuelPricePath)

            # add the technology name to the list of plants that can be built by this company
            if genName not in self.listTechnologyNames:
                self.listTechnologyNames.append(genName)
        return True
    




































        
        
