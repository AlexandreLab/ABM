import random
from random import randint

from collections import namedtuple
import numpy as np
import pandas as pd
import math
import Utils
import os


class policyMaker():
    
    def __init__(self, params, BASEYEAR):
        self.params = params
        self.BASEYEAR = BASEYEAR
        self.year= self.BASEYEAR
        self.path_save = params["path_save"]

        self.buildRatePerType = pd.DataFrame() #dataframe of the build rate per technology type per year

        carbonFilePath = 'CarbonPrice/carbonPrice'+str(self.BASEYEAR)+'_2050.txt'
        self.yearlyCarbonCost = Utils.loadTextFile(carbonFilePath)
        wholesaleElecFilePath = 'WholesaleEnergyPrices/ElectricityBaseLoad'+str(self.BASEYEAR)+'_2050_GBPPerkWh.txt'
        self.yearlyWholesalePrice = Utils.loadTextFile(wholesaleElecFilePath)
        self.curCO2Price = self.yearlyCarbonCost[0] #£/tCO2
        self.yearCO2IntensityTarget = 0 #gCO2/kWh 

        self.name = 'Government'
        self.updateCO2Target()

        self.elecGenCompanies = list()

    def updateCO2Target(self):
        # gCO2/kWh, 50-100 in https://www.current-news.co.uk/news/uk-powers-to-new-grid-carbon-intensity-low-of-just-32g-co2-kwh
        if self.year<2018:
            self.carbonIntensityTarget = 250
        elif self.year<=2035:
            CO2DecreaseFrac = (self.year - 2018)/(2035 - 2018)
            newCO2P = 250 * (1-CO2DecreaseFrac)
            self.carbonIntensityTarget = newCO2P
        else:
            self.carbonIntensityTarget = 0

    # update values for next year
    def increment_year(self):
        self.year = self.year + 1
        self.updateCO2Target()

    def getNextYearCO2Price(self, carbonIntensity):
        print('emissionsIntense from last year (gCO2/kWh)',carbonIntensity)
        print('yearCO2IntensityTarget (gCO2/kWh)',self.carbonIntensityTarget)
        BEISco2Price = self.yearlyCarbonCost[self.year-self.BASEYEAR]
        if carbonIntensity > self.carbonIntensityTarget:
            CO210PC = self.curCO2Price *1.1
            if CO210PC > BEISco2Price:
                self.curCO2Price = CO210PC
            else:
                self.curCO2Price = BEISco2Price
        else:
            curCO2 = self.curCO2Price
            if curCO2 > BEISco2Price:
                self.curCO2Price = curCO2
            else:
                self.curCO2Price = BEISco2Price
        
        return self.curCO2Price

    # estimate demand in a specific year
    def projectedPeakDemand(self, targetYear):
        
        FESYearlyPeak = Utils.loadTextFile('Generation/NationalGrid_FES_TwoDeg_PeakDemandChange.txt')
        y = targetYear-2010
        newPeakD = FESYearlyPeak[y]*1000000.0 #in kW
        return newPeakD
    
    # estimate capacity in a specific year
    def projectedCapacity(self, targetYear):
        totCap = 0.0
        for eGC in self.elecGenCompanies:
            totCap = totCap + eGC.getCapYear(targetYear,True) # true for derated capacity
        return totCap

    # Method to cap the build rate of technologies
    # if capacity excess the build rate, bids are randomly removed
    def capBuildRate(self, bids, bidColumn, ascending=True):
        frames = []
        for genName in bids.index.unique():

            temp_df = bids.loc[genName, :].copy()
            if not isinstance(temp_df, pd.DataFrame): #there is only one line so it is a Serie
                temp_df = temp_df.to_frame().T
            else:
                temp_df = temp_df.sample(frac=1) # shuffle the dataset
                temp_df.sort_values(bidColumn, ascending=ascending, inplace=True) 
            yearOfInstallation = temp_df["start_year"].mean()
            maxBuildingRate = int(self.buildRatePerType.loc[genName,yearOfInstallation])
            print("The build rate of {0} is {1} kW in {2}".format(genName, maxBuildingRate, yearOfInstallation))
            if maxBuildingRate>0:
                temp_df["cumulative_capacity_kW"] = temp_df["capacity_kW"].cumsum()
                temp_df = temp_df.loc[temp_df["cumulative_capacity_kW"]<=maxBuildingRate, :]
                capToBeInstalled = temp_df["capacity_kW"].sum()
                self.buildRatePerType.loc[genName,yearOfInstallation] = maxBuildingRate - capToBeInstalled
                frames.append(temp_df)
        if len(frames) > 0:
            newBids = pd.concat(frames)
        else:
            newBids = pd.DataFrame()
        return newBids

    # hold capacity auction
    def capacityAuction(self, timeHorizon, sorted_TNUoS_charges):
        print('---------------------- Capacity Auction Method ---------------------')
        demandYear = self.year+timeHorizon
        cap_subsidy = 0 #£/kW include cap of 75£/kW as per BRAIN paper for the bids
        scaleACS = 1.09 # The value of ACS accounts for a potential 9% increase in peak demand that could be experienced during a cold winter
        # Book: Ter-Gazarian, A.G., Energy Storage for Power Systems, Page 18
        estPeakD = (self.projectedPeakDemand(demandYear)* scaleACS)
        estDeRCap = self.projectedCapacity(demandYear)
        print(demandYear)
        print('Estimated Peak Demand ', estPeakD)
        print('Estimated Derated Capacity ', estDeRCap)
        
        if estPeakD > estDeRCap:
            print('---------------------- Holding Capacity Auction ---------------------')
            capShortFall = estPeakD - estDeRCap

            framesBids =[]
            for eGC in self.elecGenCompanies:
                temp_dfBids = eGC.getCapAuctionBid(timeHorizon, sorted_TNUoS_charges)
                framesBids.append(temp_dfBids)
            allBids = pd.concat(framesBids)
            allBids.to_csv(self.path_save+"All_CapacityMarket_bids_"+str(self.year)+".csv")
            #removed based that do not comply with the building rate of plants
            allBids = self.capBuildRate(allBids, "bid_price_GBP/kW")
            if len(allBids) > 0:
                allBids.sort_values(["bid_price_GBP/kW"], ascending=True, inplace=True)
                allBids["cumulative_derated_capacity_kW"] = allBids["derated_capacity_kW"].cumsum()
                
                # Allocate cap subsidies until demand is met
                if cap_subsidy > 0:
                    allBids.loc[allBids["bid_price_GBP/kW"] > cap_subsidy, "bid_price_GBP/kW"] = cap_subsidy
                unsuccessfulBids = allBids.loc[allBids["cumulative_derated_capacity_kW"] > capShortFall, :].index
                successfulBids = allBids.loc[~allBids.index.isin(unsuccessfulBids), :]

                if len(successfulBids) > 0: #there are successful bids
                    successfulBids.to_csv(self.path_save+"Successful_CapacityMarket_Bids"+str(self.year)+".csv")
                    for genName, row in successfulBids.iterrows(): # Add eligible plants to the construction queue
                        eGCName = row["generation_company"]
                        capacitykW = row["capacity_kW"]
                        start_year = row["start_year"]
                        end_year = row["end_year"]
                        capacity_market_sub = row["bid_price_GBP/kW"]
                        CfD_price = 0
                        busbar = row["busbar"]
                        eGC = Utils.getGenerationCompany(eGCName, self.elecGenCompanies)
                        eGC.addToConstructionQueue(genName, capacitykW, start_year, end_year, capacity_market_sub, CfD_price, busbar)
        else:
            print(' ----------------- No capacity auction ----------------------')
        return estPeakD, estDeRCap


    # method to hold CfD auction
    def cfdAuction(self, capYears, commisCap, timeHorizon, sorted_TNUoS_charges, avgElectricityPrice):
        # check if commissioning year
        y = self.year - self.BASEYEAR
        allBids = pd.DataFrame()
        if y%capYears == 0: #capYears =3
            print('++++++++++++++++++ Holding CfD auction +++++++++++++++++++++++')
            print("year", y)
            frames = []
            for eGC in self.elecGenCompanies:
                # print(eGC.name)
                temp_bids_df = eGC.getCFDAuctionBid(timeHorizon, sorted_TNUoS_charges)
                frames.append(temp_bids_df)   
            if len(frames)>0:
                # Merge the bids together and select the accepted bids
                allBids = pd.concat(frames)
                allBids = allBids.loc[allBids["capacity_kW"]>0].copy()
                allBids = self.capBuildRate(allBids, 'strike_price_GBP/kWh')

                allBids.sort_values(by=['strike_price_GBP/kWh'], inplace=True)
                allBids.to_csv(self.path_save+"All_CfD_bids_"+str(self.year)+".csv")
                print("Average electricity price {0}".format(avgElectricityPrice))
                allBids = allBids.loc[allBids['strike_price_GBP/kWh']>avgElectricityPrice, :]
                allBids["cumulative_capacity_kW"] = allBids["capacity_kW"].cumsum()
                successfulBids = allBids.loc[allBids["cumulative_capacity_kW"]<=commisCap, :] #accepted bids

                if len(successfulBids) > 0:
                    successfulBids.to_csv(self.path_save+"Successful_CfD_bids_"+str(self.year)+".csv")

                    for genName, row in successfulBids.iterrows(): # Add eligible plant to the construction queue
                        eGCName = row["generation_company"]
                        capacitykW = row["capacity_kW"]
                        start_year = row["start_year"]
                        end_year = row["end_year"]
                        CfD_price = -(avgElectricityPrice-row['strike_price_GBP/kWh'])
                        capacity_market_sub = 0
                        busbar = row["busbar"]
                        eGC = Utils.getGenerationCompany(eGCName, self.elecGenCompanies)
                        eGC.addToConstructionQueue(genName, capacitykW, start_year, end_year, capacity_market_sub, CfD_price, busbar)
        else:
            print('++++++++++++++++++ No CfD auction +++++++++++++++++++++++')

        return True




    



