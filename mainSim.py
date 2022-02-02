from __future__ import division

import random
import numpy as np
from customerGroup import customerGroup
from renewableGenerator import renewableGenerator

from generationCompany import generationCompany
from policyMaker import policyMaker
from heatProvider import heatProvider
from model import ABM
import Utils
import random
import pandas as pd 

import os
import pandas as pd

   
######### main method, code starts executing from here ##################
if __name__ == '__main__':

    np.random.seed(42)
    random.seed(42)

    print('========================begin======================== ')

    # Parameters of the simulation 
    BASEYEAR = 2010
    maxYears = 41 #16 = 2025 #9=2018 #  25 = 2034, 41 = 2050
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
    ABMmodel.initResultsVariables()


    

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # ---------------------------- Simulation begins here ----------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    
    for currentYear in range(maxYears): # Loop through years

        print('year {0}'.format(BASEYEAR+currentYear))
        ######### Initialisation 
        hourlyCurtail = np.array(timeSteps)
        DfNetDemand = pd.DataFrame()

        deRCapCols = [x+'_Derated_Capacity_kW' for x in ABMmodel.genTechList]
        capCols = [x+'_Capacity_kW' for x in ABMmodel.genTechList]

        ABMmodel.getCapacityInstalled() #get the capacity installed of the different technologies
        capacityPerType.loc[BASEYEAR+currentYear, temp_cols] = ABMmodel.capacityPerTypePerBus[temp_cols].sum().values
        DfSystemEvolution.loc[BASEYEAR+currentYear, 'Capacity_kW'] = ABMmodel.capacityPerTypePerBus[capCols].to_numpy().sum()
        DfSystemEvolution.loc[BASEYEAR+currentYear, 'Derated_Capacity_kW'] = ABMmodel.capacityPerTypePerBus[deRCapCols].to_numpy().sum()


        peakDemand, totalCustDemand = ABMmodel.getCustomerElectricityDemand()

        DfNetDemand['TotalCustomerCons'] = totalCustDemand
        netDemand = totalCustDemand  #total consumption of all consumers, 8760 hour 
        #===========================================================================================================================
        # ------------------------------------------- Dispatch RenewableEnergy Generation to meet net demand ----------------------------
        #===========================================================================================================================
        netDemand, hourlyCurtail = ABMmodel.dispatchRenewables(netDemand)
        DfNetDemand['TotalCustomerConsAfterRGen'] = netDemand
        #===========================================================================================================================
        # ------------------------------------------- Dispatch traditional generators to meet net demand ----------------------------
        #---------------- this only include specific traditional generators that are dispatched before batter charge/discharge 
        #===========================================================================================================================
        netDemand, hourlyCurtail = ABMmodel.dispatchTradGen(netDemand, hourlyCurtail, True)
        DfNetDemand['TotalCustomerConsAfterTGen1'] = netDemand
        #===========================================================================================================================
        # ------------------------------------------- Dispatch the batteries ----------------------------
        #===========================================================================================================================
        netDemand = ABMmodel.dispatchBatteries(netDemand)
        DfNetDemand['TotalCustomerConsAfterBattery'] = netDemand
        #===========================================================================================================================
        # ------------------------------------------- Dispatch the rest of the traditional generators to meet net demand ----------------------------
        #===========================================================================================================================
        netDemand, hourlyCurtail = ABMmodel.dispatchTradGen(netDemand, hourlyCurtail, False)
        DfNetDemand['TotalCustomerConsAfterTGen2'] = netDemand
        #===========================================================================================================================
        # ------------------------------------------- End of the Energy dispatch ----------------------------
        #===========================================================================================================================

        totYearGridGenkWh = ABMmodel.allGenPerTechnology.to_numpy().sum()

        wholesaleEPrice = ABMmodel.getWholeSalePrice(hourlyCurtail)
        DfWholesalePrices[BASEYEAR+currentYear] = wholesaleEPrice

        yearlyEmissions = ABMmodel.getEmissions(wholesaleEPrice)

        DfNetDemand['Curtailement'] = hourlyCurtail
        DfNetDemand['Loss of load'] = netDemand

        dercap_cols = [c for c in capacityPerType.columns if '_Derated_Capacity_kW' in c]
        cap_cols = [c for c in capacityPerType.columns if '_Capacity_kW' in c and 'Derated' not in c]
        sumTotCap = capacityPerType.loc[BASEYEAR+currentYear, cap_cols].sum()
        sumDeRateTotCap = capacityPerType.loc[BASEYEAR+currentYear, dercap_cols].sum()

        capacityMargin = (sumTotCap - peakDemand)/peakDemand # calculate margins
        deRatedCapacityMargin = (sumDeRateTotCap - peakDemand)/peakDemand

        carbonIntensity = yearlyEmissions/totYearGridGenkWh*1000
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_Margin_%'] = capacityMargin
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Derated_Capacity_Margin_%'] = deRatedCapacityMargin
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Peak_Demand_kW'] = peakDemand
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Emissions_kgCO2'] = yearlyEmissions #kgCO2
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Carbon_Intensity_Target_gCO2/kWh'] = ABMmodel.policyMaker.carbonIntensityTarget
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Carbon_Intensity_gCO2/kWh'] = carbonIntensity
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Carbon_Price_£/tCO2'] = ABMmodel.policyMaker.curCO2Price
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Generation_kWh'] = totYearGridGenkWh #kWh

        ABMmodel.exportPlantsEconomics()
        ##########################################################################
        ################ End of year, update model for next year #################
        ##########################################################################

        estPeakD, estDeRCap = ABMmodel.installNewCapacity(totalCustDemand, wholesaleEPrice)

        DfHeadroomYear[currentYear+BASEYEAR] = ABMmodel.OneYearHeadroom.copy() # Store the headroom of the current year
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_Auction_Estimated_Peak_Demand_kW'] = estPeakD 
        DfSystemEvolution.loc[currentYear+BASEYEAR, 'Capacity_Auction_Estimated_DeRated_Capacity_kW'] = estDeRCap


        # writing results to file if at the end of simulation
        if(currentYear == maxYears-1): # End of simulation
            fileOut = params["path_save"] + 'capacityPerType.csv'
            capacityPerType.to_csv(fileOut)  	

            fileOut = params["path_save"] + 'SystemEvolution.csv'
            DfSystemEvolution.to_csv(fileOut)

            fileOut = params["path_save"] + 'HeadroomBus.csv'
            DfHeadroomYear.to_csv(fileOut)

            fileOut = params["path_save"] + 'WholesalePrices.csv'
            DfWholesalePrices.to_csv(fileOut)

        # Export to CSV
        fileOut = params["path_save"] + 'NetDemand_'+str(currentYear+BASEYEAR)+'.csv'
        DfNetDemand.to_csv(fileOut)

        fileOut = params["path_save"] + 'allGenPerTechnology_'+str(currentYear+BASEYEAR)+'.csv'
        ABMmodel.allGenPerTechnology.to_csv(fileOut)

        fileOut = params["path_save"] + 'allGenPerCompany_'+str(currentYear+BASEYEAR)+'.csv'
        ABMmodel.allGenPerCompany.to_csv(fileOut)

        # fileOut = params["path_save"] + 'allTGenPerTechnology_'+str(currentYear+BASEYEAR)+'.csv'
        # allTGenPerTechnology.to_csv(fileOut)

        # fileOut = params["path_save"] + 'allTGenPerCompany_'+str(currentYear+BASEYEAR)+'.csv'
        # allTGenPerCompany.to_csv(fileOut)

        fileOut = params["path_save"] + 'customerNLs_'+str(currentYear+BASEYEAR)+'.csv'
        ABMmodel.customerNLs.to_csv(fileOut)

        fileOut = params["path_save"] + 'capacityPerCompanies_'+str(BASEYEAR+currentYear)+'.csv'
        ABMmodel.capacityPerCompanies.to_csv(fileOut)  

        fileOut = params["path_save"] + 'capacityPerTypePerBus_'+str(BASEYEAR+currentYear)+'.csv'
        ABMmodel.capacityPerTypePerBus.to_csv(fileOut)  

        fileOut = params["path_save"] + 'buildRatePerType_'+str(BASEYEAR+currentYear)+'.csv'
        ABMmodel.policyMaker.buildRatePerType.to_csv(fileOut)


        # Prepare the model for next year by updating some parameters in the agents (e.g., carbon price)
        ABMmodel.incrementYear(carbonIntensity)












