import os, sys, getopt
import json
import scipy.stats as stat
import numpy as np
from geotiff import *
import datetime
from dateutil.relativedelta import *


def displayHelp():

    print ('\nCompute SSMI index')
    print ('Options:')
    print ('          -t | --timerange              months before end of calculation to override .json file')
    print ('          -e | --dateend                calculation end date (format: YYYYMM) to override .json file ')
    print ('          -h | --help                   display this help')

def calculate_result(fileName, statsFileName, indexFold, year, month, monthCount, outIndex,sourcePrefix):
    # adjust destination folder
    dest_dir = os.path.join(indexFold, year, month)
    os.system("mkdir -p "+dest_dir)

    # estimate probability corresponding to our distribution and calculate ESI Index

    data, col, row, geoTrans, geoproj = readGeotiff (fileName)

#    mask, col, row, geoTrans, geoproj=  readGeotiff("mask_bolivia.tif")

#    data = data*mask

    data3d, col, row, geoTrans, geoproj = readGeotiff (statsFileName)
    a =     data3d[:,:,0]
    b =     data3d[:,:,1]
    loc =   data3d[:,:,2]
    scale = data3d[:,:,3]
    P0 =    data3d[:,:,4]

    probVal = stat.beta.cdf(data, a= a, b = b, loc=loc, scale=scale)

    probVal [probVal==0] = 0.0000001
    probVal [probVal==1] = 0.9999999

    probVal= (1 - P0) * probVal + P0 / 2

    SSCI = stat.norm.ppf(probVal, loc=0, scale=1)

    #simple_plot_index(SPEI,"SPEI_"+year+month)
    #simple_plot_index(probVal,"Prob_"+year+month)

    # create geotiff for spei output
    outFileName = os.path.join(dest_dir, outIndex+"{:02d}".format(monthCount)+"-"+sourcePrefix+"_" +year+month +".tif")
   # ESI[data==1] = np.nan
    writeGeotiffSingleBand (outFileName, geoTrans, geoproj,SSCI, nodata=np.nan, BandName="Standardized_SSCI")
    print ("saving... " + outFileName)

def main(argv):

    with open('SSCI-MODIS_config.json') as jf:
        params = json.load(jf)

        statsFold = params["Stats_folder"]
        if statsFold[-1] == os.path.sep:
            statsFold = statsFold[:-1]

        snowFold = params["Snow_folder"]
        if snowFold[-1] == os.path.sep:
            snowFold = snowFold[:-1]

        indexFold = params["Index_folder"]
        if indexFold[-1] == os.path.sep:
            indexFold = indexFold[:-1]

        indexPrefix= params["Index_prefix"]

        index2Prefix= params["Index2_prefix"]

        snowPrefix = params["Snow_prefix"]

        sourcePrefix = params["Source_prefix"]

        aggMonths = params["Agg_months"]

        sDateFrom = params["StartDate"]
        sDateTo = params["EndDate"]

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
                fileName = os.path.join(indexFold,year,month,snowPrefix+"{:02d}_".format(monthCount) + oDateFrom.strftime("%Y%m")+".tif")

                statsFileName = os.path.join(statsFold,"Statistics-"+indexPrefix+"-{:02d}months-Month".format(monthCount))+month+".tif"

                if os.path.exists(fileName):
                    calculate_result(fileName, statsFileName, indexFold, year, month, monthCount, index2Prefix,sourcePrefix)
                else:
                    print ("Missing data: "+fileName)
            oDateFrom = oDateFrom +relativedelta(months=+1)

if __name__ == '__main__':
    argv=sys.argv[1:]
    main(argv)
else:
    pass
