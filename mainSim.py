from __future__ import division
import joblib
import random
import numpy as np
import scipy as sp
from scipy import (dot, eye, randn, asarray, array, trace, log, exp, sqrt, mean, sum, argsort, square, arange)
from scipy.stats import multivariate_normal, norm
from scipy.linalg import (det, expm)
from customer import customer
from customerGroup import customerGroup
from renewableGenerator import renewableGenerator
from traditionalGenerator import traditionalGenerator
from energyStorage import energyStorage
from generationCompany import generationCompany
from drawMap import drawMap
from policyMaker import policyMaker
from heatProvider import heatProvider
from drawMap_noGeopy import drawMap as oldDrawMap
import Utils
import random
import pandas as pd 
import matplotlib.pyplot as plt
import pandapower.plotting as pplt
import statistics
import networkx as nx
import matplotlib as mpl
import seaborn as sns
import TransmissionNetworkOwner as TNO
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

#    Utils.graphMultSeriesOnePlot(techCap, 'Year', 'Capacity', 'Annual GB Capacity',techTypes)
#    Utils.graphMultSeriesOnePlot(techDeRCap, 'Year', 'Capacity', 'Annual GB De Rated Capacity',techTypes)

    return techTypes, techCap, techDeRCap




######### main method, code starts executing from here ##################
if __name__ == '__main__':


    np.random.seed(42)
    random.seed(42)

    print('========================begin======================== ')
    Utils.resetCurYearCapInvest()
    BASEYEAR = 2010 # 2010
    file = open("BASEYEAR.txt", "w") 
    file.write(str(BASEYEAR)) 
    file.close()

    # path to where you want results output to
    RESULTS_FILE_PATH = 'Results/2050/'

    maxYears = 1 #16 = 2025 #9=2018 #  25 = 2034, 41 = 2050
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

    years = list()
    yearlyTotCap = list()
    yearlyDeRCap = list()
    yearlyPeakD = list()
    yearlyCapM = list()
    yearlyDeRCapM = list()
    yearlyheadroom = list()
    policy = policyMaker()
    OneYearHeadroom = list([-32212711.56,-32067843.49,-31767613.28,-28212832.94,-28021373.43,-29166767.52,-28040878.71,-30277254.05,-31222433.48,-31615902.27,-35658351.5,-38698275.52,-39831850.5,-36304364.7,-40756536.12,-33969231.94,-43217107.73,-46674012.56,-44359251.32,-42836333.58,-41055681.71,-36877967.42,-35329923.93,-29181850.14,-31686007.01,-29468773.98,-28935821.38,-31005560.87,-30411533.39,-29371379.89])
    #initialise with 2010
    yearlybusdemand=list()
    energyCustomers = list()
    yearlytotalbatterycap = list()
    techTypes = list()
    techCapYear = list()
    techDeRCapYear = list()
    yearlymaxwholesale = list()
    yearlyminwholesale = list()
    yearlyavgwholesale =list()

    #for accounting basbar per tech
    batterybuslist = list()
    yearlybatterycaplist = list()

    nuclearbuslist = list()
    yearlynuclearcaplist = list()      
    coalbuslist = list()
    yearlycoalcaplist = list()      
    windoffbuslist = list()
    yearlywindoffcaplist = list()
    beccsbuslist = list()
    yearlybeccscaplist = list()    
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
  
    for c in range(1,31):
        cust = customerGroup(c)
        energyCustomers.append(cust)

    # list of generation technologies

    # genTechList = ['CCGT', 'OCGT', 'Coal', 'Nuclear', 'Wind Offshore', 'Wind Onshore', 'Solar', 'Hydro', 'Biomass', 'BECCS', 'Hydrogen']
    technologies_dataset = pd.read_csv('technologies_dataset.csv', index_col = 0)
    genTechList = list(technologies_dataset.index)

    #### Not sure what is the use of that at the moment

    # file = open("GEN_TYPE_LIST.txt", "w")
    # for i in range(len(genTechList)):
    #     temp = str(genTechList[i])+'\n'
    #     file.write(temp)
    # file.close()

    # file = open("GEN_TYPE_COMPANY_COUNT_LIST.txt", "w")
    # for i in range(len(genTechList)):
    #     temp = str(1)+'\n'
    #     file.write(temp)
    # file.close()


    # --------- Create generation companies -----------------
    print('Adding Generation Companies')
    elecGenCompanies = list()
    elecGenCompNAMESONLY = list()
    if(BASEYEAR==2018):
        mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2018_Owners2.csv'
    elif(BASEYEAR==2010):
        mainPlantsOwnersFile = 'OtherDocuments/UKPowerPlans2010_Owners.csv'
    GBGenPlantsOwners = Utils.readCSV(mainPlantsOwnersFile)

    for i in range(len(GBGenPlantsOwners['Station Name'])):
        tempName = GBGenPlantsOwners['Fuel'].iloc[i] #raw
        
        if(not (GBGenPlantsOwners['Location'].iloc[i]== 'Northern Ireland')and tempName in genTechList):
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
        
        if(not (GBGenPlantsOwners['Location'].iloc[i]== 'Northern Ireland') and tempName in genTechList):
            curCompName = GBGenPlantsOwners['Company Name'].iloc[i]
            for j in range(len(elecGenCompanies)):
                if(elecGenCompanies[j].name == curCompName):
                    tempName = GBGenPlantsOwners['Fuel'].iloc[i]
                    tempTypeID = -1 
                    lifetime = 0
                    tempRen = 0
                    tempCapKW = GBGenPlantsOwners['Installed Capacity(MW)'].iloc[i]*1000.0
                    tempbus = GBGenPlantsOwners['Bus'].iloc[i]
                    capacityInstalledMW[tempName] = capacityInstalledMW[tempName] + tempCapKW/1000
                    lifetime = int(technologies_dataset.loc[tempName, 'Lifetime_Year'])
                    tempRen = int(technologies_dataset.loc[tempName, 'Renewable_Flag'])
                    subsidy = 0
                    cfdBool = int(technologies_dataset.loc[tempName, 'CFD_Flag'])
                    capMarketBool = int(technologies_dataset.loc[tempName, 'Capacity_Market_Flag'])


                    # print("Name {0}, lifetime {1}, renewable Flag {2}".format(tempName, lifetime, tempRen))

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
                    elecGenCompanies[j].addGeneration(tempName, tempTypeID, tempRen, tempCapKW, tempStartYear, tempEndYear, tempAge, subsidy, cfdBool, capMarketBool, tempbus, OneYearHeadroom[tempbus-1])
 
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
        if(sYear>2010 and sYear<2013):
            tempName = GBWindOnPlants['Type'].iloc[i]
            cap = GBWindOnPlants['Capacity(kW)'].iloc[i]
            eYear = GBWindOnPlants['EndYear'].iloc[i]
            tempbus = GBWindOnPlants['Bus'].iloc[i]
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




    # file = open("GEN_TYPE_LIST.txt", "w")
    # for i in range(len(genTechList)):
    #     temp = str(genTechList[i])+'\n'
    #     file.write(temp)
    # file.close()

    # genTypeCompanyCount = countCompaniesPerTech(elecGenCompanies, genTechList)
    # # what is the use of that?
    # file = open("GEN_TYPE_COMPANY_COUNT_LIST.txt", "w")
    # for i in range(len(genTypeCompanyCount)):
    #     temp = str(genTypeCompanyCount[i])+'\n'
    #     file.write(temp)
    # file.close()

    # Not clear how is the build rate calculated? should it be in the generationCompany.py file instead of electricityGenerator.py?
    for i in range(len(elecGenCompanies)):
        elecGenCompanies[i].updateBuildRates()
        tname1 = elecGenCompanies[i].name
        print('name, ',tname1)

    if(boolEnergyStorage):
        batteryCapPerCompany = totalBatteryCap/len(elecGenCompanies)
        for i in range(len(elecGenCompanies)):
            elecGenCompanies[i].removeBatteries()
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
    hourlyCurtailPerYear = list()
    yearlyCurtailedInstances = list()

    hourlyLossOfLoadPerYear = list()
    yearlyLossOfLoadInstances = list()

    capacityPerType = pd.DataFrame()
    
    for y in range(maxYears): # Loop through years

        hourlyCurtail = list()
        hourlyLossOfLoad = list()

        print('year ',(BASEYEAR+y))
        print('y ',(y))




        #################### Add in some BECCS in 2019 ###############
        
        # if(BASEYEAR+y == 2019):
        #     cName = 'Drax Power Ltd'
        #     BECCSAddBool = False
        #     for k in range(len(elecGenCompanies)):
        #         if(elecGenCompanies[k].name == cName):
        #             temprand=random.choice([2,7,10,12,13,14,15,16,17,18,19,20,22,23,24,26,28,30])
        #             #addGeneration(self, genName, genTypeID, renewableID, capacityKW, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom)
        #             elecGenCompanies[k].addGeneration('BECCS', 9, 0, 500000.0, 2025, 2051, 0, 0.0, False, False, temprand, OneYearHeadroom[temprand-1])
        #             BECCSAddBool = True
        #             print('BECCS added')
        #     if(not BECCSAddBool):
        #         input('BECCS not added ******')

        #################### Add in some Hydrogen in 2035 ###############
        
        # if(BASEYEAR+y == 2035):
        #     cHydrogenName = list(['Baglan Generation Ltd', 'Barking Power', 'Centrica','Citigen (London) UK Ltd', 'Coolkeeragh ESB Ltd','Corby Power Ltd', 'Cory Energy Company Ltd','Derwent Cogeneration','Drax Power Ltd','EDF Energy','E.On UK','GDF Suez','International Power/Mitsui','Premier Power Ltd','Rocksavage Power Co. Ltd','RWE Npower Plc','Thermal','Cruachan Thermal','Seabank Power Limited','Spalding Energy Company Ltd'])
        #     HydrogenAddBool = False
        #     for k in range(len(elecGenCompanies)):
        #         if(elecGenCompanies[k].name in cHydrogenName):
        #             temprand=random.randint(1,30)
        #             #addGeneration(self, genName, genTypeID, renewableID, capacityKW, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom)
        #             elecGenCompanies[k].addGeneration('Hydrogen', 11, 0, 1.5, 2035, 2044, 0, 0.0, False, False, temprand, OneYearHeadroom[temprand-1])
        #             HydrogenAddBool = True
        #             print('Hydrogen added')
        #     if(not HydrogenAddBool):
        #         input('Hydrogen not added ******')      
        # 
        # 
        # Get the capacity installed for each technology type
        for genType in technologies_dataset.index:
            deRCapSum = 0 
            capSum = 0
            for eGC in elecGenCompanies: #all companies have been added at the beginning
                boolRenewable = int(technologies_dataset.loc[genType, 'Renewable_Flag'])
                genTypeID = int(technologies_dataset.loc[genType, 'TypeID'])
                curCap, curDeRCap = eGC.getCapacityByType(genTypeID, boolRenewable) # a value, total capacity of a tech, a company, summed by all plants 
                deRCapSum = deRCapSum + curDeRCap
                capSum = capSum + curCap #a value, total capacity of a tech, summed by all companies
            capacityPerType.loc[y, genType+'_DerCap'] = deRCapSum
            capacityPerType.loc[y, genType+'_Cap'] = capSum
        
        capacityPerType.to_csv("capacityPerType.csv")  	

        if(boolEnergyStorage):
            totalBatteryCap = 0.0
            for i in range(len(elecGenCompanies)):
                elecGenCompanies[i].setBatteryWholesalePrice()
                totalBatteryCap = totalBatteryCap + elecGenCompanies[i].getBatteryCapKW()
            annualStorageCap.append(totalBatteryCap)
            yearlytotalbatterycap.append(totalBatteryCap)

        for d in range (1): # set to 1 as each customer will simulate 8760 hours (365 days)
            customerNLs = pd.DataFrame() #list of a number of customers, each customer has 8760 hour data
            customerHeatLoads = pd.DataFrame()
            totalCustDemand = list()
            custTotalDayLoads = pd.DataFrame()
            custElecBills = pd.DataFrame()

            renewGens = list() #list of hourly generation for each plant
            totalRenewGen = list()

            for c in range (len(energyCustomers)):
                curCustNL, curCustHeat = energyCustomers[c].runSim() # sim energy consumption each hour
                # customerNLs.append(curCustNL)
                customerNLs[c] = curCustNL
                customerHeatLoads[c] = curCustHeat
                custTotalDayLoads[c] = energyCustomers[c].totalNLDemand # this is empty?
                custElecBills[c] = energyCustomers[c].elecCost

            yearlybusdemand.append(custTotalDayLoads)

            customerNLs.to_csv("customerNLs.csv")
            customerHeatLoads.to_csv("customerHeatLoads.csv")
            custTotalDayLoads.to_csv("custTotalDayLoads.csv")
            custElecBills.to_csv("custElecBills.csv")

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
            # Not sure what this section of the code does???

            yearGenPerCompanyData = list() #yearly generation, for each type, total generated by all companies all types
            yearGenPerCompanyName = list() #renewable technology list. name is not proper
            rGenType = list()

            allRGenPerCompany = pd.DataFrame() # list of total hourly renewable generation all year           
            allRGenPerTechnology = list() # 5 technologies, each has a list ,contain 8760 hourly generation summed by all plants
            # 3D list, number of renewable types -> number of plants per type -> number of hours, e.g. 2 types, 40 plants, 8760 h 
            tempAllRGenPerTechnology = list() #one tech has a list, apended by each plant's 8760
            totYearRGenKWh = 0.0
            
            for gc in range (len(elecGenCompanies)):
                # rGenProf = list of 8760 lists of rGen, e.g. 40 lists for 40 plants
                # yGenPerTechData = list of sum yearly energy gen per plant, e.g. 40 floats
                # yGenPerTechLabels = list of names of each plant type, e.g., Onshore, Onshore, Offshore, Offshore,...
                # tempTotRGEN = list of 8760 vals for total rGen from company
                rGenProf, yGenPerTechData, yGenPerTechLabels, tempTotRGEN = elecGenCompanies[gc].getRenewableGen()
                allRGenPerCompany[gc] = tempTotRGEN #list of every company, total generation per per company's 8760 (sum all its plant)
                tempRGens = list()

                for rg in range(len(rGenProf)): #loops through plants
                    renewGens.append(rGenProf[rg])
                    totYearRGenKWh = totYearRGenKWh + elecGenCompanies[gc].renewableGen[rg].yearlyEnergyGen

                    if(gc==0): #initialise the list
                        recorded = False
                        for i in range(len(rGenType)): #1,2,3,4,5
                            if(elecGenCompanies[gc].renewableGen[rg].renewableType == rGenType[i]):
                                recorded = True
                                yearGenPerCompanyData[i] = yearGenPerCompanyData[i] + elecGenCompanies[gc].renewableGen[rg].yearlyEnergyGen
                                tempAllRGenPerTechnology[i].append(rGenProf[rg])
                        if(not recorded):
                            yearGenPerCompanyData.append(elecGenCompanies[gc].renewableGen[rg].yearlyEnergyGen)
                            yearGenPerCompanyName.append(elecGenCompanies[gc].renewableGen[rg].name) #solar, wind
                            rGenType.append(elecGenCompanies[gc].renewableGen[rg].renewableType) #1,2,3,4,5
                            tempRGens = list()
                            tempRGens.append(rGenProf[rg])
                            tempAllRGenPerTechnology.append(tempRGens)

                    else:
                        recorded = False #since the initial company not necessarily has all technology
                        for i in range(len(rGenType)):
                            if(elecGenCompanies[gc].renewableGen[rg].renewableType == rGenType[i]):
                                recorded = True
                                yearGenPerCompanyData[i] = yearGenPerCompanyData[i] + elecGenCompanies[gc].renewableGen[rg].yearlyEnergyGen
                                tempAllRGenPerTechnology[i].append(rGenProf[rg])

                        if(not recorded):
                            yearGenPerCompanyData.append(elecGenCompanies[gc].renewableGen[rg].yearlyEnergyGen)
                            yearGenPerCompanyName.append(elecGenCompanies[gc].renewableGen[rg].name)
                            rGenType.append(elecGenCompanies[gc].renewableGen[rg].renewableType)
                            tempRGens = list()
                            tempRGens.append(rGenProf[rg])
                            tempAllRGenPerTechnology.append(tempRGens)


            for tg in range (len(tempAllRGenPerTechnology)): # loop through technologies , e.g. solar, onshore
                tList = tempAllRGenPerTechnology[tg][0] # is plant number, returns 8760 vals
                for rg in range(len(tempAllRGenPerTechnology[tg])): # loop through plants
                    tList = [x + y for x, y in zip(tList, tempAllRGenPerTechnology[tg][rg])] #parallal loops each technology's total 8760
                allRGenPerTechnology.append(tList)

            totalRenewGen = allRGenPerCompany.sum(axis=1).values # get total renew gen across all companies hourly, apended each hour's value

            rGenNames = yearGenPerCompanyName.copy()

            # Get electricty demand left for traditional generators to meet
            ############## subtract renewables from demand ###########
         
            netDemand = customerNLs.sum(axis=1).values  #total consumption of all consumers, 8760 hour 
            netDemand = [x - y for x, y in zip(netDemand, allRGenPerCompany.sum(axis=1).values)]
            hourlyCurtail = [abs(x) if x<0 else 0 for x in netDemand] #x<0 when generation>demand
            netDemand = [x if x>0 else 0 for x in netDemand]

            #########################################################



            #======= subtract BECCS and nuclear from net demand before battery charge/discharge ====
            #=======================================================================================
            

            tradGen = technologies_dataset.loc[(technologies_dataset['Dispatch_Before_Storage']==1) & (technologies_dataset['Renewable_Flag']==0), :].copy()

            tradGenTypes = list()
            tradGenTypes.append(5) # Biomass
            tradGenTypes.append(4) # BECCS
            tradGenTypes.append(2) # Nuclear
            tradGenTypes.append(6) # Hydrogen

            tradGenNames= list()
            tradGenNames.append('Nuclear')    
            tradGenNames.append('BECCS')        
            tradGenNames.append('Biomass')
            tradGenNames.append('Hydrogen')
            tradGenPerTech= list() # yearly total generation from each tech of traditional generation
            randGenCompaniesIndx = Utils.randomOrderListIndx(elecGenCompanies)
            totYearTGenKWh = 0.0
            allTGenPerTechnology = list() # 5 technologies, each has a list ,contain 8760 hourly generation summed by all plants
            tempNetD = netDemand.copy()

            # ------------------------------------------- Dispatch traditional generators to meet net demand ----------------------------
            for index, row in tradGen.iterrows(): # for now only have BECCS and nuclear
                genType = row['Name']
                tempSum=0.0

                deRCapSum =0.0
                capSum = 0.0
                tempCurTGen = list()
                for i, eGC in enumerate(elecGenCompanies): #all companies have been added at the beginning
                    curCap, curDeRCap = eGC.getCapacityByType(genType,False) # a value, total capacity of a tech, a company, summed by all plants 
                    deRCapSum = deRCapSum + curDeRCap
                    capSum = capSum + curCap #a value, total capacity of a tech, summed by all companies
                
                if(max(tempNetD)>deRCapSum): # that means all companies can dispatch the unit of this type
                    for gc in range(len(randGenCompaniesIndx)):
                        cIndx = randGenCompaniesIndx[gc]
                        sGen, newNetD, excessGen, hourGenProf = elecGenCompanies[cIndx].getTraditionalGenerationByType(genType, tempNetD) #here, only add company with BECCS and nuclear
                        #sGen is a value sum one year, others are 8760 lists 
                        #in this case newNetD>0, no excessGen
                        tempSum = tempSum + sGen
                        tempNetD = list()
                        tempNetD = newNetD
                        totYearTGenKWh = totYearTGenKWh + sGen
                        if(len(tempCurTGen)==0):
                            tempCurTGen = hourGenProf.copy()
                        else:
                            for k in range(len(tempCurTGen)):
                                val = tempCurTGen[k]
                                tempCurTGen[k] = val + hourGenProf[k] #sum for each tech, total gen from all companies

                                
                        if(np.sum(excessGen)>0):
                            for k in range(len(hourlyCurtail)):
                                hourlyCurtail[k] = hourlyCurtail[k] + excessGen[k]
                    tradGenPerTech.append(tempSum)
                    
                else:
                    prevTempNetD = tempNetD.copy()
                    curS = 0.0
                    for gc in range(len(randGenCompaniesIndx)):
                        cIndx = randGenCompaniesIndx[gc]
                        curCap, curDeRCap = elecGenCompanies[cIndx].getCapacityByType(tradGenTypes[gt],False)
                        if(capSum>1): # need to make sure not dividing by 0 , for noe, other types,e.g. coal CCGT is zero
                            capFrac = curCap/capSum 
                        else:
                            capFrac = 0.0

                        curTempNetD = prevTempNetD.copy()    
                        curNetD = [x*capFrac for x in curTempNetD]
                        # since netdemand<generation capacity, it will be afforded by caoacity share of each compane, the excess gen will be curtailed
                        sGen, newNetD, excessGen, hourGenProf = elecGenCompanies[cIndx].getTraditionalGenerationByType(tradGenTypes[gt], curNetD)
                        tempSum = tempSum + sGen
                        curS = curS + sGen # total year generation per tech by all companies
                        totYearTGenKWh = totYearTGenKWh + sGen
                        
                        if(len(tempCurTGen)==0):
                            tempCurTGen = hourGenProf.copy()
                        else:
                            for k in range(len(tempCurTGen)):
                                val = tempCurTGen[k]
                                tempCurTGen[k] = val + hourGenProf[k]


                        if(np.sum(excessGen)>0):
                            for k in range(len(hourlyCurtail)):
                                hourlyCurtail[k] = hourlyCurtail[k] + excessGen[k]
                    tradGenPerTech.append(tempSum)
                    if(abs(curS-np.sum(prevTempNetD))<1):
                        tempNetD = [0.0 for x in prevTempNetD]
                    else:
                        print('curS ', curS)
                        print('sum(prevTempNetD0 ',np.sum(prevTempNetD))
                        input('problem, these should be equal ....')
                    
                allTGenPerTechnology.append(tempCurTGen)
                for i in range(len(netDemand)):
                    netDemand[i] = netDemand[i] - tempCurTGen[i]
                    
                for d in range(len(netDemand)):
                    if(netDemand[d]<0.0):
                        hourlyCurtail[d] = hourlyCurtail[d] + abs(netDemand[d])
                        netDemand[d]=0.0

            
            #=======================================================================================


            