if __name__ == '__main__': # to test some of the functions of the policy Maker
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

    buildRatePerType = pd.DataFrame(index= genTechList+['Battery'],columns=[2010+y for y in range(70)])
    buildRatePerType.fillna(2000000, inplace=True)

    # path to where you want results output to
    
    params["path_save"] =  'Results/2050/'
    params["path_wholesale_fuel_price"] = r'D:\OneDrive - Cardiff University\04 - Projects\18 - ABM\01 - Code\ABM code - Jan 2022 saved\Code_WH\WholesaleEnergyPrices'

    bids_test = pd.DataFrame(Utils.getBids1())
    bids_test.set_index('Unnamed: 0', inplace=True, drop=True)

    other_bids = pd.DataFrame(Utils.getBids2())
    other_bids.set_index('Unnamed: 0', inplace=True, drop=True) 

    buildRatedf = pd.DataFrame(Utils.getBuildRate())
    buildRatedf.set_index('Unnamed: 0', inplace=True, drop=True) 

    policy = policyMaker(params, 2010)
    policy.buildRatePerType = buildRatePerType
    policy.year = 2036

    new_bids = policy.capBuildRate(bids_test, 'Bid_Price_GBP/kW')
    print(policy.buildRatePerType.loc[:, 2036:2045])
    print(len(new_bids))

    new_bids = policy.capBuildRate(other_bids, 'ROI', False)
    print(policy.buildRatePerType.loc[:, 2036:2045])
    print(len(new_bids))
    print(new_bids)











    







        
        
