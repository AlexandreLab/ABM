

import numpy as np
import pandas as pd

import sys
import math


fileName = 'RenewableGenerationTechnology2017_v2.csv'
raw_data_set = pd.read_csv(fileName)

#print(raw_data_set.columns[5])

print(raw_data_set['Technology Type'].iloc[0])
print(raw_data_set['Installed Capacity (MWelec)'].iloc[0])
print(raw_data_set['Development Status (short)'].iloc[0])
print(raw_data_set['Country'].iloc[0])
print('submit ',raw_data_set['Planning Application Submitted'].iloc[0])
print('Withdrawn ',raw_data_set['Planning Application Withdrawn'].iloc[0])
print(raw_data_set['Planning Permission Refused'].iloc[0])
print(raw_data_set['Planning Permission Granted'].iloc[0])
print(raw_data_set['Under Construction'].iloc[0])
print(raw_data_set['Operational'].iloc[0])

print('test')
print(raw_data_set['Planning Application Withdrawn'].iloc[0])
print('nan')
if(str(raw_data_set['Planning Application Withdrawn'].iloc[0]) == 'nan'):
    c=True
else:
    c=False
    

print(c)

print(math.isnan(float(raw_data_set['Planning Application Withdrawn'].iloc[0])))

print(len(raw_data_set))
raw_data_set.drop(raw_data_set.loc[raw_data_set['Country']=='Northern Ireland'].index, inplace=True)

#raw_data_set.drop(raw_data_set.loc[raw_data_set['Planning Application Withdrawn']!='NaN'].index, inplace=True)
#raw_data_set.drop(raw_data_set.loc[raw_data_set['Planning Permission Refused']!='NaN'].index, inplace=True)
print(len(raw_data_set))


df_Operational = raw_data_set[pd.notnull(raw_data_set['Operational'])]
print('df_Operational ',len(df_Operational))

# ================================ Solar start ================================


df_Operational_PV = df_Operational[raw_data_set['Technology Type']=='Solar Photovoltaics']
print('df_Operational_PV ',len(df_Operational_PV))

#df_Operational_PV2 = df_Operational.query(str('Technology Type') == 'Solar Photovoltaics').groupby('Ref ID').head(4)
df_Operational_PV2 = df_Operational[df_Operational['Technology Type']=='Solar Photovoltaics'].groupby('Ref ID').head(4)
#df_Operational_PV2 = df_Operational[df_Operational['Mounting Type for Solar']=='Ground'].groupby('Ref ID').head(4)

PV_Operate_CapSum =0.0
for i in range(len(df_Operational_PV2)):
    PV_Operate_CapSum = PV_Operate_CapSum + float(df_Operational_PV2['Installed Capacity (MWelec)'].iloc[i])

print('PV_Operate_CapSum ', PV_Operate_CapSum)

print('df_Operational_PV2 ',len(df_Operational_PV2))
print('df_Operational_PV2 ',df_Operational_PV2)


#outPVOperational = pd.Series(len(df_Operational_PV2))
#outPVOperational['ID'] = df_Operational_PV2['Ref ID'].values
#outPVOperational['Technology Type'] = df_Operational_PV2['Technology Type'].values
#outPVOperational['CapacityMW'] = df_Operational_PV2['Installed Capacity (MWelec)'].values
#outPVOperational['Operational'] = df_Operational_PV2['Operational'].values


#outPVOperational = pd.DataFrame(columns=[df_Operational_PV2['Ref ID']])
outPVOperational = pd.DataFrame(columns=['Company Name','Name','Type','TypeID','SiteID','Renewable','Capacity(MW)','Capacity(kW)','StartYear','EndYear'])
outPVOperational['Company Name'] = df_Operational_PV2['Operator (or Applicant)'].values
outPVOperational['SiteID'] = df_Operational_PV2['Ref ID'].values
outPVOperational['Name'] = df_Operational_PV2['Site Name'].values
outPVOperational['Type'] = df_Operational_PV2['Technology Type'].values
outPVOperational['Capacity(MW)'] = df_Operational_PV2['Installed Capacity (MWelec)'].values
outPVOperational['StartYear'] = df_Operational_PV2['Operational'].values

