
import joblib
import random
import numpy as np

import scipy as sp
from scipy import (dot, eye, randn, asarray, array, trace, log, exp, sqrt, mean, sum, argsort, square, arange)
from scipy.stats import multivariate_normal, norm
from scipy.linalg import (det, expm)


import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib
from matplotlib.patches import Circle


class drawMap():
    
    def __init__(self,country):
        self.country = country
        self.mapFile = 'Unknown'
        self.minRad = 20
        self.maxRad = 60
        self.name='Not_Set'
        if(country==1):
            self.name='GB'
     #       self.mapFile = 'Images/GB_Map2.png'
            self.mapFile = 'Images/GB_MapNoLabels.png'
      #      self.mapFile = 'Images/GB_MapSatView.png'
        else:
            self.name='Unknown'
        self.cities = list()
        self.cityColour = [1.0, 0.0, 0.0]
        self.cityTransparency = 0.5

    def setCity(self, city, size,regName):
        cityParam=list()
        img = plt.imread(self.mapFile)
        x = 0.0
        y = 0.0
        regionName = regName

        if(city==1): # London on map 'GB2_test.png'
            x=img.shape[1]*0.7910
            y=img.shape[0]*0.8502
        elif(city==2): # Scotland on map 'GB2_test.png'
            x=img.shape[1]*0.411
            y=img.shape[0]*0.3919
        elif(city==3): # SE on map 'GB2_test.png'
        #    x=img.shape[1]*0.7410
            x=img.shape[1]*0.7110
            y=img.shape[0]*0.8902
        elif(city==4): # NW on map 'GB2_test.png'
            x=img.shape[1]*0.5238
            y=img.shape[0]*0.6252
        elif(city==5): # EM on map 'GB2_test.png'
            x=img.shape[1]*0.7138
            y=img.shape[0]*0.7002
        elif(city==6): # EE on map 'GB2_test.png'
        #    x=img.shape[1]*0.938
            x=img.shape[1]*0.858
            y=img.shape[0]*0.757
        elif(city==7): # York on map 'GB2_test.png'
            x=img.shape[1]*0.6938
            y=img.shape[0]*0.6002
        elif(city==8): # SW on map 'GB2_test.png'
            x=img.shape[1]*0.39
            y=img.shape[0]*0.93
        elif(city==9): # WM on map 'GB2_test.png'
            x=img.shape[1]*0.5538
            y=img.shape[0]*0.7502
        elif(city==10): # Wales on map 'GB2_test.png'
            x=img.shape[1]*0.4238
            y=img.shape[0]*0.7602
        elif(city==11): # NE on map 'GB2_test.png'
            x=img.shape[1]*0.6338
            y=img.shape[0]*0.5052
        elif(city==12): # NE on map 'GB2_test.png'
            x=img.shape[1]*0.7800
            y=img.shape[0]*0.35
        else:
            print('city', city)
            input('Error. Unknown Location.')
    #    rad = self.minRad + size*(self.maxRad-self.minRad)
        rad = size*self.maxRad
        if(size>1):
            rad= self.maxRad + 10
        cityParam.append(x)
        cityParam.append(y)
        cityParam.append(rad)
        cityParam.append(regionName)
        self.cities.append(cityParam)
        
    # draw map
    def drawCities(self):
        self.img = plt.imread(self.mapFile)
        fig,ax = plt.subplots(1,figsize=(10,20))
        ax.set_aspect('equal')
        ax.imshow(self.img)
        
        for i in range (len(self.cities)):
            x = self.cities[i][0]
            y = self.cities[i][1]
            r = self.cities[i][2]
            name = self.cities[i][3]
            if(r>self.maxRad):
                circ = Circle((x,y),r,color=[1.0, 0.0, 1.0], alpha=self.cityTransparency)
            else:
                circ = Circle((x,y),r,color=self.cityColour, alpha=self.cityTransparency)
            ax.add_patch(circ)
            
            ax.annotate(name,xy=(x-100,y),color='white') # add text 
   #     plt.show()
        fig.show()


        













