import random
from random import randint
from collections import namedtuple
import numpy as np
import math
from electricityGenerator import electricityGenerator
import Utils
from timeit import default_timer as timer


class renewableGenerator(electricityGenerator):
    
    
    def __init__(self,genName, genTypeID, timeSteps, capacity,lifetime, CFDPrice, numBus, headroom): # kW
        super().__init__(genName, genTypeID, capacity,lifetime, numBus, headroom)

        self.CFDPrice = CFDPrice # GBP
        self.availabilityFactor = 0.1

        solarFiTFilePath = 'WholesaleEnergyPrices/Solar_FiT_2010_2019_GBPPerkWh.txt'
        self.yearlySolarFiT = Utils.loadTextFile(solarFiTFilePath) # GBP per kWh

        # load generation profile and scale to match desired capacity
    def loadScaleGenProfile(self,FILEPATH):
        self.marginalCost = list()
        start = timer()
        self.energyGenerated = np.array(Utils.loadTextFile(FILEPATH))

        self.marginalCost = [0]*len(self.energyGenerated)

        capital = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr # GBP/hr
        fixedOM = self.fixedOandMCost * self.genCapacity /8760# GBP/hr# GBP/hr
        if(self.name == 'Solar'): # solar
            fileGenCapacity = 13000000        
        elif(self.name == 'Hydro'): # Hydro
            fileGenCapacity = 1000000
        elif(self.name == 'Wind Onshore'): # Onshore wind
            fileGenCapacity = 9500000
        elif(self.name == 'Wind Offshore'): # Offshore wind
            fileGenCapacity = 4000000

        self.energyGenerated = self.energyGenerated*1000*self.genCapacity/fileGenCapacity
        arr_fuelCost = self.energyGenerated * self.FuelCost
        arr_VariableOM = self.energyGenerated * self.variableOandMCost
        arr_hourlyCost = np.add(arr_fuelCost,arr_VariableOM)
        arr_hourlyCost = arr_hourlyCost +capital+fixedOM+self.ConnectionFee/8760
        if(self.CFDPrice>0.0001):
            arr_hourlyIncome = self.energyGenerated * self.CFDPrice
        else:
            if(self.name=='Solar'):
                y = self.year- self.BASEYEAR
                if(y<len(self.yearlySolarFiT)):
                    arr_hourlyIncome = self.energyGenerated * self.yearlySolarFiT[y]
                else:
                    arr_hourlyIncome = np.multiply(self.energyGenerated,self.wholesaleEPriceProf)  
            else:
                arr_hourlyIncome = np.multiply(self.energyGenerated,self.wholesaleEPriceProf) 
        arr_hourlyProfit = np.subtract(arr_hourlyIncome, arr_hourlyCost)

        self.hourlyCost = list(arr_hourlyCost)
        self.hourlyProfit = list(arr_hourlyProfit)
        self.hourlyIncome = list(arr_hourlyIncome)

        self.runningCost = np.sum(self.hourlyCost)
        self.yearlyProfit = np.sum(self.hourlyProfit)
        self.yearlyCost = self.runningCost
        self.yearlyIncome = np.sum(self.hourlyIncome)

        if(self.genCapacity>0.00001):
            self.estimatedROI = (self.yearlyProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
        else:
            self.estimatedROI = 0.0
                
        self.NPV = 0.0
        for yr in range(5): # for yr in range(self.year, self.endYear):
            self.NPV = self.NPV + self.yearlyProfit/((1+self.discountR)**yr)

        print("end loadScale function: {0}".format(timer()-start))
    
 
    # method to recalculate costs etc.
    def recalcEconomics(self):

        start = timer()

        self.marginalCost = [0]*len(self.energyGenerated)
        capital = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr # GBP/hr
        fixedOM = self.fixedOandMCost * self.genCapacity /8760# GBP/hr# GBP/hr
        if(self.name == 'Solar'): # solar
            fileGenCapacity = 13000000        
        elif(self.name == 'Hydro'): # Hydro
            fileGenCapacity = 1000000
        elif(self.name == 'Wind Onshore'): # Onshore wind
            fileGenCapacity = 9500000
        elif(self.name == 'Wind Offshore'): # Offshore wind
            fileGenCapacity = 4000000
        #look at using numpy functions to replace this loop
        scaled_profile = []
        for i in range(len(self.energyGenerated)):
            curGen = self.energyGenerated[i]
            curGen = curGen*1000*self.genCapacity/fileGenCapacity
            curFuelCost = self.FuelCost * curGen
            curVariableOM = self.variableOandMCost * curGen
            curHourlyCost = curFuelCost+fixedOM+curVariableOM+capital+self.ConnectionFee/8760

            if(self.CFDPrice>0.0001):
                curHourlyIncome = self.CFDPrice*curGen
            else:
                if(self.name=='Solar'):

                    y = self.year- self.BASEYEAR
                    if(y<len(self.yearlySolarFiT)):
                        curHourlyIncome = self.yearlySolarFiT[y]*curGen
                    else:
                        curHourlyIncome = self.wholesaleEPriceProf[i]*curGen
                else:
                    curHourlyIncome = self.wholesaleEPriceProf[i]*curGen

            curHourlyProfit = curHourlyIncome - curHourlyCost

            self.hourlyCost.append(curHourlyCost)
            self.hourlyProfit.append(curHourlyProfit)
            self.hourlyIncome.append(curHourlyIncome)
            scaled_profile.append(curGen)

        self.energyGenerated = scaled_profile
        self.runningCost = np.sum(self.hourlyCost)
        self.yearlyProfit = np.sum(self.hourlyProfit)
        self.yearlyCost = self.runningCost
        self.yearlyIncome = np.sum(self.hourlyIncome)

        if(self.genCapacity>0.00001):
            self.estimatedROI = (self.yearlyProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
        else:
            self.estimatedROI = 0.0
                
        self.NPV = 0.0
        for yr in range(5): # for yr in range(self.year, self.endYear):
            self.NPV = self.NPV + self.yearlyProfit/((1+self.discountR)**yr)

        print("end recalc function: {0}".format(timer()-start))
                
    # method to load generation profile (you will probably need to scale profile so use other method)
    def loadGenProfile(self,FILEPATH):
        self.energyGenerated = Utils.loadTextFile(FILEPATH)
        self.marginalCost = [0]*len(self.energyGenerated)

        capital = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr
        fixedOM = self.fixedOandMCost * self.genCapacity /8760# GBP/hr # GBP/hr
        for i in range(len(self.energyGenerated)):
            if(self.name == 'Solar'): # solar
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW
            elif(self.name == 'Hydro'): # Hydro
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW

            elif(self.name == 'Wind Onshore'): # Onshore wind
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW
            elif(self.name == 'Wind Offshore'): # Offshore wind
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            curCost = fuel + fixedOM + variableOM + capital+self.ConnectionFee

            if(curGen<1):
                marginC=0.0
            else:
                marginC = (fuel + variableOM)/curGen
            #     self.marginalCost.append(marginC)
            self.marginalCost.append(0.0)


            if(self.CFDPrice>0.0001):
                curIncome = self.CFDPrice*curGen
            else:
                if(self.name=='Solar'):
                    y = self.year- self.BASEYEAR
                    if(y<len(self.yearlySolarFiT)):
                        sellP = self.yearlySolarFiT[y]
                    else:
                        sellP = self.wholesaleEPriceProf[i]
                    curIncome = sellP*curGen
                else:
                    curIncome = self.wholesaleEPriceProf[i]*curGen
            curProfit = curIncome-curCost

            
            self.yearlyCarbonCostSum = 0.0
            self.hourlyCost.append(curCost)
            self.hourlyProfit.append(curProfit)
            self.runningCost = self.runningCost + (curCost)
            self.yearlyProfit = self.yearlyProfit + curProfit
            self.yearlyCost = self.runningCost
            self.yearlyIncome = self.yearlyIncome + curIncome
            if(self.genCapacity>0.00001):
                self.estimatedROI = (self.yearlyProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
            else:
                self.estimatedROI = 0.0
            self.NPV = 0.0
            for yr in range(5): # for yr in range(self.year, self.endYear):
                self.NPV = self.NPV +  self.yearlyProfit/((1+self.discountR)**yr)

    # method to update generation profile (only use if modifying current plant, e.g. increasing capacity)
    # otherwise just use scaled profile method
    def updateGenProfile(self, pcChange):
        self.marginalCost = list()
        capital = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr
        fixedOM = self.fixedOandMCost * self.genCapacity /8760# GBP/hr
        for i in range(len(self.energyGenerated)):
            self.energyGenerated[i] = self.energyGenerated[i] + (self.energyGenerated[i]*(pcChange/100.0))
            
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            
            curCost = fuel + fixedOM + variableOM + capital+self.ConnectionFee
            if(curGen<1):
                marginC=0.0
            else:
                marginC = (fuel + variableOM)/curGen
            #     self.marginalCost.append(marginC)
            self.marginalCost.append(0.0)
            if(self.CFDPrice>0.0001):
                curIncome = self.CFDPrice*curGen
            else:
                if(self.name=='Solar'):
                    y = self.year- self.BASEYEAR
                    if(y<len(self.yearlySolarFiT)):
                        sellP = self.yearlySolarFiT[y]
                    else:
                        sellP = self.wholesaleEPriceProf[i]
                    curIncome = sellP*curGen
                else:
                    curIncome = self.wholesaleEPriceProf[i]*curGen
            curProfit = curIncome-curCost
            self.yearlyCarbonCostSum = 0.0
            
            self.hourlyCost.append(curCost)
            self.hourlyProfit.append(curProfit)
            self.runningCost = self.runningCost + (curCost)
            self.yearlyProfit = self.yearlyProfit + curProfit
            self.yearlyCost = self.runningCost
            self.yearlyIncome = self.yearlyIncome + curIncome
            if(self.genCapacity>0.00001):
                self.estimatedROI = (self.yearlyProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
            else:
                self.estimatedROI = 0.0

            self.NPV = 0.0

            for yr in range(5): # for yr in range(self.year, self.endYear):
                self.NPV = self.NPV +  self.yearlyProfit/((1+self.discountR)**yr)

    # again can update existing generation profile, dont use unless modifying capacity of current plant
    def updateGenProfileUsingValues(self, profileChangeVals):
        self.marginalCost = list()

        capital = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr
        fixedOM = self.fixedOandMCost * self.genCapacity /8760# GBP/hr # GBP/hr

        for i in range(len(self.energyGenerated)):
            self.energyGenerated[i] = self.energyGenerated[i] + profileChangeVals[i]
            
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            
            
            curCost = fuel + fixedOM + variableOM + capital+self.ConnectionFee
            if(curGen<1):
                marginC=0.0
            else:
                marginC = (fuel + variableOM)/curGen
            #     self.marginalCost.append(marginC)
            self.marginalCost.append(0.0)
            if(self.CFDPrice>0.0001):
                curIncome = self.CFDPrice*curGen
            else:
                if(self.name=='Solar'):
                    y = self.year- self.BASEYEAR
                    if(y<len(self.yearlySolarFiT)):
                        sellP = self.yearlySolarFiT[y]
                    else:
                        sellP = self.wholesaleEPriceProf[i]
                    curIncome = sellP*curGen
                else:
                    curIncome = self.wholesaleEPriceProf[i]*curGen
            curProfit = curIncome-curCost
            
            self.hourlyCost.append(curCost)
            self.hourlyProfit.append(curProfit)
            self.runningCost = self.runningCost + (curCost)
            self.yearlyProfit = self.yearlyProfit + curProfit
            self.yearlyCost = self.runningCost
            self.yearlyIncome = self.yearlyIncome + curIncome
            self.yearlyCarbonCostSum = 0.0
            if(self.genCapacity>0.00001):
                self.estimatedROI = (self.yearlyProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
            else:
                self.estimatedROI = 0.0
            self.NPV = 0.0
            for yr in range(5): # for yr in range(self.year, self.endYear):
                self.NPV = self.NPV +  self.yearlyProfit/((1+self.discountR)**yr)
            
        
    # used for testing
    def loadGenRandomProfile(self,timeSteps,minV, maxV):
        # For now, just generating random numbers to check if works*
        self.energyGenerated = list()
        for i in range(timeSteps): #8760 hours in year
            self.energyGenerated.append(random.uniform(minV, maxV)) #kW
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
        
    def getGeneration(self):
        return self.energyGenerated
    












































        
        
