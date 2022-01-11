from __future__ import division

import random
import numpy as np
from customerGroup import customerGroup
from renewableGenerator import renewableGenerator

from generationCompany import generationCompany
from policyMaker import policyMaker
from heatProvider import heatProvider
import Utils
import random
import pandas as pd 
import TransmissionNetworkOwner as TNO
import os
import pandas as pd


# method to count number of companies with plants of each technology, e.g. hydro, CCGT, etc.
def countCompaniesPerTech(genCompanies, genTechList):
    genTypeCompanyCount = list()
    for i in range(len(genTechList)):
        genTypeCompanyCount.append(0)
        
    for i in range(len(genCompanies)):
        genTypes, genCap, genTypesNonZero = genCompanies[i].getGenPortfolio()

        for j in range(len(genTypesNonZero)):
            indx = genTechList.index(genTypesNonZero[j])
            genTypeCompanyCount[indx] +=1

    for i in range(len(genTechList)):
        print('%s companies with %s plants '%(str(genTypeCompanyCount[i]),str(genTechList[i])))

    return genTypeCompanyCount #e.g. 4 companies with CCGT

# method to get the capacity of each technology, e.g. 4 GW of solar, etc.
def getCapacityPerTech(genCompanies):
    techTypes = list()
    techCap = list()
    techDeRCap = list()

    for i in range(len(genCompanies)):
        indx = len(genCompanies[i].yearlyCapPerTech)-1
        capPerTech = genCompanies[i].yearlyCapPerTech #50 year
        deRCapPerTech = genCompanies[i].yearlyDerateCapPerTech
        techNames = genCompanies[i].techNames

        for j in range(len(techNames)):
            yindx = len(capPerTech[j])-1 #last year

            if(not (techNames[j] in techTypes)):
                techTypes.append(techNames[j])
                techCap.append(capPerTech[j][yindx])
                techDeRCap.append(deRCapPerTech[j][yindx])
            else:
                tIndx = techTypes.index(techNames[j])
                techCap[tIndx] = techCap[tIndx] + capPerTech[j][yindx]
                techDeRCap[tIndx] = techDeRCap[tIndx] + deRCapPerTech[j][yindx]

    for i in range(len(techTypes)):
        print('%s : Cap (MW) = %s : Derated Cap (MW) = %s '%(techTypes[i],str(techCap[i]/1000.0),str(techDeRCap[i]/1000.0)))

    return techTypes, techCap, techDeRCap


