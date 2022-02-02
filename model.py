import random
import numpy as np
import pandas as pd
import Utils
import os
from customerGroup import customerGroup
from customer import customer
from renewableGenerator import renewableGenerator

from generationCompany import generationCompany
from policyMaker import policyMaker
import TransmissionNetworkOwner as TNO


class ABM():
    
    def __init__(self, params, BASEYEAR,boolEnergyStorage , timesteps = 8760):

        self.params = params
        self.BASEYEAR = BASEYEAR
        self.year = self.BASEYEAR
        self.boolEnergyStorage = boolEnergyStorage 
        self.timesteps = timesteps

        self.numberCustomers = 1 #Number of energy consumers set to 1 by default

        self.energyCustomers = list()
        self.policyMaker = None
        self.elecGenCompanies = list()
        self.elecGenCompaniesNames = list()
        self.distributedGenCompany = None # part of elecGenCompanies
        self.genTechList = list(params["technical_parameters"].index) # list of the technologies used in the model

        # variable to store the results
        self.customerNLs = pd.DataFrame() #list of a number of customers, each customer has 8760 hour data

        self.buildRatePerType = pd.DataFrame(index = self.genTechList,columns=np.arange(self.year, self.year+100))
        self.buildRatePerType.fillna(0, inplace=True)

        self.capacityInstalledMW = pd.DataFrame() # capacity installed in 2010
        self.OneYearHeadroom = []

        self.capacityPerTypePerBus = pd.DataFrame()
        self.capacityPerCompanies = pd.DataFrame()
        self.allGenPerCompany = pd.DataFrame()
        self.allGenPerTechnology = pd.DataFrame()

    def initResultsVariables(self):
        # need to be initialised after generation companies are created
        idx_8760 = np.arange(0, 8760)
        self.allGenPerCompany = pd.DataFrame(columns=self.elecGenCompaniesNames, index=idx_8760) # df of total hourly renewable generation all year           
        self.allGenPerCompany.fillna(0, inplace=True)
        self.allGenPerTechnology = pd.DataFrame(columns=self.genTechList, index=idx_8760)  # df showing the hourly generation for the renewable technologies
        self.allGenPerTechnology.fillna(0, inplace=True)

        temp_cols = [x+'_Derated_Capacity_kW' for x in self.genTechList] + [x+'_Capacity_kW' for x in self.genTechList]
        self.capacityPerCompanies = pd.DataFrame(columns=temp_cols , index=self.elecGenCompaniesNames) # store the capacity by technology type for each companies
        self.capacityPerCompanies.fillna(0, inplace=True)
        return True
    
    def createEnergyCustomers(self, numberCustomers):
        self.numberCustomers = numberCustomers
        energyCustomers = list()
        if numberCustomers==30:
            self.OneYearHeadroom = [-32212711.56,-32067843.49,-31767613.28,-28212832.94,-28021373.43,-29166767.52,-28040878.71,-30277254.05,-31222433.48,-31615902.27,-35658351.5,-38698275.52,-39831850.5,-36304364.7,-40756536.12,-33969231.94,-43217107.73,-46674012.56,-44359251.32,-42836333.58,-41055681.71,-36877967.42,-35329923.93,-29181850.14,-31686007.01,-29468773.98,-28935821.38,-31005560.87,-30411533.39,-29371379.89]

            #Create 30 customers representing the 30 bus bars
            for busbar in range(1,numberCustomers+1):
                cust = customerGroup(self.timesteps, self.BASEYEAR, busbar)
                cust.updateLoadProfile()
                energyCustomers.append(cust)
        else: #default mode has only one customer
            cust = customer(self.timesteps, self.BASEYEAR, 0)
            energyCustomers.append(cust)
        self.energyCustomers = energyCustomers
        return True  

    def createPolicyMaker(self):
        # must be created before energy companies to give them the carbon price
        self.policyMaker = policyMaker(self.params, self.BASEYEAR)
        return True

    # function to add batteries to generation Companies
    def addEnergyStorage(self):
        # these battery capacity values are only needed if a linear increase in battery is implemented
        if(self.BASEYEAR == 2018):
            totalBatteryPower = 700000.0 # 700 MW in 2018
        elif(self.BASEYEAR == 2010):
            totalBatteryPower = 10000.0 #0 MW in 2010 (set at 10MW for test purposes)

        # FES Two Degrees scenario says 3.59 GW batteries in 2018 and 22.512 GW in 2050
        # http://fes.nationalgrid.com/media/1409/fes-2019.pdf page 133
            
        totalFinalBatteryPower = 10000000.0#22512000.0 #10000000.0 # 10 GW in 2050
        totalStartBatteryPower = totalBatteryPower

        temprand=random.randint(1,30) # allocate the battery to a random busbar
        batteryPowerPerCompany = totalBatteryPower/len(self.elecGenCompanies)
        for eGC in self.elecGenCompanies:
            eGC.addBattery(batteryPowerPerCompany, temprand)
        return True

    def createGenerationCompanies(self):

        technology_technical_df = self.params["technical_parameters"]
        
    # --------- Create generation companies -----------------
        print('Adding Generation Companies')
        elecGenCompanies = list()
        elecGenCompNAMESONLY = list()
        if(self.BASEYEAR==2018):
            mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2018_Owners2.csv'
        elif(self.BASEYEAR==2010):
            mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2010_Owners.csv'
            # mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2010_Owners fortestonly.csv'
        GBGenPlantsOwners = pd.read_csv(mainPlantsOwnersFile)
        GBGenPlantsOwners.fillna(0, inplace=True)

        for i in range(len(GBGenPlantsOwners['Station Name'])):
            tempName = GBGenPlantsOwners['Fuel'].iloc[i] #raw
            tempbus = int(GBGenPlantsOwners['Bus'].iloc[i])
            if(not (tempbus == 0) and tempName in self.genTechList):
                curCompName = GBGenPlantsOwners['Company Name'].iloc[i]
                if(not (curCompName in elecGenCompNAMESONLY)):
                    print(curCompName)
                    elecGenCompNAMESONLY.append(curCompName)
                    genCompany = generationCompany(curCompName, self.timesteps, self.params, self.policyMaker.curCO2Price, self.BASEYEAR)    
                    elecGenCompanies.append(genCompany)

        distGenCompany = generationCompany('Distributed Generation', self.timesteps, self.params, self.policyMaker.curCO2Price, self.BASEYEAR)
        elecGenCompanies.append(distGenCompany)
        elecGenCompNAMESONLY.append(distGenCompany.name)
        # -----------------------------------------------------
        # --------- Add plants for main companies -------------

        capacityInstalledMW = {}
        for tech in self.genTechList:
            capacityInstalledMW[tech] = 0 # initialisation

        print('Adding Plants')

        for i in range(len(GBGenPlantsOwners['Station Name'])): # data from 2018 dukes report
            tempName = GBGenPlantsOwners['Fuel'].iloc[i]
            tempbus = int(GBGenPlantsOwners['Bus'].iloc[i])
            if (tempbus > 0) and tempName in self.genTechList: # Bus > 0 ==> the plant is for northern ireland
                curCompName = GBGenPlantsOwners['Company Name'].iloc[i]
                for eGC in elecGenCompanies:
                    if(eGC.name == curCompName):
                        tempName = GBGenPlantsOwners['Fuel'].iloc[i]
                        tempCapKW = GBGenPlantsOwners['Installed Capacity(MW)'].iloc[i]*1000
                        capacityInstalledMW[tempName] = capacityInstalledMW[tempName] + tempCapKW/1000
                        lifetime = int(technology_technical_df.loc[tempName, 'Lifetime_Years'])
                        tempRen = int(technology_technical_df.loc[tempName, 'Renewable_Flag'])
                        subsidy = 0
                        cfdBool = int(technology_technical_df.loc[tempName, 'CfD_Flag'])
                        capMarketBool = False

                        if tempName == 'Wind Offshore':
                            genTypeID = int(technology_technical_df.loc[tempName, "TypeID"])
                            renGen = renewableGenerator('Wind Offshore', genTypeID, tempCapKW, lifetime, 0.0,1,self.OneYearHeadroom[tempbus-1], self.BASEYEAR) # temporary generator to estimate the annual costs
                            subsidy = renGen.estimateCfDSubsidy()

                        tempStartYear = int(GBGenPlantsOwners['StartYear'].iloc[i])
                        tempEndYear = tempStartYear + lifetime
                        if(tempEndYear<self.BASEYEAR):
                            tempEndYear = random.randint(2018, 2025)

                        tempAge = tempStartYear - self.BASEYEAR
                        eGC.addGeneration(tempName, tempRen, tempCapKW, lifetime ,tempStartYear, tempEndYear, tempAge, subsidy, cfdBool, capMarketBool, tempbus, self.OneYearHeadroom[tempbus-1])
    
        print(capacityInstalledMW)
        self.capacityInstalledMW = capacityInstalledMW
        self.elecGenCompanies = elecGenCompanies
        self.distributedGenCompany = distGenCompany
        self.elecGenCompaniesNames = elecGenCompNAMESONLY

        self.policyMaker.elecGenCompanies = elecGenCompanies #add record of the generation companies to the Policy Maker object
        Utils.initBuildRate(self.genTechList, self.buildRatePerType, technology_technical_df) # Initialise the building rate for all the companies and technologies on year 0
        self.policyMaker.buildRatePerType = self.buildRatePerType

        # for i in range(len(GBWindOffPlants['Name'])): # Adding in offshore plants already under construction that are due to come online soon
        #     tempName = 'Wind Offshore'
        #     genTypeID = int(technology_technical_df.loc[tempName, "TypeID"])
        #     tempRen = int(technology_technical_df.loc[tempName, 'Renewable_Flag'])
        #     sYear = GBWindOffPlants['StartYear'].iloc[i]
        #     tempbus = int(GBWindOffPlants['Bus'].iloc[i])

        #     if tempbus>0: #the plant is not in Northern Ireland
        #         if(sYear>2010 and sYear<2014):
        #             tempName = GBWindOffPlants['Type'].iloc[i]
        #             tempCapKW = GBWindOffPlants['Capacity(kW)'].iloc[i]
        #             eYear = GBWindOffPlants['EndYear'].iloc[i]
                    
        #             lifetime = eYear - sYear
        #             renGen = renewableGenerator(tempName, genTypeID, tempCapKW, lifetime, 0.0,1,OneYearHeadroom[tempbus-1], BASEYEAR)
        #             cfdSubsidy = renGen.estimateCfDSubsidy()
        #             distGenCompany.addGeneration(tempName, tempRen, tempCapKW, lifetime ,sYear, 2052, 0, cfdSubsidy, True, False, tempbus, OneYearHeadroom[tempbus-1])
    
                
        # for i in range(len(GBWindOnPlants['Name'])): # Adding in onshore plants already under construction that are due to come online soon
        #     tempName = 'Wind Onshore'
        #     genTypeID = int(technology_technical_df.loc[tempName, "TypeID"])
        #     tempRen = int(technology_technical_df.loc[tempName, 'Renewable_Flag'])
        #     sYear = GBWindOnPlants['StartYear'].iloc[i]
        #     tempbus = GBWindOnPlants['Bus'].iloc[i]
        #     if tempbus>0: #the plant is not in Northern Ireland
        #         if(sYear>2010 and sYear<2013):
        #             tempName = GBWindOnPlants['Type'].iloc[i]
        #             cap = GBWindOnPlants['Capacity(kW)'].iloc[i]
        #             eYear = GBWindOnPlants['EndYear'].iloc[i]
        #             lifetime = eYear - sYear
        #             distGenCompany.addGeneration(tempName, tempRen, tempCapKW, lifetime ,sYear, eYear, 0, 0, False, False, tempbus, OneYearHeadroom[tempbus-1])

        return True

    def addDistributedGeneration(self):

        busbarConstraints = self.params["busbar_constraints"]
        technology_technical_df = self.params["technical_parameters"]

        # --------- Add generation from smaller distributed generation -------------
        
        pvPlantsFile = 'OtherDocuments/OperationalPVs2017test_wOwner.csv' # these records are for end of 2017
        GBPVPlants = pd.read_csv(pvPlantsFile)
        GBPVPlants.fillna(0, inplace=True)

        windOnPlantsFile = 'OtherDocuments/OperationalWindOnshore2017test_wOwner.csv'
        GBWindOnPlants = pd.read_csv(windOnPlantsFile)
        GBWindOnPlants.fillna(0, inplace=True)

        windOffPlantsFile = 'OtherDocuments/OperationalWindOffshore2017test_wOwner.csv'
        GBWindOffPlants = pd.read_csv(windOffPlantsFile)
        GBWindOffPlants.fillna(0, inplace=True)
        print('Adding Additional Distributed Generation')

            ## Add distributed electricity resources
        if(self.BASEYEAR==2018):
            avgPVStartYear = int(round(GBPVPlants['StartYear'].mean()))
            avgWindOnStartYear = int(round(GBWindOnPlants['StartYear'].mean()))
            avgWindOffStartYear =int(round(GBWindOffPlants['StartYear'].mean()))
        else:
            avgPVStartYear = self.BASEYEAR - 1
            avgWindOnStartYear = self.BASEYEAR - 1
            avgWindOffStartYear = self.BASEYEAR - 1
        
        solarCapMWBASEYEAR = technology_technical_df.loc['Solar', 'DER_Capacity_Installed_'+str(self.BASEYEAR)+'_MW']
        windOnshoreCapMWBASEYEAR = technology_technical_df.loc['Wind Onshore', 'DER_Capacity_Installed_'+str(self.BASEYEAR)+'_MW']
        windOffshoreCapMWBASEYEAR = technology_technical_df.loc['Wind Offshore', 'DER_Capacity_Installed_'+str(self.BASEYEAR)+'_MW']

        sCapkW = (solarCapMWBASEYEAR - self.capacityInstalledMW['Solar'])*1000.0
        wOnCapkW = (windOnshoreCapMWBASEYEAR - self.capacityInstalledMW['Wind Onshore'])*1000.0
        wOffCapkW = (windOffshoreCapMWBASEYEAR - self.capacityInstalledMW['Wind Offshore'])*1000.0  #actual data- recod large plant=distributed

        tempBus=random.randint(1,30)
        lifetime = int(technology_technical_df.loc['Solar', 'Lifetime_Years'])
        self.distributedGenCompany.addGeneration('Solar', 1, sCapkW, lifetime,avgPVStartYear, 2052, (avgPVStartYear-self.BASEYEAR), 0, False, False, tempBus, self.OneYearHeadroom[tempBus-1])

        tempBus=random.randint(1,30)
        lifetime = int(technology_technical_df.loc['Wind Onshore', 'Lifetime_Years'])
        self.distributedGenCompany.addGeneration('Wind Onshore', 1, wOnCapkW, lifetime, avgWindOnStartYear, 2052, (avgWindOnStartYear-self.BASEYEAR), 0.0, False,  False, tempBus, self.OneYearHeadroom[tempBus-1])

        tempBus = random.choice(list(busbarConstraints[busbarConstraints['Wind Offshore']>0].index))
        genTypeID = int(technology_technical_df.loc['Wind Offshore', "TypeID"])
        lifetime = int(technology_technical_df.loc['Wind Offshore', 'Lifetime_Years'])
        renGen = renewableGenerator('Wind Offshore', genTypeID,  wOffCapkW, lifetime, 0.0,1,self.OneYearHeadroom[tempBus-1], self.BASEYEAR)  # temporary generator to estimate the annual costs, for cfd
        
        cfdSubsidy = renGen.estimateCfDSubsidy()
        self.distributedGenCompany.addGeneration('Wind Offshore', 1, wOffCapkW, lifetime, avgWindOffStartYear, 2052, (avgWindOffStartYear-self.BASEYEAR), cfdSubsidy, True, False,tempBus, self.OneYearHeadroom[tempBus-1])
        return True


    def initTechPortoflio(self):
        ## init the technologies that can be built by each company based on their current portfolio
        technologyFamilies = self.params["technology_families"]
        
        for eGC in self.elecGenCompanies:
            tempListTechnology = []
            installedTech = []
            for genName in eGC.listTechnologyPortfolio:
                installedTech.append(genName)
                sameFamilyTechnologies = list(technologyFamilies[technologyFamilies[genName]>0].index)
                tempListTechnology= tempListTechnology + sameFamilyTechnologies
            eGC.listTechnologyPortfolio = list(set(tempListTechnology))
            print("list technologies")
            print(eGC.name, eGC.listTechnologyPortfolio)
            print(set(installedTech))
        return True

    def getCapacityInstalled(self):
        # Get the capacity installed for each technology type, by companies, and by bus

        temp_cols = [x+'_Derated_Capacity_kW' for x in self.genTechList] + [x+'_Capacity_kW' for x in self.genTechList]
        
        frames_capacityPerTypePerBus = []
        for eGC in self.elecGenCompanies: #all companies have been added at the beginning
            eGC.calculateCapacityByType(self.genTechList, [eC.busbar for eC in self.energyCustomers])
            temp_capacityPerTypePerBus = eGC.capacityPerTypePerBus.copy()
            self.capacityPerCompanies.loc[eGC.name, temp_cols] = temp_capacityPerTypePerBus[temp_cols].sum().values
            frames_capacityPerTypePerBus.append(temp_capacityPerTypePerBus.reset_index())
            
        self.capacityPerTypePerBus = pd.concat(frames_capacityPerTypePerBus).groupby("Busbars").sum()
        
        return True


    def getCustomerElectricityDemand(self):
        
        for eC in self.energyCustomers:
            curCustNL = eC.runSim() # sim energy consumption each hour
            self.customerNLs[eC.busbar] = curCustNL

        #------------- get total customer electricity demand -------------
        totalCustDemand = np.array(self.customerNLs.sum(axis=1).values)
        peakDemand = np.max(totalCustDemand)
        return peakDemand, totalCustDemand


    def dispatchRenewables(self, netDemand):
        print("dispatchRenewables...")
        dfTech = self.params["technical_parameters"]
        listRgen = list(dfTech.loc[dfTech['Renewable_Flag']==1, :].index)

        for genName in listRgen:
            print(genName)
            total_arr_hourlyGen = np.zeros(self.timesteps)
            for eGC in self.elecGenCompanies:
                arr_hourlyGen = eGC.getRenewableGenerationByType(genName)
                total_arr_hourlyGen = np.add(total_arr_hourlyGen, arr_hourlyGen)
                self.allGenPerCompany[eGC.name] = self.allGenPerCompany[eGC.name] + arr_hourlyGen

            self.allGenPerTechnology[genName] = total_arr_hourlyGen

        totYearRGenKWh = self.allGenPerTechnology.sum().sum() # sum of the renewable generation from all companies

        if len(self.allGenPerTechnology.columns)>1:
            totalRenewGen = self.allGenPerTechnology.sum(axis=1).values # get total renew generation profile 8760 values
        else:
            totalRenewGen = self.allGenPerTechnology.values # get total renew generation profile 8760 values

        netDemand = np.subtract(netDemand, totalRenewGen)
        hourlyCurtail = -netDemand
        hourlyCurtail = hourlyCurtail.clip(min=0) #x<0 when demand>generation
        netDemand = netDemand.clip(min=0)

        print("End of dispatchRenewables")
        return netDemand, hourlyCurtail


    def dispatchTradGen(self, netDemand, hourlyCurtail, DispatchBeforeStorage):
        dfTech = self.params["technical_parameters"]
        tradGen = dfTech.loc[(dfTech['Dispatch_Before_Storage']==DispatchBeforeStorage) & (dfTech['Renewable_Flag']==0), :].copy()
        tradGen = tradGen.sort_values(by='MeritOrder', ascending=True)
        temp_cols = [x+'_Derated_Capacity_kW' for x in self.genTechList] + [x+'_Capacity_kW' for x in self.genTechList]
        tempNetD = netDemand.copy()
        capacityPerType = self.capacityPerTypePerBus[temp_cols].sum()
        print('Dispatch of {0}'.format(list(tradGen.index)))
        tempNetD, tempHourlyCurtail = Utils.dispatchTradGen(netDemand, self.elecGenCompanies, tradGen,capacityPerType, self.capacityPerCompanies, self.allGenPerTechnology,self.allGenPerCompany, self.year)
        hourlyCurtail = np.add(hourlyCurtail,tempHourlyCurtail)
        netDemand = tempNetD

        return netDemand, hourlyCurtail

    def dispatchBatteries(self, netDemand):
        if self.boolEnergyStorage:
            print('Charging/Discharging of batteries...')
            tNetDemand = netDemand.copy()
            for eGC in self.elecGenCompanies:
                tNetDemand = eGC.chargeDischargeBatteryTime(tNetDemand)
            netDemand = tNetDemand # final net demand after account for all companies
        return netDemand


    def getWholeSalePrice(self, hourlyCurtail):
        # calculating wholesale electricity price from marginal cost of each generator
        wholesaleEPrice, nuclearMarginalCost = Utils.getWholesaleEPrice(self.elecGenCompanies)
        for k in range(len(wholesaleEPrice)): #8760
            if hourlyCurtail[k]>0:
                wholesaleEPrice[k] = 0 - nuclearMarginalCost[k]
        return wholesaleEPrice


    def getEmissions(self, wholesaleEPrice):
        # update economics of all plants and batteries and calculate the emissions
        # update the current wholesaleEPrice to calculate the profit made by each plant 
        yearlyEmissions = 0.0
        for eGC in self.elecGenCompanies:
            eGC.calcRevenue(wholesaleEPrice) #return the ROI and NPV of all the plants owned by this generator company
            yearlyEmissions += eGC.calcEmissions() #kgCO2
        return yearlyEmissions


    def exportPlantsEconomics(self):
        # Extract NPV values of all the plants
        npv_dict = {}
        
        for eGC in self.elecGenCompanies:
            for i,gen in enumerate(eGC.renewableGen+eGC.traditionalGen):
                gbp_kwh = 0
                if gen.yearlyEnergyGen>0:
                    gbp_kwh = gen.yearlyIncome/gen.yearlyEnergyGen
                npv_dict[(eGC.name, gen.name, str(i))] = [gen.yearlyIncome, gen.yearlyCost, gen.NPV, gen.ROI, gen.getActCapFactor(), gbp_kwh, gen.capitalSub, gen.CFDPrice]
        fileOut = self.params["path_save"] + 'PlantsEconomics_'+str(self.year)+'.csv'        
        pd.DataFrame(npv_dict, index=["Income_GBP", "Cost_GBP", "NPV_GBP", "ROI", "Capacity_Factor", "Income_GBP/kWh", "Capital_Subsidy_GBP/kW", "CfD_Subsidy_GBP/kWh" ]).to_csv(fileOut)
        return True


    def installNewCapacity(self, totalCustDemand, wholesaleEPrice):
        capacityPerBusValues = self.capacityPerTypePerBus.T.sum().values
        self.OneYearHeadroom = TNO.EvaluateHeadRoom(capacityPerBusValues,totalCustDemand)
        peakDemand = np.max(totalCustDemand)
        
        # cfd auction
        self.policyMaker.cfdAuction(3, 6000000, 20, self.OneYearHeadroom, np.mean(wholesaleEPrice)) # 3 years, 6 GW to be commissioned, max 20 years construction time

        # Capacity auction
        estPeakD, estDeRCap = self.policyMaker.capacityAuction(4, peakDemand, False, self.OneYearHeadroom,)

        # Capacity built by each company individually without the help of subsidies
        print("Companies investments...")
        frames = []
        for eGC in self.elecGenCompanies:
            temp_df = eGC.nextInvestment()
            frames.append(temp_df)

        fileOut = self.params["path_save"] + 'ROINPV_'+str(self.year)+'.csv'
        newCapacity = pd.concat(frames, axis=0) #Capacity that companies want to build
        newCapacity = self.policyMaker.capBuildRate(newCapacity, "ROI", False) #Capacity that will be built after removing capping the amount of technology of each type
        if len(newCapacity)>0:
            newCapacity.to_csv(fileOut)

            for genName, row in newCapacity.iterrows():
                eGCName = row["Generation_Company"]
                eGC = Utils.getGenerationCompany(eGCName, self.elecGenCompanies)
                capacitykW = row["Capacity_kW"]
                startYear = row["Start_Year"]
                tcapSub = 0
                cfdBool = False
                capMarketBool = False
                busbar = row["Busbar"]
                eGC.addToConstructionQueue(genName, capacitykW, startYear, tcapSub, cfdBool, capMarketBool, busbar)

        return estPeakD, estDeRCap


    def incrementYear(self, carbonIntensity):
        self.policyMaker.incrementYear()
        # update CO2 Price for next year
        newCO2Price = self.policyMaker.getNextYearCO2Price(carbonIntensity) #carbon intensity in gCO2/kWh input

        # Update CO2 Price and check the construction queue to build plants
        for eGC in self.elecGenCompanies:
            eGC.incrementYear(self.OneYearHeadroom, newCO2Price)

        # demand elasticity
        for eC in self.energyCustomers:
            demandChangePC = eC.incrementYear(0.0) #

        self.initResultsVariables()
        self.year = self.year + 1




