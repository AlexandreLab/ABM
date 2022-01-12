import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils
import statistics


class electricityGenerator():
    
    
    def __init__(self):

        self.initialise() 
        

    def initialise(self):
        self.age = 0
        self.opEmissions = 0.0 # kg of CO2 emitted per hour
        self.name = 'Unknown'
        self.generalInfo()
        self.renewableBool = True

    # method to initialize variable common to renewables and non renewables
    def generalInfo(self):
        file2 = open("BASEYEAR.txt", "r") 
        temp = file2.read()
        self.BASEYEAR = int(temp)
        file2.close()
        self.marginalCost = list()
        self.CFDPrice = 0.0
        self.capitalSub = 0.0 # no subsidies for capital unless specified £ / kW cap per year
        self.discountR = 0.1 # 10%
        self.year = self.BASEYEAR
        self.constructionQueueYear = list()
        self.constructionQueueCapacityIncrease = list() # kW
        self.constructionQueueRenewableValIncrease = list() # kW, need this to scale ren gen profile
        self.yearlyCapacityList = list()
        self.yearlyDeRateCapacityList = list()
        self.yearlyProfitList = list()
        self.yearlyIncomeList = list()
        self.yearlyCostList = list()
        self.yearlyEmissionsList = list()
        self.years = list()
        
        carbonFilePath = 'CarbonPrice/carbonPrice'+str(self.BASEYEAR)+'_2050.txt'
        self.loadCarbonCost(carbonFilePath)
        
        wholesalePriceFilePath = 'WholesaleEnergyPrices/ElectricityBaseLoad'+str(self.BASEYEAR)+'_2050_GBPPerkWh.txt'
        self.yearlyWholesaleElecPrice = Utils.loadTextFile(wholesalePriceFilePath) # GBP per kWh
        self.curWholesaleElecPrice = self.yearlyWholesaleElecPrice[0]

        wholesaleEPriceProfFilePath = 'WholesaleEnergyPrices/HourlyWholesaleElectricityPrice2018_GBPPerkWh.txt'
        self.wholesaleEPriceProf2018 = Utils.loadTextFile(wholesaleEPriceProfFilePath)
        priceProfAvg = statistics.mean(self.wholesaleEPriceProf2018)
        priceScale = self.curWholesaleElecPrice/priceProfAvg
        self.wholesaleEPriceProf = Utils.multiplyList(self.wholesaleEPriceProf2018,priceScale)

    # set build rate for each gen type
    def updateBuildRates(self):
        file2 = open("GEN_TYPE_LIST.txt", "r") 
        genTypesList = file2.read().split('\n')
        file2.close()
        genTypesList.pop()

        file2 = open("GEN_TYPE_COMPANY_COUNT_LIST.txt", "r") 
        genTypesCompCountList = file2.read().split('\n')
        newCountList = list()
        for i in range(len(genTypesCompCountList)-1):
            myNum = genTypesCompCountList[i]
            newCountList.append(int(myNum))
        file2.close()
        genTypesCompCountList = newCountList

        file2 = open("GB_MaxBuildRates.txt", "r") 
        GBMaxBuildRatesListTemp = file2.read().split('\n')
        GBMaxBuildRatesList = list()
        for i in range(len(GBMaxBuildRatesListTemp)):
            myNum = GBMaxBuildRatesListTemp[i]
            GBMaxBuildRatesList.append(int(myNum))
        file2.close()
        
        indx = genTypesList.index(self.name)
        self.GBmaxBuildRate = GBMaxBuildRatesList[indx]
        if(self.year>=2018 and self.name =='Wind Offshore'):
            self.GBmaxBuildRate = 3000000
        
        nComp = genTypesCompCountList[indx]
        if(nComp==0): # avoid dividing by zero
            self.maxBuildRate = int(self.GBmaxBuildRate)
        else:
            self.maxBuildRate = int(self.GBmaxBuildRate/nComp)

 
    # update date for next year
    def updateYear(self, CO2Price):
        self.yearlyCapacityList.append(self.genCapacity)
        self.yearlyDeRateCapacityList.append((self.genCapacity*self.capacityFactor))
        self.yearlyProfitList.append(self.yearlyProfit)
        self.yearlyIncomeList.append(self.yearlyIncome)
        self.yearlyCostList.append(self.yearlyCost)
        self.yearlyEmissionsList.append(self.runningEmissions)
        self.years.append(self.year)
        if(self.age>=15):
            self.CFDPrice = 0.0
        
        self.year = self.year + 1
        self.age = self.age + 1
        y = self.year - self.BASEYEAR
        if(self.year>=2018 and self.name =='Wind Offshore'):
            self.updateBuildRates()
   #     oldWholesaleEPrice = self.curWholesaleElecPrice
   #     self.curWholesaleElecPrice = self.yearlyWholesaleElecPrice[y]

   #     priceProfAvg = statistics.mean(self.wholesaleEPriceProf2018)
   #     priceScale = self.curWholesaleElecPrice/priceProfAvg
   #     self.wholesaleEPriceProf = list()
   #     self.wholesaleEPriceProf = Utils.multiplyList(self.wholesaleEPriceProf2018,priceScale)
        
        self.CarbonCost = CO2Price
        if(not self.renewableBool):
            self.FuelCost = self.yearlyFuelCost[y]     
   #     newWholesaleEPrice = self.curWholesaleElecPrice
   #     wholesEPriceChange = ((newWholesaleEPrice - oldWholesaleEPrice)/ oldWholesaleEPrice)*100
   #     return wholesEPriceChange
        return 0.0

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
                newCarbonCost = ((self.runningEmissions/1000.0)*newCO2Price)
            estCost = self.yearlyCost - oldCarbonCost + newCarbonCost
            estYearProfit = estIncome - estCost

        if(self.genCapacity>0.00001):
            tempEstimatedROI = (estYearProfit * self.lifetime)/(self.capitalCost * self.genCapacity)
        else:
            tempEstimatedROI = 0.0
            
        estNPV = 0.0
        for yr in range(5): # for yr in range(self.year, self.endYear):
            estNPV = estNPV + estYearProfit/((1+self.discountR)**yr)

        return tempEstimatedROI, estNPV
    
    # reset values for next year
    def resetYearValueRecord(self):
        self.yearlyEnergyGen=0.0
        self.hourlyProfit = list()
        self.yearlyProfit=0.0
        self.yearlyIncome = 0.0
        self.yearlyCost = 0.0
        self.runningCost=0.0
        self.runningEmissions=0.0
        self.hourlyCost = list()
        self.hourlyEmissions = list()
        self.marginalCost = list()

    # function to change capacity of this plant, not used anywhere though so ignore
    def changeCapacityPC(self, pcChange,changeBool):
        valChange = self.genCapacity * (pcChange/100.0)
        
        if(not changeBool): # no change in capacity
            self.resetYearValueRecord()
            if(self.renewableBool):
                self.updateGenProfile(0.0)
        elif(pcChange<0):
            self.resetYearValueRecord()
            self.genCapacity = self.genCapacity + valChange
            if(self.renewableBool):
                self.updateGenProfile(pcChange)
        else:
            self.constructionQueueYear.append(self.year+self.constructionTime)
            self.constructionQueueCapacityIncrease.append(valChange)
            if(self.renewableBool):
                additionalEnergyGenProfile = list()
                for i in range(len(self.energyGenerated)):
                    additionalEnergyGenProfile.append(self.energyGenerated[i]*(pcChange/100.0))
                self.constructionQueueRenewableValIncrease.append(additionalEnergyGenProfile)
            self.resetYearValueRecord()
            if(self.renewableBool):
                self.updateGenProfile(0.0)
        i=0
        while (i <len(self.constructionQueueYear) and len(self.constructionQueueYear)>0):
            if(self.year == self.constructionQueueYear[i]):
                self.resetYearValueRecord()
                self.genCapacity = self.genCapacity + self.constructionQueueCapacityIncrease[i]
                if(self.renewableBool):
                    self.updateGenProfileUsingValues(self.constructionQueueRenewableValIncrease[i])
                del self.constructionQueueYear[i]
                del self.constructionQueueCapacityIncrease[i]
                if(self.renewableBool):
                    del self.constructionQueueRenewableValIncrease[i]
            else: 
                i=i+1



    def calcProfitPerKWh(self):
        if(self.yearlyEnergyGen<1.0):
            self.profitPerKWh = 0.0
        else:           
            self.profitPerKWh = self.yearlyProfit/self.yearlyEnergyGen

    def getActCapFactor(self):
        maxEnergyGen = self.genCapacity*24*365
        self.actualCapFac = self.yearlyEnergyGen/maxEnergyGen
        return self.actualCapFac

    def graph(self):
        import matplotlib.pyplot as plt
        graphGen,genUnit = Utils.checkUnits(self.energyGenerated)
        fig, axs = plt.subplots(2,1)
        fig.suptitle(self.name, fontsize=20)
        axs[0].plot(graphGen)
        axs[0].set_ylabel('Energy Generated ('+genUnit+')')
        fig.show()
    
    def loadCarbonCost(self,FILEPATH): 
        self.yearlyCarbonCost = Utils.loadTextFile(FILEPATH)
        self.CarbonCost = self.yearlyCarbonCost[0]

    # estimate annual cost for plant of specific capacity
    def estAnnualCosts(self, testCap):
        cap = self.genCapacity

        yGenTemp = 0.0
        yCost = 0.0
        estCapitalCostPerHour = (self.capitalCost * testCap)/(8760.0 * self.lifetime) # GBP/hr
        estFixedOandMPerHour = (self.fixedOandMCost * testCap)/(8760.0) # GBP/hr
        
        for i in range(len(self.energyGenerated)):
            if(not self.genCapacity == 0): 
                curGen = (self.energyGenerated[i]/self.genCapacity)*testCap
                yGenTemp = yGenTemp + curGen
                fuel = self.FuelCost * curGen
                fixedOM = estFixedOandMPerHour # GBP/hr
                variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
                capital = estCapitalCostPerHour # GBP/hr
                if(self.renewableBool):
                    curCost = fuel + fixedOM + variableOM + capital
                else:
                    curEmiss = self.opEmissionsPkW*curGen
                    if(self.name=='BECCS'or self.name =='Biomass'or self.name =='Hydrogen'):
                        carbon = 0.0
                    else:
                        carbon = ((curEmiss/1000.0)*self.CarbonCost)
                    waste = self.wasteCost*curGen
                    curCost = fuel + fixedOM + variableOM + capital + carbon + waste
                yCost = yCost + curCost
            else:
                yCost = 0

        if(not yGenTemp>0.0001):
        	yGenTemp = 0.0001
        #    print('estAnnualCosts')
        #    print('yGenTemp ', yGenTemp)
        #    print('testCap ', testCap)
        #    print('cur gen Cap ', cap)
        #    print('self.energyGenerated ', self.energyGenerated)
        #    input('Error, divide by zero')
        costPerKWh = yCost/yGenTemp
        
        return yCost, costPerKWh

    def estAnnualCostsCfD(self, testCap):
        cap = self.genCapacity

        yGenTemp = 0.0
        yCost = 0.0
        estCapitalCostPerHour = ((self.capitalCost-self.ConnectionFee)  * testCap)/(8760.0 * self.lifetime) # GBP/hr
        estFixedOandMPerHour = (self.fixedOandMCost * testCap)/(8760.0) # GBP/hr
        
        for i in range(len(self.energyGenerated)):
            if(not self.genCapacity == 0): 
                curGen = (self.energyGenerated[i]/self.genCapacity)*testCap
                yGenTemp = yGenTemp + curGen
                fuel = self.FuelCost * curGen
                fixedOM = estFixedOandMPerHour # GBP/hr
                variableOM = self.variableOandMCost * curGen # GBP/kWh * kWh
                capital = estCapitalCostPerHour # GBP/hr
                if(self.renewableBool):
                    curCost = fuel + fixedOM + variableOM + capital
                else:
                    curEmiss = self.opEmissionsPkW*curGen
                    if(self.name=='BECCS'or self.name =='Biomass'or self.name =='Hydrogen'):
                        carbon = 0.0
                    else:
                        carbon = ((curEmiss/1000.0)*self.CarbonCost)
                    waste = self.wasteCost*curGen
                    curCost = fuel + fixedOM + variableOM + capital + carbon + waste
                yCost = yCost + curCost
            else:
                yCost = 0

        if(not yGenTemp>0.0001):
            yGenTemp = 0.0001
        #    print('estAnnualCosts')
        #    print('yGenTemp ', yGenTemp)
        #    print('testCap ', testCap)
        #    print('cur gen Cap ', cap)
        #    print('self.energyGenerated ', self.energyGenerated)
        #    input('Error, divide by zero')
        costPerKWh = yCost/yGenTemp
        
        return yCost, costPerKWh



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




























        
        
