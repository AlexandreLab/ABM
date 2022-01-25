import random
from random import randint
from collections import namedtuple
import numpy as np
import math
import Utils


class heatProvider():
    
    
    def __init__(self):

        self.initialise()
        

    def initialise(self):
        self.opCostPkW = 0.14 # generation cost for 1kW GBP
        self.opEmissionsPkW = 1.0 # kg of CO2 emitted per kW generated
        self.heatGenerated = list()
        self.genCapacity = 1E11
        self.hourlyCost = list()
        self.hourlyEmissions = list()
        self.runingCost=0.0
        self.runingEmissions=0.0
        self.name = 'Gas Provider'

    def getGeneration(self, demand):
        self.heatGenerated = list()
        newDemand = list()
        for i in range(len(demand)):
            if(self.genCapacity<demand[i]):
                self.heatGenerated.append(self.genCapacity)
                newDemand.append(demand[i]-self.genCapacity)
            else:
                self.heatGenerated.append(demand[i])
                newDemand.append(0.0)
            curCost = self.opCostPkW*self.heatGenerated[i]
            curEmiss = self.opEmissionsPkW*self.heatGenerated[i]
            
            self.hourlyCost.append(curCost)
            self.hourlyEmissions.append(curEmiss)
            self.runingCost = self.runingCost + (curCost)
            self.runingEmissions = self.runingEmissions + (curEmiss)
        return self.heatGenerated, newDemand

    
    









        
        