######### main method, code starts executing from here ##################
if __name__ == '__main__':

    np.random.seed(42)
    random.seed(42)

    print('========================begin======================== ')

    # Parameters of the simulation 
    BASEYEAR = 2010 # 2010
    maxYears = 5 #16 = 2025 #9=2018 #  25 = 2034, 41 = 2050
    timeSteps = 8760
    boolEnergyStorage = False
    boolLinearBatteryGrowth = True
 
    
    # Initialisation of variables
    idx_year = np.arange(BASEYEAR, BASEYEAR+maxYears)
    params = Utils.getParams()
    technology_technical_df = params["technical_parameters"]
    genTechList = list(technology_technical_df.index)
    


    list_tgen = list(technology_technical_df.loc[technology_technical_df['Renewable_Flag']==0, :].index)
    list_rgen = list(technology_technical_df.loc[technology_technical_df['Renewable_Flag']==1, :].index)

    temp_cols = [x+'_Derated_Capacity_kW' for x in genTechList] + [x+'_Capacity_kW' for x in genTechList]

    # Components where results are stored
    capacityPerType = pd.DataFrame(columns=temp_cols, index=idx_year) # store the capacity by technology type for each year of the simulation
    capacityPerType.fillna(0, inplace=True)

    DfSystemEvolution = pd.DataFrame() # Store the capacity, derated capacity, peak demand, capacity margin
    DfHeadroomYear = pd.DataFrame() 

    DfWholesalePrices = pd.DataFrame()

    #Creation of the agents
    ABMmodel = ABM(params, BASEYEAR, boolEnergyStorage)
    ABMmodel.createPolicyMaker()
    ABMmodel.createEnergyCustomers(30)
    ABMmodel.createGenerationCompanies()
    ABMmodel.addDistributedGeneration()
    ABMmodel.initTechPortoflio()


    for eGC in ABMmodel.elecGenCompanies:
        print(eGC.listTechnologyPortfolio)