outPVOperational['Type'] = df_Operational_PV2['Operational'].values.copy()
outPVOperational['TypeID'] = df_Operational_PV2['Operational'].values.copy()
outPVOperational['Renewable'] = df_Operational_PV2['Operational'].values.copy()
outPVOperational['Capacity(kW)'] = df_Operational_PV2['Operational'].values.copy()
outPVOperational['EndYear'] = df_Operational_PV2['Operational'].values.copy()



for i in range(len(outPVOperational)):
 #   outPVOperational['Technology'].iloc[i]='Solar'
    outPVOperational.loc[i,'Type'] = 'Solar'
 #   outPVOperational['TypeID'].iloc[i]=7
    outPVOperational.loc[i,'TypeID'] = 7
 #   outPVOperational['Renewable'].iloc[i]=1
    outPVOperational.loc[i,'Renewable'] = 1
 #   outPVOperational['Capacity(kW)'].iloc[i]= float(outPVOperational['Capacity(MW)'].iloc[i])*1000
    outPVOperational.loc[i,'Capacity(kW)'] = float(outPVOperational['Capacity(MW)'].iloc[i])*1000
 #   outPVOperational['EndYear'].iloc[i]=20
    sYear = int(outPVOperational['StartYear'].iloc[i][-2:])
    sYear = 2000+sYear
    if(sYear>2080):
        input('wait')
    outPVOperational.loc[i,'StartYear'] = sYear
    outPVOperational.loc[i,'EndYear'] = sYear+25

print('outPVOperational',outPVOperational)

outfile ='OperationalPVs2017test_wOwner.csv'
outPVOperational.to_csv(outfile)

# ================================ Solar end ================================






# ================================ Hydro start ================================


df_Operational_HydroLarge = df_Operational[raw_data_set['Technology Type']=='Large Hydro']
df_Operational_HydroSmall = df_Operational[raw_data_set['Technology Type']=='Small Hydro']

print('df_Operational_HydroSmall ',len(df_Operational_HydroSmall))
print('df_Operational_HydroLarge ',len(df_Operational_HydroLarge))



#df_Operational_PV2 = df_Operational.query(str('Technology Type') == 'Solar Photovoltaics').groupby('Ref ID').head(4)
df_Operational_HydroLarge2 = df_Operational[df_Operational['Technology Type']=='Large Hydro'].groupby('Ref ID').head(4)
df_Operational_HydroSmall2 = df_Operational[df_Operational['Technology Type']=='Small Hydro'].groupby('Ref ID').head(4)
#df_Operational_PV2 = df_Operational[df_Operational['Mounting Type for Solar']=='Ground'].groupby('Ref ID').head(4)


Hydro_Operate_CapSum =0.0
for i in range(len(df_Operational_HydroLarge2)):
    Hydro_Operate_CapSum = Hydro_Operate_CapSum + float(df_Operational_HydroLarge2['Installed Capacity (MWelec)'].iloc[i])
for i in range(len(df_Operational_HydroSmall2)):
    Hydro_Operate_CapSum = Hydro_Operate_CapSum + float(df_Operational_HydroSmall2['Installed Capacity (MWelec)'].iloc[i])

print('Hydro_Operate_CapSum ', Hydro_Operate_CapSum)

df_allHydro = pd.concat([df_Operational_HydroLarge2, df_Operational_HydroSmall2])
print('len(df_allHydro) ',len(df_allHydro))
print('df_allHydro ',df_allHydro)





