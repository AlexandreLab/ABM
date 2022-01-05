
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
from geopy.geocoders import Nominatim


class drawMap():
    
    def __init__(self,country):
        self.country = country
        self.mapFile = 'Unknown'
        self.minRad = 20
        self.maxRad = 60
        self.name='Not_Set'
        self.geolocator = Nominatim(user_agent="specify_your_app_name_here")
        if(country==1):
            self.name='GB'
            self.mapFile = 'Images/GB_Map2.png'
            img = plt.imread(self.mapFile)
            
            self.invernessMapx = img.shape[1]*0.3672
            self.invernessMapy = img.shape[0]*0.2242
            self.invernessLoc =  self.geolocator.geocode("Inverness")
            self.invernessLat = self.invernessLoc.latitude
            self.invernessLong = self.invernessLoc.longitude
            self.plymouthLoc = self.geolocator.geocode("Plymouth")
            self.plymouthLat = self.plymouthLoc.latitude
            self.plymouthLong = self.plymouthLoc.longitude
            self.plymouthMapx = img.shape[1]*0.375 
            self.plymouthMapy = img.shape[0]*0.957
            self.norwichLoc = self.geolocator.geocode("Norwich")
            self.norwichLat = self.norwichLoc.latitude
            self.norwichLong = self.norwichLoc.longitude
            self.norwichMapx = img.shape[1]*0.938 
            self.norwichMapy = img.shape[0]*0.737
            self.degDiffLat = abs(self.invernessMapy-self.plymouthMapy)/abs(self.invernessLat-self.plymouthLat)
            self.degDiffLong = abs(self.norwichMapx-self.plymouthMapx)/abs(self.norwichLong-self.plymouthLong)
            
        else:
            self.name='Unknown'
        self.cities = list()
        self.cityColour = [1.0, 0.0, 0.0]
        self.cityTransparency = 0.5

    def setCity(self, city, size,regName):
        cityLoc = self.geolocator.geocode(regName)
        lat = cityLoc.latitude
        long = cityLoc.longitude
        cityMapy = self.plymouthMapy + (self.plymouthLat-lat)*self.degDiffLat
        cityMapx = self.plymouthMapx + abs(self.plymouthLong-long)*self.degDiffLong
        cityParam=list()
        rad = self.minRad + size*(self.maxRad-self.minRad)
        cityParam.append(cityMapx)
        cityParam.append(cityMapy)
        cityParam.append(rad)
        cityParam.append(regName)
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
            circ = Circle((x,y),r,color=self.cityColour, alpha=self.cityTransparency)
            ax.add_patch(circ)
            ax.annotate(name,xy=(x,y)) # add text 
  #      plt.show()
        fig.show()


        













