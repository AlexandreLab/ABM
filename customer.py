import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils


class customer():
    def __init__(self, timesteps, BASEYEAR, busbar=0):
        self.timeSteps = timesteps
        self.busbar = 0
        self.year = BASEYEAR
        self.BASEYEAR = BASEYEAR

        self.LoadFilePath = 'Generation/TotalElectricityGeneration_hourly_2018_kWh.txt'

        self.FESYearlyPeak = Utils.loadTextFile('Generation/NationalGrid_FES_TwoDeg_PeakDemandChange.txt')
        self.FESYearlyTotal = Utils.loadTextFile('Generation/NationalGrid_FES_TwoDeg_TotalDemandChange.txt')
        self.consumerPercList = [1] 

        self.BASEYEARLoadProfile = self.getLoadProfile()*self.consumerPercList[(self.busbar-1)]
        self.loadProfile = np.zeros(timesteps)
        self.name = 'Customer '+str(self.busbar)


    def getLoadProfile(self):
        if(self.BASEYEAR==2018):
            loadProfile = Utils.loadTextFile(self.LoadFilePath)
        elif(self.BASEYEAR==2010):
            tempList = Utils.loadTextFile(self.LoadFilePath)
            loadProfile = tempList *(1+9.32)
        else:
            input('Baseyear not 2010 or 2018, do you want to continue with 2018 demand data?')
        return loadProfile

    # loops through each hour
    def runSim(self):
        netLoad = self.loadProfile
        return netLoad

    def loadPrice(self):
        FILEPATH = 'RetailElectricityPrices/ResidentialElectricityPrice'+str(self.BASEYEAR)+'_2050_GBPperkWh.txt'
        self.yearlyElecPrice = Utils.loadTextFile(FILEPATH)
        self.curElecPrice = self.yearlyElecPrice[0]

    def updateLoadProfile(self):
        y = self.year - self.BASEYEAR
        orgPeak = np.max(self.BASEYEARLoadProfile)/1000000 #peak in GW
        currentPeak = self.FESYearlyPeak[y]*self.consumerPercList[(self.busbar-1)]
        self.loadProfile = self.BASEYEARLoadProfile*currentPeak/orgPeak


    # update values for next year (demand elasticity)
    def updateYear(self,priceChangePC): # reads in pc change in wholesale elec price, e.g. + 2% or -1%
        self.year = self.year + 1
        self.updateLoadProfile()



















        
        