#outPVOperational = pd.DataFrame(columns=[df_Operational_PV2['Ref ID']])
outHydro = pd.DataFrame(columns=['Company Name','Name','Type','TypeID','SiteID','Renewable','Capacity(MW)','Capacity(kW)','StartYear','EndYear'])
outHydro['Company Name'] = df_allHydro['Operator (or Applicant)'].values
outHydro['SiteID'] = df_allHydro['Ref ID'].values
outHydro['Name'] = df_allHydro['Site Name'].values
outHydro['Type'] = df_allHydro['Technology Type'].values
outHydro['Capacity(MW)'] = df_allHydro['Installed Capacity (MWelec)'].values
outHydro['StartYear'] = df_allHydro['Operational'].values

outHydro['Type'] = df_allHydro['Operational'].values.copy()
outHydro['TypeID'] = df_allHydro['Operational'].values.copy()
outHydro['Renewable'] = df_allHydro['Operational'].values.copy()
outHydro['Capacity(kW)'] = df_allHydro['Operational'].values.copy()
outHydro['EndYear'] = df_allHydro['Operational'].values.copy()

for i in range(len(outHydro)):
    outHydro.loc[i,'Type'] = 'Hydro'
    outHydro.loc[i,'TypeID'] = 8
    outHydro.loc[i,'Renewable'] = 1
    outHydro.loc[i,'Capacity(kW)'] = float(outHydro['Capacity(MW)'].iloc[i])*1000
    sYear = int(outHydro['StartYear'].iloc[i][-2:])
    if(sYear<30):
        sYear = 2000+sYear
        eYear = sYear+41
    elif(sYear>80):
        sYear = 1900+sYear
        eYear = sYear+41
    else:
        sYear = 1900+sYear
        eYear = 2030
  #  else:
  #      sYear = 1900+sYear
    if(sYear>2080):
        print('outHydro[StartYear].iloc[i] ', outHydro['StartYear'].iloc[i])
        input('wait*********')
    outHydro.loc[i,'StartYear'] = sYear
    outHydro.loc[i,'EndYear'] = eYear

print('outHydro',outHydro)

outfile ='OperationalHydros2017test_wOwner.csv'
outHydro.to_csv(outfile)
#input('Hydro Complete')

# ================================ Hydro end ================================






# ================================ Biomass start ================================





df_Operational_Biomass1 = df_Operational[df_Operational['Technology Type']=='Biomass (dedicated)'].groupby('Ref ID').head(4)
df_Operational_Biomass2 = df_Operational[df_Operational['Technology Type']=='Biomass (co-firing)'].groupby('Ref ID').head(4)
df_Operational_Biomass3 = df_Operational[df_Operational['Technology Type']=='Anaerobic Digestion'].groupby('Ref ID').head(4)

#df_allBiomass = pd.concat([df_Operational_Biomass1, df_Operational_Biomass2, df_Operational_Biomass3])
df_allBiomass = pd.concat([df_Operational_Biomass1, df_Operational_Biomass2])
#df_allBiomass = df_Operational_Biomass1

Biomass_Operate_CapSum =0.0
for i in range(len(df_allBiomass)):
    Biomass_Operate_CapSum = Biomass_Operate_CapSum + float(df_allBiomass['Installed Capacity (MWelec)'].iloc[i])


print('Biomass_Operate_CapSum ', Biomass_Operate_CapSum)


print('len(df_allBiomass) ',len(df_allBiomass))
print('df_allBiomass ',df_allBiomass)



#outPVOperational = pd.DataFrame(columns=[df_Operational_PV2['Ref ID']])
outBio = pd.DataFrame(columns=['Company Name','Name','Type','TypeID','SiteID','Renewable','Capacity(MW)','Capacity(kW)','StartYear','EndYear'])
outBio['Company Name'] = df_allBiomass['Operator (or Applicant)'].values
outBio['SiteID'] = df_allBiomass['Ref ID'].values
outBio['Name'] = df_allBiomass['Site Name'].values
outBio['Type'] = df_allBiomass['Technology Type'].values
outBio['Capacity(MW)'] = df_allBiomass['Installed Capacity (MWelec)'].values
outBio['StartYear'] = df_allBiomass['Operational'].values

