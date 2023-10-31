import random
import numpy as np
import pandas as pd
import Utils
from customer import Customer
from customerGroup import CustomerGroup
from renewableGenerator import renewableGenerator
from generationCompany import generationCompany
from policyMaker import policyMaker


class ABM():
    
    def __init__(self, params, BASEYEAR,boolEnergyStorage, timesteps = 8760):

        self.params = params
        self.BASEYEAR = BASEYEAR
        self.year = self.BASEYEAR
        self.boolEnergyStorage = boolEnergyStorage 
        self.timesteps = timesteps
        self.numberCustomers = 1 #Number of energy consumers set to 1 by default
        self.number_eC_with_batteries = 1

        self.energyCustomers = list()
        self.policyMaker = None
        self.elecGenCompanies = list()
        self.eGC_names = list()
        self.distributedGenCompany = None # part of elecGenCompanies
        tech_df = params["technical_parameters"]
        self.gen_tech_list = params["gen_tech_list"] # list of the generation technologies used in the model
        self.storage_tech_list = params["storage_tech_list"] # list of the generation technologies used in the model

        tradGen = tech_df.loc[(tech_df['Dispatch_Before_Storage'] == False) & (tech_df['Renewable_Flag'] == 0) & (tech_df['Storage_Flag'] == 0), :].copy()
        tradGen = tradGen.sort_values(by='Initial_Merit_Order', ascending=True)
        self.merit_order = list(tradGen.index) #merit order of the traditional technologies to be dispatched after RE+Nuclear+batteries

        # variable to store the results
        self.customerNLs = pd.DataFrame() #list of a number of customers, each customer has 8760 hour data
        self.peak_demand = 0 #store the peak demand of the year
        self.buildRatePerType = pd.DataFrame(index = self.gen_tech_list,columns=np.arange(self.year, self.year+100))
        self.buildRatePerType.fillna(0, inplace=True)

        self.capacityInstalledMW = pd.DataFrame() # capacity installed in 2010

        self.gen_cap_per_type_per_bus = pd.DataFrame()
        self.gen_cap_per_companies = pd.DataFrame()
        self.storage_cap_per_type_per_bus = pd.DataFrame()
        self.storage_cap_per_companies = pd.DataFrame()

        self.allGenPerCompany = pd.DataFrame()
        self.allGenPerTechnology = pd.DataFrame()
        self.summaryEnergyDispatch = pd.DataFrame()
        self.hourlyNetDemand = np.zeros(self.timesteps) # include the total demand of the customers as well as the demand after renewable dispatch, tradggen dispatch, etc.
        self.hourlyCurtail = np.zeros(self.timesteps)

        self.TNUoS_charges = pd.DataFrame()

    def initResultsVariables(self):
        # need to be initialised after generation companies are created and after every year to be reset to 0
        idx_8760 = np.arange(0, 8760)
        self.allGenPerCompany = pd.DataFrame(columns=self.eGC_names, index=idx_8760) # df of total hourly renewable generation all year           
        self.allGenPerCompany.fillna(0, inplace=True)
        self.allGenPerTechnology = pd.DataFrame(columns=self.gen_tech_list, index=idx_8760)  # df showing the hourly generation for the renewable technologies
        self.allGenPerTechnology.fillna(0, inplace=True)

        temp_cols = [x+'_Derated_Capacity_kW' for x in self.gen_tech_list] + [x+'_Capacity_kW' for x in self.gen_tech_list]
        self.gen_cap_per_companies = pd.DataFrame(columns=temp_cols, index=self.eGC_names) # store the capacity by technology type for each companies
        self.gen_cap_per_companies.fillna(0, inplace=True)

        temp_cols = [x+'_Capacity_kWh' for x in self.storage_tech_list]
        self.storage_cap_per_companies = pd.DataFrame(columns=temp_cols, index=self.eGC_names) # store the capacity by technology type for each companies
        self.storage_cap_per_companies.fillna(0, inplace=True)

        self.hourlyNetDemand = np.zeros(self.timesteps)
        self.summaryEnergyDispatch = pd.DataFrame()
        self.hourlyCurtail = np.zeros(self.timesteps)
        self.peak_demand = 0
        return True
    
    def createEnergyCustomers(self, numberCustomers):
        self.numberCustomers = numberCustomers
        energyCustomers = list()
        if numberCustomers == 30:
            #Create 30 customers representing the 30 bus bars
            for busbar in range(1, numberCustomers+1):
                cust = CustomerGroup(self.timesteps, self.BASEYEAR, busbar)
                cust.update_load_profile()
                energyCustomers.append(cust)
                self.number_eC_with_batteries = 5
        else: #default mode has only one customer
            cust = Customer(self.timesteps, self.BASEYEAR, 0)
            energyCustomers.append(cust)
        self.energyCustomers = energyCustomers

        self.TNUoS_charges = pd.DataFrame(index=["TNUoS_charges_GBP/kW", "Derated_capacity_kW", "Derated_capacity_margin_perc", "Headroom_kW", "Peak_demand_kW"], columns=np.arange(1, numberCustomers+1))
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
            totalBatteryPower = 100000.0 #0 MW in 2010 (set at 100MW for test purposes)

        # FES Two Degrees scenario says 3.59 GW batteries in 2018 and 22.512 GW in 2050
        # http://fes.nationalgrid.com/media/1409/fes-2019.pdf page 133
            
        totalFinalBatteryPower = 10000000.0#22512000.0 #10000000.0 # 10 GW in 2050
        totalStartBatteryPower = totalBatteryPower

        # allocate battery capacity to a selected number of energy companies to randomly selected busbars
        random_eC = [x for x in range(1, self.numberCustomers+1)]
        random.shuffle(random_eC)
        name = "Li-Battery"
        batteryPowerPerCompany = totalBatteryPower/self.number_eC_with_batteries
        for idx in random_eC[:self.number_eC_with_batteries]:
            eGC = self.elecGenCompanies[idx]
            busbar = random.randint(1, 30) # allocate the battery to a random busbar
            print("Added {0} kW battery to {1}.".format(batteryPowerPerCompany, eGC.name))
            CfD_price = 0
            capacity_market_sub = 0
            start_year = self.year
            end_year = start_year + int(self.params["technical_parameters"].loc[name, 'Lifetime_Years'])
            eGC.add_unit(name, batteryPowerPerCompany, start_year, end_year, capacity_market_sub, CfD_price, busbar)

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
            if(not (tempbus == 0) and tempName in self.gen_tech_list):
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
        for tech in self.gen_tech_list:
            capacityInstalledMW[tech] = 0 # initialisation

        print('Adding Plants')

        for i in range(len(GBGenPlantsOwners['Station Name'])): # data from 2018 dukes report
            tempName = GBGenPlantsOwners['Fuel'].iloc[i]
            tempbus = int(GBGenPlantsOwners['Bus'].iloc[i])
            if (tempbus > 0) and tempName in self.gen_tech_list: # Bus > 0 ==> the plant is for northern ireland
                curCompName = GBGenPlantsOwners['Company Name'].iloc[i]
                for eGC in elecGenCompanies:
                    if(eGC.name == curCompName):
                        tempName = GBGenPlantsOwners['Fuel'].iloc[i]
                        temp_cap_kW = GBGenPlantsOwners['Installed Capacity(MW)'].iloc[i]*1000
                        capacityInstalledMW[tempName] = capacityInstalledMW[tempName] + temp_cap_kW/1000
                        lifetime = int(technology_technical_df.loc[tempName, 'Lifetime_Years'])
                        capacity_market_sub = 0
                        CfD_price = 0

                        temp_start_year = int(GBGenPlantsOwners['StartYear'].iloc[i])
                        temp_end_year = temp_start_year + lifetime
                        if(temp_end_year < self.BASEYEAR):
                            temp_end_year = random.randint(2018, 2025)

                        eGC.add_unit(tempName, temp_cap_kW, temp_start_year, temp_end_year, capacity_market_sub, CfD_price, tempbus)
    
        # Add plants to the construction queue of the distributed generation company

        # windOnPlantsFile = 'OtherDocuments/OperationalWindOnshore2017test_wOwner.csv'
        # GBWindOnPlants = pd.read_csv(windOnPlantsFile)
        # GBWindOnPlants.fillna(0, inplace=True)

        # windOffPlantsFile = 'OtherDocuments/OperationalWindOffshore2017test_wOwner.csv'
        # GBWindOffPlants = pd.read_csv(windOffPlantsFile)
        # GBWindOffPlants.fillna(0, inplace=True)
        # print('Adding Additional Distributed Generation')

        # for i in range(len(GBWindOffPlants['Name'])): # Adding in offshore plants already under construction that are due to come online soon
        #     tempName = 'Wind Offshore'
        #     genTypeID = int(technology_technical_df.loc[tempName, "TypeID"])
        #     tempRen = int(technology_technical_df.loc[tempName, 'Renewable_Flag'])
        #     sYear = GBWindOffPlants['StartYear'].iloc[i]
        #     tempbus = int(GBWindOffPlants['Bus'].iloc[i])

        #     if tempbus>0: #the plant is not in Northern Ireland
        #         if(sYear>2010 and sYear<2014):
        #             tempName = GBWindOffPlants['Type'].iloc[i]
        #             temp_cap_kW = GBWindOffPlants['Capacity(kW)'].iloc[i]
        #             eYear = GBWindOffPlants['EndYear'].iloc[i]
                    
        #             lifetime = eYear - sYear
        #             renGen = renewableGenerator(tempName, genTypeID, temp_cap_kW, lifetime, 0.0,1, self.BASEYEAR)
        #             cfdSubsidy = renGen.estimateCfDSubsidy()
        #             distGenCompany.addGeneration(tempName, tempRen, temp_cap_kW, lifetime ,sYear, 2052, 0, cfdSubsidy, True, False, tempbus)
    
                
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
        #             distGenCompany.addGeneration(tempName, tempRen, temp_cap_kW, lifetime ,sYear, eYear, 0, 0, False, False, tempbus)

        print(capacityInstalledMW)
        self.capacityInstalledMW = capacityInstalledMW
        self.elecGenCompanies = elecGenCompanies
        self.distributedGenCompany = distGenCompany
        self.eGC_names = elecGenCompNAMESONLY

        
        if self.boolEnergyStorage:
            self.addEnergyStorage()

        self.policyMaker.elecGenCompanies = elecGenCompanies #add record of the generation companies to the Policy Maker object
        Utils.initBuildRate(self.gen_tech_list, self.buildRatePerType, technology_technical_df) # Initialise the building rate for all the companies and technologies on year 0
        self.policyMaker.buildRatePerType = self.buildRatePerType

        return True

    def addDistributedGeneration(self):

        busbarConstraints = self.params["busbar_constraints"]
        tech_df = self.params["technical_parameters"]

        # --------- Add generation from smaller distributed generation -------------
        distributed_technologies = list(tech_df.loc[tech_df['DER_Capacity_Installed_'+str(self.BASEYEAR)+'_MW'] > 0, :].index)

        self.numberCustomers
        for gen_name in distributed_technologies:
            baseyear_installed_capacity = tech_df.loc[gen_name, 'DER_Capacity_Installed_'+str(self.BASEYEAR)+'_MW']
            capacity_remaining = (baseyear_installed_capacity - self.capacityInstalledMW[gen_name])*1000.0
            lifetime = int(tech_df.loc[gen_name, 'Lifetime_Years'])
            eligible_busbars = list(busbarConstraints[busbarConstraints[gen_name]>0].index)
            avg_start_year = self.BASEYEAR - lifetime/2
            avg_end_year = avg_start_year + lifetime
            capacity_market_sub = 0
            CfD_price = 0
            for busbar in eligible_busbars:
                capacit_to_install = capacity_remaining/len(eligible_busbars)
                self.distributedGenCompany.add_unit(gen_name, capacit_to_install, avg_start_year, avg_end_year, capacity_market_sub, CfD_price, busbar)
        return True


    def initTechPortoflio(self):
        ## init the technologies that can be built by each company based on their current portfolio
        technologyFamilies = self.params["technology_families"]
        
        for eGC in self.elecGenCompanies:
            tempListTechnology = []
            installedTech = []
            for genName in eGC.list_technology_portfolio:
                installedTech.append(genName)
                sameFamilyTechnologies = list(technologyFamilies[technologyFamilies[genName]>0].index)
                sameFamilyTechnologies = [x for x in sameFamilyTechnologies if x in self.gen_tech_list]

                tempListTechnology = tempListTechnology + sameFamilyTechnologies
            eGC.list_technology_portfolio = list(set(tempListTechnology))
            print("list technologies")
            print(eGC.name, eGC.list_technology_portfolio)
            print(set(installedTech))
        return True

    def get_capacity_installed(self):
        # Get the capacity installed for each technology type, by companies, and by bus
        frames_gen_cap = []
        frames_storage_cap = []

        for eGC in self.elecGenCompanies: #all companies have been added at the beginning
            eGC.calculateCapacityByType(self.gen_tech_list, self.storage_tech_list, [eC.busbar for eC in self.energyCustomers])
            self.gen_cap_per_companies.loc[eGC.name, :] = eGC.gen_cap_per_type_per_bus.sum().values
            self.storage_cap_per_companies.loc[eGC.name, :] =  eGC.storage_cap_per_type_per_bus.sum().values
            frames_gen_cap.append(eGC.gen_cap_per_type_per_bus.reset_index())
            frames_storage_cap.append(eGC.storage_cap_per_type_per_bus.reset_index())

        self.gen_cap_per_type_per_bus = pd.concat(frames_gen_cap).groupby("Busbars").sum()
        self.storage_cap_per_type_per_bus = pd.concat(frames_storage_cap).groupby("Busbars").sum()
        return True


    def getCustomerElectricityDemand(self):
        
        for eC in self.energyCustomers:
            curCustNL = eC.run_sim() # sim energy consumption each hour
            self.customerNLs[eC.busbar] = curCustNL

        #------------- get total customer electricity demand -------------
        totalCustDemand = np.array(self.customerNLs.sum(axis=1).values)
        self.hourlyNetDemand = totalCustDemand
        self.summaryEnergyDispatch['TotalCustomerCons'] = self.hourlyNetDemand.copy()
        self.peak_demand = np.max(totalCustDemand)
        return True


    def dispatchRenewables(self):
        netDemand = self.hourlyNetDemand.copy()
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
        self.hourlyCurtail  = hourlyCurtail.clip(min=0) #x<0 when demand>generation
        self.hourlyNetDemand = netDemand.clip(min=0)
        
        self.summaryEnergyDispatch['TotalCustomerConsAfterRGen'] = self.hourlyNetDemand.copy()
        print("End of dispatchRenewables")
        return True

    def dispatchTradGen(self, dispatchBeforeStorage):
        netDemand = self.hourlyNetDemand.copy()
        hourlyCurtail = self.hourlyCurtail.copy()
        dfTech = self.params["technical_parameters"]
        if dispatchBeforeStorage:
            tradGen = dfTech.loc[(dfTech['Dispatch_Before_Storage']==dispatchBeforeStorage) & (dfTech['Renewable_Flag']==0) & (dfTech['Storage_Flag']==0), :].copy()
        else:
            tradGen = dfTech.loc[self.merit_order, :].copy()
        temp_cols = [x+'_Derated_Capacity_kW' for x in self.gen_tech_list] + [x+'_Capacity_kW' for x in self.gen_tech_list]
        tempNetD = netDemand.copy()
        capacityPerType = self.gen_cap_per_type_per_bus[temp_cols].sum()
        print('Dispatch of {0}'.format(list(tradGen.index)))
        tempNetD, tempHourlyCurtail = Utils.dispatchTradGen(netDemand, self.elecGenCompanies, tradGen,capacityPerType, self.gen_cap_per_companies, self.allGenPerTechnology,self.allGenPerCompany, self.year)
        self.hourlyCurtail  = np.add(hourlyCurtail,tempHourlyCurtail)
        self.hourlyNetDemand = tempNetD

        if dispatchBeforeStorage:
            self.summaryEnergyDispatch['TotalCustomerConsAfterTGen1'] = self.hourlyNetDemand.copy()
        else:
            self.summaryEnergyDispatch['TotalCustomerConsAfterTGen2'] = self.hourlyNetDemand.copy()
            self.summaryEnergyDispatch['Curtailement'] = self.hourlyCurtail
            self.summaryEnergyDispatch['Loss of load'] = self.hourlyNetDemand
        return True

    def dispatchBatteries(self):
        netDemand = self.hourlyNetDemand.copy()
        if self.boolEnergyStorage:
            print('Charging/Discharging of batteries {0}...'.format(self.storage_tech_list))

            tNetDemand = netDemand.copy()
            for battery_cat in self.storage_tech_list:
                installed_capacity = self.storage_cap_per_type_per_bus[battery_cat+'_Capacity_kWh'].sum()
                print("Dispatch of {0} (capacity installed {1} MWh)".format(battery_cat, installed_capacity/1000))
                for eGC in self.elecGenCompanies:
                    tNetDemand = eGC.chargeDischargeBatteryTime(tNetDemand, battery_cat)

            netDemand = tNetDemand # final net demand after account for all companies
            self.summaryEnergyDispatch['TotalCustomerConsAfterBattery'] = netDemand
        return True


    def getWholeSalePrice(self):
        # calculating wholesale electricity price from marginal cost of each generator
        wholesaleEPrice = np.zeros(8760) # init at 0
        nuclearMarginalCost = list()
        for eGC in self.elecGenCompanies:
            for gen in eGC.renewable_gen + eGC.traditional_gen:
                gen.calculateHourlyData()
                if len(gen.marginal_cost) > 0:
                    wholesaleEPrice = np.max([wholesaleEPrice, gen.marginal_cost], axis=0)

                if gen.name == 'Nuclear':
                    nuclearMarginalCost = gen.marginal_cost.copy()

        for k in range(len(wholesaleEPrice)): #8760
            if self.hourlyCurtail[k] > 0:
                wholesaleEPrice[k] = 0 - nuclearMarginalCost[k]
        return wholesaleEPrice


    def getEmissions(self, wholesaleEPrice):
        # update economics of all plants and batteries and calculate the emissions
        # update the current wholesaleEPrice to calculate the profit made by each plant 
        yearlyEmissions = 0.0
        for eGC in self.elecGenCompanies:
            eGC.calc_revenue(wholesaleEPrice) #return the ROI and NPV of all the plants owned by this generator company
            yearlyEmissions += eGC.calcEmissions() #kgCO2
        return yearlyEmissions


    def exportPlantsEconomics(self):
        # generation plants economics
        npv_dict = {}
        
        for eGC in self.elecGenCompanies:
            for i,gen in enumerate(eGC.renewable_gen+eGC.traditional_gen):
                gbp_kwh = 0
                if gen.yearly_energy_generated > 0:
                    gbp_kwh = gen.yearly_income/gen.yearly_energy_generated
                npv_dict[(eGC.name, gen.name, str(i))] = [gen.cost_of_generating_electricity, gen.yearly_income, gen.yearly_cost, gen.NPV, gen.ROI, gen.getActCapFactor(), gbp_kwh, gen.capacity_market_sub, gen.CfD_price, gen.TNUoS_charge*gen.capacity*gen.availability_factor/8760, gen.capacity*gen.availability_factor, gen.busbar, gen.yearly_energy_generated]
        fileOut = self.params["path_save"] + 'gen_plants_economics_'+str(self.year)+'.csv'        
        plants_ecomomics_df = pd.DataFrame(npv_dict, index=["Cost_of_Electricity_GBP/kWh", "Income_GBP", "Cost_GBP", "NPV_GBP", "ROI", "Capacity_Factor", "Income_GBP/kWh", "Capital_Subsidy_GBP/kW", "CfD_Subsidy_GBP/kWh", "TNUoS_charges_GBP/h", "Derated_capacity_kW", "Busbar", "Electricity_generated_kWh"])
        plants_ecomomics_df.to_csv(fileOut)

        # Update the merit order of the system
        fileOut = self.params["path_save"] + 'Merit_Order_'+str(self.year)+'.csv'   
        merit_order_df = plants_ecomomics_df.T.groupby(level=[1]).mean()["Cost_of_Electricity_GBP/kWh"].to_frame()
        merit_order_df.sort_values(["Cost_of_Electricity_GBP/kWh"], ascending=True, inplace=True)
        self.merit_order = [x for x in merit_order_df.index if x in self.merit_order]

        # storage plants economics
        npv_dict = {}
        for eGC in self.elecGenCompanies:
            for i, st in enumerate(eGC.energy_stores):

                if st.yearly_energy_stored > 0:
                    gbp_kwh = st.yearly_income/st.yearly_energy_stored
                npv_dict[(eGC.name, st.name, str(i))] = [st.yearly_income, st.yearly_cost, st.NPV, st.ROI, st.getActCapFactor(), gbp_kwh, st.capacity_market_sub, st.CfD_price, st.busbar]
        fileOut = self.params["path_save"] + 'storage_plants_economics_'+str(self.year)+'.csv'        
        plants_ecomomics_df = pd.DataFrame(npv_dict, index=["Income_GBP", "Cost_GBP", "NPV_GBP", "ROI", "Capacity_Factor", "Income_GBP/kWh", "Capital_Subsidy_GBP/kW", "CfD_Subsidy_GBP/kWh", "Busbar"])
        plants_ecomomics_df.to_csv(fileOut)

        return True


    def installNewCapacity(self, wholesaleEPrice):
        #sort the busbars based on TNUoS charges from smaller to higher
        sorted_TNUoS_charges = self.TNUoS_charges.sort_values("TNUoS_charges_GBP/kW", axis=1).copy()

        # Capacity built by each company individually without the help of subsidies
        print("Companies investments...")
        frames = []
        for eGC in self.elecGenCompanies:
            temp_df = eGC.nextInvestment(sorted_TNUoS_charges)
            frames.append(temp_df)

        fileOut = self.params["path_save"] + 'Profitable_tech_to_be_built_'+str(self.year)+'.csv'
        newCapacity = pd.concat(frames, axis=0) #Capacity that companies want to build
        newCapacity = self.policyMaker.capBuildRate(newCapacity, "ROI", False) #Capacity that will be built after removing capped technology
        if len(newCapacity)>0:
            newCapacity.to_csv(fileOut)
            for unit_name, row in newCapacity.iterrows():
                eGCName = row["generation_company"]
                eGC = Utils.getGenerationCompany(eGCName, self.elecGenCompanies)
                capacitykW = row["capacity_kW"]
                start_year = row["start_year"]
                end_year = row["end_year"]
                capacity_market_sub = 0
                CfD_price = 0
                busbar = row["busbar"]
                #["name", "capacity_kW", "start_year", "end_year", "capacity_market_sub_GBP/kW", "CfD_price_GBP/kWh", "busbar"]
                eGC.addToConstructionQueue(unit_name, capacitykW, start_year, end_year, capacity_market_sub, CfD_price, busbar)

        # cfd auction
        self.policyMaker.cfdAuction(3, 6000000, 20, sorted_TNUoS_charges, np.mean(wholesaleEPrice)) # 3 years, 6 GW to be commissioned, max 20 years construction time

        # Capacity auction
        estPeakD, estDeRCap = self.policyMaker.capacityAuction(4, sorted_TNUoS_charges)

        return estPeakD, estDeRCap


    def increment_year(self, carbonIntensity):
        self.policyMaker.increment_year()
        # update CO2 Price for next year
        newCO2Price = self.policyMaker.getNextYearCO2Price(carbonIntensity) #carbon intensity in gCO2/kWh input

        # Update CO2 Price and check the construction queue to build plants
        for eGC in self.elecGenCompanies:
            eGC.increment_year(newCO2Price)

        # demand elasticity
        for eC in self.energyCustomers:
            eC.increment_year() #

        self.initResultsVariables()
        self.year = self.year + 1

    def update_TNUoS_charges(self):
        total_TNUoS = 375000000 # In 2020, 70 GW generation assets in total paid £375m
        derated_cap_cols = [x+'_Derated_Capacity_kW' for x in self.gen_tech_list]

        for eC in self.energyCustomers:
            busbar = eC.busbar
            peak_demand = np.max(eC.load_profile)
            
            derated_cap = self.gen_cap_per_type_per_bus.loc[busbar, derated_cap_cols].to_numpy().sum()
            derated_cap_margin = (derated_cap-peak_demand)/peak_demand
            # print(f"busbar {busbar} has a peak demand of {peak_demand} and deratedcapacity margin {derated_cap_margin}")
            self.TNUoS_charges.loc["Peak_demand_kW", busbar] = peak_demand
            self.TNUoS_charges.loc["Derated_capacity_margin_perc", busbar] = derated_cap_margin
            self.TNUoS_charges.loc["Derated_capacity_kW", busbar] = derated_cap
        min_derated_cap_margin = self.TNUoS_charges.loc["Derated_capacity_margin_perc", :].min()

        self.TNUoS_charges.loc["Headroom_kW", :] = self.TNUoS_charges.loc["Derated_capacity_kW", :] - self.TNUoS_charges.loc["Peak_demand_kW", :]

        self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :] = self.TNUoS_charges.loc["Derated_capacity_margin_perc", :]-min_derated_cap_margin
        # self.TNUoS_charges.loc["Percentage of the charge", :] = self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :]/self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :].to_numpy().sum()
        self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :] = self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :]/self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :].to_numpy().sum()*total_TNUoS
        self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :] = self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", :]/self.TNUoS_charges.loc["Derated_capacity_kW", :]
        fileOut = self.params["path_save"] + 'TNUOS_charges_'+str(self.year)+'.csv'
        self.TNUoS_charges.to_csv(fileOut)

        for eGC in self.elecGenCompanies:
            for gen in eGC.renewable_gen+eGC.traditional_gen:
                gen_busbar = gen.busbar
                gen.TNUoS_charge = self.TNUoS_charges.loc["TNUoS_charges_GBP/kW", gen_busbar]

        return True



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
    gen_tech_list = list(technology_technical_df.index)
    


    list_tgen = list(technology_technical_df.loc[technology_technical_df['Renewable_Flag']==0, :].index)
    list_rgen = list(technology_technical_df.loc[technology_technical_df['Renewable_Flag']==1, :].index)

    temp_cols = [x+'_Derated_Capacity_kW' for x in gen_tech_list] + [x+'_Capacity_kW' for x in gen_tech_list]

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
        print(eGC.list_technology_portfolio)