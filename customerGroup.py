import random
from random import randint
from collections import namedtuple
import numpy as np
import math
from customer import customer
import Utils

class customerGroup(customer):
    

    def __init__(self,busbar):
        self.initialise(busbar)
        
        
    def initialise(self, busbar):
        self.initializeParams()
        consumerPercList = [0.008,0.009,0.010,0.023,0.009,0.021,0.013,0.002,0.002,0.046,0.060,0.021,0.045,0.033,0.047, 0.029,0.019,0.095, 0.036,0.018,0.013,0.032,0.084,0.025,0.173,0.025,0.008,0.049, 0.023,0.023]
       # self.location = location
       # self.numCust = numCust
        LoadFilePath = 'Generation/TotalElectricityGeneration_hourly_2018_kWh.txt'
        self.LoadFilePath = LoadFilePath
        tempList = self.loadTextFile(LoadFilePath)
        curTot = sum(tempList)/1000000 # convert to GWh
        curPeak = max(tempList)/1000000 # convert to GW
        self.totDemand2018 = curTot
        self.peakDemand2018 = curPeak
        y = self.year - 2010
        actPeak = self.FESYearlyPeak[y]
        actTotal = self.FESYearlyTotal[y]  
        scale = actPeak/curPeak            
        scaledlist = Utils.multiplyList(tempList,scale)   
        consumerPerc = consumerPercList[(busbar-1)]
        self.LoadProfile = Utils.timeList(scaledlist,consumerPerc)
        self.busbar = busbar

        PVFilePath = 'PV/1Year.txt'
             

        HeatFilePath = 'Heat/1YearSeasonal.txt'
        householdChangePath = 'PopulationGrowthRates/PCIncreaseHouseholds'+str(self.BASEYEAR)+'_2050.txt'
        self.housePCChange = Utils.loadTextFile(householdChangePath)
        self.PVProfile = self.scaleList(self.loadTextFile(PVFilePath),0)     
        self.HeatLoadProfile = self.scaleList(self.loadTextFile(HeatFilePath),0)
        self.netLoad = self.LoadProfile.copy()
        self.elecCost = self.LoadProfile.copy() # GBP
        self.batteryProfile = self.LoadProfile.copy()
        self.timeSteps = len(self.LoadProfile)
        self.curBatteryCap = 0
        self.batteryProfile[0] = 0
        self.totalNLDemand = 0.0
        self.totalElecCost = 0.0
        #self.name = name
        self.loadPrice()



    


        
        
