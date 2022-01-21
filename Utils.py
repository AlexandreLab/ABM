import numpy as np
from csv import reader
import random
import pandas as pd
import os
import os.path
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as tkr
from random import randint
from timeit import default_timer as timer

GLOBAL_FIG_FORMAT = "png"
GLOBAL_DPI = 1000

#____________________________________________________________
#
# Class used to do various tasks, e.g. read txt files.
# These methods are all fairly self explanitory
#____________________________________________________________

# Normalize data
def normalize(X):
    # Find the min and max values for each column
    x_min = X.min(axis=0)
    x_max = X.max(axis=0)
    # Normalize
    for x in X:
        for j in range(X.shape[1]):
            x[j] = (x[j]-x_min[j])/(x_max[j]-x_min[j])

def random_pick(some_list, probabilities):
    x = random.uniform(0,1)
    cumulative_probability = 0.0
    for item, item_probability in zip(some_list, probabilities):
        cumulative_probability += item_probability
        if x < cumulative_probability:break
    return item

def scaleList(myList, PCChange):
    newList = list()
    for i in range(len(myList)):
        x = myList[i]
        newList.append(x + x*(PCChange/100.0))
    return newList

def timeList(myList, PCChange):
    newList = list()
    for i in range(len(myList)):
        x = myList[i]
        newList.append(x*PCChange)
    return newList


def multiplyList(myList, mult):
    newList = list()
    for i in range(len(myList)):
        x = myList[i]
        newList.append(x * mult)
    return newList
    

def loadTextFile(file):
        f = open(file, 'r')
        x = f.readlines()
        f.close()
        for i in range(len(x)):
            x[i]= float(x[i])
        return np.array(x)

def checkUnits(listOfVals):
    listCopy = listOfVals.copy()
    unit = 'kW'
    if(max(listCopy)<1000):
        unit = 'kW'
    elif(max(listCopy)<1000000):
        unit = 'MW'
        for i in range(len(listCopy)):
            listCopy[i] = listCopy[i]/1000.0
    elif(max(listCopy)<1000000000):
        unit = 'GW'
        for i in range(len(listCopy)):
            listCopy[i] = listCopy[i]/1000000.0
    else:
        unit = 'TW'
        for i in range(len(listCopy)):
            listCopy[i] = listCopy[i]/1000000000.0
    return listCopy, unit


def checkSingleValUnit(val):
    unit = 'kW'
    newVal = 0.0
    if(val<1000):
        unit = 'kW'
        newVal = 0.0
    elif(val<1000000):
        unit = 'MW'
        newVal = val/1000.0
    elif(val<1000000000):
        unit = 'GW'
        newVal = val/1000000.0
    else:
        unit = 'TW'
        newVal = val/1000000000.0
    return newVal, unit

#Return a string formatted to be used as a filename by removing special character
def getFormattedFileName(fn):
    fn = fn.replace(":", "_").replace(",", "_")
    return fn
        
    
def checkWeightUnits(listOfVals):
    listCopy = listOfVals.copy()
    unit = 'kg'
    if(max(listCopy)<1000):
        unit = 'kg'
    elif(max(listCopy)<1000000):
        unit = '10E3 kg'
        for i in range(len(listCopy)):
            listCopy[i] = listCopy[i]/1000.0
    elif(max(listCopy)<1000000000):
        unit = '10E6 kg'
        for i in range(len(listCopy)):
            listCopy[i] = listCopy[i]/1000000.0
    else:
        unit = '10E9 kg'
        for i in range(len(listCopy)):
            listCopy[i] = listCopy[i]/1000000000.0
    return listCopy, unit




def loadFuelCostFile(genName, FILEPATH):
    fileIN = np.array(loadTextFile(FILEPATH))
    
    if(genName=="Coal"): # coal
        fileIN = fileIN/1000 # tonnes to kg
        fileIN = fileIN/2.46 # 1 kg of coal produces 2.46 kWh
        fileIN = fileIN*0.77 # USD to GBP
    elif(genName=="CCGT" or genName=="OCGT"): # CCGT and OCGT
        fileIN = fileIN/100.0 # p/ therm to gbp/therm
        fileIN = fileIN/29.31 # therms to kWh, 1 therm = 29.31 kWh
    elif(genName=="Nuclear"): # Nuclear
        fileIN = fileIN/100.0 # p/ kWh to gbp/kWh
    #else self.name=="BECCS" or self.name == "Biomass"):
    #noChange 
    return fileIN




def writeListsToCSV(profiles,profNames,FILEPATH):

    # print(profiles)
    # print(profNames)
#    print('profNames[0] ',profNames[0])
 #   print('profiles[0] ',profiles[0])

    if len(profNames)>0:

        df = pd.DataFrame({profNames[0]: profiles[0]})
        for i in range(1,len(profiles)):
    #      print('profNames[i] ',profNames[i])
    #      print('profiles[i] ',profiles[i])
            dat2 = pd.DataFrame({profNames[i]: profiles[i]})
            df = pd.concat([df, dat2], axis=1)

        df.to_csv(FILEPATH)




def writeToCSV(profiles,profNames,FILEPATH):
    df = pd.DataFrame({profNames[0]:profiles[0]})
    for i in range(1,len(profiles)):
        df[profNames[i]] = profiles[i]
    df.to_csv(FILEPATH)


def readCSV(FILEPATH):
    contents = pd.read_csv(FILEPATH)
    return contents


def sumVals(listOfVals):
    sumV=0.0
    for i in range(len(listOfVals)):
        sumV = sumV + listOfVals[i]
    return sumV 


def randomOrderListIndx(myList):

    randomIndx = list()
    while(len(randomIndx)<len(myList)):
        rI = randint(0,len(myList)-1)
        if(not(rI in randomIndx)):
            randomIndx.append(rI)
    return randomIndx




def getPathWholesalePriceOfFuel(path, fuel, year):
    for subdir, dirs, files in os.walk(path):
        for file in files:
#             print(file)
            if str(year) in file and fuel in file:
                print(file)
                return subdir + os.sep + file
    return False



def addToCapGenList(genTypeName, curCap, curCapList, technologyList):

    newCapList = curCapList.copy()

    if(len(newCapList)==0):
        for i in range(len(technologyList)):
            if(genTypeName==technologyList[i]):
                newCapList.append(curCap)
            else:
                newCapList.append(0.0)
    else:
        indx = technologyList.index(genTypeName)
        newCapList[indx] += curCap

    return newCapList



def getWholesaleEPrice(elecGenCompanies):
    wholesaleEPrice = np.zeros(8760) # init at 0
    nuclearMarginalCost = list()
    for eGC in elecGenCompanies:
        for gen in eGC.renewableGen + eGC.traditionalGen:
            gen.calculateHourlyData()
            if len(gen.marginalCost)>0:
                wholesaleEPrice = np.max([wholesaleEPrice, gen.marginalCost], axis=0)

            if gen.name =='Nuclear':
                nuclearMarginalCost = gen.marginalCost.copy()

    return wholesaleEPrice, nuclearMarginalCost




























































    
