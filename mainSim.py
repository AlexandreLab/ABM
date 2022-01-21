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


def initBuildRate(genTechList, dfBuildRatePerType):
    buildRatePerType = {}
    for genName in genTechList:
        maxBuildRatekW = technology_technical_df.loc[genName, 'GBMaxBuildRate_kW']
        dfBuildRatePerType.loc[genName, :] = maxBuildRatekW
    return buildRatePerType

def dispatchTradGen(demand, elecGenCompanies, tradGen, capacityPerType, capacityPerCompanies, dfGenPerTechnology,dfGenPerCompany, year): 
    # tradGen is a dataframe with technical information about the generator to dispatch
    # capacityPerType is a dataframe with the capacity installed of each technology
    # year is the current year + BASEYEAR
    # dfGenPerTechnology dataframe where the results are stored
    #return the newDemand and the curtailement
    randGenCompaniesIndx = Utils.randomOrderListIndx(elecGenCompanies)

    tempNetD = demand.copy()
    tempHourlyCurtail = np.zeros(len(demand))

    for genName in tradGen.index:
        deRCapSum = capacityPerType.loc[year, genName+'_Derated_Capacity_kW']
        capSum = capacityPerType.loc[year, genName+'_Capacity_kW']
        print('Dispatch of {0} (capacity installed {1} MW)...'. format(genName, capSum/1000))

        if deRCapSum>0:
            if(max(tempNetD)>deRCapSum): #the remaining demand can be supplied entirely by this technology type
                for eGC in elecGenCompanies:
                    hourGenProf, excessGen, tempNetD = eGC.getTraditionalGenerationByType(genName, tempNetD) # return the generation profile, the excess profile and the new demand
                    #Store the results in the dataframes
                    dfGenPerTechnology[genName] = dfGenPerTechnology[genName] + hourGenProf
                    dfGenPerCompany[eGC.name] = dfGenPerCompany[eGC.name] + hourGenProf
                    tempHourlyCurtail = np.add(tempHourlyCurtail,excessGen)
            else:
                tempTotalTGen = 0.0 # total generation of this technology type (used for testing at the end of the loop) 
                totalExcess =0 
                totalGen = 0
                for eGCindex in randGenCompaniesIndx: # dispatch unit of the current technology type in companies based on the share of the technology installed in each of them
                    eGC = elecGenCompanies[eGCindex]
                    curCap = capacityPerCompanies.loc[eGC.name, genName+'_Capacity_kW']

                    if(capSum>0): # need to make sure not dividing by 0 , for noe, other types,e.g. coal CCGT is zero
                        capFrac = curCap/capSum 
                    else:
                        capFrac = 0.0

                    curTempNetD = tempNetD.copy() 
                    curNetD = [x*capFrac for x in curTempNetD]
                    # since netdemand<generation capacity, it will be afforded by capacity share of each company, the excess gen will be curtailed
                    hourGenProf, excessGen, curtempNetD = eGC.getTraditionalGenerationByType(genName, curNetD) #return a dataframe incl. generation and excess generation of the technology type and the new net demand
                    tempTotalTGen = tempTotalTGen + np.sum(hourGenProf) - np.sum(excessGen)
                    totalExcess += np.sum(excessGen) 
                    totalGen += np.sum(hourGenProf)

                    #Store the results in the dataframes

                    dfGenPerTechnology[genName] = dfGenPerTechnology[genName] + hourGenProf
                    dfGenPerCompany[eGC.name] = dfGenPerCompany[eGC.name] + hourGenProf
                    tempHourlyCurtail = np.add(tempHourlyCurtail,excessGen)

                # Test if the NetDemand is covered by the dispatch of these technoloy plants
                if abs(np.sum(tempNetD) - tempTotalTGen)<1:
                    tempNetD = np.zeros(len(tempNetD))
                else:
                    print(genName)
                    dfGenPerTechnology["Net Demand"] = tempNetD
                    dfGenPerTechnology["Curtail"] = excessGen
                    dfGenPerTechnology["Gen generation"] = hourGenProf

                    dfGenPerTechnology.to_csv("GenPerTech.csv")
                    print('Excess', totalExcess)
                    print('Gen', totalGen)

                    print('curS ',  tempTotalTGen)
                    print('sum(tempNetD)',np.sum(tempNetD))
                    raise ValueError('The amount of generation does not match the amount of demand covered')

                # Remove the generation of this technology type from the netDemand
                tempNetD = np.subtract(tempNetD, dfGenPerTechnology[genName].values)
                tempNetD = tempNetD.clip(min=0) # 0 if Demand-generation<0
            # print(dfGenPerTechnology)
    return tempNetD, tempHourlyCurtail

