import random
import numpy as np
from model import ABM
import Utils
import pandas as pd

   
######### main method, code starts executing from here ##################
if __name__ == '__main__':

    np.random.seed(42)
    random.seed(42)

    print('========================begin======================== ')

    # Parameters of the simulation
    BASEYEAR = 2010
    MAXYEARS = 11 #11 = 2020, 16 = 2025 #9=2018 #  25 = 2034, 41 = 2050
    timesteps = 8760
    bool_energy_storage = True
    bool_linear_battery_growth = True

    # Initialisation of variables
    IDX_YEAR = np.arange(BASEYEAR, BASEYEAR+MAXYEARS)
    PARAMS = Utils.getParams(bool_energy_storage)

    #Creation of the agents
    ABMmodel = ABM(PARAMS, BASEYEAR, bool_energy_storage)
    ABMmodel.createPolicyMaker()
    nb_customers = 30 # 30 busbars
    ABMmodel.createEnergyCustomers(nb_customers)
    ABMmodel.createGenerationCompanies()
    ABMmodel.addDistributedGeneration()
    ABMmodel.initTechPortoflio()
    ABMmodel.initResultsVariables()
    

    # Initialisation of variables 2
    tech_df = PARAMS["technical_parameters"]
    gen_tech_list = PARAMS["gen_tech_list"]
    storage_tech_list = PARAMS["storage_tech_list"]

    gen_capacity_cols = [x+'_Derated_Capacity_kW' for x in gen_tech_list] + [x+'_Capacity_kW' for x in gen_tech_list]
    derated_cap_cols = [x+'_Derated_Capacity_kW' for x in ABMmodel.gen_tech_list]
    cap_cols = [x+'_Capacity_kW' for x in ABMmodel.gen_tech_list]
    busbar_cols = np.arange(1, nb_customers+1)
    storage_capacity_cols = [x+'_Capacity_kWh' for x in storage_tech_list]


    # variables where results are stored

    gen_capacity_per_type = pd.DataFrame(columns=gen_capacity_cols, index=IDX_YEAR) # store the capacity by technology type for each year of the simulation
    gen_capacity_per_type.fillna(0, inplace=True)

    storage_capacity_per_type = pd.DataFrame(columns=storage_capacity_cols, index=IDX_YEAR) # store the capacity by technology type for each year of the simulation
    storage_capacity_per_type.fillna(0, inplace=True)

    system_evolution_df = pd.DataFrame() # Store the capacity, derated capacity, peak demand, capacity margin
    merit_order_per_year_df = pd.DataFrame(columns = ABMmodel.merit_order, index=IDX_YEAR) 
    wholesaleprice_per_year_df = pd.DataFrame()

    TNUoS_charges_per_bus_per_year_df = pd.DataFrame(columns = busbar_cols)

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # ---------------------------- Simulation begins here ----------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    for current_year in range(MAXYEARS): # Loop through years

        print('year {0}'.format(BASEYEAR+current_year))
        ######### Initialisation 
        ABMmodel.get_capacity_installed() #get the capacity installed of the different technologies
        ABMmodel.update_TNUoS_charges()
        TNUoS_charges_per_bus_per_year_df.loc[BASEYEAR+current_year, :] = ABMmodel.TNUoS_charges.loc["TNUoS_charges_GBP/kW", busbar_cols].values
        gen_capacity_per_type.loc[BASEYEAR+current_year, gen_capacity_cols] = ABMmodel.gen_cap_per_type_per_bus[gen_capacity_cols].sum().values
        storage_capacity_per_type.loc[BASEYEAR+current_year, storage_capacity_cols] = ABMmodel.storage_cap_per_type_per_bus[storage_capacity_cols].sum().values

        system_evolution_df.loc[BASEYEAR+current_year, 'Capacity_kW'] = ABMmodel.gen_cap_per_type_per_bus[cap_cols].to_numpy().sum()
        system_evolution_df.loc[BASEYEAR+current_year, 'Derated_Capacity_kW'] = ABMmodel.gen_cap_per_type_per_bus[derated_cap_cols].to_numpy().sum()
        system_evolution_df.loc[BASEYEAR+current_year, 'Storage_Capacity_kWh'] = ABMmodel.storage_cap_per_type_per_bus[storage_capacity_cols].to_numpy().sum()

        merit_order_per_year_df.loc[BASEYEAR+current_year, :] = [ABMmodel.merit_order.index(gen_name) for gen_name in merit_order_per_year_df.columns]
        ABMmodel.getCustomerElectricityDemand()
        #===========================================================================================================================
        # ------------------------------------------- Dispatch RenewableEnergy Generation to meet net demand ----------------------------
        #===========================================================================================================================
        ABMmodel.dispatchRenewables()
        #===========================================================================================================================
        # ------------------------------------------- Dispatch traditional generators to meet net demand ----------------------------
        #---------------- this only include specific traditional generators that are dispatched before batter charge/discharge 
        #===========================================================================================================================
        ABMmodel.dispatchTradGen(True)
        #===========================================================================================================================
        # ------------------------------------------- Dispatch the batteries ----------------------------
        #===========================================================================================================================
        ABMmodel.dispatchBatteries()
        #===========================================================================================================================
        # ------------------------------------------- Dispatch the rest of the traditional generators to meet net demand ----------------------------
        #===========================================================================================================================
        ABMmodel.dispatchTradGen(False)
        #===========================================================================================================================
        # ------------------------------------------- End of the Energy dispatch ----------------------------
        #===========================================================================================================================

        totYearGridGenkWh = ABMmodel.allGenPerTechnology.to_numpy().sum()

        wholesaleEPrice = ABMmodel.getWholeSalePrice()
        wholesaleprice_per_year_df[BASEYEAR+current_year] = wholesaleEPrice

        yearlyEmissions = ABMmodel.getEmissions(wholesaleEPrice)

        dercap_cols = [c for c in gen_capacity_per_type.columns if '_Derated_Capacity_kW' in c]
        cap_cols = [c for c in gen_capacity_per_type.columns if '_Capacity_kW' in c and 'Derated' not in c]
        sumTotCap = gen_capacity_per_type.loc[BASEYEAR+current_year, cap_cols].sum()
        sumDeRateTotCap = gen_capacity_per_type.loc[BASEYEAR+current_year, dercap_cols].sum()

        capacityMargin = (sumTotCap - ABMmodel.peak_demand)/ABMmodel.peak_demand # calculate margins
        deRatedCapacityMargin = (sumDeRateTotCap - ABMmodel.peak_demand)/ABMmodel.peak_demand

        carbonIntensity = yearlyEmissions/totYearGridGenkWh*1000
        system_evolution_df.loc[current_year+BASEYEAR, 'Capacity_Margin_%'] = capacityMargin
        system_evolution_df.loc[current_year+BASEYEAR, 'Derated_Capacity_Margin_%'] = deRatedCapacityMargin
        system_evolution_df.loc[current_year+BASEYEAR, 'Peak_Demand_kW'] = ABMmodel.peak_demand
        system_evolution_df.loc[current_year+BASEYEAR, 'Emissions_kgCO2'] = yearlyEmissions #kgCO2
        system_evolution_df.loc[current_year+BASEYEAR, 'Carbon_Intensity_Target_gCO2/kWh'] = ABMmodel.policyMaker.carbonIntensityTarget
        system_evolution_df.loc[current_year+BASEYEAR, 'Carbon_Intensity_gCO2/kWh'] = carbonIntensity
        system_evolution_df.loc[current_year+BASEYEAR, 'Carbon_Price_£/tCO2'] = ABMmodel.policyMaker.curCO2Price
        system_evolution_df.loc[current_year+BASEYEAR, 'Generation_kWh'] = totYearGridGenkWh #kWh

        ABMmodel.exportPlantsEconomics()

        ##########################################################################
        ################ End of year, update model for next year #################
        ##########################################################################

        estPeakD, estDeRCap = ABMmodel.installNewCapacity(wholesaleEPrice)

        system_evolution_df.loc[current_year+BASEYEAR, 'Capacity_Auction_Estimated_Peak_Demand_kW'] = estPeakD 
        system_evolution_df.loc[current_year+BASEYEAR, 'Capacity_Auction_Estimated_DeRated_Capacity_kW'] = estDeRCap

        # writing results to file if at the end of simulation
        if(current_year == MAXYEARS-1): # End of simulation
            fileOut = PARAMS["path_save"] + 'gen_capacity_per_type.csv'
            gen_capacity_per_type.to_csv(fileOut)  	

            fileOut = PARAMS["path_save"] + 'SystemEvolution.csv'
            system_evolution_df.to_csv(fileOut)


            fileOut = PARAMS["path_save"] + 'WholesalePrices.csv'
            wholesaleprice_per_year_df.to_csv(fileOut)

            fileOut = PARAMS["path_save"] + 'MeritOrder.csv'
            merit_order_per_year_df.to_csv(fileOut)

            fileOut = PARAMS["path_save"] + 'TNUoS_charges_per_bus_per_year.csv'
            TNUoS_charges_per_bus_per_year_df.to_csv(fileOut)


        # Export to CSV
        fileOut = PARAMS["path_save"] + 'NetDemand_'+str(current_year+BASEYEAR)+'.csv'
        ABMmodel.summaryEnergyDispatch.to_csv(fileOut)

        fileOut = PARAMS["path_save"] + 'allGenPerTechnology_'+str(current_year+BASEYEAR)+'.csv'
        ABMmodel.allGenPerTechnology.to_csv(fileOut)

        fileOut = PARAMS["path_save"] + 'allGenPerCompany_'+str(current_year+BASEYEAR)+'.csv'
        ABMmodel.allGenPerCompany.to_csv(fileOut)

        fileOut = PARAMS["path_save"] + 'customerNLs_'+str(current_year+BASEYEAR)+'.csv'
        ABMmodel.customerNLs.to_csv(fileOut)

        fileOut = PARAMS["path_save"] + 'gen_cap_per_companies_'+str(BASEYEAR+current_year)+'.csv'
        ABMmodel.gen_cap_per_companies.to_csv(fileOut)  

        fileOut = PARAMS["path_save"] + 'gen_cap_per_type_per_bus_'+str(BASEYEAR+current_year)+'.csv'
        ABMmodel.gen_cap_per_type_per_bus.to_csv(fileOut)  

        fileOut = PARAMS["path_save"] + 'storage_cap_per_type_per_bus_'+str(BASEYEAR+current_year)+'.csv'
        ABMmodel.storage_cap_per_type_per_bus.to_csv(fileOut)  

        fileOut = PARAMS["path_save"] + 'storage_cap_per_companies_'+str(BASEYEAR+current_year)+'.csv'
        ABMmodel.storage_cap_per_companies.to_csv(fileOut) 


        fileOut = PARAMS["path_save"] + 'buildRatePerType_'+str(BASEYEAR+current_year)+'.csv'
        ABMmodel.policyMaker.buildRatePerType.to_csv(fileOut)

        # Prepare the model for next year by updating some parameters in the agents (e.g., carbon price)
        ABMmodel.increment_year(carbonIntensity)
