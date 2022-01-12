import random
from random import randint
from collections import namedtuple
import numpy as np
import math
from electricityGenerator import electricityGenerator
import Utils

class renewableGenerator(electricityGenerator):
    
    
    def __init__(self,renGenTypeID,timeSteps, capacity, CFDPrice, NumBus, Headroom): # kW

        self.initialise(renGenTypeID,timeSteps, capacity,CFDPrice, NumBus, Headroom)


    def initialise(self,renGenTypeID,timeSteps, capacity, CFDPrice, NumBus, Headroom):
        self.generalInfo()
        self.genCapacity = capacity
        self.age = 0
        self.startYear = 0
        self.endYear = 0
        self.opEmissions = 0.0 # tonnes of CO2 emitted per hour
        self.renewableType = -1
        self.name = 'Unknown'
        self.yearlyEnergyGen=0.0
        self.hourlyProfit = list()
        self.yearlyProfit=0.0
        self.yearlyIncome = 0.0
        self.yearlyCost = 0.0
        self.runningCost=0.0
        self.runningEmissions = 0.0
        self.hourlyCost = list()
        self.renewableBool = True
        self.availabilityFactor = 0.1
        self.numbus = NumBus
        self.Headroom = Headroom
        self.genTypeID = renGenTypeID
        self.FuelCost = 0.0
        self.CarbonCost = 0.0
        self.fixedOandMCost = 0.0
        self.variableOandMCost = 0.0
        self.capitalCost = 0.0
        self.yearlyCarbonCostSum = 0.0 
        self.CFDPrice = CFDPrice # GBP
        self.ConnectionFee = (0.5174*self.Headroom*0.001-2415.7)/8760

        solarFiTFilePath = 'WholesaleEnergyPrices/Solar_FiT_2010_2019_GBPPerkWh.txt'
        self.yearlySolarFiT = Utils.loadTextFile(solarFiTFilePath) # GBP per kWh
        
        CapexSolar = list([524.0132552, 524.0132552, 524.0132552, 524.0132552, 524.0132552, 524.0132552, 524.0132552, 524.0132552, 524.0132552, 524.0132552, 524.0132552, 496.415919, 464.1670166, 447.6930044, 436.637465, 428.1875, 418.2, 408.476, 398.9305, 389.64, 382.6785, 375.802, 369.0955, 362.474, 355.9375, 351.4495, 347.038, 342.7115, 338.3935, 334.152, 331.687, 329.222, 326.8335, 324.4535, 322.065, 321.436, 320.722, 320.093, 319.464, 318.75, 318.75])
        CapexHydro = list([1150.038006, 1150.038006, 1150.038006, 1150.038006, 1150.038006, 1150.038006, 1150.038006, 1150.038006, 1150.038006, 1150.038006, 1150.038006, 1147.662557, 1122.030202, 1132.395722, 1142.80841, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5, 1147.5])

        CapexWindOnshore = list([1004.358739, 1004.358739, 1004.358739, 1004.358739, 1004.358739, 1004.358739, 1004.358739, 1004.358739, 1004.358739, 1004.358739, 1004.358739, 967.5764526, 917.6546487, 898.6907628, 879.5392132, 861.9, 850.85, 839.8, 829.6, 819.4, 809.2, 804.95, 799.85, 795.6, 791.35, 787.1, 782.85, 778.6, 774.35, 770.1, 765.85, 765.85, 765.85, 765.85, 765.85, 765.85, 765.85, 765.85, 765.85, 765.85, 765.85])
        CapexWindOffshore = list([1794.745399, 1794.745399, 1794.745399, 1794.745399, 1794.745399, 1794.745399, 1794.745399, 1794.745399, 1794.745399, 1794.745399, 1794.745399, 1707.284766, 1597.709786, 1544.466677, 1494.962705, 1447.55, 1395.7, 1344.7, 1296.25, 1266.5, 1236.75, 1207.85, 1180.65, 1153.45, 1135.6, 1118.6, 1102.45, 1085.45, 1069.3, 1053.15, 1037, 1027.65, 1018.3, 1008.95, 1000.45, 991.1, 982.6, 973.25, 964.75, 956.25, 946.9])

        if(renGenTypeID==0): # 9 gen companies with solar (10 if including 1 for distribution)
            self.renewableType = 0
            self.name = 'Solar' # PV>5MW
    #        fileLoc = 'PV/1Year.txt'
            fileLoc = 'PV/2018_GB_Solar_MW.txt'
            self.fixedOandMCost = 5.6 # gbp per kW capacity per year
            self.variableOandMCost = 0.0 # gbp per kWh
            self.capitalCost = CapexSolar[self.year-2010] # gbp per kW capacity
            self.capacityFactor = 0.11
            self.availabilityFactor = 0.012
            self.lifetime = 25 # years
            self.totConstructionTime = 1 # years
            self.preDevTime = 1 # years
            self.constructionTime = 1 # years
     #       self.GBmaxBuildRate = 1000000  # 1GW
            self.GBmaxBuildRate = 1500000  # 1.5 GW
            self.maxBuildRate = 100000 # 1GW in total. 0.1 per company
        elif(renGenTypeID==1): # ********* ignore this one *************
            self.renewableType = 1
            self.name = 'Wind'
     #       fileLoc = 'Wind/Ireland8760WindMW.txt'
            fileLoc = 'Wind/2018_GB_WindTotal_MW.txt'
            self.fixedOandMCost = 0.0 
            self.variableOandMCost = 0.0
            self.capitalCost = 0.0
            self.lifetime = 25 # years
            self.totConstructionTime = 1 # years
            self.maxBuildRate = 100000 # 0.1GW
            self.GBmaxBuildRate = 1000000  # 1GW
            input('wrong renewable type')
 #           self.loadGenProfile(fileLoc)
        elif(renGenTypeID==2): 
        	#if(self.numbus in [1,12]):

            self.renewableType = 2
            self.name = 'Hydro' # Hydro 5-16MW
            fileLoc = 'Hydro/2018_GB_Hydro_MW.txt'
            self.fixedOandMCost = 45.1 # gbp per kW capacity per year
            self.variableOandMCost = 0.006 # gbp per kWh
            self.capitalCost =  CapexHydro[self.year-2010] # gbp per kW capacity
            self.lifetime = 41 # years
            self.totConstructionTime = 4 # years
            self.preDevTime = 2 # years
            self.constructionTime = 2 # years
            self.capacityFactor = 0.35
            self.availabilityFactor = 0.84
            self.GBmaxBuildRate = 60000  # 60 MW
            self.maxBuildRate = 10000 # 10 MW # 0.05GW
            #else:
            #	input('Error. This bus is not suitable for Hydro')
                        # 0.1GW
        elif(renGenTypeID==4): # 17 gen companies with onshore wind (18 if including 1 for distribution)
            self.renewableType = 4 
            self.name = 'Wind Onshore' # Onshore UK>5MW
            fileLoc = 'Wind/2018_GB_WindOnshore_MW.txt'
            self.fixedOandMCost = 23.2 # gbp per kW capacity per year
            self.variableOandMCost = 0.005 # gbp per kWh
            self.capitalCost =  CapexWindOnshore[self.year-2010] # gbp per kW capacity
            self.FuelCost = 0.0
            self.lifetime = 24 # years
            self.totConstructionTime = 6 # years
            self.preDevTime = 4 # years
            self.constructionTime = 2 # years
            self.capacityFactor = 0.32
            self.availabilityFactor = 0.17
            self.GBmaxBuildRate = 550000  # 0.55GW
            self.maxBuildRate = 30600 # 0.55 GW in total. /18 to get 0.0306 GW          #500000 # 0.5GW 
        elif(renGenTypeID==5): # 8 gen companies with offshore wind (9 if including 1 for distribution)
            #if(self.numbus in [1,2,7,8,9,10,11,12,13,15,16,19,20,26,27,28,29]):            	
            self.renewableType = 5
            self.name = 'Wind Offshore' # Offshore R3
            fileLoc = 'Wind/2018_GB_WindOffshore_MW.txt'
            self.fixedOandMCost = 48.6 # gbp per kW capacity per year
            self.variableOandMCost = 0.004 # gbp per kWh
            self.capitalCost =  CapexWindOffshore[self.year-2010] # gbp per kW capacity
            self.FuelCost = 0.00
            self.lifetime = 22 # years
            self.totConstructionTime = 8 # years
            self.preDevTime = 5 # years
            self.constructionTime = 3 # years
            self.capacityFactor = 0.48
            self.availabilityFactor = 0.24
     #       self.GBmaxBuildRate = 3000000  #500000  # 0.5GW
            self.GBmaxBuildRate = 1000000  #500000  # 0.5GW
            self.maxBuildRate = 56000 # 0.5GW in total. /9 to get 0.056 GW           #1000000 # 1GW
            #else:
                #input('Error. This bus is not suitable for Wind Offshore')    

 
        else:
            input('Error. Undefined renewable entered.')

        self.updateBuildRates() # resetting max build rates per company

        self.fileLoc = fileLoc
        self.capitalCostPerHour = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr
        self.fixedOandMPerHour = (self.fixedOandMCost * self.genCapacity)/(8760.0) # GBP/hr
        self.loadScaleGenProfile(fileLoc,self.genCapacity)
        
    # load generation profile and scale to match desired capacity
    def loadScaleGenProfile(self,FILEPATH, cap):
        self.marginalCost = list()
        self.energyGenerated = Utils.loadTextFile(FILEPATH)
        for i in range(len(self.energyGenerated)):
            if(self.renewableType == 0): # solar
                fileGenCapacity = 13000000
                scale = cap/fileGenCapacity
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 * scale # MW to kW          
            elif(self.renewableType == 1): # wind
                fileGenCapacity = 9000000
                scale = cap/fileGenCapacity
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 * scale # MW to kW
            elif(self.renewableType == 2): # Hydro
                fileGenCapacity = 1000000
                scale = cap/fileGenCapacity
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 * scale # MW to kW

            elif(self.renewableType == 4): # Onshore wind
                fileGenCapacity = 9500000
                scale = cap/fileGenCapacity
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 * scale # MW to kW
            elif(self.renewableType == 5): # Offshore wind
                fileGenCapacity =4000000
                scale = cap/fileGenCapacity
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 * scale # MW to kW
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            capital = self.capitalCostPerHour # GBP/hr
            
            curCost = fuel + fixedOM + variableOM + capital +self.ConnectionFee
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
                self.NPV = self.NPV + self.yearlyProfit/((1+self.discountR)**yr)


    def updateProfit(self, wholesaleProf):
        cap = self.genCapacity
        self.wholesaleEPriceProf = wholesaleProf.copy()
        self.hourlyProfit = list()
        self.yearlyProfit = 0.0
        self.yearlyIncome = 0.0

        for i in range(len(self.energyGenerated)):
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            capital = self.capitalCostPerHour # GBP/hr
            curCost = fuel + fixedOM + variableOM + capital+self.ConnectionFee
            
            

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
            
            self.hourlyProfit.append(curProfit)
            self.yearlyProfit = self.yearlyProfit + curProfit
            self.yearlyIncome = self.yearlyIncome + curIncome
            if(self.genCapacity>0.00001):
                self.estimatedROI = (self.yearlyProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
            else:
                self.estimatedROI = 0.0
                
            self.NPV = 0.0
            for yr in range(5): # for yr in range(self.year, self.endYear):
                self.NPV = self.NPV + self.yearlyProfit/((1+self.discountR)**yr)




    # method to recalculate costs etc.
    def recalcEconomics(self):
        cap = self.genCapacity
        self.marginalCost = list()

        for i in range(len(self.energyGenerated)):
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            capital = self.capitalCostPerHour # GBP/hr
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
                self.NPV = self.NPV + self.yearlyProfit/((1+self.discountR)**yr)


                
    # method to load generation profile (you will probably need to scale profile so use other method)
    def loadGenProfile(self,FILEPATH):
        self.energyGenerated = Utils.loadTextFile(FILEPATH)
        self.marginalCost = list()
        for i in range(len(self.energyGenerated)):
            if(self.renewableType == 0): # solar
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW
            elif(self.renewableType == 1): # wind
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW
            elif(self.renewableType == 2): # Hydro
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW

            elif(self.renewableType == 4): # Onshore wind
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW
            elif(self.renewableType == 5): # Offshore wind
                self.energyGenerated[i] = self.energyGenerated[i]*1000.0 # MW to kW
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            capital = self.capitalCostPerHour # GBP/hr
            
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
        self.capitalCostPerHour = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr
        self.fixedOandMPerHour = (self.fixedOandMCost * self.genCapacity)/(8760.0) # GBP/hr
        
        for i in range(len(self.energyGenerated)):
            self.energyGenerated[i] = self.energyGenerated[i] + (self.energyGenerated[i]*(pcChange/100.0))
            
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            capital = self.capitalCostPerHour # GBP/hr
            
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
        self.capitalCostPerHour = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr
        self.fixedOandMPerHour = (self.fixedOandMCost * self.genCapacity)/(8760.0) # GBP/hr
        
        for i in range(len(self.energyGenerated)):
            self.energyGenerated[i] = self.energyGenerated[i] + profileChangeVals[i]
            
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            curGen = self.energyGenerated[i]
           
            fuel = self.FuelCost * curGen
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            capital = self.capitalCostPerHour # GBP/hr
            
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
    












































        
        
