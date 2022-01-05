import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils
import statistics

class energyStorage():
    
    
    def __init__(self,capacity,chargeRate,dischargeRate, year,NumBus):

        self.initialise(capacity,chargeRate,dischargeRate, year, NumBus)
        

    def initialise(self,capacity,chargeRate,dischargeRate, year, NumBus):
        file2 = open("BASEYEAR.txt", "r") 
        temp = file2.read()
        self.BASEYEAR = int(temp)
        file2.close()
        self.age = 0.0
        self.year = year
        self.numbus = NumBus
        self.capitalSub = 0.0 #50.0 # variable for subsidies, unit GBP per kW cap per year
        
        self.discountR = 0.1
        self.opCostPkW = 0.14 # generation cost for 1kW GBP
        self.estimatedROI = 0.0
        self.NPV = 0.0
            
        self.maxCapacity = capacity
        self.curCapacity = 0.0
        self.chargeRate = chargeRate
        self.dischargeRate = dischargeRate
        self.hourlyStorage = list() # real-time SoC
        self.name = 'Battery Storage'
        self.capSubKWCap = 0.0 # cap market
        self.GBmaxBuildRate = 590000.0 # kW
        self.maxBuildRate = 590000.0/56 # 56 companies in model

        self.subsNeeded = 0.0
        self.runingCost=0.0
        self.curYearDischargeKWh = 0.0
        self.hourlyCost = list()
        self.hourlyProfit = list()
        self.yearlyProfit=0.0
        self.yearlyIncome = 0.0
        self.yearlyCost = 0.0
        self.NYyearlyCost = 0.0
        self.NYyearlyProfit = 0.0
        self.chargeBoolProf = list()#-1,0,1 hourly
        self.chargeProf = list()
        self.marginalCost = list()

        self.yearlyCapSubs = 0.0 # also cap market

        self.yearlyProfitList = list()
        self.yearlyIncomeList = list()
        self.yearlyCostList = list()
        self.years = list()

        CostDataFile = 'Battery/YearlyCostData.csv'
        self.costData = Utils.readCSV(CostDataFile)

        # figures based on Li-Ion Battery from 'A simple introduction to the economics of storage'
        # - David Newbery
        # https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-energy-storage

        y = self.year - self.BASEYEAR
        self.capitalCostInverter = self.costData['power capital cost'].iloc[y] #for discharge rate
        self.otherCost = self.costData['other'].iloc[y]
        self.capitalCostStorage = self.costData['energy capital cost'].iloc[y] + self.otherCost #for capacity
        self.fixedOandMCost = self.costData['fix'].iloc[y]
        self.variableOandMCost =  self.costData['variable'].iloc[y]
        self.lifetime = self.costData['Lifetime'].iloc[y]

        self.totalLifeCAPEX = (self.capitalCostStorage * self.maxCapacity) + (self.capitalCostInverter*self.dischargeRate)
        self.capitalCostPerHour = self.totalLifeCAPEX/(8760.0 * self.lifetime) # GBP/hr
        self.fixedOandMPerHour = (self.fixedOandMCost * self.dischargeRate)/(8760.0) # GBP/hr

        # must also read cost data for next year to estimate ROI of future investment
        self.updateNextYearCosts(y+1)

    # update cost data for next year (need this to estimate ROI for next year when investing)
    def updateNextYearCosts(self, indx):

        if(indx>=len(self.costData['Lifetime'])):
            indx = len(self.costData['Lifetime'])-1 #last year?
        
        self.NEXTYEARcapitalCostInverter = self.costData['power capital cost'].iloc[indx]
        self.NEXTYEARotherCost = self.costData['other'].iloc[indx]
        self.NEXTYEARcapitalCostStorage = self.costData['energy capital cost'].iloc[indx] + self.NEXTYEARotherCost
        self.NEXTYEARfixedOandMCost = self.costData['fix'].iloc[indx]
        self.NEXTYEARvariableOandMCost =  self.costData['variable'].iloc[indx]
        self.NEXTYEARlifetime = self.costData['Lifetime'].iloc[indx]

        self.NEXTYEARtotalLifeCAPEX = (self.NEXTYEARcapitalCostStorage * self.maxCapacity) + (self.NEXTYEARcapitalCostInverter*self.dischargeRate)
        self.NEXTYEARcapitalCostPerHour = self.NEXTYEARtotalLifeCAPEX/(8760.0 * self.NEXTYEARlifetime) # GBP/hr
        self.NEXTYEARfixedOandMPerHour = (self.NEXTYEARfixedOandMCost * self.dischargeRate)/(8760.0) # GBP/hr
 
    def setWholesaleElecPrice(self, priceProfile):
        self.wholesaleEPriceProf = priceProfile.copy()
        self.curWholesaleElecPrice = statistics.mean(self.wholesaleEPriceProf)
    
    def chargeBattery(self, energyAvailable, hour):#this is removed, no use
        chargeAmnt = energyAvailable
        if(self.curCapacity+energyAvailable>self.maxCapacity): #Check battery has capacity to charge
            availCap = self.maxCapacity - self.curCapacity 
            chargeAmnt = availCap
        elif(chargeAmnt>self.chargeRate):
            chargeAmnt = self.chargeRate
        else:
            chargeAmnt = energyAvailable
        
        self.curCapacity = self.curCapacity + chargeAmnt
        newEnergyAvail = energyAvailable - chargeAmnt
        self.hourlyStorage.append(self.curCapacity)
        self.recordHourInfo(chargeAmnt, True, False, hour)
        return newEnergyAvail

    def chargeBatteryFrac(self, hour, f): # charge battery by fraction of overall storage cap kWh
        energyConsumed = 0.0
        availToCharge = self.maxCapacity - self.curCapacity # how much space remaining before full charge
        chargeAmt = f*self.maxCapacity # how much we want to charge by
        if(chargeAmt>self.chargeRate): # check this is lower than max allowed charge rate
            chargeAmt = self.chargeRate
        if(abs(availToCharge)<1): #Check if battery full
            energyConsumed = 0.0
        elif(availToCharge>chargeAmt):
            energyConsumed = chargeAmt
            self.curCapacity = self.curCapacity + energyConsumed
        else:
            energyConsumed = availToCharge
            self.curCapacity = self.curCapacity + energyConsumed
        
        self.hourlyStorage.append(self.curCapacity)
        self.recordHourInfo(energyConsumed, True, False, hour)
        
        return energyConsumed # returns energy consumed

    def chargeBatteryMax(self, hour):#this is removed, no use
        energyConsumed = 0.0
        availToCharge = self.maxCapacity - self.curCapacity # how much space remaining before full charge
        if(abs(availToCharge)<1): #Check if battery full
            energyConsumed = 0.0
        elif(availToCharge>self.chargeRate):
            energyConsumed = self.chargeRate
            self.curCapacity = self.curCapacity + energyConsumed
        else:
            energyConsumed = availToCharge
            self.curCapacity = self.curCapacity + energyConsumed
        
        self.hourlyStorage.append(self.curCapacity)
        self.recordHourInfo(energyConsumed, True, False, hour)
        
        return energyConsumed # returns energy consumed

    def dischargeBattery(self, hour, requiredEnergy):#this is removed, no use
        energyConsumed = 0.0
        dischargeAmnt = requiredEnergy
        if(self.curCapacity-requiredEnergy<0): #Check available battery capacity to discharge
            availCap = self.curCapacity 
            dischargeAmnt = availCap
        elif(dischargeAmnt>self.dischargeRate):
            dischargeAmnt = self.dischargeRate
        else:
            dischargeAmnt = requiredEnergy
            
        self.curCapacity = self.curCapacity - dischargeAmnt
        newRequiredEnergy = requiredEnergy - dischargeAmnt
        self.hourlyStorage.append(self.curCapacity)
        self.recordHourInfo(dischargeAmnt, False, True, hour)
        
        return newRequiredEnergy

    def dischargeBatteryMax(self, hour, requiredEnergy):#this is removed, no use
        energyConsumed = 0.0
        dischargeAmnt = 0.0
        if(self.curCapacity>0 and requiredEnergy>0): # is there any charge
            dischargeAmnt = self.dischargeRate
            if(self.curCapacity - dischargeAmnt<0):# if amount to be discharged is greater than capacity
                dischargeAmnt = self.curCapacity
            if(dischargeAmnt>requiredEnergy): # check if discharge is greater than needed
                dischargeAmnt = requiredEnergy
            
        self.curCapacity = self.curCapacity - dischargeAmnt
        newRequiredEnergy = requiredEnergy - dischargeAmnt
        self.hourlyStorage.append(self.curCapacity)
        self.recordHourInfo(dischargeAmnt, False, True, hour)
        
        return newRequiredEnergy, dischargeAmnt

    def dischargeBatteryFrac(self, hour, requiredEnergy, f):
        dischargeAmt = 0.0
        
        if(self.curCapacity>0 and requiredEnergy>0): # is there any charge
            dischargeAmt = f*self.maxCapacity # how much we want to discharge by
            if(dischargeAmt>self.dischargeRate): # check this is lower than max allowed discharge rate
                dischargeAmt = self.dischargeRate
                
            if(self.curCapacity - dischargeAmt<0):# if amount to be discharged is greater than capacity
                dischargeAmt = self.curCapacity
            if(dischargeAmt>requiredEnergy): # check if discharge is greater than needed
                dischargeAmt = requiredEnergy
            
        self.curCapacity = self.curCapacity - dischargeAmt
        newRequiredEnergy = requiredEnergy - dischargeAmt
        self.hourlyStorage.append(self.curCapacity)
        self.recordHourInfo(dischargeAmt, False, True, hour)
        
        return newRequiredEnergy, dischargeAmt

    def maintainCapacity(self, hour):
        self.hourlyStorage.append(self.curCapacity)
        self.recordHourInfo(-100, False, False, hour)


    def updateProfit(self, wholesaleProf):
        fixedOM = self.fixedOandMPerHour # GBP/hr
        capital = self.capitalCostPerHour # GBP/hr
        self.wholesaleEPriceProf = wholesaleProf.copy()
        self.curYearDischargeKWh = 0.0
        self.hourlyCost = list()
        self.hourlyProfit = list()
        self.runingCost = 0.0
        self.yearlyProfit = 0.0
        self.yearlyCost = 0.0
        self.yearlyIncome = 0.0

        
        for i in range(len(self.chargeBoolProf)):
            energy = self.chargeProf[i]
            if(self.chargeBoolProf[i]<0.5):#1,0,-1 means discharge to make money
                variableOM = self.variableOandMCost * energy # GBP/kWh * kWh
                curIncome = self.wholesaleEPriceProf[i]*energy 
                chargeCost = 0.0
                self.curYearDischargeKWh = self.curYearDischargeKWh + energy
                NYvariableOM = self.NEXTYEARvariableOandMCost * energy
            elif(self.chargeBoolProf[i]>0.5):# means buy energy to charge
                variableOM = self.variableOandMCost * energy
                curIncome = 0
                chargeCost = self.wholesaleEPriceProf[i]*energy
                NYvariableOM = self.NEXTYEARvariableOandMCost * energy
            else:
                variableOM = 0.0
                curIncome = 0
                chargeCost = 0.0
                NYvariableOM = 0.0
            curIncome = curIncome + ((self.capitalSub*self.dischargeRate)/(365*24))
            curCost =fixedOM + variableOM  + capital + chargeCost
            curProfit = curIncome-curCost

            NYCost = self.NEXTYEARfixedOandMPerHour + NYvariableOM + self.NEXTYEARcapitalCostPerHour + chargeCost
            NYProfit = curIncome - NYCost
            
            self.hourlyCost.append(curCost)
            self.hourlyProfit.append(curProfit)
            self.runingCost = self.runingCost + (curCost)
            self.yearlyProfit = self.yearlyProfit + curProfit
            self.yearlyCost = self.runingCost
            self.yearlyIncome = self.yearlyIncome + curIncome
            if(self.maxCapacity>0.00001):
                self.estimatedROI = ((self.yearlyProfit) * self.lifetime)/(self.totalLifeCAPEX) 
            else:
                self.estimatedROI = 0.0
            self.NPV = 0.0
            for yr in range(5): # for yr in range(self.year, self.endYear):
                self.NPV = self.NPV +  self.yearlyProfit/((1+self.discountR)**yr)

            # subs/kW needed to get ROI of 0.5
            self.subsNeeded = ((0.5*self.totalLifeCAPEX) - (self.yearlyProfit * self.lifetime))/self.chargeRate


            self.NYyearlyCost = self.NYyearlyCost + NYCost
            self.NYyearlyProfit = self.NYyearlyProfit + NYProfit
            if(self.maxCapacity>0.00001):
                self.NYestimatedROI = ((self.NYyearlyProfit) * self.NEXTYEARlifetime)/(self.NEXTYEARtotalLifeCAPEX) 
            else:
                self.NYestimatedROI = 0.0
            self.NYNPV = 0.0
            for yr in range(5):
                self.NYNPV = self.NYNPV +  self.NYyearlyProfit/((1+self.discountR)**yr)

    # method to record data and calculate profitability
    def recordHourInfo(self,energy, boolCharge, boolDischarge, hour):
        fixedOM = self.fixedOandMPerHour # GBP/hr
        capital = self.capitalCostPerHour # GBP/hr

        
        if(boolDischarge):
            variableOM = self.variableOandMCost * energy # GBP/kWh * kWh
            curIncome = self.wholesaleEPriceProf[hour]*energy 
            chargeCost = 0.0
            self.curYearDischargeKWh = self.curYearDischargeKWh + energy
            marginC = self.variableOandMCost

            NYvariableOM = self.NEXTYEARvariableOandMCost * energy
            self.chargeBoolProf.append(-1)
            self.chargeProf.append(abs(energy))
        elif(boolCharge):
            variableOM = self.variableOandMCost * energy
            curIncome = 0
            chargeCost = self.wholesaleEPriceProf[hour]*energy
            marginC=0.0

            NYvariableOM = self.NEXTYEARvariableOandMCost * energy
            self.chargeBoolProf.append(1)
            self.chargeProf.append(abs(energy))
        else:

            variableOM = 0.0
            curIncome = 0
            chargeCost = 0.0
            marginC=0.0
            NYvariableOM = 0.0
            self.chargeBoolProf.append(0)
            self.chargeProf.append(0.0)



        curIncome = curIncome + ((self.capitalSub*self.dischargeRate)/(365*24))
        curCost =fixedOM + variableOM  + capital + chargeCost
        curProfit = curIncome-curCost

        self.marginalCost.append(marginC)

        NYCost = self.NEXTYEARfixedOandMPerHour + NYvariableOM + self.NEXTYEARcapitalCostPerHour + chargeCost
        NYProfit = curIncome - NYCost
        
        self.hourlyCost.append(curCost)
        self.hourlyProfit.append(curProfit)
        self.runingCost = self.runingCost + (curCost)
        self.yearlyProfit = self.yearlyProfit + curProfit
        self.yearlyCost = self.runingCost
        self.yearlyIncome = self.yearlyIncome + curIncome
        self.yearlyCapSubs = self.capSubKWCap * self.dischargeRate
        if(self.maxCapacity>0.00001):
            self.estimatedROI = ((self.yearlyProfit) * self.lifetime)/(self.totalLifeCAPEX) 
        else:
            self.estimatedROI = 0.0
        self.NPV = 0.0
        for yr in range(5): # for yr in range(self.year, self.endYear):
            self.NPV = self.NPV +  self.yearlyProfit/((1+self.discountR)**yr)

        # subs/kW needed to get ROI of 0.5
        self.subsNeeded = ((0.5*self.totalLifeCAPEX) - (self.yearlyProfit * self.lifetime))/self.chargeRate


        self.NYyearlyCost = self.NYyearlyCost + NYCost
        self.NYyearlyProfit = self.NYyearlyProfit + NYProfit
        if(self.maxCapacity>0.00001):
            self.NYestimatedROI = ((self.NYyearlyProfit) * self.NEXTYEARlifetime)/(self.NEXTYEARtotalLifeCAPEX) 
        else:
            self.NYestimatedROI = 0.0
        self.NYNPV = 0.0
        for yr in range(5):
            self.NYNPV = self.NYNPV +  self.NYyearlyProfit/((1+self.discountR)**yr)
        
    # reset values at the end of the year
    def resetYearValueRecord(self):
        profWithCapSubs = self.yearlyCapSubs + self.yearlyProfit
        
        self.yearlyProfitList.append(profWithCapSubs)
        self.yearlyIncomeList.append(self.yearlyIncome)
        self.yearlyCostList.append(self.yearlyCost)
        self.years.append(self.year)
        self.year = self.year + 1
        self.age = self.age + 1
        self.curYearDischargeKWh = 0.0

        tempIndx = self.year - self.BASEYEAR
        self.updateNextYearCosts(tempIndx)

        self.subsNeeded = 0.0
        self.yearlyEnergyGen=0.0
        self.hourlyProfit = list()
        self.yearlyProfit=0.0
        self.yearlyIncome = 0.0
        self.yearlyCost = 0.0
        self.runingCost=0.0
        self.hourlyCost = list()
        self.hourlyStorage = list()
        self.NYyearlyCost = 0.0
        self.NYyearlyProfit = 0.0
        self.chargeBoolProf = list()
        self.chargeProf = list()
        self.marginalCost = list()
        

    def getMaxCap(self):
        return self.maxCapacity

    def getCurCap(self):
        return self.curCapacity
    
    def getChargeRate(self):
        return self.chargeRate
    
    def getDischargeRate(self):
        return self.dischargeRate
    


    def graph(self):
        import matplotlib.pyplot as plt
        graphStore,storeUnit = Utils.checkUnits(self.hourlyStorage)
        fig, axs = plt.subplots(2,1)
        fig.suptitle(self.name, fontsize=20)
        axs[0].plot(graphStore)
        axs[0].set_ylabel('Storage Capacity ('+storeUnit+'h)')
        fig.show()



    
    









        
        
