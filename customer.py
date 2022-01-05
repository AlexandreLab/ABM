import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils


class customer():
    

    
    def __init__(self):

        self.initialise()
        


    def initialise(self):
        self.initializeParams()
        
        PVFilePath = 'PV/1Year.txt'
        LoadFilePath = 'Load/1YearAvgUKHome.txt'
        HeatFilePath = 'Heat/1YearSeasonal.txt'
        self.PVProfile = self.loadTextFile(PVFilePath)
        if(self.BASEYEAR==2018):
            self.LoadProfile = self.loadTextFile(LoadFilePath)
        elif(self.BASEYEAR==2010):
            tempList = self.loadTextFile(LoadFilePath)
            self.LoadProfile = Utils.scaleList(tempList,9.32)
        else:
            input('Baseyear not 2010 or 2018, do you want to continue with 2018 demand data?')
        householdChangePath = 'PopulationGrowthRates/PCIncreaseHouseholds'+str(self.BASEYEAR)+'_2050.txt'
        self.housePCChange = Utils.loadTextFile(householdChangePath)
        
            
        self.HeatLoadProfile = self.loadTextFile(HeatFilePath)
        self.netLoad = self.LoadProfile.copy()
        self.elecCost = self.LoadProfile.copy() # GBP
        self.batteryProfile = self.LoadProfile.copy()
        self.timeSteps = len(self.LoadProfile) # full year
        self.curBatteryCap = 0
        self.batteryProfile[0] = 0
        self.totalNLDemand = 0.0
        self.totalElecCost = 0.0
        self.name = 'Customer'
        self.loadPrice()

   
    def initializeParams(self):
        file2 = open("BASEYEAR.txt", "r") 
        temp = file2.read()
        self.BASEYEAR = int(temp)
        file2.close()
        self.maxTemp = 60
        self.resolution = 60 #minutes
        self.PVInstalled = True
        self.batteryInstalled = False
        self.BatterySize = 10 # kWh
        self.batteryChargeRate = 3 #kW
        self.batteryDischargeRate = 3 #kW
        self.EVBatterySize = 0
        self.thermalStoreSize = 0
        self.year = self.BASEYEAR
        self.priceElasticityCoeff = -0.3
        self.FESYearlyPeak = self.loadTextFile('Generation/NationalGrid_FES_TwoDeg_PeakDemandChange.txt')
        self.FESYearlyTotal = self.loadTextFile('Generation/NationalGrid_FES_TwoDeg_TotalDemandChange.txt')

    # ignore
    def runLightSim(self):
        print('Loads\n')
        for i in range(len(self.LoadProfile)):
            self.netLoad[i] = self.LoadProfile[i] - self.PVProfile[i]

        self.displayAll()

    # loops through each hour
    def runSim(self):
        for i in range(self.timeSteps):
            self.step(i)
        return self.netLoad,self.HeatLoadProfile

    # simulates each hour 
    def step(self,time): # environment goes to next time step
        L = self.LoadProfile[time]
        Pv = self.PVProfile[time]
        bat_c = self.curBatteryCap
        self.batteryProfile[time] = self.curBatteryCap
        if(self.batteryInstalled):
            #Discharge
            if(L>Pv and bat_c>0): # have energy in battery and need power
                bat_o = L-Pv
                if(bat_o>self.batteryDischargeRate):
                    bat_o = self.batteryDischargeRate
                if(bat_c-bat_o<0):
                    bat_o = bat_c
                    
                self.curBatteryCap = self.curBatteryCap - bat_o
                self.netLoad[time] = self.LoadProfile[time] - bat_o - self.PVProfile[time]
            #Charge
            elif(L<Pv and bat_c<self.BatterySize):
                charge = Pv-L
                if(charge>self.batteryChargeRate):
                    charge = self.batteryChargeRate
                if(charge+bat_c>self.BatterySize):
                    charge = self.BatterySize-bat_c
                    
                self.curBatteryCap = self.curBatteryCap + charge
                self.netLoad[time] = self.LoadProfile[time] + charge - self.PVProfile[time]

            else:
                self.netLoad[time] = self.LoadProfile[time] - self.PVProfile[time]
        else:
            self.netLoad[time] = self.LoadProfile[time] - self.PVProfile[time]
        self.elecCost[time] = self.netLoad[time]*self.curElecPrice
        self.totalElecCost = self.totalElecCost + self.elecCost[time]
        self.totalNLDemand = self.totalNLDemand + self.netLoad[time]



    def displaySimProgress(self,time):
        dayRemain = time%24
        day = time/24
        if(dayRemain==0 and day%50==0):
            print("Customer %s day %s" % (self.name, str(day)))

             
    def displayNow(self,time):
        print('Time ', time)
         
        print('Load ')
        print(self.LoadProfile[time],' ')

        print('PV')
        print(self.PVProfile[time],' ')

        print('NetLoad ')
        print(self.netLoad[time],' \n')

    def displayAll(self):
        print('Loads\n')
        for i in range(len(self.LoadProfile)):
            print(self.LoadProfile[i],' ')
        print('PV\n')
        for i in range(len(self.PVProfile)):
            print(self.PVProfile[i],' ')
        print('NetLoads\n')
        for i in range(len(self.netLoad)):
            print(self.netLoad[i],' ')

    def loadPrice(self):
        FILEPATH = 'RetailElectricityPrices/ResidentialElectricityPrice'+str(self.BASEYEAR)+'_2050_GBPperkWh.txt'
        self.yearlyElecPrice = Utils.loadTextFile(FILEPATH)
        self.curElecPrice = self.yearlyElecPrice[0]

    # update values for next year (demand elasticity)
    def updateYear(self,priceChangePC,busbar): # reads in pc change in wholesale elec price, e.g. + 2% or -1%
        self.year = self.year + 1
        consumerPercList = [0.008,0.009,0.010,0.023,0.009,0.021,0.013,0.002,0.002,0.046,0.060,0.021,0.045,0.033,0.047, 0.029,0.019,0.095, 0.036,0.018,0.013,0.032,0.084,0.025,0.173,0.025,0.008,0.049, 0.023,0.023]
        y = self.year - self.BASEYEAR
        self.curElecPrice = self.yearlyElecPrice[y]
        self.curHousePCChange = self.housePCChange[y]
        e = self.priceElasticityCoeff
        demandChangePC = e*priceChangePC # demand change from price elasticity
        oldLoad = self.LoadProfile[0]

        actPeak = self.FESYearlyPeak[y]
        actTotal = self.FESYearlyTotal[y]
        scale = actPeak/self.peakDemand2018
        tempList = self.loadTextFile(self.LoadFilePath)
        self.LoadProfile = Utils.multiplyList(tempList,scale)
        
        for i in range(len(self.LoadProfile)):
            # demand change from price elasticity
            loadTemp = self.LoadProfile[i]
            self.LoadProfile[i] = loadTemp + loadTemp * (demandChangePC/100)
        consumerPerc = consumerPercList[(busbar)]
        self.LoadProfile = Utils.timeList(self.LoadProfile,consumerPerc)
        newLoad = self.LoadProfile[0]
        totalLoadPCChange = (newLoad - oldLoad)/(oldLoad)*100
        return totalLoadPCChange

    def normalizeVal(self,val, maxV, minV):
        nVal = float(val-minV)/float(maxV-minV)
        if(nVal<0 or nVal>1):
            print('max ',maxV)
            print('min ',minV)
            print('val ',val)
            print('nor ',nVal)
            input('wait')
        return nVal


    def loadTextFile(self,file):
        f = open(file, 'r')
        x = f.readlines()
        f.close()
        for i in range(len(x)):
            x[i]= float(x[i])
     #   print(x)
        return x


    def scaleList(self,myList,scale):
        for i in range (len(myList)):
            myList[i] = myList[i]*scale
        return myList


   # def lowerRes(self, dataList, curRes, desireRes):
    #    newData = list()
    #    dif = int(curRes/desireRes)-1
    #    print('Lowering Resolution')
        
    #    for i in range(len(dataList)):
    ##        if((i+dif)<len(dataList)):
     #           curP = dataList[i]
     #           nextP = dataList[i+1]
     ##           for j in range(dif+1):
     #               val = float(j)/float(dif+1)
     #print               gap = float(nextP-curP)
     #               nVal = val*gap+curP
      #              newData.append(nVal)
                    
      #  newData.append(dataList[len(dataList)-1])

      #  return newData
    

    def graph(self):
        import matplotlib.pyplot as plt

        graphLoad,loadUnit = Utils.checkUnits(self.LoadProfile)
        graphPV,PVUnit = Utils.checkUnits(self.PVProfile)
        graphHeat,HeatUnit = Utils.checkUnits(self.HeatLoadProfile)
        graphNLoad,nloadUnit = Utils.checkUnits(self.netLoad)
        graphBattery,batteryUnit = Utils.checkUnits(self.batteryProfile)
        
        fig, axs = plt.subplots(5,1)
        fig.suptitle(self.name, fontsize=20)
        axs[0].plot(graphLoad)
        axs[1].plot(graphPV)
        axs[2].plot(graphNLoad)
        axs[3].plot(graphHeat)
        axs[4].plot(graphBattery)
        axs[0].set_ylabel('Load ('+loadUnit+')')
        axs[1].set_ylabel('PV Generation ('+PVUnit+')')
        axs[2].set_ylabel('Net Load ('+nloadUnit+')')
        axs[3].set_ylabel('Heat Demand ('+HeatUnit+')')
        axs[4].set_ylabel('Battery Capacity ('+batteryUnit+'h)')
        fig.show()
    









        
        
