import numpy as np
from csv import reader
import random
import pandas as pd
import os
import os.path
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as tkr

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

def graphMultSeriesOnePlot(profiles, xLabel, yLabel, title, legendNames, path_save):

    fig = plt.figure()
    fig.suptitle(title)
    ax1 = fig.add_subplot(111)
    for i in range(len(profiles)):
        newProf, unit = checkUnits(profiles[i])
        ax1.plot(newProf)
    ax1.set_ylabel(unit)
    ax1.set_xlabel(xLabel)
    ax1.legend(legendNames, loc='upper left')
    # fig.show()
    fig.savefig(path_save+os.path.sep+title+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()


def graphMultSeriesOnePlotV2(profiles, xLabel, yLabel, title, legendNames, yVals, path_save):

    fig = plt.figure()
    fig.suptitle(title)
    ax1 = fig.add_subplot(111)
    for i in range(len(profiles)):
        newProf, unit = checkUnits(profiles[i])
        ax1.plot(yVals, profiles[i])
    ax1.set_ylabel(yLabel)
    ax1.set_xlabel(xLabel)
    
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width , box.height* 0.8])
    ax1.legend(legendNames, loc='center left', bbox_to_anchor=(-0.2, 1.23),ncol=5)
    # fig.show()
    fig.savefig(path_save+os.path.sep+getFormattedFileName(title)+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()


def graphMultSeriesOnePlotV3(profiles, xLabel, yLabel, title, legendNames, path_save):

    fig = plt.figure()
    fig.suptitle(title)
    ax1 = fig.add_subplot(111)
    for i in range(len(profiles)):
        newProf, unit = checkUnits(profiles[i])
        ax1.plot(profiles[i])
    ax1.set_ylabel(yLabel)
    ax1.set_xlabel(xLabel)
  #  ax1.legend(legendNames, loc='upper left')
    ax1.legend(legendNames, loc=2, bbox_to_anchor=(1.05,1.0),borderaxespad = 0.)
 #   ax1.legend(legendNames, loc='upper center', bbox_to_anchor=(0.5, -0.08),
 #         fancybox=True, shadow=True, ncol=3)
    # fig.show()
    fig.savefig(path_save+os.path.sep+getFormattedFileName(title)+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()



def graph(profiles, xLabels, yLabels, title, subtitles, path_save):
    
    fig, axs = plt.subplots(len(profiles),1)
    fig.suptitle(title, fontsize=20)
    for i in range(len(profiles)):
        axs[i].plot(profiles[i])
        axs[i].set_ylabel(yLabels[i])
        if(i == len(profiles)-1):
            axs[i].set_xlabel(xLabels[i])
        axs[i].set_title(subtitles[i])
    # fig.show()
    
    fig.savefig(path_save+os.path.sep+getFormattedFileName(title)+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()

def singleGraph(profile, xLabel, yLabel, title, path_save):
    
    fig, axs = plt.subplots(2,1)
    fig.suptitle(title, fontsize=20)
    axs[0].plot(profile)
    axs[0].set_ylabel(yLabel)
    axs[0].set_xlabel(xLabel)
    # fig.show()
    fig.savefig(path_save+os.path.sep+getFormattedFileName(title)+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()


def pieChart(pieData, pieLabels, title, path_save):
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))
    
    dataLabels = pieLabels
    data = pieData

    dataPC = list()
    sumDataP = sum(data)
    for i in range(len(data)):
        valPC = (data[i]/sumDataP)*100
        dataPC.append(valPC)
        dataLabels[i] = dataLabels[i] + ': '+str(round(valPC, 2))+' %'

    wedges, texts = ax.pie(data, wedgeprops=dict(width=0.5), startangle=-40)

    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
          bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(dataLabels[i], xy=(x, y), xytext=(1.1*np.sign(x), 2.5*y),
                    horizontalalignment=horizontalalignment, **kw)

    ax.set_title(title)

  #  plt.show()
    # fig.show()
    fig.savefig(path_save+os.path.sep+getFormattedFileName(title)+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()
'''
def pieChart(pieData, pieLabels, title):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))
    
    dataLabels = pieLabels
    data = pieData

    dataPC = list()
    sumDataP = sum(data)
    for i in range(len(data)):
        valPC = (data[i]/sumDataP)*100
        dataPC.append(valPC)
        dataLabels[i] = str(round(valPC, 2))+' %'


    ax.pie(data,labels=pieLabels)
    ax.axis('equal')
    fig.show()
'''

def writeListsToCSV(profiles,profNames,FILEPATH):

    print(profiles)
    print(profNames)
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
    from random import randint
    randomIndx = list()
    while(len(randomIndx)<len(myList)):
        rI = randint(0,len(myList)-1)
        if(not(rI in randomIndx)):
            randomIndx.append(rI)
    return randomIndx


def barChart(myData, xLabels,name,yLabel, path_save):

    fig = plt.figure()
    fig.suptitle(name, fontsize=20)
    ax1 = fig.add_subplot(111)

    y_pos = np.arange(len(xLabels)) #1,2,3,4,5,...xLabels
    
 #   plt.bar(y_pos, myData, align='center', alpha=0.5)
    plt.bar(y_pos, myData, align='center', color = 'blue')
    plt.xticks(y_pos, xLabels, rotation=20)
    plt.ylabel(yLabel)
    # fig.show()
    fig.savefig(path_save+os.path.sep+getFormattedFileName(name)+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()




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

    tech = list()
    margeC = list()
    wholesaleEPrice = list()
    nuclearMarginalCost = list()
    for i in range(len(elecGenCompanies)):
        genCo = elecGenCompanies[i]
        for j in range(len(genCo.renewableGen)):
            if(len(genCo.renewableGen[j].marginalCost)>0):
                mCost = genCo.renewableGen[j].marginalCost
                if(len(wholesaleEPrice)==0):
                    wholesaleEPrice = mCost.copy()
                else:
                    for p in range(len(wholesaleEPrice)):
                        if(mCost[p]>wholesaleEPrice[p]):
                            wholesaleEPrice[p] = mCost[p]
            if(not (genCo.renewableGen[j].name in tech) and (genCo.renewableGen[j].genCapacity>10)):
                tech.append(genCo.renewableGen[j].name)
                margeC.append(genCo.renewableGen[j].marginalCost)
                            
        for j in range(len(genCo.traditionalGen)):
            if(genCo.traditionalGen[j].name=='Nuclear' and len(nuclearMarginalCost)==0 and (genCo.traditionalGen[j].genCapacity>10)):
                nuclearMarginalCost = genCo.traditionalGen[j].marginalCost.copy()
            if(len(genCo.traditionalGen[j].marginalCost)>0):
                mCost = genCo.traditionalGen[j].marginalCost
                if(len(wholesaleEPrice)==0):
                    wholesaleEPrice = mCost.copy()
                else:
                    for p in range(len(wholesaleEPrice)):
                        if(mCost[p]>wholesaleEPrice[p]):
                            wholesaleEPrice[p] = mCost[p]
            if(not (genCo.traditionalGen[j].name in tech) and (genCo.traditionalGen[j].genCapacity>10)):
                tech.append(genCo.traditionalGen[j].name)
                margeC.append(genCo.traditionalGen[j].marginalCost)
                

    
    return wholesaleEPrice, nuclearMarginalCost









# draw price change
def drawwholesale(years,yearlymaxwholesale,yearlyminwholesale,yearlyavgwholesale, path_save):
    fig = plt.figure()
    fig.suptitle('Yearly Wholesale Electricity Price', fontsize=20)
    ax1 = fig.add_subplot(111)
    yearlyavgwholesale = [i*1000 for i in yearlyavgwholesale]
    yearlyminwholesale = [i*1000 for i in yearlyminwholesale]
    yearlymaxwholesale = [i*1000 for i in yearlymaxwholesale]
    ax1.plot(years,yearlyavgwholesale)
    ax1.fill_between(x=years,y1=yearlyminwholesale,y2=yearlymaxwholesale,color='blue',alpha=0.25)
    
    ax1.set_ylabel('Wholesale Price (GBP/MWh)')
    
    from matplotlib.ticker import MaxNLocator
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.set_xlabel('Year')

    ax1.legend(['Average Wholesale Price', 'Price Range'], loc=2)
    # fig.show()
    fig.savefig(path_save+os.path.sep+"WholesaleElectricityPrice."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()


# method to plot yearly capacity of each technology
def graphYearlyCapacity(years, yearlyTotCap, yearlyDeRCap, yearlyPeakD, yearlyCapM, yearlyDeRCapM, path_save):
    

    fig, ax1 = plt.subplots()
    fig.suptitle('Annual Total Capacity Change', fontsize=20)

    ax2 = ax1.twinx()

    y = years # 1,2,3,4 append

    yearlyTotCap = [i/1000 for i in yearlyTotCap]
    yearlyDeRCap = [i/1000 for i in yearlyDeRCap]
    yearlyPeakD = [i/1000 for i in yearlyPeakD]
    yearlyCapM = [i for i in yearlyCapM]
    yearlyDeRCapM = [i for i in yearlyDeRCapM]

    ax1.plot(y,yearlyTotCap, label='TotalCapacity')
    ax1.plot(y,yearlyDeRCap, label='DeRatedCapacity')
    ax1.plot(y,yearlyPeakD, label='PeakDemand')
    ax2.plot(y,yearlyCapM, label='CapacityMargin')
    ax2.plot(y,yearlyDeRCapM, label='DeRatedCapacityMargin')
    ax1.set_ylabel('MW')

    ax1.get_yaxis().set_major_formatter(tkr.FuncFormatter(lambda x, p: '{:,.0f}'.format(x)))
    ax2.get_yaxis().set_major_formatter(tkr.FuncFormatter(lambda x, p: '{:,.0f}%'.format(x*100)))

    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.set_xlabel('Year')
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width , box.height* 0.8])
    handles, labels = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    ax2.grid(False)
    ax1.legend(handles=handles+handles2, labels=labels+labels2, loc='center left', bbox_to_anchor=(-0.1, 1.2),ncol=3)
    # fig.show()
    fig.savefig(path_save+os.path.sep+"AnnualCapacityChange."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()


# method to plot yearly capacity per bus per tech
def graphYearlyBus(years, yearlycaplist, buslist, techtype, path_save):    
    
    fig = plt.figure()
    fig.suptitle('Annual Capacity Change of '+techtype, fontsize=20)
    ax1 = fig.add_subplot(111)
    y = years # 1,2,3,4 append
    #given new added bus, add zero to previous position
    b = len(yearlycaplist[-1])
    for j in range(len(yearlycaplist)):
        c = len(yearlycaplist[j])
        yearlycaplist[j] = yearlycaplist[j] + [0]*(b-c)
    #transpose the dimension of bus and year
    a=np.array(yearlycaplist)
    a = a.transpose(1,0)*0.000001
    yearlycaplist = a.tolist()
    for i in range(len(buslist)):
        ax1.plot(y,yearlycaplist[i])
        ax1.set_ylabel('GW')
    from matplotlib.ticker import MaxNLocator
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.set_xlabel('Year')
    busname=['bus'+str(i) for i in buslist]
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width , box.height* 0.8])
    ax1.legend(busname,loc='center left', bbox_to_anchor=(-0.2, -0.5),ncol=6)
    # fig.show()    
    fig.savefig(path_save+os.path.sep+"AnnualCapacityYearlyBus"+techtype+"."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)

    fileOut = path_save + os.path.sep + techtype + '.csv'
    plt.close()

def drawdemand(years, yearlybusdemand, path_save):
    import matplotlib.pyplot as plt
    fig = plt.figure()
    buslist=list(range(1,31))
    fig.suptitle('Annual Demand Change for Busbar', fontsize=20)
    ax1 = fig.add_subplot(111)
    y = years # 1,2,3,4 append
    a=np.array(yearlybusdemand)
    a = a.transpose(1,0)*0.000001
    yearlybuslist = a.tolist()
    for i in range(len(buslist)):
        ax1.plot(y,yearlybuslist[i])
        ax1.set_ylabel('MWh')

    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.set_xlabel('Year')
    busname=['bus'+str(i) for i in buslist]
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width , box.height* 0.8])
    ax1.legend(busname, loc='center left', bbox_to_anchor=(-0.2, -0.5),ncol=6)
    # fig.show()
    fig.savefig(path_save+os.path.sep+"Demand."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()   
    


def graphheadroom(years, yearlyheadroom, path_save):


    for j in range(len(yearlyheadroom)):
        yearlyheadroom[j] = [i/1000 for i in yearlyheadroom[j]]

    headroomarray = np.array(yearlyheadroom)
    fig, ax = plt.subplots(figsize=(7,8))
    im = ax.imshow(headroomarray, aspect='auto')
    bus = list(range(1,31))
    y_axis =  [str(j) for j in years]
    x_axis =  [str(k) for k in bus]

    ax.set_xticks(np.arange(len(x_axis)))
    ax.set_yticks(np.arange(len(y_axis)))
    ax.set_xticklabels(x_axis)
    ax.set_yticklabels(y_axis)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")
    ax.set_title("Headroom for 30 Busbar")

    fig.tight_layout()
    plt.xlabel('Busbar')
    plt.ylabel('Year')
    clt=plt.colorbar(ax.imshow(-headroomarray, aspect='auto'))
    clt.ax.set_title('(MW)')
    # plt.show()
    plt.close()
    fig.savefig(path_save+os.path.sep+"Headroom."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)

def drawbatteryinvestment(years,yearlytotalbatterycap, path_save):
    fig = plt.figure()
    fig.suptitle('Annual Battery Investment', fontsize=20)
    ax1 = fig.add_subplot(111)
    ax1.plot(years,yearlytotalbatterycap)
   
    ax1.set_ylabel('Battery Capacity (kW)')
    
    from matplotlib.ticker import MaxNLocator
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.set_xlabel('Year')
    ax1.legend(['Total Installed Capacity (GW)'], loc='upper left')
    # fig.show()
    fig.savefig(path_save+os.path.sep+"AnnualBatteryInvestment."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()



# draw lossofload and curtailment                
def systemevaluationGraph(years,yearlyLossOfLoadInstances,yearlyCurtailedInstances, path_save):
    fig = plt.figure()
    fig.suptitle('System Evaluation', fontsize=20)
    ax1 = fig.add_subplot(111)
    ax1.plot(years, yearlyLossOfLoadInstances)
    ax1.plot(years, yearlyCurtailedInstances)
    from matplotlib.ticker import MaxNLocator
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width , box.height* 0.8])  
    ax1.legend(['Loss of Load Instance','Curtailed Instance'],loc='center left', bbox_to_anchor=(0.2, 1.12),ncol=1)        
    # fig.show()
    fig.savefig(path_save+os.path.sep+"SystemEvaluation."+GLOBAL_FIG_FORMAT, bbox_inches='tight', format= GLOBAL_FIG_FORMAT, dpi=GLOBAL_DPI)
    plt.close()























































    
