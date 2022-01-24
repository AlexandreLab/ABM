import pandapower as pp
import pandapower.networks as nw
import seaborn
from pandapower.plotting import pf_res_plotly
from pandas import Series,DataFrame        
import pandapower.plotting as pplt
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import matplotlib as mpl

def EvaluateHeadRoom(CapPerBus,totalCustDemand):
    busheadroom = [j-k for j,k in zip(CapPerBus,totalCustDemand)] # 30bus
    return busheadroom