######### main method, code starts executing from here ##################
if __name__ == '__main__':

    np.random.seed(42)
    random.seed(42)

    print('========================begin======================== ')
    # Utils.resetCurYearCapInvest() # what does it do?
    BASEYEAR = 2010 # 2010
    RESULTS_FILE_PATH = 'Results/2050/'
    maxYears = 16 #16 = 2025 #9=2018 #  25 = 2034, 41 = 2050
    timeSteps = 8760
    boolEnergyStorage = False
    boolLinearBatteryGrowth = True

    idx_year = [BASEYEAR+y for y in range(maxYears)]
    
    path_technology_dataset = r'D:\OneDrive - Cardiff University\04 - Projects\18 - ABM\01 - Code\ABM code - Dec 2021\Code_WH'

    # list of generation technologies
    technoloy_dataset_fn = "technology_technical_economic_parameters.xlsx"
    temp_df = pd.read_excel(path_technology_dataset+os.path.sep+technoloy_dataset_fn, sheet_name = "technical_parameters", index_col=0)
    technology_technical_df = temp_df.loc[temp_df["Set"]=="Current", :].copy()

    temp_df = pd.read_excel(path_technology_dataset+os.path.sep+technoloy_dataset_fn, sheet_name = "economic_parameters")
    technology_economic_df = temp_df.loc[temp_df["Set"]=="Current", :].copy()
    technology_economic_df.fillna(0, inplace=True)

    busbarConstraints = pd.read_excel(path_technology_dataset+os.path.sep+technoloy_dataset_fn, sheet_name = "Bus constraints", index_col=0)
    busbarConstraints.fillna(0, inplace=True)

    params = {}
    params["technical_parameters"] = technology_technical_df
    params["economic_parameters"] = technology_economic_df
    params["busbar_constraints"] = busbarConstraints
    genTechList = list(technology_technical_df.index)

    buildRatePerType = pd.DataFrame(index= genTechList+['Battery'],columns=[BASEYEAR+y for y in range(70)])
    buildRatePerType.fillna(0, inplace=True)

    # path to where you want results output to
    
    params["path_save"] = RESULTS_FILE_PATH
    params["path_wholesale_fuel_price"] = r'D:\OneDrive - Cardiff University\04 - Projects\18 - ABM\01 - Code\ABM code - Jan 2022 saved\Code_WH\WholesaleEnergyPrices'

    list_tgen = list(technology_technical_df.loc[technology_technical_df['Renewable_Flag']==0, :].index)
    list_rgen = list(technology_technical_df.loc[technology_technical_df['Renewable_Flag']==1, :].index)

    heatAndGas = list() # ignore this for now
    gasProv = heatProvider() 
    heatAndGas.append(gasProv)
    demandCoeff = 1.0 # coefficient to scale non residential demand based on price elasticity#how mauch percentage change compared to 2018. e.g. 180%

    temp_cols = [x+'_Derated_Capacity_kW' for x in genTechList+['Battery']] + [x+'_Capacity_kW' for x in genTechList+['Battery']]
    
    capacityPerType = pd.DataFrame(columns=temp_cols, index=idx_year) # store the capacity by technology type for each year of the simulation
    capacityPerType.fillna(0, inplace=True)

    DfSystemEvolution = pd.DataFrame() # Store the capacity, derated capacity, peak demand, capacity margin
    DfHeadroomYear = pd.DataFrame() 



    # these battery capacity values are only needed if a linear increase in battery is implemented
    if(BASEYEAR == 2018):
        totalBatteryPower = 700000.0 # 700 MW in 2018
    elif(BASEYEAR == 2010):
        totalBatteryPower = 10000.0 #0 MW in 2010 (set at 10MW for test purposes)


    # FES Two Degrees scenario says 3.59 GW batteries in 2018 and 22.512 GW in 2050
    # http://fes.nationalgrid.com/media/1409/fes-2019.pdf page 133
        
    totalFinalBatteryPower = 10000000.0#22512000.0 #10000000.0 # 10 GW in 2050
 #   totalFinalBatteryCap = 10000000.0 # 10 GW in 2050
    totalStartBatteryPower = totalBatteryPower


    yearlyheadroom = list()
    policy = policyMaker(params, BASEYEAR)
    OneYearHeadroom = [-32212711.56,-32067843.49,-31767613.28,-28212832.94,-28021373.43,-29166767.52,-28040878.71,-30277254.05,-31222433.48,-31615902.27,-35658351.5,-38698275.52,-39831850.5,-36304364.7,-40756536.12,-33969231.94,-43217107.73,-46674012.56,-44359251.32,-42836333.58,-41055681.71,-36877967.42,-35329923.93,-29181850.14,-31686007.01,-29468773.98,-28935821.38,-31005560.87,-30411533.39,-29371379.89]
    #initialise with 2010
    energyCustomers = list()

  
    #Create 30 customers representing the 30 bus bars
    for busbar in range(1,31):
        cust = customerGroup(timeSteps, BASEYEAR, busbar)
        cust.updateLoadProfile()
        energyCustomers.append(cust)
        


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
    GBGenPlantsOwners.fillna(0, inplace=True)

    for i in range(len(GBGenPlantsOwners['Station Name'])):
        tempName = GBGenPlantsOwners['Fuel'].iloc[i] #raw
        tempbus = int(GBGenPlantsOwners['Bus'].iloc[i])
        if(not (tempbus == 0) and tempName in genTechList):
            curCompName = GBGenPlantsOwners['Company Name'].iloc[i]
            if(not (curCompName in elecGenCompNAMESONLY)):
                print(curCompName)
                elecGenCompNAMESONLY.append(curCompName)
                genCompany = generationCompany(timeSteps, params, BASEYEAR)
                genCompany.name = curCompName        
                elecGenCompanies.append(genCompany)


    distGenCompany = generationCompany(timeSteps, params, BASEYEAR)
    distGenCompany.name = 'Distributed Generation'
    elecGenCompanies.append(distGenCompany)


    list_companies_name = [eGC.name for eGC in elecGenCompanies]
    
            
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
        tempbus = int(GBGenPlantsOwners['Bus'].iloc[i])
        if (tempbus > 0) and tempName in genTechList: # Bus > 0 ==> the plant is for northern ireland
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
                    capMarketBool = int(technology_technical_df.loc[tempName, 'Capacity_Market_Flag'])

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
                        genTypeID = int(technology_technical_df.loc[tempName, "TypeID"])
                        renGen = renewableGenerator('Wind Offshore', genTypeID, tempCapKW, lifetime, 0.0,1,OneYearHeadroom[tempbus-1], BASEYEAR) # temporary generator to estimate the annual costs
                        yearCost, subsidy = renGen.estAnnualCosts(tempCapKW)

                    tempStartYear = int(GBGenPlantsOwners['StartYear'].iloc[i])
                    tempEndYear = tempStartYear + lifetime
                    if(tempEndYear<BASEYEAR):
                        tempEndYear = random.randint(2018, 2025)

                    tempAge = tempStartYear - BASEYEAR
                    eGC.addGeneration(tempName, tempRen, tempCapKW, lifetime ,tempStartYear, tempEndYear, tempAge, subsidy, cfdBool, capMarketBool, tempbus, OneYearHeadroom[tempbus-1])
 
    print(capacityInstalledMW)
    # --------------------------------------------------------------------------

    # --------- Add generation from smaller distributed generation -------------
    


    pvPlantsFile = 'OtherDocuments/OperationalPVs2017test_wOwner.csv' # these records are for end of 2017
    GBPVPlants = Utils.readCSV(pvPlantsFile)
    GBPVPlants.fillna(0, inplace=True)

    windOnPlantsFile = 'OtherDocuments/OperationalWindOnshore2017test_wOwner.csv'
    GBWindOnPlants = Utils.readCSV(windOnPlantsFile)
    GBWindOnPlants.fillna(0, inplace=True)

    windOffPlantsFile = 'OtherDocuments/OperationalWindOffshore2017test_wOwner.csv'
    GBWindOffPlants = Utils.readCSV(windOffPlantsFile)
    GBWindOffPlants.fillna(0, inplace=True)
    print('Adding Additional Distributed Generation')


    for i in range(len(GBWindOffPlants['Name'])): # Adding in offshore plants already under construction that are due to come online soon
        tempName = 'Wind Offshore'
        genTypeID = int(technology_technical_df.loc[tempName, "TypeID"])
        tempRen = int(technology_technical_df.loc[tempName, 'Renewable_Flag'])
        sYear = GBWindOffPlants['StartYear'].iloc[i]
        tempbus = int(GBWindOffPlants['Bus'].iloc[i])

        if tempbus>0: #the plant is not in Northern Ireland
            if(sYear>2010 and sYear<2014):
                tempName = GBWindOffPlants['Type'].iloc[i]
                tempCapKW = GBWindOffPlants['Capacity(kW)'].iloc[i]
                eYear = GBWindOffPlants['EndYear'].iloc[i]
                
                lifetime = eYear - sYear
                renGen = renewableGenerator(tempName, genTypeID, tempCapKW, lifetime, 0.0,1,OneYearHeadroom[tempbus-1], BASEYEAR)
                yearCost, yCostPerKWh = renGen.estAnnualCosts(tempCapKW)
                distGenCompany.addGeneration(tempName, tempRen, tempCapKW, lifetime ,sYear, 2052, 0, yearCost, True, False, tempbus, OneYearHeadroom[tempbus-1])
 
            
    for i in range(len(GBWindOnPlants['Name'])): # Adding in onshore plants already under construction that are due to come online soon
        tempName = 'Wind Onshore'
        genTypeID = int(technology_technical_df.loc[tempName, "TypeID"])
        tempRen = int(technology_technical_df.loc[tempName, 'Renewable_Flag'])
        sYear = GBWindOnPlants['StartYear'].iloc[i]
        tempbus = GBWindOnPlants['Bus'].iloc[i]
        if tempbus>0: #the plant is not in Northern Ireland
            if(sYear>2010 and sYear<2013):
                tempName = GBWindOnPlants['Type'].iloc[i]
                cap = GBWindOnPlants['Capacity(kW)'].iloc[i]
                eYear = GBWindOnPlants['EndYear'].iloc[i]
                lifetime = eYear - sYear
                distGenCompany.addGeneration(tempName, tempRen, tempCapKW, lifetime ,sYear, eYear, 0, 0, False, False, tempbus, OneYearHeadroom[tempbus-1])

    
    if(BASEYEAR==2018):
        avgPVStartYear = int(round(GBPVPlants['StartYear'].mean()))
        avgWindOnStartYear = int(round(GBWindOnPlants['StartYear'].mean()))
        avgWindOffStartYear =int(round(GBWindOffPlants['StartYear'].mean()))
    else:
        avgPVStartYear = BASEYEAR - 1
        avgWindOnStartYear = BASEYEAR - 1
        avgWindOffStartYear = BASEYEAR - 1
    
    solarCapMWBASEYEAR = technology_technical_df.loc['Solar', 'DER_Capacity_Installed_'+str(BASEYEAR)+'_MW']
    windOnshoreCapMWBASEYEAR = technology_technical_df.loc['Wind Onshore', 'DER_Capacity_Installed_'+str(BASEYEAR)+'_MW']
    windOffshoreCapMWBASEYEAR = technology_technical_df.loc['Wind Offshore', 'DER_Capacity_Installed_'+str(BASEYEAR)+'_MW']

    sCapkW = (solarCapMWBASEYEAR - capacityInstalledMW['Solar'])*1000.0
    wOnCapkW = (windOnshoreCapMWBASEYEAR - capacityInstalledMW['Wind Onshore'])*1000.0
    wOffCapkW = (windOffshoreCapMWBASEYEAR - capacityInstalledMW['Wind Offshore'])*1000.0  #actual data- recod large plant=distributed

    temprand=random.randint(1,30)
    lifetime = int(technology_technical_df.loc['Solar', 'Lifetime_Years'])
    distGenCompany.addGeneration('Solar', 1, sCapkW, lifetime,avgPVStartYear, 2052, (avgPVStartYear-BASEYEAR), 0, False, False, temprand, OneYearHeadroom[temprand-1])

    temprand=random.randint(1,30)
    lifetime = int(technology_technical_df.loc['Wind Onshore', 'Lifetime_Years'])
    distGenCompany.addGeneration('Wind Onshore', 1, wOnCapkW, lifetime, avgWindOnStartYear, 2052, (avgWindOnStartYear-BASEYEAR), 0.0, False,  False, temprand, OneYearHeadroom[temprand-1])
    
    temprand = random.choice([1,2,7,8,9,10,11,12,13,15,16,19,20,26,27,28,29])
    genTypeID = int(technology_technical_df.loc['Wind Offshore', "TypeID"])
    lifetime = int(technology_technical_df.loc['Wind Offshore', 'Lifetime_Years'])
    renGen = renewableGenerator('Wind Offshore', genTypeID,  wOffCapkW, lifetime, 0.0,1,OneYearHeadroom[tempbus-1], BASEYEAR)  # temporary generator to estimate the annual costs, for cfd
    yearCost, yCostPerKWh = renGen.estAnnualCosts(wOffCapkW)
    distGenCompany.addGeneration('Wind Offshore', 1, wOffCapkW, lifetime, avgWindOffStartYear, 2052, (avgWindOffStartYear-BASEYEAR), yearCost, True, False,temprand, OneYearHeadroom[temprand-1])
    

    # Add batteries to the elecGenCompanies
    if(boolEnergyStorage):
        temprand=random.randint(1,30) # allocate the battery to a random busbar
        batteryPowerPerCompany = totalBatteryPower/len(elecGenCompanies)
        for eGC in elecGenCompanies:
            eGC.addBattery(batteryPowerPerCompany, temprand)

    policy.genCompanies = elecGenCompanies #add record of the generation companies to the Policy Maker object
    # Initialise the building rate for all the companies and technologies on year 0
    initBuildRate(genTechList, buildRatePerType)
    buildRatePerType.to_csv(RESULTS_FILE_PATH+"Initial_buildRateperType.csv")
    policy.buildRatePerType = buildRatePerType
    
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # ---------------------------- Simulation begins here ----------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    



    for currentYear in range(maxYears): # Loop through years

        ######### Initialisation 
        idx_8760 = [x for x in range(8760)]

        hourlyCurtail = np.array(timeSteps)
        hourlyLossOfLoad = np.array(timeSteps)
        DfNetDemand = pd.DataFrame()
        allRGenPerCompany = pd.DataFrame(columns=list_companies_name, index=idx_8760) # df of total hourly renewable generation all year           
        allRGenPerCompany.fillna(0, inplace=True)
        allRGenPerTechnology = pd.DataFrame(columns=list_rgen, index=idx_8760)  # df showing the hourly generation for the renewable technologies
        allRGenPerTechnology.fillna(0, inplace=True)
        allTGenPerCompany = pd.DataFrame(columns=list_companies_name, index=idx_8760) # df of total hourly traditional generation all year           
        allTGenPerCompany.fillna(0, inplace=True)
        allTGenPerTechnology = pd.DataFrame(columns=list_tgen, index=idx_8760)  # df showing the hourly generation for the traditional technologies
        allTGenPerTechnology.fillna(0, inplace=True)

        
        
        print('year ',(BASEYEAR+currentYear))
        print('y ',(currentYear))

        #################### Add in some BECCS in 2019 ###############
        lifetime = int(technology_technical_df.loc['BECCS', 'Lifetime_Years'])
        if(BASEYEAR+currentYear == 2019):
            cName = 'Drax Power Ltd'
            BECCSAddBool = False
            for eGC in elecGenCompanies:
                if eGC.name == cName:
                    temprand=random.choice([2,7,10,12,13,14,15,16,17,18,19,20,22,23,24,26,28,30])

                    #addGeneration(self, genName, renewableFlag, capacityKW, lifetime, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom):
                    eGC.addGeneration('BECCS', 0, 500000.0, 25, 2019, 2019+25, 0, 0.0, False, False, temprand, OneYearHeadroom[temprand-1])
                    BECCSAddBool = True
                    print('BECCS added')
            if(not BECCSAddBool):
                input('BECCS not added ******')

        # ################### Add in some Hydrogen in 2035 ###############
        # lifetime = int(technology_technical_df.loc['Hydrogen', 'Lifetime_Years'])
        # if(BASEYEAR+currentYear == 2035):
        #     cHydrogenName = list(['Baglan Generation Ltd', 'Barking Power', 'Centrica','Citigen (London) UK Ltd', 'Coolkeeragh ESB Ltd','Corby Power Ltd', 'Cory Energy Company Ltd','Derwent Cogeneration','Drax Power Ltd','EDF Energy','E.On UK','GDF Suez','International Power/Mitsui','Premier Power Ltd','Rocksavage Power Co. Ltd','RWE Npower Plc','Thermal','Cruachan Thermal','Seabank Power Limited','Spalding Energy Company Ltd'])
        #     HydrogenAddBool = False
        #     for eGC in elecGenCompanies:
        #         if eGC.name in cHydrogenName:
        #             temprand=random.randint(1,30)
        #             #addGeneration(self, genName, renewableFlag, capacityKW, lifetime, startYear, endYear, age, subsidy, cfdBool, capMarketBool, BusNum, Headroom):
        #             eGC.addGeneration('Hydrogen', 0, 1.5, 2035, 2044, 0, 0.0, False, False, temprand, OneYearHeadroom[temprand-1])
        #             HydrogenAddBool = True
        #             print('Hydrogen added')
        #     if(not HydrogenAddBool):
        #         input('Hydrogen not added ******')      
        
        # Get the capacity installed for each technology type, by companies, and by bus
        capacityPerTypePerBus = pd.DataFrame()
        temp_cols = [x+'_Derated_Capacity_kW' for x in genTechList+['Battery']] + [x+'_Capacity_kW' for x in genTechList+['Battery']]
        capacityPerCompanies = pd.DataFrame(columns=temp_cols , index=list_companies_name) # store the capacity by technology type for each companies
        capacityPerCompanies.fillna(0, inplace=True)


        deRCapCols = [x+'_Derated_Capacity_kW' for x in genTechList+['Battery']]
        capCols = [x+'_Capacity_kW' for x in genTechList+['Battery']]

        frames_capacityPerTypePerBus = []
        for eGC in elecGenCompanies: #all companies have been added at the beginning
            eGC.calculateCapacityByType(genTechList+['Battery'], [eC.busbar for eC in energyCustomers])
            temp_capacityPerTypePerBus = eGC.capacityPerTypePerBus.copy()
            capacityPerCompanies.loc[eGC.name, temp_cols] = temp_capacityPerTypePerBus[temp_cols].sum().values

            frames_capacityPerTypePerBus.append(temp_capacityPerTypePerBus.reset_index())
            
        capacityPerTypePerBus = pd.concat(frames_capacityPerTypePerBus).groupby("Busbars").sum()
        capacityPerType.loc[BASEYEAR+currentYear, temp_cols] = capacityPerTypePerBus[temp_cols].sum().values
        DfSystemEvolution.loc[BASEYEAR+currentYear, 'Capacity_kW'] = capacityPerTypePerBus[capCols].to_numpy().sum()
        DfSystemEvolution.loc[BASEYEAR+currentYear, 'Derated_Capacity_kW'] = capacityPerTypePerBus[deRCapCols].to_numpy().sum()





        # Update the wholesalePrice of the batteries
        if boolEnergyStorage:
            totalBatteryCap = 0.0
            for eGC in elecGenCompanies:
                eGC.setBatteryWholesalePrice()
            

        for d in range (1): # set to 1 as each customer will simulate 8760 hours (365 days)
            customerNLs = pd.DataFrame() #list of a number of customers, each customer has 8760 hour data
            customerHeatLoads = pd.DataFrame()
            totalCustDemand = list()
            custElecBills = pd.DataFrame()

            totalRenewGen = list()

            for eC in energyCustomers:
                curCustNL = eC.runSim() # sim energy consumption each hour
                customerNLs[eC.busbar] = curCustNL


            # --------------- Heat Demand -----------------
            # again, ignore this section for now
            # get heat and gas providers to meet demand
            # Not use anywhere for now? not sure what is the role of the heatProvider
            # for c in range(len(heatAndGas)):
            #     curHeatGen,newHeatD = heatAndGas[c].getGeneration(customerHeatLoads.sum(axis=1).values)
            #     tempHeatD = list()
            #     tempHeatD = newHeatD

            #------------- get total customer electricity demand -------------
            totalCustDemand = np.array(customerNLs.sum(axis=1).values)
            peakDemand = customerNLs.sum(axis=1).max()

            DfNetDemand['TotalCustomerCons'] = customerNLs.sum(axis=1).values
            netDemand = customerNLs.sum(axis=1).values  #total consumption of all consumers, 8760 hour 

            #===========================================================================================================================
            # ------------------------------------------- Dispatch RenewableEnergy Generation to meet net demand ----------------------------
            #===========================================================================================================================

            for genName in list_rgen:
                total_arr_hourlyGen = np.zeros(timeSteps)
                for eGC in elecGenCompanies:
                    arr_hourlyGen = eGC.getRenewableGenerationByType(genName)
                    total_arr_hourlyGen = np.add(total_arr_hourlyGen, arr_hourlyGen)
                    allRGenPerCompany[eGC.name] = allRGenPerCompany[eGC.name] + arr_hourlyGen

                allRGenPerTechnology[genName] = total_arr_hourlyGen
 
            totYearRGenKWh = allRGenPerTechnology.sum().sum() # sum of the renewable generation from all companies

            if len(allRGenPerTechnology.columns)>1:
                totalRenewGen = allRGenPerTechnology.sum(axis=1).values # get total renew generation profile 8760 values
            else:
                totalRenewGen = allRGenPerTechnology.values # get total renew generation profile 8760 values

            netDemand = np.subtract(netDemand, totalRenewGen)
            hourlyCurtail = -netDemand
            hourlyCurtail = hourlyCurtail.clip(min=0) #x<0 when demand>generation
            netDemand = netDemand.clip(min=0)

            DfNetDemand['TotalCustomerConsAfterRGen'] = netDemand

            #===========================================================================================================================
            # ------------------------------------------- Dispatch traditional generators to meet net demand ----------------------------
            #---------------- this only include specific traditional generators that are dispatched before batter charge/discharge 
            #===========================================================================================================================
            
            tradGen = technology_technical_df.loc[(technology_technical_df['Dispatch_Before_Storage']==1) & (technology_technical_df['Renewable_Flag']==0), :].copy()
            tradGen = tradGen.sort_values(by='MeritOrder', ascending=True)

            tempNetD = netDemand.copy()

            print('Dispatch of {0}'.format(list(tradGen.index)))
            tempNetD, tempHourlyCurtail = dispatchTradGen(netDemand, elecGenCompanies, tradGen,capacityPerType, capacityPerCompanies, allTGenPerTechnology,allTGenPerCompany, BASEYEAR+currentYear)
            hourlyCurtail = np.add(hourlyCurtail,tempHourlyCurtail)
            netDemand = tempNetD
            DfNetDemand['TotalCustomerConsAfterTGen1'] = netDemand

            #===========================================================================================================================
            # ------------------------------------------- Dispatch the batteries ----------------------------
            #===========================================================================================================================
            
            if boolEnergyStorage:
                print('Charging/Discharging of batteries...')
                tNetDemand = netDemand.copy()
                for eGC in elecGenCompanies:
                    tNetDemand = eGC.chargeDischargeBatteryTime(tNetDemand)
                netDemand = tNetDemand # final net demand after account for all companies
                    
            DfNetDemand['TotalCustomerConsAfterBattery'] = netDemand

            #===========================================================================================================================
            # ------------------------------------------- Dispatch the rest of the traditional generators to meet net demand ----------------------------
            #===========================================================================================================================
            tradGen = technology_technical_df.loc[(technology_technical_df['Dispatch_Before_Storage']==0) & (technology_technical_df['Renewable_Flag']==0), :].copy()
            tradGen = tradGen.sort_values(by='MeritOrder', ascending=True)


            print('Dispatch of {0}'.format(list(tradGen.index)))

            tempNetD, tempHourlyCurtail = dispatchTradGen(netDemand, elecGenCompanies, tradGen,capacityPerType, capacityPerCompanies, allTGenPerTechnology,allTGenPerCompany, BASEYEAR+currentYear)
            hourlyCurtail = np.add(hourlyCurtail,tempHourlyCurtail)
            netDemand = tempNetD
            DfNetDemand['TotalCustomerConsAfterTGen2'] = netDemand

            #===========================================================================================================================
            # ------------------------------------------- End of the Energy dispatch ----------------------------
            #===========================================================================================================================

        totYearGridGenkWh = allTGenPerTechnology.to_numpy().sum() + allRGenPerTechnology.to_numpy().sum()

        # calculating wholesale electricity price from marginal cost of each generator
        wholesaleEPrice, nuclearMarginalCost = Utils.getWholesaleEPrice(elecGenCompanies)
        boolNegPrice = False

        for k in range(len(wholesaleEPrice)): #8760
            if hourlyCurtail[k]>0:
                boolNegPrice = True
                wholesaleEPrice[k] = 0 - nuclearMarginalCost[k]

        DfWholesalePrices = pd.DataFrame()
        DfWholesalePrices['WholesalePrice'] = wholesaleEPrice

        # update economics of all plants and batteries and calculate the emissions
        # update the current wholesaleEPrice to calculate the profit made by each plant 
        yearlyEmissions = 0.0
        for eGC in elecGenCompanies:
            eGC.calcRevenue(wholesaleEPrice)
            yearlyEmissions += eGC.calcEmissions() #kgCO2

        hourlyLossOfLoad = tempNetD

        DfNetDemand['Curtailement'] = hourlyCurtail
        DfNetDemand['Loss of load'] = hourlyLossOfLoad

        dercap_cols = [c for c in capacityPerType.columns if '_Derated_Capacity_kW' in c]
        cap_cols = [c for c in capacityPerType.columns if '_Capacity_kW' in c and 'Derated' not in c]
        sumTotCap = capacityPerType.loc[BASEYEAR+currentYear, cap_cols].sum()
        sumDeRateTotCap = capacityPerType.loc[BASEYEAR+currentYear, dercap_cols].sum()

        capacityMargin = (sumTotCap - peakDemand)/peakDemand # calculate margins
        deRatedCapacityMargin = (sumDeRateTotCap - peakDemand)/peakDemand

        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_Margin_%'] = capacityMargin
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Derated_Capacity_Margin_%'] = deRatedCapacityMargin
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Peak_Demand_kW'] = peakDemand
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Emissions_kgCO2'] = yearlyEmissions #kgCO2
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Generation_kWh'] = totYearGridGenkWh #kgCO2
            
        ##########################################################################
        ################ End of year, update model for next year #################
        ##########################################################################


        


        ####### Capacity auction ######


        
        # introduce battery storage in 2018
        # this next part of code should only be used if using a linear increase in battery storage
        # Need to be updated
        # if(boolEnergyStorage and boolLinearBatteryGrowth and currentYear + BASEYEAR +1 >= 2018):
        #     prevYearBatteryPower = totalBatteryPower #total discharge rate last year
        #     total2018BatPower = 3590000
        #     batPowerRange = totalFinalBatteryPower - total2018BatPower
        #     numY = (BASEYEAR + maxYears -1) - 2018 #(2050-2018) 2010+41-1=2050
            
        #     if(numY > 1):
        #         batteryPowerYearIncrement = batPowerRange/ numY
        #     else:
        #         batteryPowerYearIncrement = batPowerRange

        #     if(currentYear + BASEYEAR + 1 == 2018):
        #         totalBatteryPower = total2018BatPower
        #     else:
        #         totalBatteryPower = prevYearBatteryPower + batteryPowerYearIncrement
            
        #     batteryPowerPerCompany = totalBatteryPower/len(elecGenCompanies)
        #     for eGC in elecGenCompanies:
        #         eGC.addBatterySize(batteryPowerPerCompany)
        #         eGC.curYearBatteryBuild = batteryPowerPerCompany
        


        capacityPerBusValues = capacityPerTypePerBus.T.sum().values
        OneYearHeadroom = TNO.EvaluateHeadRoom(capacityPerBusValues,totalCustDemand)
        DfHeadroomYear[currentYear+BASEYEAR] = OneYearHeadroom.copy() # Store the headroom of the current year

        # cfd auction
        policy.cfdAuction(3, 6000000, 4, OneYearHeadroom, np.mean(wholesaleEPrice)) # 3 years, 6 GW to be commissioned, max 4 years construction time



        #Capacity auction
        estPeakD, estDeRCap = policy.capacityAuction(4, peakDemand, False, OneYearHeadroom,)

        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_Auction_Estimated_Peak_Demand_kW'] = estPeakD 
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_Auction_Estimated_DeRated_Capacity_kW'] = estDeRCap

        # update CO2 Price for next year
        newCO2Price = policy.getNextYearCO2Price(yearlyEmissions/totYearGridGenkWh*1000) #carbon intensity in gCO2/kWh input

        # Update CO2 Price and check the construction queue to build plants
        for eGC in elecGenCompanies:
            eGC.updateYear(OneYearHeadroom, newCO2Price)

        # # capacity auction
        # if(boolLinearBatteryGrowth and boolEnergyStorage):
        #     technologyList, newCapList_CapacityAuction = policy.capacityAuction(4, peakDemand, elecGenCompanies, False, OneYearHeadroom)
        # else:
        #     technologyList, newCapList_CapacityAuction = policy.capacityAuction(4, peakDemand, elecGenCompanies, boolEnergyStorage, OneYearHeadroom)
            

        # totYearGridGenKWh = allTGenPerTechnology.sum().sum() + allRGenPerTechnology.sum().sum()
        # gridCO2emisIntens = (yearlyEmissions/totYearGridGenKWh)*1000 # *1000 because want gCO2/kWh not kgCO2
        # print('year ',(BASEYEAR+currentYear))
        # print('gridCO2emisIntens (gCO2/kWh) ',gridCO2emisIntens)

        policy.increaseYear()
        # # update CO2 Price for next year
        # newCO2Price = policy.getNextYearCO2Price(gridCO2emisIntens)
        # policy.recordYearData()



        # # update wholesale electricity price
        # for eGC in elecGenCompanies: # loop through all gen companies
        #     eGC.updateTechnologiesYear(newCO2Price)#wholesEPriceChange returns 0

        # demand elasticity
        for eC in energyCustomers:
            demandChangePC = eC.updateYear(0.0) #

        # demandCoeff = 1.0 + (demandChangePC/100.0) #how mauch percentage change compared to 2018. e.g. 180%

        # # each generation company agent makes decision to invest in new capacity
        # for eGC in elecGenCompanies: # loop through all gen companies
        #     if(boolLinearBatteryGrowth and boolEnergyStorage):
        #         newCapList = eGC.updateCapacityDecision(peakDemand, False,OneYearHeadroom, newCapList)
        #     else:
        #         newCapList = eGC.updateCapacityDecision(peakDemand, boolEnergyStorage,OneYearHeadroom, newCapList)
                
        # batSubsReq = list()
        # for eGC in elecGenCompanies:
        #     batSubsReq.append(eGC.yearlyBatterySubsNeeded)
        
        # for eGC in elecGenCompanies: # reset values
        #     eGC.resetYearlyValues()

            
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

        fileOut = RESULTS_FILE_PATH + 'capacityPerCompanies'+str(BASEYEAR+currentYear)+'.csv'
        capacityPerCompanies.to_csv(fileOut)  

        fileOut = RESULTS_FILE_PATH + 'capacityPerTypePerBus'+str(BASEYEAR+currentYear)+'.csv'
        capacityPerTypePerBus.to_csv(fileOut)  

        fileOut = RESULTS_FILE_PATH + 'WholesalePrice'+str(BASEYEAR+currentYear)+'.csv'
        DfWholesalePrices.to_csv(fileOut)

            

    
   
    











