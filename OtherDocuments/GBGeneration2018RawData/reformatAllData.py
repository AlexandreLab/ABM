

import numpy as np
import pandas as pd

import sys



fileName = 'GenerationbyFuelType_FullYear_GB.csv'
raw_data_set = pd.read_csv(fileName)

data_set_hourly = pd.DataFrame(columns=raw_data_set.columns)

for column in raw_data_set.columns[1:]:
    tempList = list()
    for i in range(len(raw_data_set[column])):
        if(i%2==1):
            val = (raw_data_set[column][i]+raw_data_set[column][i-1])/2.0
            tempList.append(val)
    data_set_hourly[column] = tempList



outfile ='GenerationbyFuelType_FullYear_GB_2018_hourly.csv'
data_set_hourly.to_csv(outfile)


dataset = raw_data_set.values[::]



for column in data_set_hourly.columns[1:]:
    print(data_set_hourly[column])
    print('column ',column)
    outfile ='2018_GB_hourly_'+column+'.csv'
    data_set_hourly[column].to_csv(outfile)






































