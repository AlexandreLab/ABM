import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils

class energyStorage():
    
    
    def __init__(self,capacity,chargeRate,dischargeRate, year,NumBus, BASEYEAR):

        self.age = 0.0
        self.BASEYEAR = BASEYEAR
        self.year = year
        self.busbar = NumBus
        self.capitalSub = 0.0 #50.0 # variable for subsidies, unit GBP per kW cap per year
        
        self.discountR = 0.1
        self.opCostPkW = 0.14 # generation cost for 1kW GBP
        self.estimatedROI = 0.0
        self.NPV = 0.0
            
        self.maxCapacity = capacity
        self.curCapacity = 0.0
        self.chargeRate = chargeRate
        self.dischargeRate = dischargeRate
        self.hourlyStorage = np.array(8760) # real-time SoC
        self.hourlyEnergyExchange = np.array(8760)
        self.name = 'Battery Storage'
        self.capSubKWCap = 0.0 # cap market
        self.GBmaxBuildRate = 590000.0 # kW
        self.maxBuildRate = 590000.0/56 # 56 companies in model

        self.subsNeeded = 0.0
        self.curYearDischargeKWh = 0.0
        self.yearlyProfit=0.0
        self.yearlyIncome = 0.0
        self.yearlyCost = 0.0
        self.NYyearlyCost = 0.0
        self.NYyearlyProfit = 0.0

        self.marginalCost = np.zeros(8760)

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

        self.wholesaleEPriceProf = np.zeros(8760)

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
        self.curWholesaleElecPrice = np.mean(self.wholesaleEPriceProf)


    def chargingDischargingBattery(self, arr_chargeRate, arr_dischargeRate, netDemand):
        arr_charge = arr_chargeRate*self.maxCapacity # how much we want to charge by
        arr_charge = arr_charge.clip(max=self.chargeRate) #cap it to the max chargeRate

        arr_discharge = arr_dischargeRate*self.maxCapacity # how much we want to charge by
        arr_discharge = arr_discharge.clip(max=self.dischargeRate) #cap it to the max dischargeRate
        arr_discharge = np.min([arr_discharge, netDemand], axis=0)  # we should not discharge more than the demand
        
        curCapacity = 0
        list_energyStored = []
        list_curCapacity = []
        for val in np.subtract(arr_charge, arr_discharge):
            energyStored = val
            if val>0: #charging
                if curCapacity+val>=self.maxCapacity: # battery is full
                    energyStored = self.maxCapacity-self.curCapacity
                    curCapacity = self.maxCapacity
                else:
                    curCapacity = curCapacity + energyStored
            else: #discharging
                if curCapacity-val<= 0: # battery is empty
                    energyStored = -curCapacity
                    curCapacity = 0
                else:
                    curCapacity = curCapacity + energyStored
            list_energyStored.append(energyStored)
            list_curCapacity.append(curCapacity)

        self.hourlyEnergyExchange = np.array(list_energyStored) #+charging, -discharging
        self.hourlyStorage = np.array(list_curCapacity)
         
        #return the netDemand minus what was stored in the battery and what was released from the battery
        return np.subtract(netDemand, -self.hourlyEnergyExchange)

    def updateProfit(self, wholesaleProf=[]):
        if len(wholesaleProf)>0:
            self.wholesaleEPriceProf = wholesaleProf.copy()

        arr_hourlyVariableOM = np.absolute(self.hourlyEnergyExchange) * self.variableOandMCost

        arr_hourlyIncome = self.hourlyEnergyExchange.copy() # Income occurs when discharging the battery
        arr_hourlyIncome = -arr_hourlyIncome.clip(max=0) #remove the values when the battery is charging
        arr_hourlyIncome = np.multiply(arr_hourlyIncome, self.wholesaleEPriceProf) + ((self.capitalSub*self.dischargeRate)/(365*24))

        arr_hourlyChargeCost = self.hourlyEnergyExchange.copy() # Charging cost occurs when charging the battery
        arr_hourlyChargeCost = arr_hourlyChargeCost.clip(min=0) #remove the values when the battery is discharging
        arr_hourlyChargeCost = np.multiply(arr_hourlyChargeCost, self.wholesaleEPriceProf)

        arr_hourlyCost = np.add(arr_hourlyChargeCost, arr_hourlyVariableOM) + self.capitalCostPerHour + self.fixedOandMPerHour
        arr_hourlyProfit = np.subtract(arr_hourlyIncome, arr_hourlyCost)

        arr_NYhourlyVariableOM = np.absolute(self.hourlyEnergyExchange) * self.NEXTYEARvariableOandMCost
        arr_NYhourlyCost = np.add(arr_hourlyChargeCost, arr_NYhourlyVariableOM) + self.NEXTYEARcapitalCostPerHour + self.NEXTYEARfixedOandMPerHour
        arr_NYhourlyProfit = np.subtract(arr_hourlyIncome, arr_NYhourlyCost)

        self.marginalCost = np.zeros(8760)
        self.marginalCost[np.where(self.hourlyEnergyExchange<0)] = self.variableOandMCost

        self.runingCost = np.sum(arr_hourlyCost)
        self.yearlyProfit = np.sum(arr_hourlyProfit)
        self.yearlyCost = self.runingCost
        self.yearlyIncome = np.sum(arr_hourlyIncome)

        self.NYyearlyCost = np.sum(arr_NYhourlyCost)
        self.NYyearlyProfit = np.sum(arr_NYhourlyProfit)

        if(self.maxCapacity>0.00001):
            self.estimatedROI = ((self.yearlyProfit) * self.lifetime)/(self.totalLifeCAPEX) 
        else:
            self.estimatedROI = 0.0
        self.NPV = 0.0
        for yr in range(5): # for yr in range(self.year, self.endYear):
            self.NPV = self.NPV +  self.yearlyProfit/((1+self.discountR)**yr)

        # subs/kW needed to get ROI of 0.5
        self.subsNeeded = ((0.5*self.totalLifeCAPEX) - (self.yearlyProfit * self.lifetime))/self.chargeRate
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

        
    




    
    









        
        
