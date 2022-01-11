import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils
from electricityGenerator import electricityGenerator

class traditionalGenerator(electricityGenerator):
    
    
    def __init__(self,genTypeID,capacity, NumBus, Headroom):

        self.initialise(genTypeID,capacity, NumBus, Headroom)
        

    def initialise(self,genTypeID,capacity, NumBus, Headroom):
        self.generalInfo()
        self.age = 0
        self.startYear = 0
        self.endYear = 0
        self.opEmissionsPkW = 0.0 # kg of CO2 emitted per kW generated
        self.genCapacity = capacity
        self.energyGenerated = list()
        self.runingCost=0.0
        self.runingEmissions=0.0
        self.hourlyCost = list()
        self.hourlyEmissions = list()
        self.hourlyProfit = list()
        self.genTypeID = genTypeID
        self.yearlyEnergyGen=0.0
        self.yearlyProfit=0.0
        self.yearlyIncome = 0.0
        self.yearlyCost = 0.0
        self.renewableBool = False
        self.numbus = NumBus
        self.FuelCost = 0.0
        self.CarbonCost = 0.0
        self.fixedOandMCost = 0.0
        self.variableOandMCost = 0.0
        self.capitalCost = 0.0
        self.wasteCost = 0.0
        self.yearlyCarbonCostSum = 0.0
        self.Headroom = Headroom
        self.capacityFactor = 0.0
        self.availabilityFactor = 0.9
        self.ConnectionFee = 0.5174*self.Headroom*0.001-2415.7
        fuelFilePath = ''
        CapexCoal = list([1353.700909, 1353.700909, 1353.700909, 1353.700909, 1353.700909, 1353.700909, 1353.700909, 1353.700909, 1353.700909, 1353.700909, 1353.700909, 1337.862178, 1301.340078, 1306.726719, 1312.113359, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5, 1317.5])
        CapexCCGT = list([497.8125925, 497.8125925, 497.8125925, 497.8125925, 497.8125925, 497.8125925, 497.8125925, 497.8125925, 497.8125925, 497.8125925, 497.8125925, 494.8651209, 484.1545087, 488.9687077, 493.8060748, 498.666695, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5, 501.5])
        CapexNuclear = list([4803.45484, 4803.45484, 4803.45484, 4803.45484, 4803.45484, 4803.45484, 4803.45484, 4803.45484, 4803.45484, 4803.45484, 4803.45484, 4747.252889, 4617.658342, 4636.772228, 4655.886114, 4675, 4628.25, 4581.9675, 4536.14825, 4490.7863, 4445.87825, 4401.41985, 4357.40515, 4313.8316, 4270.69325, 4227.9867, 4185.706, 4143.84945, 4102.4111, 4061.3867, 4020.77285, 4020.77285, 4020.77285, 4020.77285, 4020.77285, 4020.77285, 4020.77285, 4020.77285, 4020.77285, 4020.77285, 4020.77285])
        CapexOCGT = list([419.2106042, 419.2106042, 419.2106042, 419.2106042, 419.2106042, 419.2106042, 419.2106042, 419.2106042, 419.2106042, 419.2106042, 419.2106042, 417.1828009, 408.5928267, 413.094253, 417.6188475, 422.166695, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425, 425])
        CapexBECCS = list([3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3396.6, 3374.5, 3353.25, 3332, 3311.6, 3292.05, 3272.5, 3253.8, 3235.1, 3217.25, 3199.4, 3182.4, 3166.25, 3149.25, 3133.95, 3117.8, 3102.5, 3088.05, 3073.6, 3059.15, 3044.7])
        CapexHydrogen = list([535.1485369, 535.1485369, 535.1485369, 535.1485369, 535.1485369, 535.1485369, 535.1485369, 535.1485369, 535.1485369, 535.1485369, 535.1485369, 531.9800071, 520.4660948, 525.6413608, 530.8415325, 536.066695,  539.1125, 539.1125, 539.1125, 539.1125, 539.1125, 539.1125, 539.1125,539.1125, 539.1125,  539.1125, 539.1125, 539.1125, 539.1125, 539.1125, 539.1125, 539.1125,539.1125,539.1125,539.1125,539.1125,539.1125,539.1125,539.1125,539.1125,539.1125])
        CapexBiomass = list([1624.441091, 1624.441091, 1624.441091, 1624.441091, 1624.441091, 1624.441091, 1624.441091, 1624.441091, 1624.441091, 1624.441091, 1624.441091, 1605.434614, 1561.608094, 1568.072063, 1574.536031, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581, 1581]) 

        
        if(genTypeID==0):
            #if(self.numbus in [4,11,15,16,18]):                
            self.name = 'Coal' # Coal - CCS ASC Oxy FOAK
            self.opEmissionsPkW = 0.907 # kg CO2/kWh # no CCS
    #        self.opEmissionsPkW = 0.0907 # kg CO2/kWh
            # Electricity generation cost source data
            # https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/566567/BEIS_Electricity_Generation_Cost_Report.pdf
            self.fixedOandMCost = 68.2 # gbp per kW capacity per year
            self.variableOandMCost = 0.006 # gbp per kWh
            self.capitalCost = CapexCoal[self.year-2010]+self.ConnectionFee # gbp per kW capacity
            self.capacityFactor = 0.17
            self.availabilityFactor = 0.88
            self.lifetime = 25 # years
            self.totConstructionTime = 12 # years
            self.preDevTime = 6 # years
            self.constructionTime = 6 # years
            # Build rate source data
            # https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/42562/216-2050-pathways-analysis-report.pdf
            self.maxBuildRate = 100000  # 0.1GW
            self.GBmaxBuildRate = 2000000  # 6GW 
            fuelFilePath = 'WholesaleEnergyPrices/Coal'+str(self.BASEYEAR)+'_2050_dollarPerTonne.txt'
            #else:
               # input('Error. This bus is not suitable for Coal') 
        elif(genTypeID==1): # 17 CCGT gen companies
            self.name = 'CCGT' # CCGT H Class
            self.opEmissionsPkW = 0.365 # kg CO2/kWh 
            self.fixedOandMCost = 12.2 # gbp per kW capacity per year
            self.variableOandMCost = 0.003 # gbp per kWh 
            self.capitalCost = CapexCCGT[self.year-2010]+self.ConnectionFee # gbp per kW capacity
            self.capacityFactor = 0.453
            self.availabilityFactor = 0.85
            self.lifetime = 25 # years
            self.totConstructionTime = 5 # years
            self.preDevTime = 2 # years
            self.constructionTime = 3 # years
     #       self.GBmaxBuildRate = 1000000  # 6GW
    #        self.GBmaxBuildRate = 6000000  # 6GW
            self.GBmaxBuildRate = 2000000  # 6GW
            self.maxBuildRate = 350000 # 6GW total max. 6/17 GW per company max build rate
            fuelFilePath = 'WholesaleEnergyPrices/NaturalGas'+str(self.BASEYEAR)+'_2050_pencePerTherm.txt'
        elif(genTypeID==2):
            #if(self.numbus in [5,7,10,11,20,27]):
            self.name = 'Nuclear' # Nuclear PWR FOAK
            self.opEmissionsPkW = 0.0 # kg CO2/kWh
            self.fixedOandMCost = 72.9 # gbp per kW capacity per year
            self.variableOandMCost = 0.005 # gbp per kWh
            self.capitalCost = CapexNuclear[self.year-2010]+self.ConnectionFee # gbp per kW capacity
      #      self.wasteCost = 0.002
            self.capacityFactor = 0.774
      #      self.availabilityFactor = 0.9
            self.availabilityFactor = 0.81
            self.lifetime = 60 # years
            self.totConstructionTime = 13 # years
            self.preDevTime = 5 # years
            self.constructionTime = 8 # years
            self.GBmaxBuildRate = 1000000  # 1GW
            self.maxBuildRate = 1000000 #1.0 GW #100000 #1000000 # 1GW
            fuelFilePath = 'WholesaleEnergyPrices/NuclearFuel'+str(self.BASEYEAR)+'_2050_pencePerkWh.txt'
            #else:
                #input('Error. This bus is not suitable for Nuclear') 
        elif(genTypeID==3):# 8 OCGT companies
            self.name = 'OCGT' # OCGT 600MW 500 hr
            self.opEmissionsPkW = 0.46 # kg CO2/kWh 
            self.fixedOandMCost = 4.6 # gbp per kW capacity per year
            self.variableOandMCost = 0.003 # gbp per kWh 
            self.capitalCost = CapexOCGT[self.year-2010]+self.ConnectionFee # gbp per kW capacity
            self.capacityFactor = 0.19
            self.availabilityFactor = 0.92
            self.lifetime = 25 # years
            self.totConstructionTime = 4 # years
            self.preDevTime = 2 # years
            self.constructionTime = 2 # years
   #         self.GBmaxBuildRate = 4000000  # 4GW
            self.GBmaxBuildRate = 1000000  # 4GW
            self.maxBuildRate = 500000 # 4GW total max. 0.5 GW max build rate per company
            fuelFilePath = 'WholesaleEnergyPrices/NaturalGas'+str(self.BASEYEAR)+'_2050_pencePerTherm.txt'
        elif(genTypeID==4):# BECCS
            self.name = 'BECCS' # BECCS
            # https://reader.elsevier.com/reader/sd/pii/S1876610217319380?token=F7B61950FD8DC18C0829C7057AFF7E8BDA8BE245B5790AE2C490581EE4110BE970170DB19AF359BE5610D05B60CF806E
            self.opEmissionsPkW = -0.295 # kg CO2/kWh 
            self.fixedOandMCost = 65.5 # same as regular biomass # gbp per kW capacity per year
            self.variableOandMCost = 0.036 #0.008 #0.036 gbp per kWh # page 10 (opex + transport)
            # CAPEX page 9: https://www.theccc.org.uk/wp-content/uploads/2018/12/Biomass-response-to-Call-for-Evidence-ICL.pdf
            self.capitalCost = CapexBECCS[self.year-2010]+self.ConnectionFee # gbp per kW capacity # 3010 for normal biomass???
            self.capacityFactor = 0.45
            self.availabilityFactor = 0.88
            self.lifetime = 25 # years
            self.totConstructionTime = 5 # years
            self.preDevTime = 2 # years
            self.constructionTime = 3 # years
            self.GBmaxBuildRate = 500000  # GW
            self.maxBuildRate = 500000 
          #  fuelFilePath = 'WholesaleEnergyPrices/BiomassMiscanthusPellet'+str(self.BASEYEAR)+'_2050_GBPPerkWh.txt'
            fuelFilePath = 'WholesaleEnergyPrices/WasteWood'+str(self.BASEYEAR)+'_2050_GBPPerkWh.txt'



        elif(genTypeID==5):# Biomass
            self.name = 'Biomass' # Biomass
            # https://reader.elsevier.com/reader/sd/pii/S1876610217319380?token=F7B61950FD8DC18C0829C7057AFF7E8BDA8BE245B5790AE2C490581EE4110BE970170DB19AF359BE5610D05B60CF806E
            self.opEmissionsPkW = 0 # kg CO2/kWh 
            self.fixedOandMCost = 72.9 # same as regular biomass # gbp per kW capacity per year
            self.variableOandMCost = 0.005 #0.008 #0.036 gbp per kWh # page 10 (opex + transport)
            # CAPEX page 9: https://www.theccc.org.uk/wp-content/uploads/2018/12/Biomass-response-to-Call-for-Evidence-ICL.pdf
            self.capitalCost = CapexBiomass[self.year-2010]+self.ConnectionFee # gbp per kW capacity # 3010 for normal biomass???
            self.capacityFactor = 0.84
            self.availabilityFactor = 0.88
            self.lifetime = 25 # years
            self.totConstructionTime = 5 # years
            self.preDevTime = 3 # years
            self.constructionTime = 2 # years
            self.GBmaxBuildRate = 500000  # GW
            self.maxBuildRate = 14000
          #  fuelFilePath = 'WholesaleEnergyPrices/BiomassMiscanthusPellet'+str(self.BASEYEAR)+'_2050_GBPPerkWh.txt'
            fuelFilePath = 'WholesaleEnergyPrices/WasteWood'+str(self.BASEYEAR)+'_2050_GBPPerkWh.txt'
        elif(genTypeID==6):# Hydrogen
            self.name = 'Hydrogen' # Hydrogen
            self.opEmissionsPkW = 0 # kg CO2/kWh line 263 , 319 change as well
            self.fixedOandMCost = 12.2 # same as regular biomass # gbp per kW capacity per year
            self.variableOandMCost = 0.003 #0.008 #0.036 gbp per kWh # page 10 (opex + transport)            # CAPEX page 9: https://www.theccc.org.uk/wp-content/uploads/2018/12/Biomass-response-to-Call-for-Evidence-ICL.pdf
            self.capitalCost = CapexCCGT[self.year-2010]+self.ConnectionFee # gbp per kW capacity # 3010 for normal biomass???
            self.capacityFactor = 0.453
            self.availabilityFactor = 0.85
            self.lifetime = 25 # years
            self.totConstructionTime = 5 # years
            self.preDevTime = 2 # years
            self.constructionTime = 3 # years
            self.GBmaxBuildRate = 1.5  # GW
            self.maxBuildRate = 0.075
          
            fuelFilePath = 'WholesaleEnergyPrices/Hydrogen'+str(self.BASEYEAR)+'_2050_GBPPerkWh.txt'    
        else:
            self.name = 'Unknown'
            input('ERROR: Unknown traditional gen type?')

        self.updateBuildRates()

        self.capitalCostPerHour = (self.capitalCost * self.genCapacity)/(8760.0 * self.lifetime) # GBP/hr
        self.fixedOandMPerHour = (self.fixedOandMCost * self.genCapacity)/(8760.0) # GBP/hr
        self.loadFuelCost(fuelFilePath)

    # load fuel cost method
    def loadFuelCost(self,FILEPATH): 
        fileIN = Utils.loadTextFile(FILEPATH)
        self.yearlyFuelCost = list()
        if(self.genTypeID==0): # coal
            for i in range(len(fileIN)):
                val = fileIN[i]
                newVal = val/1000.0 # tonnes to kg
                newVal = newVal/2.46 # 1 kg of coal produces 2.46 kWh
                newVal = newVal*0.77 # USD to GBP
                self.yearlyFuelCost.append(newVal) # gbp per kWh
        elif(self.genTypeID==1 or self.genTypeID==3): # CCGT and OCGT
            for i in range(len(fileIN)):
                val = fileIN[i]
                newVal = val/100.0 # p/ therm to gbp/therm
                newVal = newVal/29.31 # therms to kWh, 1 therm = 29.31 kWh
           #     print('Fuel cost CCGT GBP/kWh ',)
                self.yearlyFuelCost.append(newVal) # gbp per kWh
        elif(self.genTypeID==2): # Nuclear
            for i in range(len(fileIN)):
                val = fileIN[i]
                newVal = val/100.0 # p/ kWh to gbp/kWh
                self.yearlyFuelCost.append(newVal) # gbp per kWh
        elif(self.genTypeID==4 or self.genTypeID==5 or self.genTypeID==6): # BECCS
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
            self.runingCost = self.runingCost + (curCost)
            self.runingEmissions = self.runingEmissions + (curEmiss)
            self.yearlyEnergyGen = self.yearlyEnergyGen + self.energyGenerated[i]
            self.yearlyProfit = self.yearlyProfit + curProfit
            self.yearlyCost = self.runingCost
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



    
    









        
        
