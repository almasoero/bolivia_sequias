import os
import json
import gdal
import datetime
from shutil import rmtree
import string
import scipy.stats as stat
import numpy as np
from dateutil.relativedelta import *
from calendar import monthrange
from geotiff import *
from lmoments3 import distr


def get_all_dates(foldAdd, nameIndex):
    # remove path separator from end of folder address
    if foldAdd[-1] == os.path.sep:
        foldAdd = foldAdd[:-1]

    # get list of all files
    allFiles = [x[2] for x in os.walk(foldAdd)]

    # get dates from file names
    count = len(nameIndex)
    result = []
    for str in allFiles:
        if len(str) > 0:
            for stf in str:
                if nameIndex in stf:
                    date=stf.split('_')[1].split(".")[0]
                    #date = stf[count+1:count+9]
                     # print(date)
                    result.append(date)

    result.sort()
    return result


def get_date(dateStr):
    year = int(dateStr[0:4])
    month = int(dateStr[4:6])
    day = int(dateStr[6:8])
    return year, month, day

def diff_date_str(curDate, refDate):
    dateVal = datetime.datetime.strptime(curDate, "%Y%m%d").date()
    refDateVal = datetime.datetime.strptime(refDate, "%Y%m%d").date()
    return (dateVal - refDateVal).days

def convert_to_monthly_data(foldAdd, nameIndex, tempFold, monthCount):
    newFold = os.path.join(tempFold,"{:d}-Month-Files".format(monthCount))
    if os.path.isdir(newFold):
        rmtree(newFold)
    os.system ("mkdir -p " + newFold)
    dateList = get_all_dates(foldAdd, nameIndex)
    dateList.sort()
    #print ([int(s[0:6]) for s in dateList])

    dateListMonths =[]

    oDateFrom = datetime.datetime.strptime(dateList[0],"%Y%m%d")
    oDateTo =   datetime.datetime.strptime(dateList[-1],"%Y%m%d")

    #oDateFrom = oDateFrom + relativedelta(months=monthCount)
    oDate = oDateFrom
    while (oDate <= oDateTo):

        if oDate < oDateFrom + relativedelta(months=monthCount-1):
            # remove the first monthCount from dateList
            #dateList = [s for s in dateList if oDate.strftime("%Y%m") not in s]
            oDate = oDate +relativedelta(months=+1)
            continue
        year = int(oDate.strftime("%Y"))
        month = int(oDate.strftime("%m"))

        convert_to_month_average_data(foldAdd, nameIndex, dateList, newFold, month, year, monthCount)
        dateListMonths.append(oDate.strftime("%Y%m"))
        oDate = oDate +relativedelta(months=+1)


def convert_to_month_average_data(foldAdd, nameIndex, dateList, newFold,
                                  month, year, monthCount):
    dateCountDic = dict()
    for i in range(monthCount):
        yy = year
        mm = month - i
        if (mm < 1):
            mm += 12
            yy -= 1
        totalDays = monthrange(yy, mm)[1]

        for dd in range(1, totalDays + 1):
            dateStr = "{:4d}{:02d}{:02d}".format(yy, mm, dd)
            if dateStr in dateList:
                if dateStr in dateCountDic:
                    dateCountDic[dateStr] += 1
                else:
                    dateCountDic[dateStr] = 1
            else:
                dateList.append(dateStr)
                dateList.sort()
                ind = dateList.index(dateStr)
                topDate, bottDate = str(), str()
                if ind == 0:
                    topDate = dateList[1]
                    bottDate = dateList[1]
                elif ind == len(dateList) - 1:
                    topDate = dateList[-2]
                    bottDate = dateList[-2]
                else:
                    topDate = dateList[ind + 1]
                    bottDate = dateList[ind - 1]
                dateList.remove(dateStr)
                refDate = bottDate
                diff = diff_date_str(dateStr, bottDate)
                if diff >= 8:
                    newDiff = diff_date_str(dateStr, topDate)
                    if newDiff < diff:
                        refDate = topDate
                if refDate in dateCountDic:
                    dateCountDic[refDate] += 1
                else:
                    dateCountDic[refDate] = 1
    if nameIndex=="PERSIANN" or monthCount>6:
        calculate_weighted_averge_prec(foldAdd, nameIndex, dateCountDic, newFold, year, month)
    else:
        print ("ATTENTION: variable "+nameIndex+" not admitted! valid values: PERSIANN, MODIS-PET")