#             # --------- check if battery considered, if it is, charge/discharge accordingly ----------
#             # ----------------------------------------------------------------------------------------
            
#             if(boolEnergyStorage):
#                 tNetDemand = netDemand.copy()
#                 for i in range(len(elecGenCompanies)):
#                     newNet = elecGenCompanies[i].chargeDischargeBatteryTime(tNetDemand)
#                     tNetDemand = newNet.copy()
#                 tempNetD = tNetDemand.copy() # final net demand after account for all companies
#                 batteryProf = list()
#                 for k in range(len(tempNetD)):#loop through hour
#                     val = netDemand[k] - tempNetD[k]
#                     batteryProf.append(val)

#                 # graph first and final years
#                 if((y==0 or y==maxYears-1)):
#                     graphProf = list()
#                     graphProf.append(totalCustDemand)# GB electricity demand
#                     graphProf.append(netDemand) # demand - renewables - BECCS-Nuclear
#                     graphProf.append(tempNetD) # demand - renewables -BECCS-Nuclear - battery

#                     maxPeak = max(totalCustDemand) # peak for total demand
#                     NBPeak = max(netDemand) # peak for net demand (demand - renewables- BECCS-Nuclear) without battery
#                     BPeak = max(tempNetD) # peak for net demand (demand - renewables - BECCS-Nuclear- battery) with battery
#                     maxPeakList = list()
#                     NBPeakList = list()
#                     BPeakList = list()
#                     for i in range(len(netDemand)):#8760 hr have the same value, straght line indicates peak
#                         NBPeakList.append(NBPeak)
#                         BPeakList.append(BPeak)
#                         maxPeakList.append(maxPeak)
                        
