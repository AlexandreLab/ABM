

import numpy as np
import pandas as pd

import sys

months = list()
months.append('Jan')
months.append('Feb')
months.append('Mar')
months.append('Apr')
months.append('May')
months.append('June')
months.append('July')
months.append('Aug')
months.append('Sept')
months.append('Oct')
months.append('Nov')
months.append('Dec')

solar = list()
windOnshore = list()
windOffshore = list()
day=0

for i in range(len(months)):
    fileLoc = months[i]+'/'
    daysInMonth = 31
    if(i==1):
        daysInMonth = 28
    elif(i==3 or i==5 or i==8 or i==10):
        daysInMonth = 30
    else:
        daysInMonth = 31
    
    for j in range(daysInMonth):
        day=day+1
        datavals = list()
        if(i==0):
            fileName = fileLoc+'B1630_'+str(j+1)+'Jan18.csv'
        else:
            if(j==0):
                fileName = fileLoc+'B1630.csv'
            else:
                fileName = fileLoc+'B1630('+str(j)+').csv'

        raw_data_set = pd.read_csv(fileName)
        
        
 #       print(raw_data_set.values)
 #       print(raw_data_set.shape)
        col = raw_data_set.shape[1]-1
  #      dataset = raw_data_set.values[::]
        dataset = raw_data_set.values[:,col]
  #      print(dataset)

            
        for k in range(len(dataset)-1,0,-1):
     #      print('val '+dataset[k])
            datavals.append(float(dataset[k]))

    #    print('datavals')
    #    print(datavals)

        for k in range (len(datavals)):
            if(k%3==0):
                solar.append(datavals[k])
            elif((k+2)%3==0):
                windOffshore.append(datavals[k])
            elif((k+1)%3==0):
                windOnshore.append(datavals[k])
            
                
        if(len(datavals)!=144):
            print('!!!!!!!! j',j)
            print(len(datavals))

    
    print(months[i])
    
print('Solar')
print(len(solar))
print('windOffshore')
print(len(windOffshore))
print('windOnshore')
print(len(windOnshore))
        
    

solarHourly = list()
windOnHourly = list()
windOffHourly = list()



for i in range (len(solar)):
    if(i%2==1):
        val = (solar[i]+solar[i-1])/2.0
        solarHourly.append(val)

        val = (windOnshore[i]+windOnshore[i-1])/2.0
        windOnHourly.append(val)

        val = (windOffshore[i]+windOffshore[i-1])/2.0
        windOffHourly.append(val)
        


df_solar = pd.DataFrame({'col':solarHourly})
df_windOnshore = pd.DataFrame({'col':windOnHourly})
df_windOffshore = pd.DataFrame({'col':windOffHourly})

outfile ='2018_GB_Solar.csv'
df_solar.to_csv(outfile)

outfile ='2018_GB_WindOnshore.csv'
df_windOnshore.to_csv(outfile)

outfile ='2018_GB_WindOffshore.csv'
df_windOffshore.to_csv(outfile)





































