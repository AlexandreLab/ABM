import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils
from electricityGenerator import electricityGenerator


class traditionalGenerator(electricityGenerator):
    
    
    def __init__(self, genName, genTypeID, capacity, lifetime, numBus, headroom):
        super().__init__(genName, genTypeID, capacity, lifetime, numBus, headroom)
        self.renewableBool = False
        self.availabilityFactor = 0.9
    


    # load fuel cost method
    def loadFuelCost(self,FILEPATH): 
        fileIN = Utils.loadTextFile(FILEPATH)
        self.yearlyFuelCost = list()
        if(self.name=="Coal"): # coal
            for i in range(len(fileIN)):
                val = fileIN[i]
                newVal = val/1000.0 # tonnes to kg
                newVal = newVal/2.46 # 1 kg of coal produces 2.46 kWh
                newVal = newVal*0.77 # USD to GBP
                self.yearlyFuelCost.append(newVal) # gbp per kWh
        elif(self.name=="CCGT" or self.name=="OCGT"): # CCGT and OCGT
            for i in range(len(fileIN)):
                val = fileIN[i]
                newVal = val/100.0 # p/ therm to gbp/therm
                newVal = newVal/29.31 # therms to kWh, 1 therm = 29.31 kWh
           #     print('Fuel cost CCGT GBP/kWh ',)
                self.yearlyFuelCost.append(newVal) # gbp per kWh
        elif(self.name=="Nuclear"): # Nuclear
            for i in range(len(fileIN)):
                val = fileIN[i]
                newVal = val/100.0 # p/ kWh to gbp/kWh
                self.yearlyFuelCost.append(newVal) # gbp per kWh
        elif(self.name=="BECCS" or self.name == "Biomass"): # BECCS
            for i in range(len(fileIN)):
                newVal = fileIN[i]
                self.yearlyFuelCost.append(newVal) # gbp per kWh
        self.FuelCost = self.yearlyFuelCost[0]

    # get generation for demand profile, this function could be done at the generation company level to save memory
    def getGeneration(self, demand):
        self.marginalCost = list()
        self.energyGenerated = list()
        newDemand = list()
        excessGen = list()

        
        for i in range(len(demand)):
            if(self.name == 'Nuclear'):
                if(i>=151 and i <243): # 3 months of summer
                    minNuclearOpCap = self.genCapacity*0.5
                else: # rest of year
                    minNuclearOpCap = self.genCapacity*0.65
            
            if((self.genCapacity*self.availabilityFactor)<demand[i]): # is the demand greater than max available capacity 
                self.energyGenerated.append(self.genCapacity*self.availabilityFactor)
                newDemand.append(demand[i]-(self.genCapacity*self.availabilityFactor))
                excessGen.append(0.0)
            elif(self.name == 'Nuclear' and demand[i]<minNuclearOpCap): # minimum for nuclear 
                self.energyGenerated.append(minNuclearOpCap)
                newDemand.append(0.0)
                tempEGen = float(minNuclearOpCap-demand[i])
                excessGen.append(tempEGen)
            else:
                self.energyGenerated.append(demand[i])
                newDemand.append(0.0)
                excessGen.append(0.0)
            curGen = self.energyGenerated[i]
            curEmiss = self.opEmissionsPkW*curGen # emissions in kg

            fuel = curGen*self.FuelCost
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            
            if(self.name =='BECCS' or self.name =='Hydrogen'):
                carbon = 0.0
            else:
                carbon = ((curEmiss/1000.0)*self.CarbonCost)
            capital = self.capitalCostPerHour # GBP/hr
            waste = self.wasteCost*curGen
            
            curCost = fuel + fixedOM + variableOM + carbon + capital + waste

            if(curGen<1 or self.name =='BECCS'):
                marginC = 0.0
            else:
                marginC = (fuel + variableOM + carbon)/curGen
            self.marginalCost.append(marginC)

            if((self.genTypeID==2 or self.genTypeID==4) and self.CFDPrice>0.0001): # nuclear and BECCS
                curIncome = (self.CFDPrice*curGen) + ((self.capitalSub*self.genCapacity)/(365*24))
            else:
                curIncome = (self.wholesaleEPriceProf[i]*curGen) + ((self.capitalSub*self.genCapacity)/(365*24))
            
            curProfit = curIncome-curCost

            self.yearlyCarbonCostSum = self.yearlyCarbonCostSum + carbon
            self.hourlyCost.append(curCost)
            self.hourlyEmissions.append(curEmiss)
            self.hourlyProfit.append(curProfit)
            self.runningCost = self.runningCost + (curCost)
            self.runningEmissions = self.runningEmissions + (curEmiss)
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
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

        return self.energyGenerated, newDemand, excessGen

    def updateProfit(self, wholesaleProf):
        self.wholesaleEPriceProf = wholesaleProf.copy()
        self.hourlyProfit = list()
        self.yearlyProfit = 0.0
        self.yearlyIncome = 0.0
        self.marginalCost = list()
        for i in range(len(self.energyGenerated)):
            curGen = self.energyGenerated[i]
            curEmiss = self.opEmissionsPkW*curGen # emissions in kg

            fuel = curGen*self.FuelCost
            fixedOM = self.fixedOandMPerHour # GBP/hr
            variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
            
            if(self.name =='BECCS' or self.name =='Hydrogen'):
                carbon = 0.0
            else:
                carbon = ((curEmiss/1000.0)*self.CarbonCost)
            capital = self.capitalCostPerHour # GBP/hr
            waste = self.wasteCost*curGen
            
            curCost = fuel + fixedOM + variableOM + carbon + capital + waste

            if(curGen<1 or self.name =='BECCS'):
                marginC = 0.0
            else:
                marginC = (fuel + variableOM + carbon)/curGen
            self.marginalCost.append(marginC)

            if((self.genTypeID==2 or self.genTypeID==4) and self.CFDPrice>0.0001): # nuclear and BECCS
                curIncome = (self.CFDPrice*curGen) + ((self.capitalSub*self.genCapacity)/(365*24))
            else:
                curIncome = (self.wholesaleEPriceProf[i]*curGen) + ((self.capitalSub*self.genCapacity)/(365*24))
            
            curProfit = curIncome-curCost


            self.hourlyProfit.append(curProfit)
            self.yearlyProfit = self.yearlyProfit + curProfit
            self.yearlyIncome = self.yearlyIncome + curIncome
            if(self.genCapacity>0.00001):
                self.estimatedROI = (self.yearlyProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
            else:
                self.estimatedROI = 0.0
            self.NPV = 0.0
            for yr in range(5): # for yr in range(self.year, self.endYear):
                self.NPV = self.NPV +  self.yearlyProfit/((1+self.discountR)**yr)

            

    def graph(self):
        import matplotlib.pyplot as plt
        graphGen,genUnit = Utils.checkUnits(self.energyGenerated)
        graphEmiss,emissUnit = Utils.checkWeightUnits(self.hourlyEmissions)
        
        fig, axs = plt.subplots(4,1)
        fig.suptitle(self.name, fontsize=20)
        axs[0].plot(graphGen)
        axs[0].set_ylabel('Energy Generated ('+genUnit+')')
        axs[1].plot(self.hourlyCost)
        axs[1].set_ylabel('Generation Cost (GBP)')
        axs[2].plot(graphEmiss)
        axs[2].set_ylabel('CO2 Emissions ('+emissUnit+')')
        axs[3].plot(self.hourlyProfit)
        axs[3].set_ylabel('Profit (GBP)')
        fig.show()



    
    









        
        