#                     graphProf.append(maxPeakList)
#                     graphProf.append(NBPeakList)
#                     graphProf.append(BPeakList)

                    
#                     graphNames = list()
#                     graphNames.append('GB Electricity Demand')
#                     graphNames.append('Demand - Renewables')
#                     graphNames.append('Demand - Renewables - Battery')
#                     p1 = round((maxPeak/1000000),2)
#                     p2 = round((NBPeak/1000000),2)
#                     p3 = round((BPeak/1000000),2)
#                     peak1 = 'Peak: '+str(p1)+' GW'
#                     graphNames.append(peak1)
#                     peak2 = 'Peak - Renewables: '+str(p2)+' GW'
#                     graphNames.append(peak2)
#                     peak3 = 'Peak - Renewables - Battery: '+str(p3)+' GW'
#                     graphNames.append(peak3)
#                     graphT = 'Battery vs No Battery '+str(y+BASEYEAR)+', Battery Capacity: '+str(totalBatteryCap/1000000)+' GW'
#                     Utils.graphMultSeriesOnePlotV3(graphProf, 'Hour', 'Electricity Demand', graphT, graphNames, RESULTS_FILE_PATH)

#                     graphProf.append(batteryProf)
#                     graphNames.append('Battery Charge/Discharge')
                    