######### main method, code starts executing from here ##################
if __name__ == '__main__':

    np.random.seed(42)
    random.seed(42)

    print('========================begin======================== ')
    # Utils.resetCurYearCapInvest() # what does it do?
    BASEYEAR = 2010 # 2010
    # file = open('BASEYEAR.txt', 'w') 
    # file.write(str(BASEYEAR)) 
    # file.close()

    # path to where you want results output to
    RESULTS_FILE_PATH = 'Results/2050/'

    maxYears = 41 #16 = 2025 #9=2018 #  25 = 2034, 41 = 2050
    timeSteps=8760

    boolDraw = True
    boolEnergyStorage = True
    boolLinearBatteryGrowth = True

    # these battery capacity values are only needed if a linear increase in battery is implemented
    if(BASEYEAR == 2018):
        totalBatteryCap = 700000.0 # 700 MW in 2018
    elif(BASEYEAR == 2010):
        totalBatteryCap = 0.0 #10000.0 # 10 MW in 2010????
  #      totalBatteryCap = 22512000.0 #10000.0 # 10 MW in 2010????

    # FES Two Degrees scenario says 3.59 GW batteries in 2018 and 22.512 GW in 2050
    # http://fes.nationalgrid.com/media/1409/fes-2019.pdf page 133
        
    totalFinalBatteryCap = 10000000.0#22512000.0 #10000000.0 # 10 GW in 2050
 #   totalFinalBatteryCap = 10000000.0 # 10 GW in 2050
    totalStartBatteryCap = totalBatteryCap


    yearlyheadroom = list()
    policy = policyMaker(RESULTS_FILE_PATH)
    OneYearHeadroom = [-32212711.56,-32067843.49,-31767613.28,-28212832.94,-28021373.43,-29166767.52,-28040878.71,-30277254.05,-31222433.48,-31615902.27,-35658351.5,-38698275.52,-39831850.5,-36304364.7,-40756536.12,-33969231.94,-43217107.73,-46674012.56,-44359251.32,-42836333.58,-41055681.71,-36877967.42,-35329923.93,-29181850.14,-31686007.01,-29468773.98,-28935821.38,-31005560.87,-30411533.39,-29371379.89]
    #initialise with 2010
    energyCustomers = list()

    # If you want to break down the customers by region, use this code
    '''
    cust = customerGroup(3147588, 0.00, 1, 'London') 
    energyCustomers.append(cust)
    cust = customerGroup(2466175, 0.00, 2, 'Scotland') 
    energyCustomers.append(cust)
    cust = customerGroup(3617257, 0.00, 3, 'South East') 
    energyCustomers.append(cust)
    cust = customerGroup(3109317, 0.00, 4, 'North West') 
    energyCustomers.append(cust)
    cust = customerGroup(1945382, 0.00, 5, 'East Midlands') 
    energyCustomers.append(cust)
    cust = customerGroup(2495526, 0.00, 6, 'East England') 
    energyCustomers.append(cust)
    cust = customerGroup(2291848, 0.00, 7, 'Yorkshire') 
    energyCustomers.append(cust)
    cust = customerGroup(2324274, 0.00, 8, 'South West') 
    energyCustomers.append(cust)
    cust = customerGroup(2348914, 0.00, 9, 'West Midlands') 
    energyCustomers.append(cust)
    cust = customerGroup(1349610, 0.00, 10, 'Wales') 
    energyCustomers.append(cust)
    cust = customerGroup(1168992, 0.00, 11, 'North East') 
    energyCustomers.append(cust)
    cust = customerGroup(0, 0.00, 12, 'Non-Residential') 
    energyCustomers.append(cust)
    
    '''

    # if you want to use 1 customer for all GB, use this code
    #cust = customerGroup(0, 0.00, 13, 'All GB Consumers') 
  
    #Create 30 customers representing the 30 bus bars
    for c in range(1,31):
        cust = customerGroup(c)
        energyCustomers.append(cust)

    # list of generation technologies
    technologies_dataset = pd.read_csv('technologies_dataset.csv', index_col = 0)
    genTechList = list(technologies_dataset.index)


    # --------- Create generation companies -----------------
    print('Adding Generation Companies')
    elecGenCompanies = list()
    elecGenCompNAMESONLY = list()
    if(BASEYEAR==2018):
        mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2018_Owners2.csv'
    elif(BASEYEAR==2010):
        mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2010_Owners.csv'
        # mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2010_Owners fortestonly.csv'
    GBGenPlantsOwners = Utils.readCSV(mainPlantsOwnersFile)

    for i in range(len(GBGenPlantsOwners['Station Name'])):
        tempName = GBGenPlantsOwners['Fuel'].iloc[i] #raw
        tempbus = GBGenPlantsOwners['Bus'].iloc[i]
        if(not (tempbus == 0) and tempName in genTechList):
            curCompName = GBGenPlantsOwners['Company Name'].iloc[i]
            if(not (curCompName in elecGenCompNAMESONLY)):
                print(curCompName)
                elecGenCompNAMESONLY.append(curCompName)
                genCompany = generationCompany(timeSteps)
                genCompany.name = curCompName        
                genCompany.removeGeneration()
                elecGenCompanies.append(genCompany)
            
    # -----------------------------------------------------
    # --------- Add plants for main companies -------------

    capacityInstalledMW = {}
    for tech in genTechList:
        capacityInstalledMW[tech] = 0 # initialisation

    print('Adding Plants')
    totCoalSubs = 15000000 # 15GW of cap market subs for coal
    curCoalSub = 0

    for i in range(len(GBGenPlantsOwners['Station Name'])): # data from 2018 dukes report
        tempName = GBGenPlantsOwners['Fuel'].iloc[i]
        tempbus = GBGenPlantsOwners['Bus'].iloc[i]
        if (tempbus > 0) and tempName in genTechList: # Bus > 0 ==> the plant is for northern ireland
            curCompName = GBGenPlantsOwners['Company Name'].iloc[i]
            for eGC in elecGenCompanies:
                if(eGC.name == curCompName):
                    tempName = GBGenPlantsOwners['Fuel'].iloc[i]
                    tempTypeID = -1 
                    lifetime = 0
                    tempRen = 0
                    tempCapKW = GBGenPlantsOwners['Installed Capacity(MW)'].iloc[i]*1000
                    tempbus = GBGenPlantsOwners['Bus'].iloc[i]
                    capacityInstalledMW[tempName] = capacityInstalledMW[tempName] + tempCapKW/1000
                    lifetime = int(technologies_dataset.loc[tempName, 'Lifetime_Year'])
                    tempRen = int(technologies_dataset.loc[tempName, 'Renewable_Flag'])
                    subsidy = 0
                    cfdBool = int(technologies_dataset.loc[tempName, 'CFD_Flag'])
                    capMarketBool = int(technologies_dataset.loc[tempName, 'Capacity_Market_Flag'])

                    # print('Name {0}, lifetime {1}, renewable Flag {2}'.format(tempName, lifetime, tempRen))

                    if tempName == 'Coal':
                        if(curCoalSub<totCoalSubs):
                            coalCapSub = 75
                            curCoalSub = curCoalSub + tempCapKW
                            coalCapMarketBool = True
                        else:
                            coalCapSub = 0
                            coalCapMarketBool = False

                    if tempName == 'Wind Offshore':
                        renGen = renewableGenerator(5,8760, tempCapKW,0.0,1,OneYearHeadroom[0]) # temporary generator to estimate the annual costs
                        yearCost, subsidy = renGen.estAnnualCosts(tempCapKW)

                    tempStartYear = int(GBGenPlantsOwners['StartYear'].iloc[i])
                    tempEndYear = tempStartYear + lifetime
                    if(tempEndYear<BASEYEAR):
                        tempEndYear = random.randint(2018, 2025)

                    tempAge = tempStartYear - BASEYEAR
                    eGC.addGeneration(tempName, tempTypeID, tempRen, tempCapKW, tempStartYear, tempEndYear, tempAge, subsidy, cfdBool, capMarketBool, tempbus, OneYearHeadroom[tempbus-1])
 
    print(capacityInstalledMW)
    # --------------------------------------------------------------------------

    # --------- Add generation from smaller distributed generation -------------
    
    distGenCompany = generationCompany(timeSteps)
    distGenCompany.name = 'Distributed Generation'
    distGenCompany.removeGeneration()
    
    pvPlantsFile = 'OtherDocuments/OperationalPVs2017test_wOwner.csv' # these records are for end of 2017
    GBPVPlants = Utils.readCSV(pvPlantsFile)
    
    windOnPlantsFile = 'OtherDocuments/OperationalWindOnshore2017test_wOwner.csv'
    GBWindOnPlants = Utils.readCSV(windOnPlantsFile)
    
    windOffPlantsFile = 'OtherDocuments/OperationalWindOffshore2017test_wOwner.csv'
    GBWindOffPlants = Utils.readCSV(windOffPlantsFile)
    print('Adding Additional Distributed Generation')


    for i in range(len(GBWindOffPlants['Name'])): # Adding in offshore plants already under construction that are due to come online soon
        
        sYear = GBWindOffPlants['StartYear'].iloc[i]
        tempbus = GBWindOffPlants['Bus'].iloc[i]
        if tempbus>0: #the plant is not in Northern Ireland
            if(sYear>2010 and sYear<2014):
                tempName = GBWindOffPlants['Type'].iloc[i]
                cap = GBWindOffPlants['Capacity(kW)'].iloc[i]
                eYear = GBWindOffPlants['EndYear'].iloc[i]
                tempbus = GBWindOffPlants['Bus'].iloc[i]
                lifetime = eYear - sYear
                renGen = renewableGenerator(5,8760, cap,0.0, tempbus,OneYearHeadroom[tempbus-1]) # temporary generator to estimate the annual costs
                yearCost, yCostPerKWh = renGen.estAnnualCosts(cap)
                if(tempCapKW==183600):
                    print('Wind offshore')
                    print('yearCost ',yearCost)
                    print('2 ')
                    input('wait')
                distGenCompany.addGeneration('Wind Offshore', -1, 1, cap, sYear, 2052, 0, yearCost, True, False, tempbus, OneYearHeadroom[tempbus-1])
            
    for i in range(len(GBWindOnPlants['Name'])): # Adding in onshore plants already under construction that are due to come online soon
        sYear = GBWindOnPlants['StartYear'].iloc[i]
        tempbus = GBWindOnPlants['Bus'].iloc[i]
        if tempbus>0: #the plant is not in Northern Ireland
            if(sYear>2010 and sYear<2013):
                tempName = GBWindOnPlants['Type'].iloc[i]
                cap = GBWindOnPlants['Capacity(kW)'].iloc[i]
                eYear = GBWindOnPlants['EndYear'].iloc[i]
                lifetime = eYear - sYear
                distGenCompany.addGeneration('Wind Onshore', -1, 1, cap, sYear, eYear, 0, 0.0, False, False, tempbus, OneYearHeadroom[tempbus-1])
        

    if(BASEYEAR==2018):
        avgPVStartYear = int(round(GBPVPlants['StartYear'].mean()))
        avgWindOnStartYear = int(round(GBWindOnPlants['StartYear'].mean()))
        avgWindOffStartYear =int(round(GBWindOffPlants['StartYear'].mean()))
    else:
        avgPVStartYear = BASEYEAR - 1
        avgWindOnStartYear = BASEYEAR - 1
        avgWindOffStartYear = BASEYEAR - 1
    
    print('avgPVStartYear ',avgPVStartYear)
    print('avgWindOnStartYear ',avgWindOnStartYear)
    print('avgWindOffStartYear ',avgWindOffStartYear)

    solarCapMWBASEYEAR = technologies_dataset.loc['Solar', 'DER_Capacity_Installed_'+str(BASEYEAR)+'_MW']
    windOnshoreCapMWBASEYEAR = technologies_dataset.loc['Wind Onshore', 'DER_Capacity_Installed_'+str(BASEYEAR)+'_MW']
    windOffshoreCapMWBASEYEAR = technologies_dataset.loc['Wind Offshore', 'DER_Capacity_Installed_'+str(BASEYEAR)+'_MW']

    sCapkW = (solarCapMWBASEYEAR - capacityInstalledMW['Solar'])*1000.0
    wOnCapkW = (windOnshoreCapMWBASEYEAR - capacityInstalledMW['Wind Onshore'])*1000.0
    wOffCapkW = (windOffshoreCapMWBASEYEAR - capacityInstalledMW['Wind Offshore'])*1000.0  #actual data- recod large plant=distributed

    print('sCapkW ',sCapkW) # distributed capacity
    print('wOnCapkW ',wOnCapkW)
    print('wOffCapkW ',wOffCapkW)
    temprand=random.randint(1,30)
    distGenCompany.addGeneration('Solar', -1, 1, sCapkW, avgPVStartYear, 2052, (avgPVStartYear-BASEYEAR), 0.0, False, False, temprand, OneYearHeadroom[temprand-1])

    temprand=random.randint(1,30)
    distGenCompany.addGeneration('Wind Onshore', -1, 1, wOnCapkW, avgWindOnStartYear, 2052, (avgWindOnStartYear-BASEYEAR), 0.0, False,  False, temprand, OneYearHeadroom[temprand-1])
    
    renGen = renewableGenerator(5,8760, wOffCapkW,0.0,1,OneYearHeadroom[0]) # temporary generator to estimate the annual costs, for cfd
    yearCost, yCostPerKWh = renGen.estAnnualCosts(wOffCapkW)
    temprand = random.choice([1,2,7,8,9,10,11,12,13,15,16,19,20,26,27,28,29])
    distGenCompany.addGeneration('Wind Offshore', -1, 1, wOffCapkW, avgWindOffStartYear, 2052, (avgWindOffStartYear-BASEYEAR), yearCost, True, False,temprand, OneYearHeadroom[temprand-1])

    elecGenCompanies.append(distGenCompany)


    # Not clear how is the build rate calculated? should it be in the generationCompany.py file instead of electricityGenerator.py?
    for eGC in elecGenCompanies:
        eGC.updateBuildRates()
        tname1 = eGC.name
        print('name, ',tname1)

    if(boolEnergyStorage):
        batteryCapPerCompany = totalBatteryCap/len(elecGenCompanies)
        for eGC in elecGenCompanies:
            eGC.removeBatteries()
    annualStorageCap = list()
    
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # ---------------------------- Simulation begins here ----------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    
    
    
    heatAndGas = list() # ignore this for now
    gasProv = heatProvider() 
    heatAndGas.append(gasProv)
    demandCoeff = 1.0 # coefficient to scale non residential demand based on price elasticity#how mauch percentage change compared to 2018. e.g. 180%


    capacityPerType = pd.DataFrame() # store the capacity by technology type for each year of the simulation
    capacityPerBus = pd.DataFrame(columns=[eC.busbar for eC in energyCustomers]) # store the capacity by bus for each year of the simulation

    capacityPerCompanies = pd.DataFrame() # store the capacity by technology type for each companies
    DfSystemEvolution = pd.DataFrame() # Store the capacity, derated capacity, peak demand, capacity margin
    DfHeadroomYear = pd.DataFrame() 

    for currentYear in range(maxYears): # Loop through years

        hourlyCurtail = list()
        hourlyLossOfLoad = list()

        DfNetDemand = pd.DataFrame()
        

        print('year ',(BASEYEAR+currentYear))
        print('y ',(currentYear))




        #################### Add in some BECCS in 2019 ###############
        
        if(BASEYEAR+currentYear == 2019):
            cName = 'Drax Power Ltd'
            BECCSAddBool = False
            for eGC in elecGenCompanies:
                if eGC.name == cName:
                    temprand=random.choice([2,7,10,12,13,14,15,16,17,18,19,20,22,23,24,26,28,30])
                    #addGeneration(self, genName, genTypeID, renewableID, capacityKW, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom)
                    eGC.addGeneration('BECCS', 9, 0, 500000.0, 2025, 2051, 0, 0.0, False, False, temprand, OneYearHeadroom[temprand-1])
                    BECCSAddBool = True
                    print('BECCS added')
            if(not BECCSAddBool):
                input('BECCS not added ******')

        ################### Add in some Hydrogen in 2035 ###############
        
        if(BASEYEAR+currentYear == 2035):
            cHydrogenName = list(['Baglan Generation Ltd', 'Barking Power', 'Centrica','Citigen (London) UK Ltd', 'Coolkeeragh ESB Ltd','Corby Power Ltd', 'Cory Energy Company Ltd','Derwent Cogeneration','Drax Power Ltd','EDF Energy','E.On UK','GDF Suez','International Power/Mitsui','Premier Power Ltd','Rocksavage Power Co. Ltd','RWE Npower Plc','Thermal','Cruachan Thermal','Seabank Power Limited','Spalding Energy Company Ltd'])
            HydrogenAddBool = False
            for eGC in elecGenCompanies:
                if eGC.name in cHydrogenName:
                    temprand=random.randint(1,30)
                    #addGeneration(self, genName, genTypeID, renewableID, capacityKW, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom)
                    eGC.addGeneration('Hydrogen', 11, 0, 1.5, 2035, 2044, 0, 0.0, False, False, temprand, OneYearHeadroom[temprand-1])
                    HydrogenAddBool = True
                    print('Hydrogen added')
            if(not HydrogenAddBool):
                input('Hydrogen not added ******')      
        
        


        # Get the capacity installed for each technology type, by companies, and by bus
        totalDeRCapSum = 0
        totalCapSum = 0
        for genType in technologies_dataset.index:
            deRCapSum = 0 
            capSum = 0
            for eGC in elecGenCompanies: #all companies have been added at the beginning
                boolRenewable = int(technologies_dataset.loc[genType, 'Renewable_Flag'])
                genTypeID = int(technologies_dataset.loc[genType, 'TypeID'])
                curCap, curDeRCap = eGC.getCapacityByType(genTypeID, boolRenewable) # a value, total capacity of a tech, a company, summed by all plants 
                deRCapSum = deRCapSum + curDeRCap
                capSum = capSum + curCap #a value, total capacity of a tech, summed by all companies

                capacityPerCompanies.loc[eGC.name, genType+'_Derated_Capacity_kW'] = curDeRCap
                capacityPerCompanies.loc[eGC.name, genType+'_Capacity_kW'] = curCap

            capacityPerType.loc[BASEYEAR+currentYear, genType+'_Derated_Capacity_kW'] = deRCapSum
            capacityPerType.loc[BASEYEAR+currentYear, genType+'_Capacity_kW'] = capSum
            totalDeRCapSum = totalDeRCapSum + deRCapSum
            totalCapSum = totalCapSum + capSum
        
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_kW'] = totalCapSum
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Derated_Capacity_kW'] = totalDeRCapSum

        if boolEnergyStorage:
            totalBatteryCap = 0.0
            for eGC in elecGenCompanies:
                eGC.setBatteryWholesalePrice()
                totalBatteryCap = totalBatteryCap + eGC.getBatteryCapKW()
            
            # annualStorageCap.append(totalBatteryCap)
            # yearlytotalbatterycap.append(totalBatteryCap)

        for d in range (1): # set to 1 as each customer will simulate 8760 hours (365 days)
            customerNLs = pd.DataFrame() #list of a number of customers, each customer has 8760 hour data
            customerHeatLoads = pd.DataFrame()
            totalCustDemand = list()
            custElecBills = pd.DataFrame()

            totalRenewGen = list()

            for eC in energyCustomers:
                curCustNL, curCustHeat = eC.runSim() # sim energy consumption each hour
                # customerNLs.append(curCustNL)
                customerNLs[eC.busbar] = curCustNL
                customerHeatLoads[eC.busbar] = curCustHeat
                custElecBills[eC.busbar] = eC.elecCost




            # --------------- Heat Demand -----------------
            # again, ignore this section for now
            # get heat and gas providers to meet demand
            # Not use anywhere for now? not sure what is the role of the heatProvider
            # for c in range(len(heatAndGas)):
            #     curHeatGen,newHeatD = heatAndGas[c].getGeneration(customerHeatLoads.sum(axis=1).values)
            #     tempHeatD = list()
            #     tempHeatD = newHeatD

            #------------- get total customer electricity demand -------------
            totalCustDemand = customerNLs.sum(axis=1).values
            peakDemand = customerNLs.sum(axis=1).max()

            # ---------------- get renewable generation --------------------

            allRGenPerCompany = pd.DataFrame() # df of total hourly renewable generation all year           
            allRGenPerTechnology = pd.DataFrame() # df showing the hourly generation for the renewable technologies

            for eGC in elecGenCompanies:
                # rGenPlants = dataframe of 8760 lists of rGen, e.g. 40 lists for 40 plants
                #  rGenTypes = dataframe of 8760 lists of rGen, e.g. 5 lists for 5 types
                rGenPlants, rGenTypes  = eGC.getRenewableGen()
                allRGenPerCompany[eGC.name] = rGenPlants.sum(axis=1).values
                tempRGens = list()

                for name in rGenTypes.columns:
                    if name in allRGenPerTechnology.columns:
                        allRGenPerTechnology[name] = allRGenPerTechnology[name] + rGenTypes[name]
                    else:
                        allRGenPerTechnology[name] = rGenTypes[name]
            totYearRGenKWh = allRGenPerTechnology.sum().sum() # sum of the reneable generation from all companies

            totalRenewGen = allRGenPerTechnology.sum(axis=1).values # get total renew generation profile 8760 values

            # Get electricty demand left for traditional generators to meet


            ############## subtract renewables from demand ###########
            DfNetDemand['TotalCustomerCons'] = customerNLs.sum(axis=1).values


            netDemand = customerNLs.sum(axis=1).values  #total consumption of all consumers, 8760 hour 
            netDemand = [x - y for x, y in zip(netDemand, allRGenPerTechnology.sum(axis=1).values)]
            hourlyCurtail = [abs(x) if x<0 else 0 for x in netDemand] #x<0 when generation>demand
            netDemand = [x if x>0 else 0 for x in netDemand]

            DfNetDemand['TotalCustomerConsAfterRGen'] = netDemand

            #########################################################


            # ------------------------------------------- Dispatch traditional generators to meet net demand ----------------------------
            #---------------- this only include specific traditional generators that are dispatched before batter charge/discharge 
            #===========================================================================================================================
            
            tradGen = technologies_dataset.loc[(technologies_dataset['Dispatch_Before_Storage']==1) & (technologies_dataset['Renewable_Flag']==0), :].copy()
            tradGen = tradGen.sort_values(by='MeritOrder', ascending=True)

            randGenCompaniesIndx = Utils.randomOrderListIndx(elecGenCompanies)

            tempNetD = netDemand.copy()

            allTGenPerCompany = pd.DataFrame() # df of total hourly traditional generation all year           
            allTGenPerTechnology = pd.DataFrame() # df showing the hourly generation for the traditional technologies

            print('Dispatch of {0}'.format(list(tradGen.index)))

            for index, row in tradGen.iterrows():
                print('Dispatch of {0}...'. format(index))
                genType = index
                genTypeID = row['TypeID']
                tempSum=0.0
                deRCapSum = capacityPerType.loc[BASEYEAR+currentYear, genType+'_Derated_Capacity_kW']
                capSum = capacityPerType.loc[BASEYEAR+currentYear, genType+'_Capacity_kW']
                tempCurTGen = list()
                if deRCapSum>0:
                    if(max(tempNetD)>deRCapSum): #the remaining demand can be supplied entirely by this technology type
                        for eGC in elecGenCompanies:

                            df_tradGenType = eGC.getTraditionalGenerationByType(genTypeID, tempNetD) # return the generation profile, the excess profile and the new demand

                            hourGenProf = df_tradGenType['Hourly_Generation'].values
                            excessGen = df_tradGenType['Excess_Generation'].values

                            tempNetD = df_tradGenType['NewNetDemand'].values
                            #Store the results in the dataframes
                            if genType in allTGenPerTechnology.columns:
                                allTGenPerTechnology[genType] = allTGenPerTechnology[genType] + hourGenProf
                            else:
                                allTGenPerTechnology[genType] = hourGenProf

                            if eGC.name in allTGenPerCompany.columns:
                                allTGenPerCompany[eGC.name] = allTGenPerCompany[eGC.name] + hourGenProf
                            else:
                                allTGenPerCompany[eGC.name] = hourGenProf

                            hourlyCurtail = [x+y for x,y in zip(hourlyCurtail,excessGen)]
                            
                    else:
                         
                        tempTotalTGen = 0.0 # total generation of this technology type (used for testing at the end of the loop) 
                        for eGCindex in randGenCompaniesIndx: # dispatch unit of the current technology type in companies based on the share of the technology installed in each of them
                            eGC = elecGenCompanies[eGCindex]
                            curCap = capacityPerCompanies.loc[eGC.name, genType+'_Capacity_kW']
                            curDeRCap = capacityPerCompanies.loc[eGC.name, genType+'_Derated_Capacity_kW']

                            if(capSum>0): # need to make sure not dividing by 0 , for noe, other types,e.g. coal CCGT is zero
                                capFrac = curCap/capSum 
                            else:
                                capFrac = 0.0

                            curTempNetD = tempNetD.copy() 
                            curNetD = [x*capFrac for x in curTempNetD]
                            # since netdemand<generation capacity, it will be afforded by capacity share of each company, the excess gen will be curtailed
                            df_tradGenType = eGC.getTraditionalGenerationByType(genTypeID, curNetD) #return a dataframe incl. generation and excess generation of the technology type and the new net demand

                            hourGenProf = df_tradGenType['Hourly_Generation'].values
                            excessGen = df_tradGenType['Excess_Generation'].values
                            tempTotalTGen = tempTotalTGen + np.sum(hourGenProf) -np.sum(excessGen)
                            #Store the results in the dataframes
                            if genType in allTGenPerTechnology.columns:
                                allTGenPerTechnology[genType] = allTGenPerTechnology[genType] + hourGenProf
                            else:
                                allTGenPerTechnology[genType] = hourGenProf

                            if eGC.name in allTGenPerCompany.columns:
                                allTGenPerCompany[eGC.name] = allTGenPerCompany[eGC.name] + hourGenProf
                            else:
                                allTGenPerCompany[eGC.name] = hourGenProf

                            hourlyCurtail = [x+y for x,y in zip(hourlyCurtail,excessGen)]

                        
                        # Test if the NetDemand is covered by the dispatch of these technoloy plants
                        if abs(np.sum(tempNetD) - tempTotalTGen)<1:
                            tempNetD = [0.0 for x in tempNetD]
                        else:
                            print('curS ',  tempTotalTGen)
                            print('sum(tempNetD)',np.sum(tempNetD))
                            raise ValueError('The amount of generation does not match the amount of demand covered')

                        # Remove the generation of this technology type from the netDemand
                        tempNetD = [x-y if x-y>0 else 0 for x,y in zip(tempNetD, allTGenPerTechnology[genType].values)]
                        

            netDemand = tempNetD
            DfNetDemand['TotalCustomerConsAfterTGen1'] = netDemand

            # --------- check if battery considered, if it is, charge/discharge accordingly ----------
            # ----------------------------------------------------------------------------------------
            
            if boolEnergyStorage:
                print('Charging/Discharging of batteries...')
                tNetDemand = netDemand.copy()
                for eGC in elecGenCompanies:
                    newNet = eGC.chargeDischargeBatteryTime(tNetDemand)
                    tNetDemand = newNet.copy()
                tempNetD = tNetDemand.copy() # final net demand after account for all companies
                batteryProf = list()
                batteryProf = [x - y for x, y in zip(netDemand, tempNetD)]

                if boolDraw: # This section needs to be removed
                    # graph first and final years
                    if currentYear == 0 or currentYear == maxYears-1:
                        graphProf = list()
                        graphProf.append(totalCustDemand)# GB electricity demand
                        graphProf.append(netDemand) # demand - renewables - BECCS-Nuclear
                        graphProf.append(tempNetD) # demand - renewables -BECCS-Nuclear - battery

                        maxPeak = max(totalCustDemand) # peak for total demand
                        NBPeak = max(netDemand) # peak for net demand (demand - renewables- BECCS-Nuclear) without battery
                        BPeak = max(tempNetD) # peak for net demand (demand - renewables - BECCS-Nuclear- battery) with battery
                        maxPeakList = list()
                        NBPeakList = list()
                        BPeakList = list()
                        for i in range(len(netDemand)):#8760 hr have the same value, straght line indicates peak
                            NBPeakList.append(NBPeak)
                            BPeakList.append(BPeak)
                            maxPeakList.append(maxPeak)
                            
                        graphProf.append(maxPeakList)
                        graphProf.append(NBPeakList)
                        graphProf.append(BPeakList)

                        graphNames = list()
                        graphNames.append('GB Electricity Demand')
                        graphNames.append('Demand - Renewables')
                        graphNames.append('Demand - Renewables - Battery')
                        p1 = round((maxPeak/1000000),2)
                        p2 = round((NBPeak/1000000),2)
                        p3 = round((BPeak/1000000),2)
                        peak1 = 'Peak: '+str(p1)+' GW'
                        graphNames.append(peak1)
                        peak2 = 'Peak - Renewables: '+str(p2)+' GW'
                        graphNames.append(peak2)
                        peak3 = 'Peak - Renewables - Battery: '+str(p3)+' GW'
                        graphNames.append(peak3)
                        graphT = 'Battery vs No Battery '+str(currentYear+BASEYEAR)+', Battery Capacity: '+str(totalBatteryCap/1000000)+' GW'
                        Utils.graphMultSeriesOnePlotV3(graphProf, 'Hour', 'Electricity Demand', graphT, graphNames, RESULTS_FILE_PATH)

                        graphProf.append(batteryProf)
                        graphNames.append('Battery Charge/Discharge')
                        
                        fileOut = RESULTS_FILE_PATH + 'BatteryPeakYear'+str(currentYear+BASEYEAR)+'.csv'
                        Utils.writeListsToCSV(graphProf,graphNames,fileOut)


            else: # otherwise, no battery considered
                tempNetD = netDemand.copy()

            # Not sure what this part does
            for k in range(len(tempNetD)):
                if(tempNetD[d]<0.0):
                    hourlyCurtail[k] = hourlyCurtail[k] + abs(tempNetD[d])
                    tempNetD[d]=0.0

            netDemand = tempNetD # Net demand after charging/discharging batteries
                    
            DfNetDemand['TotalCustomerConsAfterBattery'] = netDemand
            #===========================================================================================================================
            # ------------------------------------------- Dispatch the rest of the traditional generators to meet net demand ----------------------------
            #===========================================================================================================================
                  
            tradGen = technologies_dataset.loc[(technologies_dataset['Dispatch_Before_Storage']==0) & (technologies_dataset['Renewable_Flag']==0), :].copy()
            tradGen = tradGen.sort_values(by='MeritOrder', ascending=True)

            randGenCompaniesIndx = Utils.randomOrderListIndx(elecGenCompanies)
            tempNetD = netDemand.copy()
            print('Dispatch of {0}'.format(list(tradGen.index)))

            for index, row in tradGen.iterrows():
                print('Dispatch of {0}...'. format(index))
                genType = index
                genTypeID = row['TypeID']
                tempSum=0.0
                deRCapSum = capacityPerType.loc[BASEYEAR+currentYear, genType+'_Derated_Capacity_kW']
                capSum = capacityPerType.loc[BASEYEAR+currentYear, genType+'_Capacity_kW']
                tempCurTGen = list()
                # print(genType, deRCapSum, capSum)
                if deRCapSum>0:
                    if(max(tempNetD)>deRCapSum): #the remaining demand can be supplied entirely by this technology type
                        for eGC in elecGenCompanies:
                            df_tradGenType = eGC.getTraditionalGenerationByType(genTypeID, tempNetD) # return the generation profile, the excess profile and the new demand

                            hourGenProf = df_tradGenType['Hourly_Generation'].values
                            excessGen = df_tradGenType['Excess_Generation'].values
                            tempNetD = df_tradGenType['NewNetDemand'].values

                            #Store the results in the dataframes
                            if genType in allTGenPerTechnology.columns:
                                allTGenPerTechnology[genType] = allTGenPerTechnology[genType] + hourGenProf
                            else:
                                allTGenPerTechnology[genType] = hourGenProf

                            if eGC.name in allTGenPerCompany.columns:
                                allTGenPerCompany[eGC.name] = allTGenPerCompany[eGC.name] + hourGenProf
                            else:
                                allTGenPerCompany[eGC.name] = hourGenProf

                            hourlyCurtail = [x+y for x,y in zip(hourlyCurtail,excessGen)]
                    else:
                        tempTotalTGen = 0.0 # total generation of this technology type (used for testing at the end of the loop) 
                        for eGCindex in randGenCompaniesIndx: # dispatch unit of the current technology type in companies based on the share of the technology installed in each of them
                            eGC = elecGenCompanies[eGCindex]
                            curCap = capacityPerCompanies.loc[eGC.name, genType+'_Capacity_kW']
                            curDeRCap = capacityPerCompanies.loc[eGC.name, genType+'_Derated_Capacity_kW']

                            if(capSum>0): # need to make sure not dividing by 0 , for noe, other types,e.g. coal CCGT is zero
                                capFrac = curCap/capSum 
                            else:
                                capFrac = 0.0

                            curTempNetD = tempNetD.copy() 
                            curNetD = [x*capFrac for x in curTempNetD]
                            # since netdemand<generation capacity, it will be afforded by capacity share of each company, the excess gen will be curtailed
                            df_tradGenType = eGC.getTraditionalGenerationByType(genTypeID, curNetD) #return a dataframe incl. generation and excess generation of the technology type and the new net demand

                            hourGenProf = df_tradGenType['Hourly_Generation'].values
                            excessGen = df_tradGenType['Excess_Generation'].values
                            tempTotalTGen = tempTotalTGen + np.sum(hourGenProf) -np.sum(excessGen)
                            #Store the results in the dataframes
                            if genType in allTGenPerTechnology.columns:
                                allTGenPerTechnology[genType] = allTGenPerTechnology[genType] + hourGenProf
                            else:
                                allTGenPerTechnology[genType] = hourGenProf

                            if eGC.name in allTGenPerCompany.columns:
                                allTGenPerCompany[eGC.name] = allTGenPerCompany[eGC.name] + hourGenProf
                            else:
                                allTGenPerCompany[eGC.name] = hourGenProf

                            hourlyCurtail = [x+y for x,y in zip(hourlyCurtail,excessGen)]

                        # Test if the NetDemand is covered by the dispatch of these technoloy plants
                        if abs(np.sum(tempNetD) - tempTotalTGen)<1:
                            tempNetD = [0.0 for x in tempNetD]
                        else:
                            print('curS ',  tempTotalTGen)
                            print('sum(tempNetD)',np.sum(tempNetD))
                            raise ValueError('The amount of generation does not match the amount of demand covered')

                        # Remove the generation of this technology type from the netDemand
                        tempNetD = [x-y if x-y>0 else 0 for x,y in zip(tempNetD, allTGenPerTechnology[genType].values)]

            netDemand = tempNetD # Net demand after the dispatch of these plants
            DfNetDemand['TotalCustomerConsAfterTGen2'] = netDemand

            # calculating wholesale electricity price from marginal cost
            wholesaleEPrice, nuclearMarginalCost = Utils.getWholesaleEPrice(elecGenCompanies)
            boolNegPrice = False
            for k in range(len(wholesaleEPrice)): #8760
                if hourlyCurtail[k]>0:
                    boolNegPrice = True
                    wholesaleEPrice[k] = 0 - nuclearMarginalCost[k]

            DfWholesalePrices = pd.DataFrame()
            DfWholesalePrices['WholesalePrice'] = wholesaleEPrice

            # update economics of all plants and batteries
            for eGC in elecGenCompanies:
                eGC.calcRevenue(wholesaleEPrice)

            for val in tempNetD:
                if val>0.001:
                    hourlyLossOfLoad.append(val)
                else:
                    hourlyLossOfLoad.append(0.0)

            
            DfNetDemand['Curtailement'] = hourlyCurtail
            DfNetDemand['Loss of load'] = hourlyLossOfLoad
            

        
        #--------------------------------------------------------------------
            

        ##########################################################################
        ################ End of year, update model for next year #################
        ##########################################################################

        # calculating yearly emissions

        yearlyEmissions = 0.0
        for eGC in elecGenCompanies: # loop through all gen companies
            eGC.calculateYearlyProfit() # get profit
            yearlyEmissions = yearlyEmissions + eGC.totalEmissionsYear
        
        capacityPerType.loc[BASEYEAR+currentYear, genType+'_Derated_Capacity_kW'] = deRCapSum
        capacityPerType.loc[BASEYEAR+currentYear, genType+'_Capacity_kW'] = capSum

        dercap_cols = [c for c in capacityPerType.columns if '_Derated_Capacity_kW' in c]
        cap_cols = [c for c in capacityPerType.columns if '_Capacity_kW' in c]
        sumTotCap = capacityPerType.loc[BASEYEAR+currentYear, cap_cols].sum()
        sumDeRateTotCap = capacityPerType.loc[BASEYEAR+currentYear, dercap_cols].sum()

        capacityMargin = (sumTotCap - peakDemand)/peakDemand # calculate margins
        deRatedCapacityMargin = (sumDeRateTotCap - peakDemand)/peakDemand

        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_Margin_%'] = capacityMargin
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Derated_Capacity_Margin_%'] = deRatedCapacityMargin
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Peak_Demand_kW'] = peakDemand

        capacityPerTypePerBus = pd.DataFrame(columns=list(technologies_dataset.index)+['Battery'], index = [eC.busbar for eC in energyCustomers])
        capacityPerTypePerBus.fillna(0, inplace=True)
        # calculating capacity capacity per tech per busbar

        for eGC in elecGenCompanies:
            for tGen in eGC.traditionalGen:
                name = tGen.name
                capacity = tGen.genCapacity
                bus = tGen.numbus
                print(name, bus, capacity)
                if capacity>0:
                    capacityPerTypePerBus.loc[bus, name] = capacityPerTypePerBus.loc[bus, name] + capacity

            for rGen in eGC.renewableGen:
                name = rGen.name
                capacity = rGen.genCapacity
                bus = rGen.numbus
                if capacity>0:
                    capacityPerTypePerBus.loc[bus, name] = capacityPerTypePerBus.loc[bus, name] + capacity

            for store in eGC.energyStores:
                capacity = store.maxCapacity
                bus = store.numbus
                name = 'Battery'
                if capacity>0:
                    capacityPerTypePerBus.loc[bus, name] = capacityPerTypePerBus.loc[bus, name] + capacity

        ####### Capacity auction ######

        # Utils.resetCurYearCapInvest() What does it do??

        # introduce battery storage in 2018
        # this next part of code should only be used if using a linear increase in battery storage
        
        if(boolEnergyStorage and boolLinearBatteryGrowth and currentYear + BASEYEAR +1 >= 2018):
            prevYearBatteryCap = totalBatteryCap #total discharge rate last year
            total2018BatCap = 3590000
            batCapRange = totalFinalBatteryCap - total2018BatCap
            numY = (BASEYEAR + maxYears -1) - 2018 #(2050-2018) 2010+41-1=2050
            
            if(numY > 1):
                batteryCapYearIncrement = batCapRange/ numY
            else:
                batteryCapYearIncrement = batCapRange

            if(currentYear + BASEYEAR + 1 == 2018):
                totalBatteryCap = total2018BatCap
            else:
                totalBatteryCap = prevYearBatteryCap + batteryCapYearIncrement
            
            batteryCapPerCompany = totalBatteryCap/len(elecGenCompanies)
            for eGC in elecGenCompanies:
                eGC.removeBatteries()
                eGC.addBatterySize(batteryCapPerCompany)
                eGC.curYearBatteryBuild = batteryCapPerCompany
        


        capacityPerBus.loc[currentYear+BASEYEAR, :] = 0 # init the values

        for eC in energyCustomers:
            busc = eC.busbar         
            for eGC in elecGenCompanies:
                for tGen in eGC.traditionalGen:
                    if tGen.numbus == busc:
                        c = tGen.genCapacity
                        capacityPerBus.loc[currentYear+BASEYEAR, busc] = capacityPerBus.loc[currentYear+BASEYEAR, busc] + c
                for rGen in eGC.renewableGen:
                    if rGen.numbus == busc:
                        c = rGen.genCapacity
                        capacityPerBus.loc[currentYear+BASEYEAR, busc] = capacityPerBus.loc[currentYear+BASEYEAR, busc] + c

        # PeakDPerBus = list()

        # for c in customerNLs.columns:
        #     tempeakd = max(customerNLs[c])
        #     PeakDPerBus.append(tempeakd)

        print(OneYearHeadroom)
        DfHeadroomYear[currentYear+BASEYEAR] = OneYearHeadroom # Store the headroom of the current year
        busheadroom = TNO.EvaluateHeadRoom(capacityPerBus.loc[currentYear+BASEYEAR,:].values,totalCustDemand)
        print(busheadroom)
        OneYearHeadroom = busheadroom

        # cfd auction
        policy.cfdAuction(3, 6000000, elecGenCompanies, busheadroom) # 3 years, 6 GW to be commissioned
        # capacity auction
        if(boolLinearBatteryGrowth and boolEnergyStorage):
            policy.capacityAuction(4, peakDemand, elecGenCompanies, False, busheadroom)
        else:
            policy.capacityAuction(4, peakDemand, elecGenCompanies, boolEnergyStorage, busheadroom)
            

        totYearGridGenKWh = allTGenPerTechnology.sum().sum() + allRGenPerTechnology.sum().sum()
        gridCO2emisIntens = (yearlyEmissions/totYearGridGenKWh)*1000 # *1000 because want gCO2/kWh not kgCO2
        print('year ',(BASEYEAR+currentYear))
        print('gridCO2emisIntens (gCO2/kWh) ',gridCO2emisIntens)

        
        policy.increaseYear()
        # update CO2 Price for next year
        newCO2Price = policy.getNextYearCO2Price(gridCO2emisIntens)
        policy.recordYearData()

        # update wholesale electricity price
        for eGC in elecGenCompanies: # loop through all gen companies
            wholesEPriceChange = eGC.updateTechnologiesYear(newCO2Price)#wholesEPriceChange returns 0

        # demand elasticity
        for eC in energyCustomers:
            demandChangePC = eC.updateYear(0.0,eC.busbar-1) #

        demandCoeff = 1.0 + (demandChangePC/100.0) #how mauch percentage change compared to 2018. e.g. 180%

        # each generation company agent makes decision to invest in new capacity
        for eGC in elecGenCompanies: # loop through all gen companies
            if(boolLinearBatteryGrowth and boolEnergyStorage):
                eGC.updateCapacityDecision(peakDemand, False,OneYearHeadroom)
            else:
                eGC.updateCapacityDecision(peakDemand, boolEnergyStorage,OneYearHeadroom)
                
        batSubsReq = list()
        for eGC in elecGenCompanies:
            batSubsReq.append(eGC.yearlyBatterySubsNeeded)
        
        techT, techCap, techDRCap =  getCapacityPerTech(elecGenCompanies)
        techNamesGraph = techT.copy()

        for eGC in elecGenCompanies: # reset values
            eGC.resetYearlyValues()

        # Utils.resetCurYearCapInvest() What does it do??

        #Calculate net demand
        netdemand = [x-y for x,y in zip(totalCustDemand, allRGenPerTechnology.sum(axis=1).values)]

        #run DC power flow analysis
        if(currentYear in [100]):  
            TNO.RunPowerFlow(netdemand,elecGenCompanies,customerNLs)
            
        # writing results to file if at the end of simulation
        if(currentYear == maxYears-1): # End of simulation
            fileOut = RESULTS_FILE_PATH + 'capacityPerType.csv'
            capacityPerType.to_csv(fileOut)  	

            fileOut = RESULTS_FILE_PATH + 'SystemEvolution.csv'
            DfSystemEvolution.to_csv(fileOut)

            fileOut = RESULTS_FILE_PATH + 'HeadroomBus.csv'
            DfHeadroomYear.to_csv(fileOut)

        # Export to CSV
        fileOut = RESULTS_FILE_PATH + 'NetDemand'+str(currentYear+BASEYEAR)+'.csv'
        DfNetDemand.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'allRGenPerTechnology'+str(currentYear+BASEYEAR)+'.csv'
        allRGenPerTechnology.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'allRGenPerCompany'+str(currentYear+BASEYEAR)+'.csv'
        allRGenPerCompany.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'allTGenPerTechnology'+str(currentYear+BASEYEAR)+'.csv'
        allTGenPerTechnology.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'allTGenPerCompany'+str(currentYear+BASEYEAR)+'.csv'
        allTGenPerCompany.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'customerNLs'+str(currentYear+BASEYEAR)+'.csv'
        customerNLs.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'customerHeatLoads'+str(currentYear+BASEYEAR)+'.csv'
        customerHeatLoads.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'custElecBills'+str(currentYear+BASEYEAR)+'.csv'
        custElecBills.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'WholesalePrice'+str(BASEYEAR+currentYear)+'.csv'
        DfWholesalePrices.to_csv(fileOut)

        fileOut = RESULTS_FILE_PATH + 'capacityPerCompanies'+str(BASEYEAR+currentYear)+'.csv'
        capacityPerCompanies.to_csv(fileOut)  

        fileOut = RESULTS_FILE_PATH + 'capacityPerTypePerBus'+str(BASEYEAR+currentYear)+'.csv'
        capacityPerTypePerBus.to_csv(fileOut)  
            
            

    
   
    











