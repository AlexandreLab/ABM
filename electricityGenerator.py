import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils
import statistics


class electricityGenerator():
    
    
    def __init__(self, genName, genTypeID, capacity, lifetime, numBus, headroom, BASEYEAR):

        self.name = genName
        self.timeSteps = 8760
        
        self.busbar = numBus
        self.headroom = headroom

        self.genTypeID = genTypeID
        if lifetime == 0 :
            raise ValueError('The lifetime cannot be equal to 0 for the asset {0} with a capacity of {1}'.format(genName, capacity))


        #Technical parameters
        self.opEmissionsPkW = 0.0 # kg of CO2 emitted per kW generated
        self.lifetime = lifetime
        self.genCapacity = capacity #kW
        self.renewableBool = False
        self.yearlyEmissions=0.0
        self.yearlyEnergyGen=0.0
        self.energyGenerated = np.zeros(self.timeSteps)
        self.hourlyEmissions = np.zeros(self.timeSteps)
        self.capacityFactor = 0
        self.availabilityFactor = 0

        # Construction parameters
        self.preDevTime = 0 # years
        self.constructionTime = 0 # years
        self.totConstructionTime = 0 # years

        self.age = 0
        self.startYear = 0
        self.endYear = 0
        self.BASEYEAR = BASEYEAR
        self.year = self.BASEYEAR

        #Economic parameters
        self.yearlyIncome = 0.0
        self.yearlyCost = 0.0
        self.yearlyProfit=0.0
        self.hourlyProfit = np.zeros(self.timeSteps)
        self.hourlyIncome = np.zeros(self.timeSteps)
        self.hourlyCost = np.zeros(self.timeSteps)
        self.marginalCost = np.zeros(self.timeSteps)
        self.yearlyFuelCost = list()

        self.yearlyProfitList = list() # not sure of the use of this variable

        self.fuelCost = 0.0 #£/kWh
        self.curCO2Price = 0.0 #£/tCO2
        self.fixedOandMCost = 0.0 #£/kW
        self.variableOandMCost = 0.0 #£/kWh
        self.capitalCost = 0.0 #£/kW
        self.yearlycurCO2PriceSum = 0.0 
        self.wasteCost = 0.0

        self.connectionFee = 0.5174*self.headroom*0.001-2415.7
        self.capitalSub = 0.0 # no subsidies for capital unless specified £ / kW cap per year
        self.discountR = 0
        self.CFDPrice = 0 # GBP

        self.wholesaleEPrice = np.zeros(self.timeSteps)
        self.yearlySolarFiT = np.array([]) # initialize as an empty array

    def calculateHourlyData(self):
        temp_arr_emissions = self.energyGenerated*self.opEmissionsPkW #kgCO2
        temp_arr_fuelCost = self.energyGenerated*self.fuelCost
        temp_arr_variableOM = self.energyGenerated*self.variableOandMCost
        temp_arr_carbonCost = temp_arr_emissions/1000.0*self.curCO2Price
        temp_arr_waste = self.energyGenerated*self.wasteCost
        
        # margin cost is 0 if the current generation is 0
        temp_arr_marginalCost = np.sum([temp_arr_fuelCost,temp_arr_waste, temp_arr_variableOM, temp_arr_carbonCost], axis=0)
        temp_arr_marginalCost = np.divide(temp_arr_marginalCost, self.energyGenerated, out=np.zeros_like(temp_arr_marginalCost), where=self.energyGenerated!=0)

        temp_arr_hourlyCost = temp_arr_marginalCost + self.fixedOandMCost*self.genCapacity/8760

        self.yearlyCarbonCost = np.sum(temp_arr_carbonCost)
        self.hourlyCost = temp_arr_hourlyCost
        self.marginalCost = temp_arr_marginalCost
        self.hourlyEmissions = temp_arr_emissions 
        self.yearlyCost = np.sum(temp_arr_hourlyCost)
        self.yearlyEmissions = np.sum(temp_arr_emissions)
        return True

    def calculateProfit(self):

        if (self.name=='Nuclear' or self.name=='BECCS') and self.CFDPrice>0.0001: # nuclear and BECCS
            temp_arr_hourlyIncome = self.energyGenerated*self.CFDPrice + ((self.capitalSub*self.genCapacity)/(365*24))
        else:
            temp_arr_hourlyIncome = self.energyGenerated*self.wholesaleEPrice + ((self.capitalSub*self.genCapacity)/(365*24))

        if(self.CFDPrice>0):
            temp_arr_hourlyIncome = self.energyGenerated * self.CFDPrice
        else:
            if(self.name=='Solar'):
                y = self.year- self.BASEYEAR
                if(y<len(self.yearlySolarFiT)):
                    temp_arr_hourlyIncome = self.energyGenerated * self.yearlySolarFiT[y]
                else:
                    temp_arr_hourlyIncome = np.multiply(self.energyGenerated,self.wholesaleEPrice) + ((self.capitalSub*self.genCapacity)/(365*24))
            else:
                temp_arr_hourlyIncome = np.multiply(self.energyGenerated,self.wholesaleEPrice) + ((self.capitalSub*self.genCapacity)/(365*24))

        temp_arr_hourlyProfit = np.subtract(temp_arr_hourlyIncome, self.hourlyCost)
            
        self.hourlyProfit = temp_arr_hourlyProfit
        self.yearlyProfit = np.sum(temp_arr_hourlyProfit)
        self.yearlyIncome = np.sum(temp_arr_hourlyIncome)

        totalInitialInvestment = self.capitalCost*self.genCapacity + self.connectionFee
        self.ROI = (self.yearlyProfit*(1-(1+self.discountR)**-self.lifetime)/self.discountR - totalInitialInvestment)/totalInitialInvestment
        self.NPV = self.yearlyProfit*(1-(1+self.discountR)**-self.lifetime)/self.discountR - totalInitialInvestment

    # update date for next year
    def updateYear(self, CO2Price):
        self.yearlyProfitList.append(self.yearlyProfit)
        if(self.age>=15):
            self.CFDPrice = 0.0
        self.year = self.year + 1
        self.age = self.age + 1
        y = self.year - self.BASEYEAR
        
        self.curCO2Price = CO2Price
        if not self.renewableBool:
            self.fuelCost = self.yearlyFuelCost[y]    
            self.energyGenerated = np.zeros(self.timeSteps)
            self.hourlyEmissions = np.zeros(self.timeSteps)
        self.resetYearValueRecord()
        return True

    # estimate ROI and NPV 
    def estimateROIandNPV(self, newCfD, newCO2Price, boolUseCfD):
        if((self.renewableBool or self.name =='Nuclear' or self.name =='BECCS'or self.name =='Biomass'or self.name =='Hydrogen') and boolUseCfD):
            estIncome = newCfD*self.yearlyEnergyGen
            estYearProfit = estIncome - self.yearlyCost
        elif(self.renewableBool):
            estIncome = 0.0
            for i in range(len(self.energyGenerated)):
                estIncome = estIncome + self.energyGenerated[i]*self.wholesaleEPriceProf[i]
                
            if(self.name=='Solar'):
                y = self.year- self.BASEYEAR
                if(y<len(self.yearlySolarFiT)):
                    sellP = self.yearlySolarFiT[y]
                    estIncome = sellP*self.yearlyEnergyGen
                else:
                    estIncome = 0.0
                    for i in range(len(self.energyGenerated)):
                        estIncome = estIncome + self.energyGenerated[i]*self.wholesaleEPriceProf[i]
            estYearProfit = estIncome - self.yearlyCost
        else:
            estIncome = 0.0
            for i in range(len(self.energyGenerated)):
                estIncome = estIncome + self.energyGenerated[i]*self.wholesaleEPriceProf[i]
            
            oldCarbonCost = self.yearlyCarbonCostSum
            if(self.name=='BECCS'or self.name =='Biomass'or self.name =='Hydrogen'):
                newCarbonCost = 0.0
            else:
                newCarbonCost = ((self.yearlyEmissions/1000.0)*newCO2Price)
            estCost = self.yearlyCost - oldCarbonCost + newCarbonCost
            estYearProfit = estIncome - estCost

        if(self.genCapacity>0.00001):
            tempEstimatedROI = (estYearProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
        else:
            tempEstimatedROI = 0.0
            
        estNPV = 0.0
        for yr in range(self.lifetime): # for yr in range(self.year, self.endYear):
            estNPV = estNPV + estYearProfit/((1+self.discountR)**yr)

        return tempEstimatedROI, estNPV
    
    # reset values for next year
    def resetYearValueRecord(self):
        self.yearlyEnergyGen=0.0
        self.yearlyCost = 0.0
        self.yearlyProfit = 0
        self.yearlyIncome = 0
        self.yearlyEmissions = 0
        self.yearlyCarbonCost = 0
        
        self.hourlyCost = np.zeros(self.timeSteps)
        
        self.marginalCost = np.zeros(self.timeSteps)
        self.hourlyProfit = np.zeros(self.timeSteps)
        self.NPV = 0
        

    def getActCapFactor(self):
        maxEnergyGen = self.genCapacity*24*365
        self.actualCapFac = self.yearlyEnergyGen/maxEnergyGen
        return self.actualCapFac


    def estimateCfDSubsidy(self):
        estCfD = 0
        return estCfD




    # estimate revenue for a specific capacity
    def estAnnualRevenue(self, testCap):
        yGenTemp = 0.0
        yRevenue = 0.0
        
        for i in range(len(self.energyGenerated)):
            curGen = (self.energyGenerated[i]/self.genCapacity)*testCap
            
            yGenTemp = yGenTemp + curGen
            curIncome = self.wholesaleEPriceProf[i]*curGen
            yRevenue = yRevenue + curIncome

        if(not yGenTemp>0.0001):
        #    print('estAnnualRevenue')
        #    print('yGenTemp ', yGenTemp)
        #    print('testCap ', testCap)
        #    print('cur gen Cap ', self.genCapacity)
        #    print('self.energyGenerated ', self.energyGenerated)
        #    input('Error, divide by zero')
             yGenTemp = 0.0001
        revenuePerKWh = yRevenue/yGenTemp
        

        return yRevenue, revenuePerKWh




























        
        
