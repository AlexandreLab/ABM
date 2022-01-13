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
        return x

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



def updateCurYearCapInvest(technologies, curYearCapInvest):
    TECHFILENAME = 'GEN_TYPE_LIST.txt'
    CAPINVESTFILENAME = 'CUR_YEAR_GEN_CAP_INVEST_LIST.txt'
     
    if os.path.isfile(CAPINVESTFILENAME): # already investment in capacity this year      
        file2 = open(CAPINVESTFILENAME, "r") 
        totCurYearCapInvest = file2.read().split('\n')
        file2.close()
        totCurYearCapInvest.pop()

        file2 = open(TECHFILENAME, "r") 
        technologyList = file2.read().split('\n')
        file2.close()
        technologyList.pop()

        for i in range(len(technologies)):
            indx = technologyList.index(technologies[i])
            if (len(totCurYearCapInvest)>0 and len(curYearCapInvest)>0):
                temp = float(totCurYearCapInvest[indx]) + float(curYearCapInvest[i])
                totCurYearCapInvest[indx] = temp

            
            

        # delete old file so we can update with new one
        try:
            os.remove(CAPINVESTFILENAME)
        except OSError as e:  ## if failed, report it back to the user ##
            print ("Error: %s - %s." % (e.filename, e.strerror))

        # writing new total capacity to file
        file = open(CAPINVESTFILENAME, "w")
        for i in range(len(totCurYearCapInvest)):
            temp = str(totCurYearCapInvest[i])+'\n'
            file.write(temp)
        file.close()
        
        
    else: # no investment yet
        totCurYearCapInvest = curYearCapInvest
        technologyList = technologies

        file = open(CAPINVESTFILENAME, "w")
        for i in range(len(totCurYearCapInvest)):
            temp = str(totCurYearCapInvest[i])+'\n'
            file.write(temp)
        file.close()



def resetCurYearCapInvest():
    CAPINVESTFILENAME = 'CUR_YEAR_GEN_CAP_INVEST_LIST.txt'

    try:
        os.remove(CAPINVESTFILENAME)
    except OSError as e:  ## if failed, report it back to the user ##
        print ("Error: %s - %s." % (e.filename, e.strerror))



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


def getCurYearCapInvest():
    TECHFILENAME = 'GEN_TYPE_LIST.txt'
    CAPINVESTFILENAME = 'CUR_YEAR_GEN_CAP_INVEST_LIST.txt'
    
    if os.path.isfile(CAPINVESTFILENAME): # already investment in capacity this year      
        file2 = open(CAPINVESTFILENAME, "r") 
        totCurYearCapInvest = file2.read().split('\n')
        file2.close()
        totCurYearCapInvest.pop()

        file2 = open(TECHFILENAME, "r") 
        technologyList = file2.read().split('\n')
        file2.close()
        technologyList.pop()

        return technologyList, totCurYearCapInvest

    else:
        file2 = open(TECHFILENAME, "r") 
        technologyList = file2.read().split('\n')
        file2.close()
        technologyList.pop()

        totCurYearCapInvest = list()

        for i in range(len(technologyList)):
            totCurYearCapInvest.append(0.0)

        return technologyList, totCurYearCapInvest


def getWholesaleEPrice(elecGenCompanies):

    # tech = list()
    # margeC = list()
    wholesaleEPrice = list()
    nuclearMarginalCost = list()
    for eGC in elecGenCompanies:
        for renGen in eGC.renewableGen:
            if len(renGen.marginalCost)>0:
                mCost = renGen.marginalCost
                if(len(wholesaleEPrice)==0):
                    wholesaleEPrice = mCost.copy()
                else:
                    for p in range(len(wholesaleEPrice)):
                        if(mCost[p]>wholesaleEPrice[p]):
                            wholesaleEPrice[p] = mCost[p]

            # if not (renGen.name in tech) and (renGen.genCapacity>10):
            #     tech.append(renGen.name)
            #     margeC.append(renGen.marginalCost)
                            
        for tradGen in eGC.traditionalGen:
            if tradGen.name =='Nuclear' and len(nuclearMarginalCost)==0 and tradGen.genCapacity>10:
                nuclearMarginalCost = tradGen.marginalCost.copy()
            if len(tradGen.marginalCost)>0:
                mCost = tradGen.marginalCost
                if(len(wholesaleEPrice)==0):
                    wholesaleEPrice = mCost.copy()
                else:
                    for p in range(len(wholesaleEPrice)):
                        if(mCost[p]>wholesaleEPrice[p]):
                            wholesaleEPrice[p] = mCost[p]
            # if not (tradGen.name in tech) and (tradGen.genCapacity>10):
            #     tech.append(tradGen.name)
            #     margeC.append(tradGen.marginalCost)
                
    
    return wholesaleEPrice, nuclearMarginalCost




























































    