#                     fileOut = RESULTS_FILE_PATH + 'BatteryPeakYear'+str(y+BASEYEAR)+'.csv'
#                     Utils.writeListsToCSV(graphProf,graphNames,fileOut)


#             else: # otherwise, no battery considered
#                 tempNetD = netDemand.copy()

#             for k in range(len(tempNetD)):
#                 if(tempNetD[d]<0.0):
#                     tempV = hourlyCurtail[k]
#                     hourlyCurtail[k] = tempV + abs(tempNetD[d])
#                     tempNetD[d]=0.0
                    
#             # ----------------------------------------------------------------------------------------
                  


#             # This is the dispatch order for traditional generation technologies
#             tradGenTypes = list()# at this clear the list with BECCS and nuclear
#    #         tradGenTypes.append(4) # BECCS         #
#    #         tradGenTypes.append(2) # Nuclear       #
#             tradGenTypes.append(1) # CCGT
#             tradGenTypes.append(0) # Coal
#             tradGenTypes.append(3) # OCGT
            
#             tradGenNames= list()
#    #         tradGenNames.append('BECCS')           #
#    #         tradGenNames.append('Nuclear')         #
#             tradGenNames.append('CCGT')
#             tradGenNames.append('Coal')
#             tradGenNames.append('OCGT')


#     #        tradGenPerTech= list()                 #
#             randGenCompaniesIndx = Utils.randomOrderListIndx(elecGenCompanies)
#    #         totYearTGenKWh = 0.0                   #
#    #         allTGenPerTechnology = list()          #

#             # ------------------------------------------- Dispatch traditional generators to meet net demand ----------------------------
#             for gt in range(len(tradGenTypes)):
#                 tempSum=0.0

#                 deRCapSum =0.0
#                 capSum = 0.0
#                 tempCurTGen = list()
#                 for i in range(len(elecGenCompanies)):
#                     curCap, curDeRCap = elecGenCompanies[i].getCapacityByType(tradGenTypes[gt],False)
#                     deRCapSum = deRCapSum + curDeRCap
#                     capSum = capSum + curCap
                
#                 if(max(tempNetD)>deRCapSum):
#                     for gc in range(len(randGenCompaniesIndx)):
#                         cIndx = randGenCompaniesIndx[gc]
#                         sGen, newNetD, excessGen, hourGenProf = elecGenCompanies[cIndx].getTraditionalGenerationByType(tradGenTypes[gt], tempNetD)
#                         tempSum = tempSum + sGen
#                         tempNetD = list()
#                         tempNetD = newNetD
#                         totYearTGenKWh = totYearTGenKWh + sGen
#                         if(len(tempCurTGen)==0):
#                             tempCurTGen = hourGenProf.copy()
#                         else:
#                             for k in range(len(tempCurTGen)):
#                                 val = tempCurTGen[k]
#                                 tempCurTGen[k] = val + hourGenProf[k]

                                
#                         if(np.sum(excessGen)>0):
#                             for k in range(len(hourlyCurtail)):
#                                 hourlyCurtail[k] = hourlyCurtail[k] + excessGen[k]
#                     tradGenPerTech.append(tempSum)
                    
#                 else:
#                     prevTempNetD = tempNetD.copy()
#                     curS = 0.0
#                     for gc in range(len(randGenCompaniesIndx)):
#                         cIndx = randGenCompaniesIndx[gc]
#                         curCap, curDeRCap = elecGenCompanies[cIndx].getCapacityByType(tradGenTypes[gt],False)
#                         if(capSum>1): # need to make sure not dividing by 0 
#                             capFrac = curCap/capSum
#                         else:
#                             capFrac = 0.0

#                         curTempNetD = prevTempNetD.copy()    
#                         curNetD = [x*capFrac for x in curTempNetD]
                        
#                         sGen, newNetD, excessGen, hourGenProf = elecGenCompanies[cIndx].getTraditionalGenerationByType(tradGenTypes[gt], curNetD)
#                         tempSum = tempSum + sGen
#                         curS = curS + sGen
#                         totYearTGenKWh = totYearTGenKWh + sGen
                        
#                         if(len(tempCurTGen)==0):
#                             tempCurTGen = hourGenProf.copy()
#                         else:
#                             for k in range(len(tempCurTGen)): #technology
#                                 val = tempCurTGen[k]
#                                 tempCurTGen[k] = val + hourGenProf[k]


#                         if(np.sum(excessGen)>0):
#                             for k in range(len(hourlyCurtail)):
#                                 hourlyCurtail[k] = hourlyCurtail[k] + excessGen[k]
#                     tradGenPerTech.append(tempSum)
#                     if(abs(curS-np.sum(prevTempNetD))<1):
#                         tempNetD = [0.0 for x in prevTempNetD]
#                     else:
#                         print('curS ', curS)
#                         print('sum(prevTempNetD0 ', np.sum(prevTempNetD))
#                         input('problem, these should be equal ....')
                    
#                 allTGenPerTechnology.append(tempCurTGen)

#             # calculating wholesale electricity price from marginal cost
#             wholesaleEPrice, nuclearMarginalCost = Utils.getWholesaleEPrice(elecGenCompanies)
#             boolNegPrice = False
#             for k in range(len(wholesaleEPrice)): #8760
#                 if hourlyCurtail[k]>0:
#                     boolNegPrice = True
#      #               print('nuclearMarginalCost[k] old ',nuclearMarginalCost[k])
#      #               print('wholesaleEPrice[k] old ',wholesaleEPrice[k])
#                     wholesaleEPrice[k] = 0 - nuclearMarginalCost[k]
#      #               print('wholesaleEPrice[k] new ',wholesaleEPrice[k])
#      #       if(boolNegPrice):
#      #           input('????? Did wholesale price go negative ?????')
#             fileOut = RESULTS_FILE_PATH + 'WholesalePrice'+str(BASEYEAR+y)+'.csv'
#             wholesaleList = list()
#             wholesaleList.append(wholesaleEPrice)
#             maxwholesale = max(wholesaleEPrice)
#             minwholesale = min(wholesaleEPrice)
#             avgwholesale = statistics.mean(wholesaleEPrice)
#             yearlymaxwholesale.append(maxwholesale)
#             yearlyminwholesale.append(minwholesale)
#             yearlyavgwholesale.append(avgwholesale)

#             yearListTemp = list()
#             yearListTemp.append(str(BASEYEAR+y))
#             Utils.writeListsToCSV(wholesaleList,yearListTemp,fileOut)

