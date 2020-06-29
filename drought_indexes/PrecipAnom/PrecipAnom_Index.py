import os, sys, getopt
import json
import numpy as np
from geotiff import *
import datetime
from dateutil.relativedelta import *



def displayHelp():

    print ('\nCompute index')
    print ('Options:')
    print ('          -t | --timerange              months before end of calculation to override .json file')
    print ('          -e | --dateend                calculation end date (format: YYYYMM) to override .json file ')
    print ('          -h | --help                   display this help')



def calculate_result(fileName, statsFileName, destFold, year, month, monthCount, indexPrefix,PrecNameIndex):
    # adjust destination folder
    dest_dir = os.path.join(destFold, year, month)
    os.system("mkdir -p "+dest_dir)

    # first copy file to new folderlo
    #newFileName = os.path.join(dest_dir, PrecNameIndex+"-{:02d}_".format(monthCount)+year+month+".tif".format(monthCount))
    #copyfile(fileName, newFileName)

    # estimate probability corresponding to our distribution and calculate ESI Index

    data, col, row, geoTrans, geoproj = readGeotiff (fileName)

    mask, col, row, geoTrans, geoproj=  readGeotiff("mask_bolivia.tif")

    data = data*mask
    data [data==1] = np.nan

    data3d, col, row, geoTrans, geoproj = readGeotiff (statsFileName)
    mean = data3d[:,:,0]

    PrecAnom = (data-mean)

    # create geotiff for spei output
    outFileName = os.path.join(dest_dir, indexPrefix+"{:02d}".format(monthCount)+"-"+PrecNameIndex+"_" +year+month +".tif")
   # ESI[data==1] = np.nan
    writeGeotiffSingleBand (outFileName, geoTrans, geoproj,PrecAnom, nodata=np.nan, BandName="Precipitation_anomaly")
    print ("saving... " + outFileName)

def main(argv):

    with open('PrecipAnom_config.json') as jf:

        params = json.load(jf)

        statsFold = params["Stats_folder"]
        if statsFold[-1] == os.path.sep:
            statsFold = statsFold[:-1]

        PrecFold = params["Prec_folder"]
        if PrecFold[-1] == os.path.sep:
            PrecFold = PrecFold[:-1]

        indexFold = params["Index_folder"]
        if indexFold[-1] == os.path.sep:
            indexFold = PrecFold[:-1]

        outFold = params["Out_folder"]
        if indexFold[-1] == os.path.sep:
            indexFold = PrecFold[:-1]

        PrecNameIndex = params["Prec_prefix"]

        aggMonths = params["Agg_months"]
        sDateFrom = params["StartDate"]
        sDateTo = params["EndDate"]
        indexPrefix= params["Index_prefix"]

        oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m")
        oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m")

        monthlyFolder = os.path.join(indexFold,PrecNameIndex+"-Monthly-Files")

        #override

        opts, a1Args = getopt.getopt(argv,"ht:e:",["help","timerange=","dateend="])

        monthsBefore = None
        dateend = None

        for opt, arg in opts:
            if opt in ('-h',"--help"):
                displayHelp();
                sys.exit()
            elif opt in ("-t", "--timerange"):
                monthsBefore = arg
            elif opt in ("-e", "--dateend"):
                dateend = arg

        if dateend != None:
            oDateTo = datetime.datetime.strptime(dateend,"%Y%m")
        else:
            oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m")

        if monthsBefore !=None:
            oDateFrom = oDateTo +relativedelta(months=-int(monthsBefore))
        else:
            oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m")

        while (oDateFrom <= oDateTo):

            year=oDateFrom.strftime("%Y")
            month=oDateFrom.strftime("%m")

            for monthCount in aggMonths:
                fileName = os.path.join(monthlyFolder, "{:d}-Month-Files".format(monthCount),
                                        PrecNameIndex + "_" + oDateFrom.strftime("%Y%m")+".tif")

                statsFileName = os.path.join(statsFold,"Statistics-"+indexPrefix+"-{:02d}months-Month".format(monthCount))+month+".tif"

                calculate_result(fileName, statsFileName, outFold, year, month, monthCount, indexPrefix,PrecNameIndex)

            oDateFrom = oDateFrom +relativedelta(months=+1)

if __name__ == '__main__':
    argv=sys.argv[1:]
    main(argv)
else:
    pass
