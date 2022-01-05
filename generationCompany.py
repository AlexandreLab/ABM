import random
from random import randint
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

class generationCompany():
    
    
    def __init__(self,timeSteps, companyType, companyID):

        self.initialise(timeSteps, companyType, companyID)

    def __init__(self,timeSteps):

        self.initialise(timeSteps, 1, 1)
        

    def initialise(self,timeSteps, companyType, companyID):
        file2 = open("BASEYEAR.txt", "r") 
        temp = file2.read()
        self.BASEYEAR = int(temp)
        file2.close()
        
        self.timeSteps = timeSteps
        self.companyID = companyID
        self.companyType = companyType
        self.opCostPkW = 0.14 # ignore***
        self.opEmissionsPkW = 1.0 # ignore***
        self.heatGenerated = list()
        self.genCapacity = 1E11
        self.hourlyCost = list()
        self.hourlyEmissions = list()
        self.runingCost=0.0
        self.runingEmissions=0.0
        self.totalEmissionsYear = 0.0 # total emissions of all technologies for cur year
        self.name = 'Generation Company '+ str(self.companyID)+': '
        self.elecLoss = 0.0 #0.1
        self.CFDPrice = 0.0 #0.12
        self.CFDPriceChange = 0.0

        self.traditionalGen = list()
        self.renewableGen = list()
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

        self.year = self.BASEYEAR
        self.years = list()

        self.energyStores = list()
        battery = energyStorage(10000,1000,500,self.year, random.randint(1,30)) # need to give values
        self.energyStores.append(battery)
        carbonFilePath = 'CarbonPrice/carbonPrice'+str(self.BASEYEAR)+'_2050.txt'
        self.yearlyCarbonCost = Utils.loadTextFile(carbonFilePath)
        self.CarbonCost = self.yearlyCarbonCost[0]

    def calcRevenue(self, wholesaleProf): # method to recalculate profit for all plants
        for i in range(len(self.traditionalGen)):
            self.traditionalGen[i].updateProfit(wholesaleProf)
        for i in range(len(self.renewableGen)):
            self.renewableGen[i].updateProfit(wholesaleProf)
        for i in range(len(self.energyStores)):
            self.energyStores[i].updateProfit(wholesaleProf)
        try:
            self.estimateBattery.updateProfit(wholesaleProf)
        except Exception as err:
            a = 1
            


    def getRenewableGen(self): # Get renewable gen for current year
        self.renewGens = list()#hourly profile for each type
        yearGenPerTechData = list()
        yearGenPerTechLabels = list()
        
        for rg in range(len(self.renewableGen)): #by type
            curRenewGen = self.renewableGen[rg].getGeneration() # return to the generation profile for each technology
          #  renewableGen[rg].graph() # graph hourly generation for each technology, hydro, solar, etc
            self.renewGens.append(curRenewGen)
            yearGenPerTechData.append(self.renewableGen[rg].yearlyEnergyGen) #each rg call the class once
            yearGenPerTechLabels.append(self.renewableGen[rg].name)

        self.totalRenewGen = list() # all electricity from renewables - losses
        for g in range (len(self.renewGens[0])): # loop through hours
            sumGen= 0.0
            for i in range (len(self.renewGens)): # loop through renewable gen sources
                sumGen = sumGen + self.renewGens[i][g]
            sumGen = sumGen * (1-self.elecLoss)
            self.totalRenewGen.append(sumGen)
                
        return self.renewGens, yearGenPerTechData, yearGenPerTechLabels, self.totalRenewGen



    # method to charge/ discharge battery and return net demand - battery
    def chargeDischargeBatteryTime(self, totalCustDemand):
        self.totalCustDemand = totalCustDemand # required energy charge to battery
        self.netDemand=list()

        tempDemand = totalCustDemand.copy()
        avg24HrNetDList = list()
        temp24NetD = list()
        for n in range (len(totalCustDemand)): # loop each hour
            time = n%24
            if((time==0 and n>0) or n== len(totalCustDemand)-1):
                avgNetD = statistics.mean(temp24NetD)
                avg24HrNetDList.append(avgNetD)#account for average value every 24 hr
                temp24NetD = list()#clear
            else:
                temp24NetD.append(totalCustDemand[n])#add to this list for calculating aforemented average

   #     print('len avg24HrNetDList',len(avg24HrNetDList))
        batteryChargeProf = list()
        for d in range (365):
        #    print('d',d)
         #   print('len avg24HrNetDList',len(avg24HrNetDList))
            avgND = avg24HrNetDList[d]
            diff24 = list()
            sumNeg = 0.0
            sumPos = 0.0
            for h in range (24):
                n = (d*24) + h
                curNetD = tempDemand[n]
                cDiff = curNetD - avgND
                if(cDiff<0):
                    sumNeg = sumNeg + cDiff
                elif(cDiff>0):
                    sumPos = sumPos + cDiff
                
                diff24.append(cDiff)

            for h in range (24):
                if(diff24[h]<0 and abs(sumNeg)>1):#charging
                    chargeFrac = diff24[h]/ abs(sumNeg)
                elif(diff24[h]<0 and abs(sumNeg)<1):
                    chargeFrac = 0.0
                elif(diff24[h]>0 and abs(sumPos)>1):#discharging
                    chargeFrac = diff24[h]/ abs(sumPos)
                else:
                    chargeFrac = 0.0
                batteryChargeProf.append(chargeFrac)
   #     print('len batteryChargeProf',len(batteryChargeProf))
                
        for n in range (len(totalCustDemand)): # loop each hour
            time = n%24
            chargeHours = list()
            dischargeHours = list()
           
                
            if(batteryChargeProf[n]<-0.001): # charging 
                for s in range(len(self.energyStores)):
                    energyConsumed = self.energyStores[s].chargeBatteryFrac(n, abs(batteryChargeProf[n]))
                    tempDemand[n] = tempDemand[n]+energyConsumed


            elif(batteryChargeProf[n]>0.001): # discharging
                for s in range(len(self.energyStores)):
                    var, energyDischarge = self.energyStores[s].dischargeBatteryFrac(n, tempDemand[n], abs(batteryChargeProf[n]))
                    tempDemand[n] = tempDemand[n] - energyDischarge

            elif(abs(batteryChargeProf[n])<=0.001):
                for s in range(len(self.energyStores)):
                    self.energyStores[s].maintainCapacity(n)
                
        self.netDemand = tempDemand.copy()
        
       # if(len(self.energyStores)==0):
        self.estimatePotentialBatteryProfit(totalCustDemand, batteryChargeProf)

        
        for h in range(len(self.netDemand)):
            if(self.netDemand[h]<0): # renewable generation > energy demand
                self.netDemand[h] = 0.0
        return self.netDemand

    
    '''
    # method to charge/ discharge battery and return net demand - battery
    def chargeDischargeBatteryTime(self, totalCustDemand):
        self.totalCustDemand = totalCustDemand
        self.netDemand=list()

        tempDemand = totalCustDemand.copy()
        for n in range (len(totalCustDemand)): # loop each hour
            time = n%24
            chargeHours = list()
            dischargeHours = list()
            if(self.batteryDuration==3):
                chargeHours.append(3)
                chargeHours.append(4)
                chargeHours.append(5)
                dischargeHours.append(17)
                dischargeHours.append(18)
                dischargeHours.append(19)
            elif(self.batteryDuration==5):
                chargeHours.append(3)
                chargeHours.append(4)
                chargeHours.append(5)
                chargeHours.append(1)
                chargeHours.append(2)
                dischargeHours.append(17)
                dischargeHours.append(18)
                dischargeHours.append(19)
                dischargeHours.append(16)
                dischargeHours.append(20)
            elif(self.batteryDuration==7):
                chargeHours.append(3)
                chargeHours.append(4)
                chargeHours.append(5)
                chargeHours.append(1)
                chargeHours.append(2)
                chargeHours.append(0)
                chargeHours.append(23)
                dischargeHours.append(17)
                dischargeHours.append(18)
                dischargeHours.append(19)
                dischargeHours.append(16)
                dischargeHours.append(20)
                dischargeHours.append(15)
                dischargeHours.append(9)
                
            if(time in chargeHours): 
                for s in range(len(self.energyStores)):
                    energyConsumed = self.energyStores[s].chargeBatteryMax(n)
                    tempDemand[n] = tempDemand[n]+energyConsumed


            if(time in dischargeHours):
                for s in range(len(self.energyStores)):
                    var, energyDischarge = self.energyStores[s].dischargeBatteryMax(n, tempDemand[n])
                    tempDemand[n] = tempDemand[n] - energyDischarge

            else:
                for s in range(len(self.energyStores)):
                    self.energyStores[s].maintainCapacity(n)
                
        self.netDemand = tempDemand.copy()
        
       # if(len(self.energyStores)==0):
        self.estimatePotentialBatteryProfit(totalCustDemand, chargeHours,dischargeHours)

        
        for h in range(len(self.netDemand)):
            if(self.netDemand[h]<0): # renewable generation > energy demand
                self.netDemand[h] = 0.0
        return self.netDemand
    '''

    # if company has no battery capacity, this method will estimate POTENTIAL battery profit
    def estimatePotentialBatteryProfit(self,totalCustDemand, batteryChargeProf):
        tempCharge = 590000.0/56
        tempKWh = tempCharge*self.batteryDuration # 3 hours to charge from empty
        self.estimateBattery = energyStorage(tempKWh,tempCharge,tempCharge,self.year,random.randint(1,30))
        priceProfile = self.traditionalGen[0].wholesaleEPriceProf
        self.estimateBattery.setWholesaleElecPrice(priceProfile)
        
        for n in range (len(totalCustDemand)): # loop each hour
            time = n%24
            if(batteryChargeProf[n]<-0.001): # charging
                energyConsumed = self.estimateBattery.chargeBatteryFrac(n, abs(batteryChargeProf[n]))
            elif(batteryChargeProf[n]>0.001):
                var, energyDischarge = self.estimateBattery.dischargeBatteryFrac(n, totalCustDemand[n], abs(batteryChargeProf[n]))
            elif(abs(batteryChargeProf[n])<=0.001):
                self.estimateBattery.maintainCapacity(n)

    # set wholesale electricity price
    def setBatteryWholesalePrice(self):
        priceProfile = self.traditionalGen[0].wholesaleEPriceProf
        for i in range(len(self.energyStores)):
            self.energyStores[i].setWholesaleElecPrice(priceProfile)

    # reset values at the end of a year
    def resetYearlyValues(self):
        for i in range(len(self.energyStores)):
            self.energyStores[i].resetYearValueRecord()

        for i in range(len(self.traditionalGen)):
            self.traditionalGen[i].resetYearValueRecord()

        for i in range(len(self.renewableGen)):
            self.renewableGen[i].resetYearValueRecord()
            
        for i in range(len(self.renewableGen)):
            self.renewableGen[i].recalcEconomics()

    # get generation from a particular plant, e.g. CCGT plant 2
    def getTraditionalGeneration(self, genIndx, curNetD):
        curGen,newNetD, excessGen = self.traditionalGen[genIndx].getGeneration(curNetD)
        return curGen, newNetD, excessGen

    # get generation from specific technology type ,e.g. CCGT
    def getTraditionalGenerationByType(self, genType, curNetD):
        tempNetD = curNetD.copy()
        sumGen = 0.0
        totExcessGen = list()
        hourGenProf = list()
        for i in range(len(self.traditionalGen)):
            if(self.traditionalGen[i].genType==genType):
                curGen,newNetD, curExcessGen = self.getTraditionalGeneration(i, tempNetD)
                sumGen = sumGen + sum(curGen)
                tempNetD = list()
                tempNetD = newNetD
                if(len(hourGenProf)==0):
                    hourGenProf = curGen.copy()
                else:
                    for k in range(len(hourGenProf)):
                        val = hourGenProf[k]
                        hourGenProf[k] = val + curGen[k] #accumulate by each type

                if(len(totExcessGen)==0):
                    totExcessGen = curExcessGen.copy()
                else:
                    for j in range(len(totExcessGen)):
                        totExcessGen[j] = totExcessGen[j] + curExcessGen[j]
        return sumGen, newNetD, totExcessGen, hourGenProf

    # calculate yearly profit
    def calculateYearlyProfit(self):
        self.totalEmissionsYear = 0.0
        for i in range(len(self.traditionalGen)):
            self.traditionalGen[i].calcProfitPerKWh()
            self.totalEmissionsYear = self.totalEmissionsYear + self.traditionalGen[i].runingEmissions #running emissions is yearly value
        for i in range(len(self.renewableGen)):
            self.renewableGen[i].calcProfitPerKWh()
            self.totalEmissionsYear = self.totalEmissionsYear + self.renewableGen[i].runingEmissions

    # get capacity of all battery storage in kW. In here, capacity id discharge
    def getBatteryCapKW(self):
        totalCapKW = 0.0
        for i in range(len(self.energyStores)):
            totalCapKW = totalCapKW + self.energyStores[i].dischargeRate
        return totalCapKW

    # make decision to invest in battery
    def updateCapacityDecisionBattery(self):
        print('battery decision method')
        # invest in new batteries
        newInvestment = False
        batterySubsNeeded = list()
        batterySubsNeeded.append(self.year)
        batterySubsNeeded.append(self.estimateBattery.subsNeeded)

        # do we already have bettery to assess profitability of
        if(len(self.energyStores)>0):
    #        for i in range(len(self.energyStores)):
    #            batterySubsNeeded.append(self.energyStores[i].subsNeeded)
            if((self.energyStores[0].maxBuildRate - self.curYearBatteryBuild)>10):
                print('under max build rate')
                for i in range(len(self.energyStores)):
                    print('Est next year battery ROI ',self.energyStores[i].NYestimatedROI)
               #     if(self.energyStores[i].estimatedROI>0.5 and (not newInvestment)):
                    if(self.energyStores[i].NYestimatedROI>0.5 and (not newInvestment)):
                        print('suitable battery investment')
                        print('ROI ',self.energyStores[i].NYestimatedROI)
                        self.addBatterySize(self.energyStores[i].maxBuildRate)
                        self.curYearBatteryBuild = self.energyStores[i].maxBuildRate
                        newInvestment = True
        else: # use test battery to estimate profitability
            print('No existing battery storage')
     #       batterySubsNeeded.append(self.estimateBattery.subsNeeded)
            if((self.estimateBattery.maxBuildRate - self.curYearBatteryBuild)>10):
                print('under max build rate')
                if(self.estimateBattery.NYestimatedROI>0.5 and (not newInvestment)):
                    print('suitable battery investment')
                    print('ROI ',self.estimateBattery.NYestimatedROI)
                    self.addBatterySize(self.estimateBattery.maxBuildRate)
                    self.curYearBatteryBuild = self.estimateBattery.maxBuildRate
                    newInvestment = True
                
        print('investment in new battery ',newInvestment)
   #     tempYear = list()
    #    tempYear.append(self.year)
   #     self.yearlyBatterySubsNeeded.append(tempYear)
        self.yearlyBatterySubsNeeded.append(batterySubsNeeded)

        # remove old batteries
        i = 0
        while(i<len(self.energyStores) and len(self.energyStores)>0):
            if(self.energyStores[i].age>self.energyStores[i].lifetime):
                print('removed old battery')
                self.energyStores.pop(i)
            else:
                i = i+1

        # if we want to remove unprofitable battery, uncomment code below
        '''
        i=0
        removed = False
        yearsWait = 8 
        while(i <len(self.energyStores) and len(self.energyStores)>0): 
            count = 0
            tcount=0
            for j in reversed (self.energyStores[i].yearlyProfitList): # loop through yearly profits from most recent
                tcount+=1
                if(not removed):
                    if(j<-10 and self.energyStores[i].maxCapacity>10): # if not profitable and not one of the gens with zero capacity
                        # use -10 not 0 because there may be rounding errors when using subsidies to make profitable
                        count +=1
                        
                    # if not profitable for x years and no plant has been removed yet
                    if(count== yearsWait and tcount== yearsWait and not removed): 
                        print('Removing Unprofitable Battery')
                        print('Profit ',self.energyStores[i].yearlyProfitList)
                        print('type ',self.energyStores[i].name)
                        print('capacity ',self.energyStores[i].maxCapacity)
                        del self.energyStores[i]
                        removed = True
            i=i+1
        '''


    # make decision to invest in new generation plants 
    def updateCapacityDecision(self, peakDemand, boolEnergyStorage,OneYearHeadroom):
        # make decision for battery first
        if(self.year>=2018 and boolEnergyStorage):
            print('suitable year to consider battery')
            self.updateCapacityDecisionBattery() # decide on battery investment
            self.curYearBatteryBuild = 0.0 # set to 0 for next year
              
        TECHFILENAME = 'GEN_TYPE_LIST.txt'
        file2 = open(TECHFILENAME, "r") 
        technologyList = file2.read().split('\n')
        file2.close()
        technologyList.pop()
        
        self.getCapacityMargin(peakDemand)
        capacityMargin = self.capacityMargin
        deRatedCapacityMargin = self.deRatedCapacityMargin

        self.getTotalCapacity()
        self.yearlyTotalCapacity.append(self.totalCapacity)
        self.yearlyDeRatedCapacity.append(self.deRatedCapacity)
        self.years.append(self.year)

        tempCapM, tempCapMUnit = Utils.checkSingleValUnit(capacityMargin)
        tempDCapM, tempDCapMUnit = Utils.checkSingleValUnit(deRatedCapacityMargin)
        
        highROIsTradGenType, highROIsTradGenTypeINDX, highROIsRenGenType, highROIsRenGenTypeINDX = self.getHighestROIPerTech()
        technologyList, totCurYearCapInvest = Utils.getCurYearCapInvest()

        # make decision for traditional generation technologies 
        for i in range(len(highROIsTradGenType)):
            newCapList = list()
            
            if(highROIsTradGenType[i]>0.5):
                gen = self.traditionalGen[highROIsTradGenTypeINDX[i]]
                tGenName = gen.name
                indx = technologyList.index(tGenName)
                curCapInvest = totCurYearCapInvest[indx] # how much has already been invested in that technology
                maxAllowedCapInvest = gen.GBmaxBuildRate - float(curCapInvest) 
                tNumBus = gen.numbus
                tRenewableID = 0
                tCapacityKW = gen.genCapacity
                tStartYear = self.year + gen.constructionTime
                tEndYear = tStartYear + gen.lifetime
                tAge = 0
                optCap = self.estimateOptimalCapacity(gen, maxAllowedCapInvest)
                if(optCap>0):
                    print('Adding new capacity')
                    self.addToConstructionQueue(tGenName, tRenewableID, optCap, tStartYear, tEndYear, tAge, 0.0, False, False, tNumBus)
                    tempCapList = Utils.addToCapGenList(tGenName, optCap,newCapList,technologyList)
                    newCapList = tempCapList
                    Utils.updateCurYearCapInvest(technologyList, newCapList)
                    print(tGenName)
                    print('Capacity ',tCapacityKW)
                    print('Cur ROI ',highROIsTradGenType[i])
                
        # renewable investment decision
        for i in range(len(highROIsRenGenType)):
            newCapList = list()
            gen = self.renewableGen[highROIsRenGenTypeINDX[i]]
            tGenName = gen.name

            if(highROIsRenGenType[i]>0.5 and len(technologyList)>0):
                gen = self.renewableGen[highROIsRenGenTypeINDX[i]]
                tGenName = gen.name
                indx = technologyList.index(tGenName)
                if (len(totCurYearCapInvest)>0):
                    curCapInvest = totCurYearCapInvest[indx] # how much has already been invested in that technology
                    maxAllowedCapInvest = gen.GBmaxBuildRate - float(curCapInvest) 
                else:
                	maxAllowedCapInvest = gen.GBmaxBuildRate
                tNumBus = gen.numbus
                tRenewableID = 1
                tCapacityKW = gen.genCapacity
                tStartYear = self.year + gen.constructionTime
                tEndYear = tStartYear + gen.lifetime
                tAge = 0
                optCap = self.estimateOptimalCapacity(gen, maxAllowedCapInvest)

                if(optCap>0):
                    print('Adding new capacity')
                    self.addToConstructionQueue(tGenName, tRenewableID, optCap, tStartYear, tEndYear, tAge, 0.0, False, False, tNumBus)
                    tempCapList = Utils.addToCapGenList(tGenName, optCap,newCapList,technologyList)
                    newCapList = tempCapList
                    Utils.updateCurYearCapInvest(technologyList, newCapList)
                    print(tGenName)
                    print('Capacity ',tCapacityKW)
                    print('Cur ROI ',highROIsRenGenType[i])

        self.recordYearlyCapacity()
        # remove old and unprofitable generation plants
        self.removeOldCapacity()
        self.removeUnprofitableCapacity()
        self.year = self.year + 1
        # add any new plants that are in the construction queue and are meant to come online
        self.checkConstructionQueue(OneYearHeadroom)
        
    # estimate optmum capacity of a plant
    def estimateOptimalCapacity(self, generator, maxAllowedCapInvest):
        curCap = generator.genCapacity
        curCost = generator.yearlyCost
        curRevenue = generator.yearlyIncome
        curProfit = generator.yearlyProfit
        curEnGen = generator.yearlyEnergyGen
        actualCapFactor = generator.getActCapFactor() #yearly energy generated/max energy generated by capacity
        #print('actualCapFactor ',actualCapFactor)
        curROI = generator.estimatedROI

        suitableCapFound=False

        # initialize optimum as current capacity
        optimalCap = curCap
        optimalROI = curROI
        optimalProfit = curProfit

        if(optimalCap>generator.maxBuildRate):
            optimalCap = generator.maxBuildRate
        

        name = generator.name
        RenBool = generator.renewableBool
        if(RenBool): # renewable
            minGenSize = 10000 # 10MW
        else:
            minGenSize = 500000 # 500 MW
            
        # assume same capacity factor
        estCapFactor = actualCapFactor
        for i in range(10000,(generator.maxBuildRate+10000),10000):
            estCap = i
            estEnGen = estCapFactor * estCap * 24*365
            
            estFixOM = generator.fixedOandMCost * estCap #yearly
            estVarOM = generator.variableOandMCost * estEnGen
            estCapital = (generator.capitalCost*estCap)/generator.lifetime
            
            estCost = curCost * (estCap/curCap)
            estRevenue = curRevenue * (estCap/curCap) # yearly
            estProfit = estRevenue - estCost
            estROI = (estProfit * generator.lifetime)/(generator.capitalCost*estCap)


            if((estROI>=curROI or abs(estROI-curROI)<0.00001) and (estCap< maxAllowedCapInvest)):
                optimalCap = estCap
                optimalROI = estROI
                optimalProfit = estProfit
                suitableCapFound = True
                    
        
        # assume same energy generated but check
        # if operating at a low capacity factor
        '''
        if(actualCapFactor<generator.capacityFactor):
            estCapFactor = generator.capacityFactor
            estEnGen = curEnGen
            estCap = estEnGen/(estCapFactor*24*365)
            estRevenue = curRevenue
            capDiff = curCap - estCap
            estCost = curCost - ((capDiff*generator.fixedOandMCost)+((generator.capitalCost*capDiff)/generator.lifetime))
            estProfit = estRevenue - estCost
            estROI = (estProfit * generator.lifetime)/(generator.capitalCost*estCap)
            optimalCap = estCap
            optimalROI = estROI
            optimalProfit = estProfit


        # otherwise if plant cap factor is close to max, we should build more
        if(abs(actualCapFactor-generator.capacityFactor)<0.1):
            if(curCap*1.5<generator.maxBuildRate):
                estCap = curCap*1.5
                estROI = curROI*1.5
                estProfit = curProfit*1.5
            else:
                estCap = generator.maxBuildRate                
                estROI = curROI* (estCap/curCap)
                estProfit = curProfit* (estCap/curCap)
            
            optimalCap = estCap
            optimalROI = estROI
            optimalProfit = estProfit

        '''
        '''
        print('curCap ',curCap)
        print('curROI ',curROI)
        print('curProfit ',curProfit)
        print('optimalCap ',optimalCap)
        print('optimalROI ',optimalROI)
        print('optimalProfit ',optimalProfit)
        input('stop')
        '''
        if(optimalCap> maxAllowedCapInvest):
            return -1
        elif(not suitableCapFound):
            return -1
        else:
            return optimalCap
        

    # gent plant indices that have a NPV>0
    def getIndxOfPositiveNPVGens(self):
        profitableTradGen = list()
        profitableRenGen = list()
        
        profitableTradGenROI = list()
        profitableRenGenROI = list()

        for i in range(len(self.traditionalGen)):
            curROI, curNPV = self.traditionalGen[i].estimateROIandNPV(self.CFDPrice, self.CarbonCost, False)   
            if(curNPV>0):
                profitableTradGen.append(i)
                profitableTradGenROI.append(curROI)

        for i in range(len(self.renewableGen)):
            curROI, curNPV = self.renewableGen[i].estimateROIandNPV(self.CFDPrice, self.CarbonCost, False)
            if(curNPV>0):
                profitableRenGen.append(i)
                profitableRenGenROI.append(curROI)
        return profitableTradGen, profitableRenGen, profitableTradGenROI, profitableRenGenROI

    # get plants of each technology that have the highest ROI
    def getHighestROIPerTech(self):
        profitableTradGen, profitableRenGen, profitableTradGenROI, profitableRenGenROI = self.getIndxOfPositiveNPVGens()
        windOnshoreHighIndx = 0
        windOffshoreHighIndx = 0
        solarHighIndx = 0
        hydroHighIndx = 0


        
        windOnshoreHighROI = -1
        windOffshoreHighROI = -1
        solarHighROI = -1
        hydroHighROI = -1


        coalHighIndx = 0
        CCGTHighIndx = 0
        nuclearHighIndx = 0
        OCGTHighIndx = 0
        BECCSHighIndx = 0
        biomassHighIndx = 0
        hydrogenHighIndx = 0


        coalHighROI = -1
        CCGTHighROI = -1
        nuclearHighROI = -1
        OCGTHighROI = -1
        BECCSHighROI = -1
        biomassHighROI = -1        
        hydrogenHighROI = -1

        for i in range(len(profitableTradGenROI)):
            curTGen = self.traditionalGen[profitableTradGen[i]]
            if(curTGen.genType==0): # coal
                if(profitableTradGenROI[i]>coalHighROI):
                    coalHighROI = profitableTradGenROI[i]
                    coalHighIndx = profitableTradGen[i]
            elif(curTGen.genType==1): # CCGT
                if(profitableTradGenROI[i]>CCGTHighROI):
                    CCGTHighROI = profitableTradGenROI[i]
                    CCGTHighIndx = profitableTradGen[i]
            elif(curTGen.genType==2): # nuclear
                if(profitableTradGenROI[i]>nuclearHighROI):
                    nuclearHighROI = profitableTradGenROI[i]
                    nuclearHighIndx = profitableTradGen[i]
            elif(curTGen.genType==3): # OCGT
                if(profitableTradGenROI[i]>OCGTHighROI):
                    OCGTHighROI = profitableTradGenROI[i]
                    OCGTHighIndx = profitableTradGen[i]
            elif(curTGen.genType==4): # BECCS
                if(profitableTradGenROI[i]>BECCSHighROI):
                    BECCSHighROI = profitableTradGenROI[i]
                    BECCSHighIndx = profitableTradGen[i]
            elif(curTGen.genType==5): # biomass
                if(profitableTradGenROI[i]>biomassHighROI):
                    biomassHighROI = profitableTradGenROI[i]
                    biomassHighIndx = profitableTradGen[i]
            elif(curTGen.genType==6): # hydrogen
                if(profitableTradGenROI[i]>hydrogenHighROI):
                    hydrogenHighROI = profitableTradGenROI[i]
                    hydrogenHighIndx = profitableTradGen[i]


        for i in range(len(profitableRenGenROI)):
            curRGen = self.renewableGen[profitableRenGen[i]]
            if(curRGen.renewableType==0): # solar
                if(profitableRenGenROI[i]>solarHighROI):
                    solarHighROI = profitableRenGenROI[i]
                    solarHighIndx = profitableRenGen[i]
            elif(curRGen.renewableType==1): #** Wrong indx**
                input('Wrong renewable type, should be onshore or offshore wind')
            elif(curRGen.renewableType==2): # hydro
                if(profitableRenGenROI[i]>hydroHighROI):
                    hydroHighROI = profitableRenGenROI[i]
                    hydroHighIndx = profitableRenGen[i]

            elif(curRGen.renewableType==4): # Wind onshore
                if(profitableRenGenROI[i]>windOnshoreHighROI):
                    windOnshoreHighROI = profitableRenGenROI[i]
                    windOnshoreHighIndx = profitableRenGen[i]
            elif(curRGen.renewableType==5): # Wind offshore
                if(profitableRenGenROI[i]>windOffshoreHighROI):
                    windOffshoreHighROI = profitableRenGenROI[i]
                    windOffshoreHighIndx = profitableRenGen[i]
                

        highestROIsPerTradGenType = list()
        highestROIsPerRenGenType = list()
        highestROIsPerTradGenTypeINDX = list()
        highestROIsPerRenGenTypeINDX = list()

        if(coalHighROI>0):
            highestROIsPerTradGenType.append(coalHighROI)
            highestROIsPerTradGenTypeINDX.append(coalHighIndx)
        if(CCGTHighROI>0):
            highestROIsPerTradGenType.append(CCGTHighROI)
            highestROIsPerTradGenTypeINDX.append(CCGTHighIndx)
        if(nuclearHighROI>0):
            highestROIsPerTradGenType.append(nuclearHighROI)
            highestROIsPerTradGenTypeINDX.append(nuclearHighIndx)
        if(OCGTHighROI>0):
            highestROIsPerTradGenType.append(OCGTHighROI)
            highestROIsPerTradGenTypeINDX.append(OCGTHighIndx)
        if(BECCSHighROI>0):
            highestROIsPerTradGenType.append(BECCSHighROI)
            highestROIsPerTradGenTypeINDX.append(BECCSHighIndx)
        if(biomassHighROI>0):
            highestROIsPerTradGenType.append(biomassHighROI)
            highestROIsPerTradGenTypeINDX.append(biomassHighIndx)
        if(hydrogenHighROI>0):
            highestROIsPerTradGenType.append(hydrogenHighROI)
            highestROIsPerTradGenTypeINDX.append(hydrogenHighIndx)



        if(solarHighROI>0):
            highestROIsPerRenGenType.append(solarHighROI)
            highestROIsPerRenGenTypeINDX.append(solarHighIndx)
        if(hydroHighROI>0):
            highestROIsPerRenGenType.append(hydroHighROI)
            highestROIsPerRenGenTypeINDX.append(hydroHighIndx)

        if(windOnshoreHighROI>0):
            highestROIsPerRenGenType.append(windOnshoreHighROI)
            highestROIsPerRenGenTypeINDX.append(windOnshoreHighIndx)
        if(windOffshoreHighROI>0):
            highestROIsPerRenGenType.append(windOffshoreHighROI)
            highestROIsPerRenGenTypeINDX.append(windOffshoreHighIndx)

        return highestROIsPerTradGenType, highestROIsPerTradGenTypeINDX, highestROIsPerRenGenType, highestROIsPerRenGenTypeINDX


    # method to record yearly capacity
    def recordYearlyCapacity(self):
        renIndx,tradIndx = self.getGenIndxByType()#this is how many technology
        for i in range(len(renIndx)):
            capPerTech = list()
            derateCapPerTech = list()
            profitPerTech = list()
            revenuePerTech = list()
            costPerTech = list()
            emissionsPerTech = list()
            generationPerTech = list()
            
            sumCap = 0.0
            sumDeRCap = 0.0
            sumProfit = 0.0
            sumRevenue = 0.0
            sumCost = 0.0
            sumEmissions = 0.0
            sumGeneration = 0.0
            capFactor = 0.0
            for j in range(len(renIndx[i])):#
                sumCap = sumCap + self.renewableGen[renIndx[i][j]].genCapacity # i tech's jth plant
                sumDeRCap = sumDeRCap + (self.renewableGen[renIndx[i][j]].genCapacity* self.renewableGen[renIndx[i][j]].availabilityFactor)
                capFactor = self.renewableGen[renIndx[i][j]].capacityFactor
                sumProfit = sumProfit + self.renewableGen[renIndx[i][j]].yearlyProfit
                sumRevenue = sumRevenue + self.renewableGen[renIndx[i][j]].yearlyIncome
                sumCost = sumCost + self.renewableGen[renIndx[i][j]].yearlyCost
                sumEmissions = sumEmissions + 0.0
                sumGeneration = sumGeneration + self.renewableGen[renIndx[i][j]].yearlyEnergyGen

            if(self.year == self.BASEYEAR):
                capPerTech.append(sumCap)#i tech
                derateCapPerTech.append(sumDeRCap)
                profitPerTech.append(sumProfit)
                revenuePerTech.append(sumRevenue)
                costPerTech.append(sumCost)
                emissionsPerTech.append(sumEmissions)
                generationPerTech.append(sumGeneration)
                
                self.yearlyCapPerTech.append(capPerTech)
                self.yearlyDerateCapPerTech.append(derateCapPerTech)
                self.yearlyProfitPerTech.append(profitPerTech)
                self.yearlyRevenuePerTech.append(revenuePerTech)
                self.yearlyCostPerTech.append(costPerTech)
                self.yearlyEmissionsPerTech.append(emissionsPerTech)
                self.yearlyGenerationPerTech.append(generationPerTech)
                self.techNames.append(self.renewableGen[renIndx[i][0]].name)#technology name
            else:
                self.yearlyCapPerTech[i].append(sumCap)
                self.yearlyDerateCapPerTech[i].append(sumDeRCap)
                self.yearlyProfitPerTech[i].append(sumProfit)
                self.yearlyRevenuePerTech[i].append(sumRevenue)
                self.yearlyCostPerTech[i].append(sumCost)
                self.yearlyEmissionsPerTech[i].append(sumEmissions)
                self.yearlyGenerationPerTech[i].append(sumGeneration)

        for i in range(len(tradIndx)):
            capPerTech = list()
            derateCapPerTech = list()
            profitPerTech = list()
            revenuePerTech = list()
            costPerTech = list()
            emissionsPerTech = list()
            generationPerTech = list()
            
            sumCap = 0.0
            sumProfit = 0.0
            sumRevenue = 0.0
            sumCost = 0.0
            sumEmissions = 0.0
            sumGeneration = 0.0
            deRFactor = 0.0
            for j in range(len(tradIndx[i])):
                sumCap = sumCap + self.traditionalGen[tradIndx[i][j]].genCapacity
                deRFactor = self.traditionalGen[tradIndx[i][j]].availabilityFactor
                sumProfit = sumProfit + self.traditionalGen[tradIndx[i][j]].yearlyProfit
                sumRevenue = sumRevenue + self.traditionalGen[tradIndx[i][j]].yearlyIncome
                sumCost = sumCost + self.traditionalGen[tradIndx[i][j]].yearlyCost
                sumEmissions = sumEmissions + self.traditionalGen[tradIndx[i][j]].runingEmissions
                sumGeneration = sumGeneration + self.traditionalGen[tradIndx[i][j]].yearlyEnergyGen

            if(self.year == self.BASEYEAR):
                capPerTech.append(sumCap)
                derateCapPerTech.append(sumCap*deRFactor)
                profitPerTech.append(sumProfit)
                revenuePerTech.append(sumRevenue)
                costPerTech.append(sumCost)
                emissionsPerTech.append(sumEmissions)
                generationPerTech.append(sumGeneration)
                
                self.yearlyCapPerTech.append(capPerTech)
                self.yearlyDerateCapPerTech.append(derateCapPerTech)
                self.yearlyProfitPerTech.append(profitPerTech)
                self.yearlyRevenuePerTech.append(revenuePerTech)
                self.yearlyCostPerTech.append(costPerTech)
                self.yearlyEmissionsPerTech.append(emissionsPerTech)
                self.yearlyGenerationPerTech.append(generationPerTech)
                self.techNames.append(self.traditionalGen[tradIndx[i][0]].name)
            else:
                self.yearlyCapPerTech[i+len(renIndx)].append(sumCap)
                self.yearlyDerateCapPerTech[i+len(renIndx)].append(sumCap*deRFactor)
                self.yearlyProfitPerTech[i+len(renIndx)].append(sumProfit)
                self.yearlyRevenuePerTech[i+len(renIndx)].append(sumRevenue)
                self.yearlyCostPerTech[i+len(renIndx)].append(sumCost)
                self.yearlyEmissionsPerTech[i+len(renIndx)].append(sumEmissions)
                self.yearlyGenerationPerTech[i+len(renIndx)].append(sumGeneration)

        if(len(self.energyStores)>0):
            batteryKWh = self.getCurYearBatteryGenKWh()
            batteryKW = self.getTotalBatteryKW()
            self.yearlyStorageCapKW.append(batteryKW) # yearly discharge
            self.yearlyStorageGenKWh.append(batteryKWh)# yearly discharge
            batteryData = self.getTotalBatteryInfo() #cost and subs
            self.yearlyStorageCost.append(batteryData[0])
            self.yearlyStorageCapSubs.append(batteryData[1])
        else:
            self.yearlyStorageCapKW.append(0.0)
            self.yearlyStorageGenKWh.append(0.0)
            self.yearlyStorageCost.append(0.0)
            self.yearlyStorageCapSubs.append(0.0)


    # method to add plants to construction queue so that they come online after build time has completed
    def addToConstructionQueue(self, tGenName, tRenewableID, tCapacityKW, tStartYear, tEndYear, tAge, tcapSub, cfdBool, capMarketBool, BusNum):
        queuePlant = list()
        queuePlant.append(tGenName)
        queuePlant.append(tRenewableID)
        queuePlant.append(tCapacityKW)
        queuePlant.append(tStartYear)
        queuePlant.append(tEndYear)
        queuePlant.append(tAge)
        queuePlant.append(tcapSub)
        queuePlant.append(cfdBool)
        queuePlant.append(capMarketBool)
        queuePlant.append(BusNum)
        if(tGenName=='Nuclear' and self.year<2018):
            print('Not adding nuclear to construction queue before 2018')
        else:
            self.constructionQueue.append(queuePlant)

    # check plants that are in construction queue to see if ready to come online
    def checkConstructionQueue(self,OneYearHeadroom):
        i=0
        while(i <len(self.constructionQueue) and len(self.constructionQueue)>0):
            if(self.constructionQueue[i][3]==self.year): # start year is now
                name = self.constructionQueue[i][0]
                renewableID = self.constructionQueue[i][1]
                capacityKW = self.constructionQueue[i][2]
                startYear = self.constructionQueue[i][3]
                endYear = self.constructionQueue[i][4]
                age = self.constructionQueue[i][5]
                capitalSub = self.constructionQueue[i][6]
                cfdBool = self.constructionQueue[i][7]
                capMarketBool = self.constructionQueue[i][8]
                BusNum = self.constructionQueue[i][9]
                self.addGeneration(name, -1, renewableID, capacityKW, startYear, endYear, age, capitalSub, cfdBool, capMarketBool, BusNum, OneYearHeadroom[BusNum-1])
                del self.constructionQueue[i]
            else:
                i=i+1

    # method to remove old capacity whos age>lifetime
    def removeOldCapacity(self):
        i=0
        while(i <len(self.traditionalGen) and len(self.traditionalGen)>0):
            if(self.traditionalGen[i].endYear<=self.year):
                print('Removing Old Capacity')
                print('type ',self.traditionalGen[i].name)
                print('capacity ',self.traditionalGen[i].genCapacity)
                print('Cur Year: %s,   End Year: %s'%(str(self.year), str(self.traditionalGen[i].endYear)))
                del self.traditionalGen[i]
            else:
                i=i+1
        i=0
        while(i <len(self.renewableGen) and len(self.renewableGen)>0):
            if(self.renewableGen[i].endYear<=self.year):
                print('Removing Old Capacity')
                print('type ',self.renewableGen[i].name)
                print('capacity ',self.renewableGen[i].genCapacity)
                print('Cur Year: %s,   End Year: %s'%(str(self.year), str(self.renewableGen[i].endYear)))
                del self.renewableGen[i]
            else:
                i=i+1

    # method to remove unprofitable generation plants
    def removeUnprofitableCapacity(self):
        # remove at most 1 plant (renewable or non renewable) that is not profitable
        i=0
        removed = False
        yearsWait = 8 # number of years allowed to make a loss for before removed
        while(i <len(self.traditionalGen) and len(self.traditionalGen)>0): # go through all trad gens
            count = 0
            tcount=0
            for j in reversed (self.traditionalGen[i].yearlyProfitList): # loop through yearly profits from most recent
                tcount+=1
                if(not removed):
                    if(j<-10 and self.traditionalGen[i].genCapacity>10): # if not profitable and not one of the gens with zero capacity
                        # use -10 not 0 because there may be rounding errors when using subsidies to make profitable
                        count +=1
                        
                    # if not profitable for x years and no plant has been removed yet
                    if(count== yearsWait and tcount== yearsWait and not removed): 
                        print('Removing Unprofitable Capacity')
                        print('Profit ',self.traditionalGen[i].yearlyProfitList)
                        print('type ',self.traditionalGen[i].name)
                        print('capacity ',self.traditionalGen[i].genCapacity)
                        del self.traditionalGen[i]
                        removed = True
            i=i+1
            
        i=0
        while(i <len(self.renewableGen) and len(self.renewableGen)>0):
            count = 0
            tcount=0
            for j in reversed (self.renewableGen[i].yearlyProfitList):
                tcount+=1
                if(not removed):
                    if(j<-10 and self.renewableGen[i].genCapacity>10):
                        count +=1
                    if(count== yearsWait and tcount== yearsWait and not removed):
                        if(self.renewableGen[i].name =='Wind Offshore'):
                            print('Removing Unprofitable Capacity')
                            print('**** Offshore wind ****')
                            print('Profit ',self.renewableGen[i].yearlyProfitList)
                            print('type ',self.renewableGen[i].name)
                            print('capacity ',self.renewableGen[i].genCapacity)
                            print('StartYear ',self.renewableGen[i].startYear)
                            print('Age ',self.renewableGen[i].age)
                            print('CfD ',self.renewableGen[i].CFDPrice)
                        del self.renewableGen[i]
                        removed = True
            i=i+1


    # method to get bid for CFD auction
    def getCFDAuctionBid(self,busheadroom):
        bidType = list() # solar, biomass, etc
        bidPrice = list() # price
        bidCapacity = list() # 10000 kW, etc
        bidConstructionTime = list()
        makeBid = False
        bidbus = list()
        tempb = array(busheadroom)
        tempb = tempb.argsort()
        tempb = tempb.tolist()
        bussort = [i+1 for i in tempb]
        for i in range (len(self.renewableGen)):
            gen = self.renewableGen[i]
            name = gen.name
            curROI, curNPV = gen.estimateROIandNPV(self.CFDPrice, self.CarbonCost, False)

            if(gen.genCapacity>0.1 and (not name in bidType) and (not name == 'Solar') and (curROI<=0.5 or curNPV<0)): # making sure not a zero cap generator



               

                # get yearly costs for gen
                cap = gen.maxBuildRate
        # return to order of bus number
                
                windoffbus = [1,7,8,10,11,12,13,15,16,19,20,26,27,28,30]
                bussortwindoff = bussort.copy()
                for i in range(len(windoffbus)):
                    if(not bussortwindoff[i] in windoffbus):
                        bussortwindoff.pop(i)

                hydrobus = [1,3,4,5,6,7,8,9,10,12,30]
                bussorthydro = bussort.copy()
                for i in range(len(hydrobus)):
                    if(not bussorthydro[i] in hydrobus):
                        bussorthydro.pop(i)

                if(name =='Wind Onshore'):
                    #bus = Utils.random_pick(bussort,[0.1,0.1,0.1,0.1,0.05,0.05,0.05,0.05,0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02,0,0])
                    #bus = Utils.random_pick(bussort,[1,0,0,0,0,0 ,0,0,0,0,0,0 ,0,0,0,0,0,0 ,0,0,0,0,0,0 ,0,0,0,0,0,0])
                    bus = Utils.random_pick(bussort,[0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.043])
                elif(name == 'Wind Offshore'):
                    #bus = Utils.random_pick(bussortwindoff,[0.3,0.3,0.1,0.1, 0.02,0.02,0.02,0.02,0.02,  0.02,0.02,0.02,0.02,0.02, 0])
                    #bus = Utils.random_pick(bussortwindoff,[1,0,0,0,0,0 ,0,0,0,0,0,0 ,0,0,0])
                    bus = Utils.random_pick(bussortwindoff,[0.2,0.2,0.2,0.2,0.2,0.2 ,0.2,0.2,0.2,0.2,0.2,0.2 ,0.2,0.2,0.2])
                elif(name == 'Hydro'):
                    #bus = Utils.random_pick(bussorthydro,[0.3,0.2,0.2,0.1,0.05,0.05,0.05,0.05,0,0,0])
                    #bus = Utils.random_pick(bussorthydro,[1,0,0,0,0,0 ,0,0,0,0,0])
                    bus = Utils.random_pick(bussorthydro,[0.09,0.09,0.09,0.09,0.09,0.09 ,0.09,0.09,0.09,0.09,0.1])
                yearCost, yCostPerKWh = gen.estAnnualCostsCfD(cap)
                bidType.append(name)
                bidCapacity.append(cap)
                bidPrice.append(yCostPerKWh)
                bidbus.append(bus)
                bidConstructionTime.append(gen.constructionTime)
                makeBid = True
                
        for i in range(len(self.traditionalGen)):
            gen = self.traditionalGen[i]
            name = gen.name
            curROI, curNPV = gen.estimateROIandNPV(self.CFDPrice, self.CarbonCost, False)
            if((name=='Nuclear' or name =='BECCS' or name =='Biomass' or name =='Hydrogen') and gen.genCapacity>0.1 and (not name in bidType) and (curROI<=0.5 or curNPV<0)):
                cap = gen.maxBuildRate

                beccsbus = [2,7,10,12,13,14,15,16,17,18,19,20,22,23,24,26,28,30]
                bussortbeccs = bussort.copy()
                for i in range(len(beccsbus)):
                    if(not bussortbeccs[i] in beccsbus):
                        bussortbeccs.pop(i)

                nuclearbus = [5,7,10,11,12,17,20,27,29]
                bussortnuclear = bussort.copy()
                for i in range(len(nuclearbus)):
                    if(not bussortnuclear[i] in nuclearbus):
                        bussortnuclear.pop(i)
                if(name == 'BECCS'):
                    #bus = Utils.random_pick(bussortbeccs,[0.3,0.2,0.1,0.1,0.05,0.05,0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02,0,0]) 
                    #bus = Utils.random_pick(bussortbeccs,[1,0,0,0,0,0, 0,0,0,0,0,0 ,0,0,0,0,0,0])
                    bus = Utils.random_pick(bussortbeccs,[0.055,0.055,0.055,0.055,0.055,0.055, 0.055,0.055,0.055,0.055,0.055,0.055 ,0.055,0.055,0.055,0.055,0.055,0.065])

                elif(name == 'Nuclear'):
                    #bus = Utils.random_pick(bussortnuclear,[0.4,0.2,0.1,0.1,0.1,0.05,0.05,0,0])
                    #bus = Utils.random_pick(bussortnuclear,[1,0,0,0,0,0,0,0,0])
                    bus = Utils.random_pick(bussortnuclear,[0.11,0.11,0.11,0.11,0.11,0.11,0.11,0.11,0.12])

                elif(name == 'Biomass' or name == 'Hydrogen'):
                    bus = Utils.random_pick(bussort,[0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.043])



                yearCost, yCostPerKWh = gen.estAnnualCostsCfD(cap)
                bidType.append(name)
                bidCapacity.append(cap)
                bidPrice.append(yCostPerKWh)
                bidbus.append(bus)
                bidConstructionTime.append(gen.constructionTime)
                makeBid = True

        return bidType, bidPrice, bidCapacity, bidConstructionTime, makeBid, bidbus

    # method to get cap auction bid
    def getCapAuctionBid(self, timeHorizon, capShortFall, boolEnergyStorage, busheadroom):
        bidPrice = 0.0
        bidCap = 0.0
        maxNPV  = float('-inf')
        bestPlantIndx = -1
        makeBid = False

        bidType = list() # solar, biomass, etc
        bidPrice = list() # price
        bidCapacity = list() # 10000 kW, etc
        bidDeRCapacity = list() # 10000 kW, etc
        bidConstructionTime = list()
        batteryBoolList = list()
        makeBid = False
        bidbus = list()
        tempb = array(busheadroom)
        tempb = tempb.argsort()
        tempb = tempb.tolist()
        bussort = [i+1 for i in tempb]   # return to order of bus number        
        for i in range (len(self.traditionalGen)):
            gen = self.traditionalGen[i]
            name = gen.name
            #  can technology be built in time horizon, e.g. 4 years
            if(self.traditionalGen[i].constructionTime<= timeHorizon and self.traditionalGen[i].genCapacity>10 and (not name in bidType)):
                cap = gen.maxBuildRate
                deRCap = cap*gen.availabilityFactor

                
                beccsbus = [2,7,10,12,13,14,15,16,17,18,19,20,22,23,24,26,28,30]
                bussortbeccs = bussort.copy()
                for i in range(len(beccsbus)):
                    if(not bussortbeccs[i] in beccsbus):
                        bussortbeccs.pop(i)

                nuclearbus = [5,7,10,11,12,17,20,27,29]
                bussortnuclear = bussort.copy()
                for i in range(len(nuclearbus)):
                    if(not bussortnuclear[i] in nuclearbus):
                        bussortnuclear.pop(i)

                if(name in ['CCGT', 'OCGT','Coal','Biomass','Hydrogen']):
                    #bus = Utils.random_pick(bussort,[0.1,0.1,0.1,0.1,0.05,0.05,0.05,0.05,0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02,0,0])
                    #bus = Utils.random_pick(bussort,[1,0,0,0,0,0 ,0,0,0,0,0,0 ,0,0,0,0,0,0 ,0,0,0,0,0,0 ,0,0,0,0,0,0])
                    bus = Utils.random_pick(bussort,[0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.033 ,0.033,0.033,0.033,0.033,0.033,0.043])
                elif(name == 'BECCS'):
                    #bus = Utils.random_pick(bussortbeccs,[0.3,0.2,0.1,0.1,0.05,0.05,0.02,0.02,0.02,0.02,0.02, 0.02,0.02,0.02,0.02,0.02,0,0]) 
                    #bus = Utils.random_pick(bussortbeccs,[1,0,0,0,0,0, 0,0,0,0,0,0 ,0,0,0,0,0,0]) 
                    bus = Utils.random_pick(bussortbeccs,[0.055,0.055,0.055,0.055,0.055,0.055, 0.055,0.055,0.055,0.055,0.055,0.055 ,0.055,0.055,0.055,0.055,0.055,0.065]) 
                elif(name == 'Nuclear'):
                    #bus = Utils.random_pick(bussortnuclear,[0.4,0.2,0.1,0.1,0.1,0.05,0.05,0,0])
                    #bus = Utils.random_pick(bussortnuclear,[1,0,0,0,0,0,0,0,0])
                    bus = Utils.random_pick(bussortnuclear,[0.11,0.11,0.11,0.11,0.11,0.11,0.11,0.11,0.12])


                bidType.append(name)
                bidCapacity.append(cap)
                bidDeRCapacity.append(deRCap)
                bidbus.append(bus)
                batteryBoolList.append(0) # not a battery bid
                if(gen.NPV>0):
                    bidPrice.append(0.0)
                else:
                    loss = gen.yearlyCost - gen.yearlyIncome
                    lossPerKW = loss / gen.genCapacity
                    bidPrice.append(lossPerKW)
                bidConstructionTime.append(gen.constructionTime)
                makeBid = True

        batteryBid = False
        if(self.year>=2018 and boolEnergyStorage):
            if(not len(self.energyStores)>0):
                if((not batteryBid) and (self.estimateBattery.maxBuildRate - self.curYearBatteryBuild)>10):
                    bidType.append(self.estimateBattery.name)
                    bidCapacity.append(self.estimateBattery.dischargeRate)
                    bidDeRCapacity.append(self.estimateBattery.dischargeRate)
                    bidConstructionTime.append(0)
                    batteryBoolList.append(1) 
                    bus = random.randint(1,31)
                    bidbus.append(bus)
                    if(self.estimateBattery.NYNPV>0):
                        bidPrice.append(0.0)
                    else:
                        loss = self.estimateBattery.NYyearlyCost - self.estimateBattery.yearlyIncome
                        lossPerKW = loss / self.estimateBattery.dischargeRate
                        bidPrice.append(lossPerKW)
                    batteryBid = True
                    makeBid = True

            else:
                for i in range (len(self.energyStores)):
                    if(not batteryBid and (self.energyStores[0].maxBuildRate - self.curYearBatteryBuild)>10):
                        bidType.append(self.energyStores[i].name)
                        bidCapacity.append(self.energyStores[i].dischargeRate)
                        bidDeRCapacity.append(self.energyStores[i].dischargeRate)
                        bidConstructionTime.append(0)
                        batteryBoolList.append(1) 
                        bus = random.randint(1,30)
                        bidbus.append(bus)
                        if(self.energyStores[i].NYNPV>0):
                            bidPrice.append(0.0)
                        else:
                            loss = self.energyStores[i].NYyearlyCost - self.energyStores[i].yearlyIncome
                            lossPerKW = loss / self.energyStores[i].dischargeRate
                            bidPrice.append(lossPerKW)
                        batteryBid = True
                        makeBid = True


        return bidType, bidPrice, bidCapacity, bidConstructionTime, bidDeRCapacity, batteryBoolList, makeBid, bidbus
    

    # method to get (derated) capacity in a specific year in the future
    def getCapYear(self, capYear, deratedBool):
        runCap = 0.0
        for i in range(len(self.traditionalGen)):
            if(self.traditionalGen[i].endYear>capYear and self.traditionalGen[i].startYear<=capYear):
                if(deratedBool):
                    runCap = runCap + (self.traditionalGen[i].genCapacity * self.traditionalGen[i].availabilityFactor)
                else:
                    runCap = runCap + self.traditionalGen[i].genCapacity

        for i in range(len(self.renewableGen)):
            if(self.renewableGen[i].endYear>capYear and self.renewableGen[i].startYear<=capYear):
                if(deratedBool):
                    runCap = runCap + (self.renewableGen[i].genCapacity * self.renewableGen[i].availabilityFactor)
                else:
                    runCap = runCap + self.renewableGen[i].genCapacity

        for i in range(len(self.constructionQueue)):
            constructSYear = self.constructionQueue[i][3]
            if(constructSYear<=capYear):
                if(deratedBool):
                    genname = self.constructionQueue[i][0]
                    genID, renewBool = self.genTechNameToClassID(genname)
                    tempCapF = 0.0
                    if(renewBool):
                        tempGen = renewableGenerator(genID,8760, 10,10,0,0) # ramdom bus number and capacity, does not affect availability factor
                        tempCapF = tempGen.availabilityFactor
                    else:
                        tempGen = traditionalGenerator(genID,10,1,0)
                        tempCapF = tempGen.availabilityFactor
                        
                    runCap = runCap + (self.constructionQueue[i][2] * tempCapF)
                else:
                    runCap = runCap + self.constructionQueue[i][2]

        return  runCap
        
    # method to return capacity margin
    def getCapacityMargin(self, peakDemand):
        
        self.getTotalCapacity()
        totalCapacity = self.totalCapacity
        deRatedCapacity = self.deRatedCapacity
        

        capacityMargin = totalCapacity - peakDemand
        deRatedCapacityMargin = deRatedCapacity - peakDemand
        
        peakD, peakDUnit = Utils.checkSingleValUnit(peakDemand)
        tempTCap, tempTCapUnit = Utils.checkSingleValUnit(totalCapacity)
        tempDCap, tempDCapUnit = Utils.checkSingleValUnit(deRatedCapacity)
        self.capacityMargin = capacityMargin
        self.deRatedCapacityMargin = deRatedCapacityMargin
        
        self.yearlyPeakDemand.append(peakDemand)
        self.yearlyCapacityMargin.append(capacityMargin)
        self.yearlyDeRatedCapacityMargin.append(deRatedCapacityMargin)
        return capacityMargin, deRatedCapacityMargin

    # get total capacity
    def getTotalCapacity(self):
        totalCapacity = 0.0
        deRatedCapacity = 0.0
        for i in range(len(self.traditionalGen)):
            totalCapacity = totalCapacity + self.traditionalGen[i].genCapacity
            deRatedCapacity = deRatedCapacity + (self.traditionalGen[i].genCapacity*self.traditionalGen[i].availabilityFactor)

        for i in range(len(self.renewableGen)):
            totalCapacity = totalCapacity + self.renewableGen[i].genCapacity
            deRatedCapacity = deRatedCapacity + (self.renewableGen[i].genCapacity*self.renewableGen[i].availabilityFactor)
        self.totalCapacity = totalCapacity
        self.deRatedCapacity = deRatedCapacity
        return self.totalCapacity, self.deRatedCapacity

    # method to get capacity by generation type, e.g. all solar plants, etc.
    def getCapacityByType(self, genTypeID, boolRenewable):
        sumCap = 0.0
        if(boolRenewable):
            for i in range(len(self.renewableGen)):
                if(self.renewableGen[i].genType == genTypeID):
                    sumCap = sumCap + self.renewableGen[i].genCapacity
                    deR = self.renewableGen[i].availabilityFactor

        else:
            for i in range(len(self.traditionalGen)):
                if(self.traditionalGen[i].genType == genTypeID):
                    sumCap = sumCap + self.traditionalGen[i].genCapacity
                    deR = self.traditionalGen[i].availabilityFactor
                    
        deRSumCap = sumCap*deR
        return sumCap, deRSumCap
                
    # update CO2 price
    def setNewPolicyValues(self, newCO2Price,newCFDPrice):
        self.CarbonCost = newCO2Price
        self.CFDPriceChange = newCFDPrice - self.CFDPrice # REnergySub
        self.CFDPrice = newCFDPrice # this can be ignored**


    # update CO2 price for each plant
    def updateTechnologiesYear(self, newCO2Price):
        wholesEPriceChange = 0.0
        for i in range(len(self.renewableGen)):
            wholesEPriceChange = self.renewableGen[i].updateYear(newCO2Price)
                
        for i in range(len(self.traditionalGen)):
            wholesEPriceChange= self.traditionalGen[i].updateYear(newCO2Price)

        return wholesEPriceChange

    # remove all energy stores
    def removeBatteries(self):
        self.energyStores = list()
        self.maxBatteryCap = 0.0 # maximum available capacity
        self.curBatteryCap = 0.0 # current state of charge

    # add a new battery
    def addBatterySize(self, capacity): # capacity refers to kW, not kWh
        capkWh = capacity*self.batteryDuration # kWh
        chargeRate = capacity # kW
        dischargeRate = capacity # kW

        battery = energyStorage(capkWh,chargeRate,dischargeRate,self.year, random.randint(1,30))
        self.energyStores.append(battery)

    # add battery with capacity subsidies
    def addBatterySizeCapacitySub(self, capacity, bidSubKWCap):
        capkWh = capacity*self.batteryDuration # kWh
        chargeRate = capacity # kW
        dischargeRate = capacity # kW
        battery = energyStorage(capkWh,chargeRate,dischargeRate,self.year,random.randint(1,30))
        battery.capSubKWCap = bidSubKWCap
        self.energyStores.append(battery)

    # add specific battery
    def addBattery(self, newBattery):
        self.energyStores.append(newBattery)

    # get cost and subs
    def getTotalBatteryInfo(self):
        batData = list()
        totCost = 0
        totCapSubs = 0
        for i in range(len(self.energyStores)):
            totCost = totCost + self.energyStores[i].yearlyCost
            totCapSubs = totCapSubs + self.energyStores[i].yearlyCapSubs
        batData.append(totCost)
        batData.append(totCapSubs)
        return batData

    # return total capacity of battery kW
    def getTotalBatteryKW(self):
        totKW = 0.0
        for i in range(len(self.energyStores)):
            totKW = totKW + self.energyStores[i].dischargeRate
        return totKW

    # return amount of battery discharge in the current year kWh
    def getCurYearBatteryGenKWh(self):
        totKWh = 0.0
        for i in range(len(self.energyStores)):
            totKWh = totKWh + self.energyStores[i].curYearDischargeKWh
        return totKWh

    # return battery storage capacity kWh
    def getMaxBatteryCap(self):
        self.maxBatteryCap = 0.0
        for i in range(len(self.energyStores)):
            self.maxBatteryCap = self.maxBatteryCap + self.energyStores[i].maxCapacity
        return self.maxBatteryCap

    # return current state of charge of battery kWh
    def getCurBatteryCap(self):
        self.curBatteryCap = 0.0
        for i in range(len(self.energyStores)):
            self.curBatteryCap = self.curBatteryCap + self.energyStores[i].curCapacity
        return self.curBatteryCap

    # method to remove all generation plants and initialize with new plant of 0 capacity (needed for looping through plants in mainSim)
    def removeGeneration(self):
        self.traditionalGen = list()
        self.renewableGen = list()
        renGenWindOn = renewableGenerator(4,self.timeSteps, 0, self.CFDPrice, 0,0)#bus number 0 is for initialisation


             # 0 capacity
        renGenWindOff = renewableGenerator(5,self.timeSteps, 0, self.CFDPrice, 0,0) # 0 capacity
        renGenPV = renewableGenerator(0,self.timeSteps, 0, self.CFDPrice, 0,0) # 0 capacity
        renGenHydro = renewableGenerator(2,self.timeSteps, 0, self.CFDPrice, 0,0) # 0 capacity

        tradGenCoal = traditionalGenerator(0,0,0,0) # 0 capacity
        tradGenGas = traditionalGenerator(1,0,0,0) # 0 capacity
        tradGenNuclear = traditionalGenerator(2,0,0,0) # 0 capacity
        tradGenOCGT = traditionalGenerator(3,0, 0,0) # 0 capacity
        tradGenBECCS = traditionalGenerator(4,0, 0,0) # 0 capacity
        tradGenBiomass = traditionalGenerator(5,0,0,0) # 0 capacity
        tradGenHydrogen = traditionalGenerator(6,0,0,0) # 0 capacity        
        self.renewableGen.append(renGenWindOn)
        self.renewableGen.append(renGenWindOff)
        self.renewableGen.append(renGenPV)
        self.renewableGen.append(renGenHydro)

        self.traditionalGen.append(tradGenNuclear)
        self.traditionalGen.append(tradGenGas)
        self.traditionalGen.append(tradGenCoal)
        self.traditionalGen.append(tradGenOCGT)
        self.traditionalGen.append(tradGenBECCS)
        self.traditionalGen.append(tradGenBiomass)
        self.traditionalGen.append(tradGenHydrogen)        
        for i in range(len(self.renewableGen)):
            self.renewableGen[i].startYear = 2000
            self.renewableGen[i].endYear = 3000
            self.renewableGen[i].age = 0
        for i in range(len(self.traditionalGen)):
            self.traditionalGen[i].startYear = 2000
            self.traditionalGen[i].endYear = 3000
            self.traditionalGen[i].age = 0

    # get id of plant name (although in general its probably better to just use name rather than IDs....)
    def genTechNameToClassID(self, name):
        genID = -1
        renewableBool = True
        if(name =='Nuclear'):
            genID = 2 # Nuclear, 2,
            renewableBool = False
        elif(name =='CCGT'):
            genID = 1 # CCGT, 1
            renewableBool = False
        elif(name =='Coal'):
            genID = 0 # Coal, 0
            renewableBool = False
        elif(name =='OCGT'):
            genID = 3 # OCGT, 3
            renewableBool = False
        elif(name =='BECCS'):
            genID = 4 # BECCS, 4
            renewableBool = False
        elif(name =='Biomass'): 
            genID = 5 # 
            renewableBool = False
        elif(name =='Hydrogen'): 
            genID = 6 # 
            renewableBool = False


        elif(name =='Wind Offshore'): 
            genID = 5 # offshore
            renewableBool = True
        elif(name =='Wind Onshore'): 
            genID = 4 # onshore
            renewableBool = True
        elif(name =='Solar'): 
            genID = 0 # 
            renewableBool = True
        elif(name =='Hydro'): 
            genID = 2 # 
            renewableBool = True

        return genID, renewableBool
        
    # method to Generation new generation plants
    def addGeneration(self, genName, genTypeID, renewableID, capacityKW, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom):
        addGen = False
        if(cfdBool and capMarketBool):
            input('****** Problem, both capacity market bool and cfd bool are true......')
        elif(cfdBool):
            cfdSub = subsidy # GBP/kWh
            capitalSub = 0.0 # GBP/ kW Cap /year
            print('**** CfD ', cfdSub)
            print("Name: %s, ID: %s, renID: %s, CapKW: %s, startY: %s, endY: %s" % (genName, str(genTypeID), str(renewableID), str(capacityKW), str(startYear), str(endYear)))
        elif(capMarketBool):
            cfdSub = 0.0 # GBP/kWh
            capitalSub = subsidy # GBP/ kW Cap /year
            print('**** Capactiy Market ', capitalSub)
            print("Name: %s, ID: %s, renID: %s, CapKW: %s, startY: %s, endY: %s" % (genName, str(genTypeID), str(renewableID), str(capacityKW), str(startYear), str(endYear)))
       #     input('wait')
        else:
            capitalSub = 0.0 # GBP/ kW Cap /year
            cfdSub = 0.0 # GBP/kWh
            
        if(startYear> self.year): # not built yet
            print('Add to construction queue')
            self.addToConstructionQueue(genName, renewableID, capacityKW, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum)

        elif(endYear<self.year):
            print('Plant already decommissioned, not adding to capacity!')

        else:
            addGen = True
            if(genTypeID==1 or genName =='Nuclear'):
                tradGen = traditionalGenerator(2,capacityKW, BusNum, Headroom) # Nuclear, 2,
                tradGen.CFDPrice = cfdSub
            elif(genTypeID==2 or genName =='CCGT'):
                tradGen = traditionalGenerator(1,capacityKW, BusNum, Headroom) # CCGT, 1
            elif(genTypeID==3 or genName =='Coal'):
                tradGen = traditionalGenerator(0,capacityKW, BusNum, Headroom) # Coal, 0
            elif(genTypeID==4 or genName =='OCGT'): 
                tradGen = traditionalGenerator(3,capacityKW, BusNum, Headroom) # OCGT, 3
            elif(genTypeID==9 or genName =='BECCS'): 
                tradGen = traditionalGenerator(4,capacityKW, BusNum, Headroom) # BECCS, 4
            elif(genTypeID==10 or genName =='Biomass'): 
                tradGen = traditionalGenerator(5,capacityKW,BusNum, Headroom) # 
            elif(genTypeID==11 or genName =='Hydrogen'): 
                tradGen = traditionalGenerator(6,capacityKW, BusNum, Headroom) # 

            elif(genTypeID==5 or genName =='Wind Offshore'): 
                renGen = renewableGenerator(5,self.timeSteps, capacityKW,cfdSub, BusNum, Headroom) # offshore
            elif(genTypeID==6 or genName =='Wind Onshore'): 
                renGen = renewableGenerator(4,self.timeSteps, capacityKW,cfdSub, BusNum, Headroom) # onshore
            elif(genTypeID==7 or genName =='Solar'): 
                renGen = renewableGenerator(0,self.timeSteps, capacityKW,cfdSub, BusNum, Headroom) # 
            elif(genTypeID==8 or genName =='Hydro'): 
                renGen = renewableGenerator(2,self.timeSteps, capacityKW,cfdSub, BusNum, Headroom) #


               
        if(addGen):
            if(renewableID==0):
                tradGen.startYear = startYear
                tradGen.endYear = endYear
                tradGen.age = age
                tradGen.CFDPrice = cfdSub
                tradGen.capitalSub = capitalSub
                self.traditionalGen.append(tradGen)
            else:
                renGen.startYear = startYear
                renGen.endYear = endYear
                renGen.age = age
                renGen.CFDPrice = cfdSub
                renGen.capitalSub = capitalSub
                renGen.resetYearValueRecord()
                renGen.recalcEconomics()
                if((startYear>2010 or cfdSub<1) and genName =='Wind Offshore'):
                    print('renGen.cfd ',renGen.CFDPrice)
                    print('renGen.capitalSub ',renGen.capitalSub)
                self.renewableGen.append(renGen)
                
    # method to graph capacity
    def graph(self):
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(2,1)
        fig.suptitle('Capacity Change: Total Capacity', fontsize=20)

        y = self.years
        d, unit = Utils.checkUnits(self.yearlyTotalCapacity)
        axs[0].plot(y,d)
        d, unit = Utils.checkUnits(self.yearlyDeRatedCapacity)
        axs[0].plot(y,d)
        d, unit = Utils.checkUnits(self.yearlyPeakDemand)
        axs[0].plot(y,d)
        d, unit = Utils.checkUnits(self.yearlyCapacityMargin)
        axs[0].plot(y,d)
        d, unit = Utils.checkUnits(self.yearlyDeRatedCapacityMargin)
        axs[0].plot(y,d)
        axs[0].set_ylabel(unit)
        from matplotlib.ticker import MaxNLocator
        axs[0].xaxis.set_major_locator(MaxNLocator(integer=True)) 


        axs[0].legend(['TotalCapacity', 'DeRatedCapacity', 'PeakDemand','CapacityMargin','DeRatedCapacityMargin'], loc='upper left')
        fig.show()

    # method to output results to a file
    def writeToFileAllYears(self, RESULTS_FILE_PATH, compNum):
        fileOut = RESULTS_FILE_PATH+'Company'+str(compNum)+'_YearlyData.csv'

        outNames = list()
        outNames.append('Year')
        for i in range(len(self.techNames)):
            outNames.append(self.techNames[i]+' Capacity')
        for i in range(len(self.techNames)):
            outNames.append(self.techNames[i]+' Derated Capacity')
        for i in range(len(self.techNames)):
            outNames.append(self.techNames[i]+' Profit')
        for i in range(len(self.techNames)):
            outNames.append(self.techNames[i]+' Revenue')
        for i in range(len(self.techNames)):
            outNames.append(self.techNames[i]+' Cost')
        for i in range(len(self.techNames)):
            outNames.append(self.techNames[i]+' Emissions')
        for i in range(len(self.techNames)):
            outNames.append(self.techNames[i]+' Generation')


        outData = list()
        outData.append(self.years)
        for i in range(len(self.techNames)):
            outData.append(self.yearlyCapPerTech[i])
        for i in range(len(self.techNames)):
            outData.append(self.yearlyDerateCapPerTech[i])
        for i in range(len(self.techNames)):
            outData.append(self.yearlyProfitPerTech[i])
        for i in range(len(self.techNames)):
            outData.append(self.yearlyRevenuePerTech[i])
        for i in range(len(self.techNames)):
            outData.append(self.yearlyCostPerTech[i])
        for i in range(len(self.techNames)):
            outData.append(self.yearlyEmissionsPerTech[i])
        for i in range(len(self.techNames)):
            outData.append(self.yearlyGenerationPerTech[i])


        outNames.append('Battery Capacity kW')
        outNames.append('Battery Discharge kWh')
        outNames.append('Battery Cost GBP')
        outNames.append('Battery Cap Subs GBP')
        outData.append(self.yearlyStorageCapKW)
        outData.append(self.yearlyStorageGenKWh)
        outData.append(self.yearlyStorageCost)
        outData.append(self.yearlyStorageCapSubs)

        Utils.writeListsToCSV(outData,outNames,fileOut)


    # method to graph all data each year
    def graphAllGensAllYears(self):
        import matplotlib.pyplot as plt
       
        y = self.years
     
        graphNames = list()

        fig = plt.figure()
        fig.suptitle(self.name+' : Annual Change', fontsize=20)
        ax1 = fig.add_subplot(231)
        ax2 = fig.add_subplot(232)
        ax3 = fig.add_subplot(233)
        ax4 = fig.add_subplot(234)
        ax5 = fig.add_subplot(235)
        ax6 = fig.add_subplot(236)
        ax1.title.set_text('Yearly Capacity')
        ax2.title.set_text('Yearly Derated Capacity')
        ax3.title.set_text('Yearly Profit')
        ax4.title.set_text('Yearly Revenue')
        ax5.title.set_text('Yearly Cost')
        ax6.title.set_text('Yearly Emissions')

        print('len(self.yearlyCapPerTech)',len(self.yearlyCapPerTech))
        print('len(self.yearlyCapPerTech[0])',len(self.yearlyCapPerTech[0])) #how much tech
        print('self.yearlyCapPerTech[0]',self.yearlyCapPerTech[0]) #how much year
        print('len(self.renewableGen)',len(self.renewableGen))
        print('len(self.traditionalGen)',len(self.traditionalGen))


        for i in range(len(self.yearlyCapPerTech)):
            graphNames.append(self.techNames[i]) # i each year
            
            d = [x /1000.0 for x in self.yearlyCapPerTech[i]] #x corresponds to tech
            ax1.plot(y,d)

            d = [x /1000.0 for x in self.yearlyDerateCapPerTech[i]]
            ax2.plot(y,d)

            d = self.yearlyProfitPerTech[i]
            ax3.plot(y,d)

            d = self.yearlyRevenuePerTech[i]
            ax4.plot(y,d)

            d = self.yearlyCostPerTech[i]
            ax5.plot(y,d)

            d = self.yearlyEmissionsPerTech[i]
            ax6.plot(y,d)
                
   

        ax1.set_ylabel('MW')
        ax2.set_ylabel('MW')
        ax3.set_ylabel('GBP')
        ax4.set_ylabel('GBP')
        ax5.set_ylabel('GBP')
        ax6.set_ylabel('kg')
        from matplotlib.ticker import MaxNLocator
        ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax3.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax4.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax5.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax6.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax1.set_xlabel('Year')
        ax2.set_xlabel('Year')
        ax3.set_xlabel('Year')
        ax4.set_xlabel('Year')
        ax5.set_xlabel('Year')
        ax6.set_xlabel('Year')
        ax1.legend(graphNames, loc='upper left')
        ax2.legend(graphNames, loc='upper left')
        ax3.legend(graphNames, loc='lower left')
        ax4.legend(graphNames, loc='upper left')
        ax5.legend(graphNames, loc='upper left')
        ax6.legend(graphNames, loc='upper left')
        fig.show()
        

    def getGenCapByBus(self):
        Bus4Tech = list(range(1,31))
        Bus4Cap = list(range(1,31))
        for i in range (range(1,31)):
            for j in range (len(self.renewableGen)):
                if(self.renewableGen[j].Bus == Bus4Tech[i]):
                    if(not self.renewableGen[j].renewableType in Bus4Tech[i]):
                        Bus4Tech[i].append(self.renewableGen[j].renewableType)
                        Bus4Cap[i].append(self.renewableGen[j].genCapacity)
                    else:
                        indx = Bus4Tech[i].index(self.renewableGen[j].renewableType)
                        Bus4Cap[indx] = Bus4Cap[indx] + self.renewableGen[j].genCapacity
            for k in range (len(self.traditionalGen)):
                if(self.traditionalGen[k].Bus == Bus4Tech[i]):
                    if(not (self.traditionalGen[k].genType+6) in Bus4Tech[i]):
                        Bus4Tech[i].append((self.traditionalGen[k].genType+6))
                        Bus4Cap[i].append(self.traditionalGen[k].genCapacity)
                    else:
                        indx = Bus4Tech[i].index((self.traditionalGen[k].genType+6))
                        Bus4Cap[i][indx] = Bus4Cap[i][indx] + self.traditionalGen[k].genCapacity
        return Bus4Tech, Bus4Cap


    # method to return indices of plants of a specific type
    def getGenIndxByType(self): 
        renTypes = list()
        renIndx = list()
        for i in range (len(self.renewableGen)):
            if(not (self.renewableGen[i].renewableType in renTypes)):
                renTypes.append(self.renewableGen[i].renewableType) #type is denoted by 0,1,2,3
                tempL = list()
                tempL.append(i)
                renIndx.append(tempL) #company number
            else:
                for j in range(len(renTypes)):
                    if(renTypes[j]==self.renewableGen[i].renewableType):
                        renIndx[j].append(i) #add company number

        tradTypes = list()
        tradIndx = list()
        for i in range (len(self.traditionalGen)):
            if(not (self.traditionalGen[i].genType in tradTypes)):
                tradTypes.append(self.traditionalGen[i].genType)
                tempL = list()
                tempL.append(i)
                tradIndx.append(tempL)
            else:
                for j in range(len(tradTypes)):
                    if(tradTypes[j]==self.traditionalGen[i].genType):
                        tradIndx[j].append(i)
        return renIndx,tradIndx # each type has a number of company number

    # method to update build rates of each generation plant type
    def updateBuildRates(self):
        for i in range(len(self.traditionalGen)):
            self.traditionalGen[i].updateBuildRates()

        for i in range(len(self.renewableGen)):
            self.renewableGen[i].updateBuildRates()

    # return capacity portfolio of plants
    def getGenPortfolio(self):
        genTypes = list()
        genCap = list()
        genTypesNonZero = list()
        
        for i in range(len(self.traditionalGen)):
            n = self.traditionalGen[i].name
            c = self.traditionalGen[i].genCapacity
            if(c>0.1 and (not (n in genTypesNonZero))): # 0.1 kW, not using 0 because have some gens = 0.0.. that don't want to count (might be slightly over 0)
                genTypesNonZero.append(n)
            if(not (n in genTypes)):
                genTypes.append(n)
                genCap.append(c)
            else:
                indx = genTypes.index(n)
                genCap[indx] = genCap[indx] + c
       
        for i in range(len(self.renewableGen)):
            n = self.renewableGen[i].name
            c = self.renewableGen[i].genCapacity
            if(c>0.1 and (not (n in genTypesNonZero))): # 0.1 kW, not using 0 because have some gens = 0.0.. that don't want to count (might be slightly over 0)
                genTypesNonZero.append(n)
            if(not (n in genTypes)):
                genTypes.append(n)
                genCap.append(c)
            else:
                indx = genTypes.index(n)
                genCap[indx] = genCap[indx] + c

        return genTypes, genCap, genTypesNonZero

    # method to check lifetime of plant type
    def checkPlantLifeTime(self, plantName, renewableBool):
        life=0
        if(renewableBool):
            for i in range(len(self.renewableGen)):
                if(plantName == self.renewableGen[i].name):
                    life = self.renewableGen[i].lifetime
        else:
            for i in range(len(self.traditionalGen)):
                if(plantName == self.traditionalGen[i].name):
                    life = self.traditionalGen[i].lifetime

        if(life==0):
            input('Error, lifetime incorrect')
        else:
            return life

    




































        
        