#             # update economics of all plants and batteries
#             for k in range(len(elecGenCompanies)):
#                 elecGenCompanies[k].calcRevenue(wholesaleEPrice)

#             lossOfLoadC = 0 # energy unserved
#             for k in range(len(tempNetD)):
#                 if(tempNetD[k]>0.001):
#                     val = tempNetD[k]
#                     hourlyLossOfLoad.append(val)
#                     lossOfLoadC+=1
#                 else:
#                     hourlyLossOfLoad.append(0.0)
#             hourlyLossOfLoadPerYear.append(hourlyLossOfLoad)
#             yearlyLossOfLoadInstances.append(lossOfLoadC)
                    
            

#             yearGenPerCompanyDataTemp = list()
#             yearGenPerCompanyNameTemp = list()
#             hourlyGenPerCompanyDataTemp = list()
#             hourlyTotTGen = list()

#             plotDemandGenProf = list()
#             plotDemandGenProf.append(totalCustDemand)
#             plotDemandGenProf.append(totalRenewGen)
#             plotDemandGenNames = list()
#             plotDemandGenNames.append('totalCustDemand')
#             plotDemandGenNames.append('totalRenewGen')

#             traditionalYearlyEnergyGen = 0.0
#             traditionalYearlyEnergyGenProf = elecGenCompanies[0].traditionalGen[0].energyGenerated.copy() #8760
            
#             for gc in range (len(elecGenCompanies)):
#                 for tg in range (len(elecGenCompanies[gc].traditionalGen)):
#                     traditionalYearlyEnergyGen = traditionalYearlyEnergyGen + elecGenCompanies[gc].traditionalGen[tg].yearlyEnergyGen #yearly
#                     traditionalYearlyEnergyGenProf = [x + y for x, y in zip(traditionalYearlyEnergyGenProf, elecGenCompanies[gc].traditionalGen[tg].energyGenerated)]
                    
#             hourlyTotTGen = traditionalYearlyEnergyGenProf.copy() #8760 from all traditional plants of all companies
            
#             plotDemandGenProf.append(hourlyTotTGen)
#             plotDemandGenNames.append('hourlyTotTGen')
            
#             if((y==0 or y==maxYears-1) and boolDrawDemandGenGraph):
#                 Utils.graphMultSeriesOnePlot(plotDemandGenProf, 'Hour', 'kW', 'Demand vs Gen '+str(BASEYEAR+y), plotDemandGenNames, RESULTS_FILE_PATH)

#             yearGenPerCompanyData.extend(tradGenPerTech)# yearly total generation per traditional technology
#             tradGenNames= list()
#             tradGenNames.append('Hydrogen')
#             tradGenNames.append('Biomass')            
#             tradGenNames.append('BECCS')
#             tradGenNames.append('Nuclear')
#             tradGenNames.append('CCGT')
#             tradGenNames.append('Coal')
#             tradGenNames.append('OCGT')
#             yearGenPerCompanyName.extend(tradGenNames)


#             operationalDataOut = list()
#             operationalNamesOut = list()

#             operationalNamesOut.append('Demand')
#             operationalDataOut.append(totalCustDemand.copy())
#             if(boolEnergyStorage):
#                 operationalNamesOut.append('Battery')
#                 operationalDataOut.append(batteryProf.copy())

#             for k in range(len(rGenNames)): # solar wind etc.
#                 operationalNamesOut.append(rGenNames[k])
#                 operationalDataOut.append(allRGenPerTechnology[k].copy())

#             for k in range(len(tradGenNames)):
#                 operationalNamesOut.append(tradGenNames[k])
#                 operationalDataOut.append(allTGenPerTechnology[k].copy())

#             fileOut = RESULTS_FILE_PATH + 'HourlyOperationYear'+str(BASEYEAR+y)+'.csv'
#             Utils.writeListsToCSV(operationalDataOut,operationalNamesOut,fileOut)
#             operationalDataOut = list()
#             operationalNamesOut = list()

#             if(y==0):
#                 yearlyGenPerCompanyData = list()
#                 tempYears = list()
#                 tempYears.append(BASEYEAR)
#                 for k in range(len(yearGenPerCompanyData)):#yearGenPerCompanyData is the total generation per technology in current year (10 value for 10 tech)
#                     tempList = list()
#                     tempList.append(yearGenPerCompanyData[k])
#                     yearlyGenPerCompanyData.append(tempList)#10 list for 10 tech, each list contain many years
#             else:
#                 tempYears.append(BASEYEAR+y)
#                 for k in range(len(yearGenPerCompanyData)):
#                     yearlyGenPerCompanyData[k].append(yearGenPerCompanyData[k])
                    
#             fileOut = RESULTS_FILE_PATH + 'YearlyGeneration.csv'
#             if(y==maxYears-1):
#                 genNamesOut = yearGenPerCompanyName.copy()
#                 genNamesOut.insert(0,'Year')
#                 genDataOut = yearlyGenPerCompanyData.copy()
#                 genDataOut.insert(0,tempYears) #insert serial number of years
                
#                 Utils.writeListsToCSV(genDataOut,genNamesOut,fileOut)

#             print('yearGenPerCompanyName ',yearGenPerCompanyName)
#             print('yearGenPerCompanyData ',yearGenPerCompanyData)
            
#             #for gc in range (len(elecGenCompanies)):
#                 #for tg in range (len(elecGenCompanies[gc].traditionalGen)):
#                 #    traditionalYearlyEnergyGen = traditionalYearlyEnergyGen + elecGenCompanies[gc].traditionalGen[tg].yearlyEnergyGen #yearly
#                 #    traditionalYearlyEnergyGenProf = [x + y for x, y in zip(traditionalYearlyEnergyGenProf, elecGenCompanies[gc].traditionalGen[tg].energyGenerated)]
                  
                    
#             #########################################################






#             # -------------- Calculate Profit for each suppier ---------------
#             # ignore this section for now, not considering suppliers
#             totCustBill = list() # hourly total electricity bill from all customers
            
#             for i in range(len(custElecBills[0])):
#                 totHourBill = 0.0
#                 for j in range(len(custElecBills)):
#                     totHourBill = totHourBill + custElecBills[j][i]
#                 totCustBill.append(totHourBill)
#             # ----------------------------------------------------------------

         

#             #--------------------- Map results ---------------------------------
#             # no point in using this if not considering customers from different regions
#             if(boolDrawMap):
#                 totalDayDemand = 0.0
#                 maxDayDemand = max(custTotalDayLoads) #custtotaldayloads is the sum of all year for each consumer, for single consumer  maxDayDemand =ustTotalDayLoads
#                 tempCustTotalDayLoads = custTotalDayLoads.copy()
#                 del tempCustTotalDayLoads[len(tempCustTotalDayLoads)-1]
#                 maxResDayDemand = max(tempCustTotalDayLoads)
#                 for i in range (len(custTotalDayLoads)):#all consumers
#                     totalDayDemand = totalDayDemand + custTotalDayLoads[i] 

#                 newDrawMap = True
#                 try:
#                     GBMap = drawMap(1) # 1 = GB
#                     # sometimes drawing the map using the geopy throws an error due to internet connection so just skipping on purpose
#                     for c in range(len(energyCustomers)):
#                         demandSize = energyCustomers[c].totalNLDemand/maxResDayDemand
#                 #        demandSize = energyCustomers[c].totalNLDemand/maxDayDemand
#                         loc = energyCustomers[c].location
#                         custName = energyCustomers[c].name
#                         GBMap.setCity(loc,demandSize,custName)
#                     print('Geopy successful.')
#                 except:
#                     GBMap = oldDrawMap(1)
#                     newDrawMap = False
#                     for c in range(len(energyCustomers)):
#                         demandSize = energyCustomers[c].totalNLDemand/maxResDayDemand
#                #         demandSize = energyCustomers[c].totalNLDemand/maxDayDemand
#                         loc = energyCustomers[c].location
#                         custName = energyCustomers[c].name
#                         GBMap.setCity(loc,demandSize,custName)
#                     print('Geopy unsuccessful. Using old version.')
#                 GBMap.drawCities()