outBio['Type'] = df_allBiomass['Operational'].values.copy()
outBio['TypeID'] = df_allBiomass['Operational'].values.copy()
outBio['Renewable'] = df_allBiomass['Operational'].values.copy()
outBio['Capacity(kW)'] = df_allBiomass['Operational'].values.copy()
outBio['EndYear'] = df_allBiomass['Operational'].values.copy()

for i in range(len(outBio)):
    outBio.loc[i,'Type'] = 'Biomass'
    outBio.loc[i,'TypeID'] = 9
    outBio.loc[i,'Renewable'] = 1
    outBio.loc[i,'Capacity(kW)'] = float(outBio['Capacity(MW)'].iloc[i])*1000
    sYear = int(outBio['StartYear'].iloc[i][-2:])
    if(sYear<30):
        sYear = 2000+sYear
        eYear = sYear+25
    elif(sYear>80):
        sYear = 1900+sYear
        eYear = sYear+25
    else:
        sYear = 1900+sYear
        eYear = 2030
  #  else:
  #      sYear = 1900+sYear
    if(sYear>2080):
        print('outHydro[StartYear].iloc[i] ', outBio['StartYear'].iloc[i])
        input('wait*********')
    outBio.loc[i,'StartYear'] = sYear
    outBio.loc[i,'EndYear'] = eYear

print('outBio',outBio)

outfile ='OperationalBiomass2017test_wOwner.csv'
outBio.to_csv(outfile)
#input('Biomass Complete')

# ================================ Biomass end ================================


# ================================ Wind Offshore end ================================


df_Operational_Biomass1 = df_Operational[df_Operational['Technology Type']=='Wind Offshore'].groupby('Ref ID').head(4)


#df_allBiomass = pd.concat([df_Operational_Biomass1, df_Operational_Biomass2, df_Operational_Biomass3])
#df_allBiomass = pd.concat([df_Operational_Biomass1, df_Operational_Biomass2])
df_allBiomass = df_Operational_Biomass1

Biomass_Operate_CapSum =0.0
for i in range(len(df_allBiomass)):
    Biomass_Operate_CapSum = Biomass_Operate_CapSum + float(df_allBiomass['Installed Capacity (MWelec)'].iloc[i])


print('Biomass_Operate_CapSum ', Biomass_Operate_CapSum)


print('len(df_allBiomass) ',len(df_allBiomass))
print('df_allBiomass ',df_allBiomass)



#outPVOperational = pd.DataFrame(columns=[df_Operational_PV2['Ref ID']])
outBio = pd.DataFrame(columns=['Company Name','Name','Type','TypeID','SiteID','Renewable','Capacity(MW)','Capacity(kW)','StartYear','EndYear'])
outBio['Company Name'] = df_allBiomass['Operator (or Applicant)'].values
outBio['SiteID'] = df_allBiomass['Ref ID'].values
outBio['Name'] = df_allBiomass['Site Name'].values
outBio['Type'] = df_allBiomass['Technology Type'].values
outBio['Capacity(MW)'] = df_allBiomass['Installed Capacity (MWelec)'].values
outBio['StartYear'] = df_allBiomass['Operational'].values

outBio['Type'] = df_allBiomass['Operational'].values.copy()
outBio['TypeID'] = df_allBiomass['Operational'].values.copy()
outBio['Renewable'] = df_allBiomass['Operational'].values.copy()
outBio['Capacity(kW)'] = df_allBiomass['Operational'].values.copy()
outBio['EndYear'] = df_allBiomass['Operational'].values.copy()

