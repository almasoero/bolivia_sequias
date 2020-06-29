__author__ = 'lauro'

#from geotiff import *
import datetime
import os
from dateutil.relativedelta import *
import numpy as np

products_dir = "/home/sequia/drought/products/RDI/"

sDateFrom = '20130101'
oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m%d")

sDateTo = '20200601'
oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m%d")

#VAR = ["MODIS-FAPAR", "MODIS-FAPAR-QControl"]
VAR = ["NDWI-Popoo"]

while (oDateFrom <= oDateTo):

        yy=oDateFrom.strftime("%Y")
        mm=oDateFrom.strftime("%m")
        dd=oDateFrom.strftime("%d")

        for i in range(0, len(VAR)):

            #fileIn = os.path.join(products_dir,yy,mm,dd,VAR[i] +"_"+yy+mm+dd+".tif")

            fileIn = os.path.join(VAR[i] +"_"+yy+mm+dd+".tif")

            fileOut = os.path.join(products_dir,yy,mm,dd,"NDWI-POOPO_"+yy+mm+dd+"000000.tif")

            if os.path.exists(fileIn):
                print ("cp "+fileIn+" "+fileOut)
                os.system("mkdir -p "+os.path.join(products_dir,yy,mm,dd))
                os.system("cp "+fileIn+" "+fileOut)
            #else:
                #print("File does not exist")

        oDateFrom = oDateFrom +relativedelta(days=+1)