#             #--------------------------------------------------------------------
            

        

        
#         ##########################################################################
#         ################ End of year, update model for next year #################
#         ##########################################################################

#         # record curtailment
#         hourlyCurtailPerYear.append(hourlyCurtail)#hourlyCurtail8760 ; hourlyCurtailPerYear many years
#         tempCurtailCount = 0
#         for k in range(len(hourlyCurtail)):
#             if(hourlyCurtail[k]>0):
#                 tempCurtailCount+=1
#         yearlyCurtailedInstances.append(tempCurtailCount)

#         # calculating yearly emissions
#         sumTotCap = 0.0
#         sumDeRateTotCap = 0.0
#         yearlyEmissions = 0.0
#         for gc in range(len(elecGenCompanies)): # loop through all gen companies
#             elecGenCompanies[gc].calculateYearlyProfit() # get profit
#             curCap, curDeRateCap = elecGenCompanies[gc].getTotalCapacity() # get installed capacity
#             sumTotCap = sumTotCap + curCap # from initial year until now
#             sumDeRateTotCap = sumDeRateTotCap + curDeRateCap
#             yearlyEmissions = yearlyEmissions + elecGenCompanies[gc].totalEmissionsYear
        
#         capacityMargin = (sumTotCap - peakDemand)/peakDemand # calculate margins
#         deRatedCapacityMargin = (sumDeRateTotCap - peakDemand)/peakDemand

#         # calculating capacity capacity per tech per busbar
#         nuclearcaplist = [0]*len(nuclearbuslist)
#         batterycaplist = [0]*len(batterybuslist)
#         coalcaplist = [0]*len(coalbuslist)
#         windoffcaplist = [0]*len(windoffbuslist) 
#         beccscaplist = [0]*len(beccsbuslist)             
#         for gc in range(len(elecGenCompanies)):
#             for i in range(len(elecGenCompanies[gc].traditionalGen)):
#                 if(elecGenCompanies[gc].traditionalGen[i].name == 'Nuclear'):        		
#                     c = elecGenCompanies[gc].traditionalGen[i].genCapacity
#                     b = elecGenCompanies[gc].traditionalGen[i].numbus
#                     if(c>0.1 and (not (b in nuclearbuslist))):
#                         nuclearbuslist.append(b)
#                         nuclearcaplist.append(c)
#                     elif(c>0.1 and (b in nuclearbuslist)):
#                         indx = nuclearbuslist.index(b)
#                         nuclearcaplist[indx] = nuclearcaplist[indx] + c
                    
#                 elif(elecGenCompanies[gc].traditionalGen[i].name == 'Coal'):        		
#                     c = elecGenCompanies[gc].traditionalGen[i].genCapacity
#                     b = elecGenCompanies[gc].traditionalGen[i].numbus
#                     if(c>0.1 and (not (b in coalbuslist))):
#                         coalbuslist.append(b)
#                         coalcaplist.append(c)
#                     elif(c>0.1 and (b in coalbuslist)):
#                         indx = coalbuslist.index(b)
#                         coalcaplist[indx] = coalcaplist[indx] + c

#                 elif(elecGenCompanies[gc].traditionalGen[i].name == 'BECCS'):        		
#                     c = elecGenCompanies[gc].traditionalGen[i].genCapacity
#                     b = elecGenCompanies[gc].traditionalGen[i].numbus
#                     if(c>0.1 and (not (b in beccsbuslist))):
#                         beccsbuslist.append(b)
#                         beccscaplist.append(c)
#                     elif(c>0.1 and (b in beccsbuslist)):
#                         indx = beccsbuslist.index(b)
#                         beccscaplist[indx] = beccscaplist[indx] + c




#             for i in range(len(elecGenCompanies[gc].renewableGen)):
#                 if(elecGenCompanies[gc].renewableGen[i].name == 'Wind Offshore'):        		
#                     c = elecGenCompanies[gc].renewableGen[i].genCapacity
#                     b = elecGenCompanies[gc].renewableGen[i].numbus
#                     if(c>0.1 and (not (b in windoffbuslist))):
#                         windoffbuslist.append(b)
#                         windoffcaplist.append(c)
#                     elif(c>0.1 and (b in windoffbuslist)):
#                         indx = windoffbuslist.index(b)
#                         windoffcaplist[indx] = windoffcaplist[indx] + c

#             for i in range(len(elecGenCompanies[gc].energyStores)):
#                 c = elecGenCompanies[gc].energyStores[i].maxCapacity
#                 b = elecGenCompanies[gc].energyStores[i].numbus
#                 if(c>0.1 and (not (b in batterybuslist))):
#                     batterybuslist.append(b)
#                     batterycaplist.append(c)
#                 elif(c>0.1 and (b in batterybuslist)):
#                     indx = batterybuslist.index(b)
#                     batterycaplist[indx] = batterycaplist[indx] + c



#         yearlybatterycaplist.append(batterycaplist)  
#         yearlynuclearcaplist.append(nuclearcaplist)                
#         yearlycoalcaplist.append(coalcaplist)             
#         yearlywindoffcaplist.append(windoffcaplist)
#         yearlybeccscaplist.append(beccscaplist)
        
#         '''
#         # draw pie chart for 30 buses 
#         TechBus = list()
#         CapBus = list()

#         #for bus in range(1,31):
#             TechPerBus = list()
#            CapPerBus = list()
#             for gc in range(len(elecGenCompanies)):
#                 for i in range(len(elecGenCompanies[gc].traditionalGen)):
#                     if(elecGenCompanies[gc].traditionalGen[i].numbus == bus):
#                         n = elecGenCompanies[gc].traditionalGen[i].name
#                         c = elecGenCompanies[gc].traditionalGen[i].genCapacity
#                         if(c>0.1 and (not (n in TechPerBus))):
#                             TechPerBus.append(n)
#                             CapPerBus.append(c)
#                         elif(c>0.1 and (n in TechPerBus)):
#                             indx = TechPerBus.index(n)
#                             CapPerBus[indx] = CapPerBus[indx] + c
#                 for i in range(len(elecGenCompanies[gc].renewableGen)):
#                #     if(elecGenCompanies[gc].renewableGen[i].numbus == bus):
#                #         n = elecGenCompanies[gc].renewableGen[i].name
#                #         c = elecGenCompanies[gc].renewableGen[i].genCapacity
#                 #        if(c>0.1 and (not (n in TechPerBus))):
#                  #           TechPerBus.append(n)
#                  #           CapPerBus.append(c)
#                    #     elif(c>0.1 and (n in TechPerBus)):
#                             indx = TechPerBus.index(n)
#                             CapPerBus[indx] = CapPerBus[indx] + c
#             TechBus.append(TechPerBus)
#             CapBus.append(CapPerBus)
                        


#         #draw
    
#         import seaborn as sns
#         import matplotlib
#         import matplotlib.pyplot as plt
 
#         sns.set_style("whitegrid")
#         matplotlib.rcParams['font.sans-serif'] = ['SimHei']
#         matplotlib.rcParams['font.family']='sans-serif'
 
#         matplotlib.rcParams['axes.unicode_minus'] = False

#         fig, axs = plt.subplots(5,6, figsize=(50,60), sharey=True) 
#         for b in range(0,30):
#             data = CapBus[b]
#             datapc = list()
#             sumdata = np.sum(data)
#             datalabels = TechBus[b]
#             for i in range(len(data)):
#                 valpc = (data[i]/sumdata)*100
#                 datapc.append(valpc)
#                 datalabels[i] = datalabels[i] + ': '+str(round(valpc, 2))+'%'
#             a = b % 6
#             if(b<=5):
#                 c=0
#             elif(b<=11):
#                 c=1
#             elif(b<=17):
#                 c=2
#             elif(b<=23):
#                 c=3
#             else:
#                 c=4
 
#             wedges, texts = axs[c,a].pie(data, wedgeprops=dict(width=0.5), startangle=-40)
#             #axs[c,a].pie(data)
#             #axs[c,a].legend(datalabels)
#             axs[c,a].set_title('Bus '+str(b+1))
#             bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
#             kw = dict(arrowprops=dict(arrowstyle="-"),
#                   bbox=bbox_props, zorder=0, va="center")