for i in range(len(outBio)):
    outBio.loc[i,'Type'] = 'Wind Offshore'
    outBio.loc[i,'TypeID'] = 9
    outBio.loc[i,'Renewable'] = 1
    outBio.loc[i,'Capacity(kW)'] = float(outBio['Capacity(MW)'].iloc[i])*1000
    sYear = int(outBio['StartYear'].iloc[i][-2:])
    if(sYear<30):
        sYear = 2000+sYear
        eYear = sYear+22
    elif(sYear>80):
        sYear = 1900+sYear
        eYear = sYear+22
    else:
        sYear = 1900+sYear
        eYear = 2030
  #  else:
  #      sYear = 1900+sYear
    if(sYear>2080):
        print('outHydro[StartYear].iloc[i] ', outBio['StartYear'].iloc[i])
        input('wait*********')
    outBio.loc[i,'StartYear'] = sYear
    outBio.loc[i,'EndYear'] = eYear

print('outBio',outBio)

outfile ='OperationalWindOffshore2017test_wOwner.csv'
outBio.to_csv(outfile)
#input('Wind Offshore Complete')



# ================================ Wind offshore end ================================

# ================================ Wind onshore start ================================



df_Operational_Biomass1 = df_Operational[df_Operational['Technology Type']=='Wind Onshore'].groupby('Ref ID').head(4)


#df_allBiomass = pd.concat([df_Operational_Biomass1, df_Operational_Biomass2, df_Operational_Biomass3])
#df_allBiomass = pd.concat([df_Operational_Biomass1, df_Operational_Biomass2])
df_allBiomass = df_Operational_Biomass1

Biomass_Operate_CapSum =0.0
for i in range(len(df_allBiomass)):
    Biomass_Operate_CapSum = Biomass_Operate_CapSum + float(df_allBiomass['Installed Capacity (MWelec)'].iloc[i])


print('Biomass_Operate_CapSum ', Biomass_Operate_CapSum)


print('len(df_allBiomass) ',len(df_allBiomass))
print('df_allBiomass ',df_allBiomass)



#outPVOperational = pd.DataFrame(columns=[df_Operational_PV2['Ref ID']])
outBio = pd.DataFrame(columns=['Company Name','Name','Type','TypeID','SiteID','Renewable','Capacity(MW)','Capacity(kW)','StartYear','EndYear'])
outBio['Company Name'] = df_allBiomass['Operator (or Applicant)'].values
outBio['SiteID'] = df_allBiomass['Ref ID'].values
outBio['Name'] = df_allBiomass['Site Name'].values
outBio['Type'] = df_allBiomass['Technology Type'].values
outBio['Capacity(MW)'] = df_allBiomass['Installed Capacity (MWelec)'].values
outBio['StartYear'] = df_allBiomass['Operational'].values

outBio['Type'] = df_allBiomass['Operational'].values.copy()
outBio['TypeID'] = df_allBiomass['Operational'].values.copy()
outBio['Renewable'] = df_allBiomass['Operational'].values.copy()
outBio['Capacity(kW)'] = df_allBiomass['Operational'].values.copy()
outBio['EndYear'] = df_allBiomass['Operational'].values.copy()

for i in range(len(outBio)):
    outBio.loc[i,'Type'] = 'Wind Onshore'
    outBio.loc[i,'TypeID'] = 9
    outBio.loc[i,'Renewable'] = 1
    outBio.loc[i,'Capacity(kW)'] = float(outBio['Capacity(MW)'].iloc[i])*1000
    sYear = int(outBio['StartYear'].iloc[i][-2:])
    if(sYear<30):
        sYear = 2000+sYear
        eYear = sYear+24
    elif(sYear>80):
        sYear = 1900+sYear
        eYear = sYear+24
    else:
        sYear = 1900+sYear
        eYear = 2030
  #  else:
  #      sYear = 1900+sYear
    if(sYear>2080):
        print('outHydro[StartYear].iloc[i] ', outBio['StartYear'].iloc[i])
        input('wait*********')
    outBio.loc[i,'StartYear'] = sYear
    outBio.loc[i,'EndYear'] = eYear

print('outBio',outBio)

outfile ='OperationalWindOnshore2017test_wOwner.csv'
outBio.to_csv(outfile)
input('Wind Onshore Complete')





