def calculate_weighted_averge_prec(foldAdd, nameIndex, dateCountDic, newFold, year, month):
    alphabetList = list(string.ascii_uppercase)
    args = ["gdal_calc.py"]
    calcStr = "--calc=("
    sumValue = 0
    data , col, row, geoTrans, geoproj = readGeotiff ("mask_bolivia.tif")

    data3d = np.zeros((row, col, len (dateCountDic)))
    datasum = np.zeros((row, col ))
    for i, key in enumerate(dateCountDic):
        daFold = os.path.join(foldAdd, key[0:4], key[4:6], key[6:8])
        fileName = os.path.join(daFold, nameIndex + "_" + key + ".tif")
        data , col, row, geoTrans, geoproj = readGeotiff (fileName)
        #simple_plot_index(data)
        data3d [:,:,i] = data

    data_mean = np.nanmean(data3d,axis=2)

    outFileName= os.path.join(newFold, nameIndex + "_" +"{:4d}{:02d}.tif".format(year, month))

    #simple_plot_index(data_mean)
    print (outFileName)
    writeGeotiffSingleBand(outFileName, geoTrans, geoproj, data_mean,nodata=np.nan, BandName="Prec_accumulation")


def create_statistics(mainFoldAdd, newFold, nameIndex, monthCount, indexPrefix):
    dateList = get_all_dates(mainFoldAdd, nameIndex)
    dateList.sort()
#    newFold = os.path.join(mainFoldAdd, "Normal PDF")
    if not(os.path.isdir(newFold)):
        os.system ("mkdir -p "+newFold)

    for month in range(1, 13):
        fileNames = []
        for str in dateList:
            yy = int(str[0:4])
            mm = int(str[4:6])
            if mm == month:
                fileNames.append(nameIndex + "_" + str + ".tif")
        compute_statistics (mainFoldAdd, fileNames, newFold, monthCount, month,nameIndex, indexPrefix)


def compute_statistics(mainFoldAdd, fileNames, newFold, monthCount, month,nameIndex, indexPrefix):
    print("Create statistics GeoTiff for {:d} months from month {:02d}".
          format(monthCount, month))

    mask, col, row, geoTrans, geoproj=  readGeotiff("mask_bolivia.tif")

    data3d = np.zeros((row,col,len(fileNames)))

    for i, f in enumerate(fileNames):

        data , col, row, geoTrans, geoproj = readGeotiff (os.path.join(mainFoldAdd,f))

        data3d [:,:,i]= data

    stats_param =np.zeros((row,col,2))* np.nan

    stats_param [:,:,0] = np.nanmean(data3d,axis=2) * mask

    stats_param [:,:,1] = np.nanstd(data3d, axis = 2) * mask

    bandDescr = ["mean_precip","stand_dev_precip"]

    name = "Statistics-"+ indexPrefix +"-{:02d}months-Month{:02d}.tif".format(monthCount, month)
    fileStatsOut = os.path.join(newFold, name)

    writeGeotiff(fileStatsOut,geoTrans, geoproj,stats_param, nodata=np.nan, BandNames= bandDescr,globalDescr = "Precip_anom_mean_std")


def main():
    with open('PrecipAnom_config.json') as jf:
        params = json.load(jf)

        # get FAPARFold tif files

        PrecFold = params["Prec_folder"]
        if PrecFold[-1] == os.path.sep:
            PrecFold = PrecFold[:-1]

        IndexFold = params["Index_folder"]
        if IndexFold[-1] == os.path.sep:
            IndexFold = PrecFold[:-1]

        PrecNameIndex = params["Prec_prefix"]

        indexPrefix = params["Index_prefix"]

       # monthlyFold = params["Monthly_folder"]

        statsFold = params["Stats_folder"]

        aggMonths = params["Agg_months"]

        PrecmonthlyFold = os.path.join(IndexFold,PrecNameIndex+"-Monthly-Files")

        for nmonths in aggMonths:

            # monthly averages

#            convert_to_monthly_data(PrecFold, PrecNameIndex, PrecmonthlyFold, nmonths)

            monthsFold = os.path.join(PrecmonthlyFold, "{:d}-Month-Files".format(nmonths))

            create_statistics(monthsFold, statsFold, PrecNameIndex, nmonths,indexPrefix)

if __name__ == '__main__':
    main()
else:
    pass