#             for i, p in enumerate(wedges):
#                 ang = (p.theta2 - p.theta1)/2. + p.theta1
#                 y = np.sin(np.deg2rad(ang))
#                 x = np.cos(np.deg2rad(ang))
#                 horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
#                 connectionstyle = "angle,angleA=0,angleB={}".format(ang)
#                 kw["arrowprops"].update({"connectionstyle": connectionstyle})
#                 axs[c,a].annotate(datalabels[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
#                             horizontalalignment=horizontalalignment, **kw)
#         #plt.show()
        
#         #plt.save(RESULTS_FILE_PATH+str(BASEYEAR+y)+'.png')

#         '''
#         ####### Capacity auction ######

#         Utils.resetCurYearCapInvest()

#         # introduce battery storage in 2018
#         # this next part of code should only be used if using a linear increase in battery storage
        
#         if(boolEnergyStorage and boolLinearBatteryGrowth and y + BASEYEAR +1 >= 2018):
#             prevYearBatteryCap = totalBatteryCap #total discharge rate last year
#             total2018BatCap = 3590000
#             batCapRange = totalFinalBatteryCap - total2018BatCap
#             numY = (BASEYEAR + maxYears -1) - 2018 #(2050-2018) 2010+41-1=2050
            
#             if(numY > 1):
#                 batteryCapYearIncrement = batCapRange/ numY
#             else:
#                 batteryCapYearIncrement = batCapRange

#             if(y + BASEYEAR + 1 == 2018):
#                 totalBatteryCap = total2018BatCap
#             else:
#                 totalBatteryCap = prevYearBatteryCap + batteryCapYearIncrement
            
#             batteryCapPerCompany = totalBatteryCap/len(elecGenCompanies)
#             for i in range(len(elecGenCompanies)):
#                 elecGenCompanies[i].removeBatteries()
#                 elecGenCompanies[i].addBatterySize(batteryCapPerCompany)
#                 elecGenCompanies[i].curYearBatteryBuild = batteryCapPerCompany
        

#         CapPerBus = list()
#         for busc in range(1,31):            
#             for gc in range(len(elecGenCompanies)):
#                 for i in range(len(elecGenCompanies[gc].traditionalGen)):
#                     if(elecGenCompanies[gc].traditionalGen[i].numbus == busc):
#                         c = elecGenCompanies[gc].traditionalGen[i].genCapacity
#                         if(len(CapPerBus)==busc-1):
#                             CapPerBus.append(c)
#                         elif(len(CapPerBus)==busc):
#                             CapPerBus[busc-1] = CapPerBus[busc-1] + c
#                 for i in range(len(elecGenCompanies[gc].renewableGen)):
#                     if(elecGenCompanies[gc].renewableGen[i].numbus == busc):
#                         c = elecGenCompanies[gc].renewableGen[i].genCapacity
#                         if(len(CapPerBus)==busc-1):
#                             CapPerBus.append(c)
#                         elif(len(CapPerBus)==busc):
#                             CapPerBus[busc-1] = CapPerBus[busc-1] + c
#             if(len(CapPerBus)==busc-1):
#                 CapPerBus.append(0)
#             elif(len(CapPerBus)>busc):
#                 input('error')

#         PeakDPerBus = list()
#         for c in range(0,30):
#             tempeakd = max(customerNLs[c])
#             PeakDPerBus.append(tempeakd)

#         busheadroom = TNO.EvaluateHeadRoom(CapPerBus,totalCustDemand)
        
#         yearlyheadroom.append(busheadroom)
#         OneYearHeadroom = yearlyheadroom[y]
#         # cfd auction
#         policy.cfdAuction(3, 6000000, elecGenCompanies, busheadroom) # 3 years, 6 GW to be commissioned
#         # capacity auction
#         if(boolLinearBatteryGrowth and boolEnergyStorage):
#             policy.capacityAuction(4, peakDemand, elecGenCompanies, False, busheadroom)
#         else:
#             policy.capacityAuction(4, peakDemand, elecGenCompanies, boolEnergyStorage, busheadroom)

#         years.append((BASEYEAR+y))
#         yearlyTotCap.append(sumTotCap)
#         yearlyDeRCap.append(sumDeRateTotCap)
#         yearlyPeakD.append(peakDemand)
#         yearlyCapM.append(capacityMargin)
#         yearlyDeRCapM.append(deRatedCapacityMargin)
            

#         totYearGridGenKWh = totYearTGenKWh + totYearRGenKWh
#         gridCO2emisIntens = (yearlyEmissions/totYearGridGenKWh)*1000 # *1000 because want gCO2/kWh not kgCO2
#         print('year ',(BASEYEAR+y))
#         print('gridCO2emisIntens (gCO2/kWh) ',gridCO2emisIntens)

        
#         policy.increaseYear()
#         # update CO2 Price for next year
#         newCO2Price = policy.getNextYearCO2Price(gridCO2emisIntens)
#         policy.recordYearData()

#         # update wholesale electricity price
#         for gc in range(len(elecGenCompanies)): # loop through all gen companies
#             wholesEPriceChange = elecGenCompanies[gc].updateTechnologiesYear(newCO2Price)#wholesEPriceChange returns 0

#         # demand elasticity
#         for i in range(len(energyCustomers)):
#      #       demandChangePC = energyCustomers[i].updateYear(wholesEPriceChange)
#             demandChangePC = energyCustomers[i].updateYear(0.0,i) #

#         demandCoeff = 1.0 + (demandChangePC/100.0) #how mauch percentage change compared to 2018. e.g. 180%


#         # each generation company agent makes decision to invest in new capacity
#         for gc in range(len(elecGenCompanies)): # loop through all gen companies
#             if(boolLinearBatteryGrowth and boolEnergyStorage):
#                 elecGenCompanies[gc].updateCapacityDecision(peakDemand, False,OneYearHeadroom)
#             else:
#                 elecGenCompanies[gc].updateCapacityDecision(peakDemand, boolEnergyStorage,OneYearHeadroom)
                

#         batSubsReq = list()
#         for gc in range(len(elecGenCompanies)):
#             batSubsReq.append(elecGenCompanies[gc].yearlyBatterySubsNeeded)
        
#         techT, techCap, techDRCap =  getCapacityPerTech(elecGenCompanies)
#         techNamesGraph = techT.copy()

#         # draw capacity mix chart
#         if((y==0 or y==maxYears-1) and boolDrawGenMixGraph):
#             pieName = 'Capacity Mix '+str(BASEYEAR+y)
#             Utils.pieChart(techCap,techT,pieName, RESULTS_FILE_PATH)
#             techCapGW = [x / 1000000 for x in techCap]
#             Utils.barChart(techCapGW,techT,pieName, 'Capacity (GW)', RESULTS_FILE_PATH)

#         # record information
#         if(y==0):
#             techTypes = techT
#             for i in range(len(techCap)):#10 techs
#                 tempL = list()
#                 tempL.append(techCap[i])
#                 techCapYear.append(tempL) #10 list for 10 tech, each has many years

#                 tempD = list()
#                 tempD.append(techDRCap[i])
#                 techDeRCapYear.append(tempD)
#         else:
#             for i in range(len(techCap)):
#                 techCapYear[i].append(techCap[i])
#                 techDeRCapYear[i].append(techDRCap[i])

#         for gc in range(len(elecGenCompanies)): # reset values
#             elecGenCompanies[gc].resetYearlyValues()

#         Utils.resetCurYearCapInvest()

#         #Calculate net demand
#         demand = np.zeros(8760)
#         reneGen = np.zeros(8760)
#         netdemand = np.zeros(8760)
#         for c in range(30):
#             demand = np.array(customerNLs[c]) + demand
#         for gc in range(len(elecGenCompanies)):
#             for jj in range(len(elecGenCompanies[gc].renewableGen)):
#                 if(len(elecGenCompanies[gc].renewableGen[jj].energyGenerated)>0 and elecGenCompanies[gc].renewableGen[jj].numbus!=0):
#                     reneGen = reneGen + np.array(elecGenCompanies[gc].renewableGen[jj].energyGenerated)
#         netdemand = demand - reneGen
#         aaa = np.max(netdemand)
#         aa=np.argmax(netdemand)

        
#         #run DC power flow analysis
        
#         if(y in [100]):  
#             TNO.RunPowerFlow(netdemand,elecGenCompanies,customerNLs)

            
#         # writing results to file if at the end of simulation
#         if(y== maxYears-1): # End of simulation

#             print('battery subs required')
#             for k in range(len(batSubsReq)):
#                 print('k ',k)
#                 print(batSubsReq[k])
#             '''
#             try:
#                 my_np_array = np.array(batSubsReq)
#                 fileOut = RESULTS_FILE_PATH + 'BatterySubsNeeded.csv'
#                 pd.DataFrame(my_np_array).to_csv(fileOut, index = False)
#             except ZeroDivisionError:
#                 print('cant convert to numpy and write output')
#             '''
                
#             if(boolEnergyStorage):
#                 try:
#                     fileOut = RESULTS_FILE_PATH + 'BatterySubsNeeded.csv'
#                     newPD =  pd.DataFrame(np.concatenate(batSubsReq))
#                     newPD.to_csv(fileOut, index = False)
#                 except ZeroDivisionError:
#                     print('cant convert to numpy and write output v2')
                


#             #export results to csv

#             for j in range(len(techCapYear)):
#                 techCapYear[j] = [i/100 for i in techCapYear[j]]
            
#             capNamesOut = techNamesGraph.copy()
#             capNamesOut.insert(0,'Year')
#             capDataOut = techCapYear.copy()
#             capDataOut.insert(0,years)
#             fileOut = RESULTS_FILE_PATH + 'YearlyCapacity.csv'
#             Utils.writeListsToCSV(capDataOut,capNamesOut,fileOut)

#             fileOut = RESULTS_FILE_PATH + 'YearlyCapFactor.csv'
#             capFacNames = genNamesOut.copy()
#             capFacData = genDataOut.copy()
#             for k in range(len(capFacNames)):
#                 for l in range(len(capNamesOut)):
#                     if(capFacNames[k]==capNamesOut[l] and capFacNames[k]!='Year'):
#                         for m in range(len(genDataOut[k])):   #year                         
#                             actGen = genDataOut[k][m]
#                             tempCap = capDataOut[l][m]
#                             if(actGen<0.001 or tempCap<0.001):
#                                 capFacData[k][m] = 0.0
#                             else:
#                                 capFacData[k][m] = 100*actGen/(tempCap*24*365) #hourly average, actgen each hour/capacity 100 convert to percentage
                
#             Utils.writeListsToCSV(capFacData,capFacNames,fileOut)

#             fileOut = RESULTS_FILE_PATH + 'HourlyCurtailment.csv'
#             Utils.writeListsToCSV(hourlyCurtailPerYear,years,fileOut)
            
#             fileOut = RESULTS_FILE_PATH + 'HourlyLossOfLoad.csv'
#             Utils.writeListsToCSV(hourlyLossOfLoadPerYear,years,fileOut)
            
#             tempData = [years,yearlyTotCap,yearlyDeRCap ,yearlyPeakD, yearlyCapM, yearlyDeRCapM, yearlyCurtailedInstances, yearlyLossOfLoadInstances]
#             tempNames = ['Year', 'Capacity', 'Derated Capacity', 'Peak Demand', 'Capacity Margin', 'Derated Capacity Margin','Curtailed Hours', 'LossOfLoad Hours']

#             if(boolEnergyStorage):
#                 tempData.append(annualStorageCap)
#                 tempNames.append('Annual Storage Capacity')

#             fileOut = RESULTS_FILE_PATH + 'YearlySystemEvolution.csv'
#             Utils.writeListsToCSV(tempData,tempNames,fileOut)

#             policy.writeResultsToFile(RESULTS_FILE_PATH)
            
#             for k in range(len(elecGenCompanies)):    
#                 elecGenCompanies[k].writeToFileAllYears(RESULTS_FILE_PATH,k)
            
#             fileOut = RESULTS_FILE_PATH + os.path.sep + 'Nuclear' + '.csv'
#             Utils.writeListsToCSV(yearlynuclearcaplist,nuclearbuslist,fileOut)

#             fileOut = RESULTS_FILE_PATH + os.path.sep + 'Storage' + '.csv'
#             Utils.writeListsToCSV(yearlybatterycaplist,batterybuslist,fileOut)

#             fileOut = RESULTS_FILE_PATH + os.path.sep + 'Coal' + '.csv'
#             Utils.writeListsToCSV(yearlycoalcaplist,coalbuslist,fileOut)
            
#             fileOut = RESULTS_FILE_PATH + os.path.sep + 'Wind Offshore' + '.csv'
#             Utils.writeListsToCSV(yearlywindoffcaplist,windoffbuslist,fileOut)

#             fileOut = RESULTS_FILE_PATH + os.path.sep + 'BECCS' + '.csv'
#             Utils.writeListsToCSV(yearlybeccscaplist,beccsbuslist,fileOut)

#             fileOut = RESULTS_FILE_PATH + os.path.sep + 'BusDemand' + '.csv'
#             Utils.writeListsToCSV(yearlybusdemand,years, fileOut)

#             fileOut = RESULTS_FILE_PATH + os.path.sep + 'Headroom' + '.csv'
#             Utils.writeListsToCSV(yearlyheadroom,years,fileOut)

#             tempData = [years,yearlymaxwholesale,yearlyminwholesale ,yearlyavgwholesale]
#             tempNames = ['Year', 'Max Wholesale Price', 'Min Wholesale Price', 'Avg Wholesale Price'] 

#             fileOut = RESULTS_FILE_PATH + 'WholesalePriceSummary.csv'
#             Utils.writeListsToCSV(tempData,tempNames,fileOut)

#             if (boolDraw):

#                 Utils.graphMultSeriesOnePlotV2(techCapYear, 'Year', 'Capacity (MW)', 'Yearly Capacity',techNamesGraph,years, RESULTS_FILE_PATH)   
#                 Utils.graphYearlyBus(years, yearlynuclearcaplist, nuclearbuslist, 'Nuclear', RESULTS_FILE_PATH)
#                 Utils.graphYearlyBus(years, yearlybatterycaplist, batterybuslist, 'Storage', RESULTS_FILE_PATH)
#                 Utils.graphYearlyBus(years, yearlycoalcaplist, coalbuslist, 'Coal', RESULTS_FILE_PATH) 
#                 Utils.graphYearlyBus(years, yearlywindoffcaplist, windoffbuslist, 'Wind Offshore', RESULTS_FILE_PATH) 
#                 Utils.graphYearlyBus(years, yearlybeccscaplist, beccsbuslist, 'BECCS', RESULTS_FILE_PATH)   
#                 Utils.graphheadroom(years, yearlyheadroom, RESULTS_FILE_PATH)
#                 Utils.drawdemand(years, yearlybusdemand, RESULTS_FILE_PATH)
#                 Utils.graphYearlyCapacity(years, yearlyTotCap, yearlyDeRCap, yearlyPeakD, yearlyCapM, yearlyDeRCapM, RESULTS_FILE_PATH)
#                 Utils.drawwholesale(years,yearlymaxwholesale,yearlyminwholesale,yearlyavgwholesale, RESULTS_FILE_PATH)
#                 Utils.systemevaluationGraph(years,yearlyLossOfLoadInstances,yearlyCurtailedInstances, RESULTS_FILE_PATH)
#                 policy.yearGraph()

#                 # if we want to look at individual companies 
#                 displayCompanies = list()
#                 displayCompanies.append('E.On UK')
#                 displayCompanies.append('EDF Energy')
#                 displayCompanies.append('Scottish power')
#                 displayCompanies.append('SSE') 
#                 displayCompanies.append('Centrica')
                
#                 for i in range(len(elecGenCompanies)):
#                     if(elecGenCompanies[i].name in displayCompanies):
#                         elecGenCompanies[i].graphAllGensAllYears()

            
            


    
   
    











