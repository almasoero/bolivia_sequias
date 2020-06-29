import os, sys, getopt
import json
import gdal
import datetime
from shutil import copyfile, rmtree
import numpy as np
from dateutil.relativedelta import *
from calendar import monthrange
from geotiff import *

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
    newFold = os.path.join(tempFold, "{:d}-Month-Files".format(monthCount))
    if os.path.isdir(newFold):
        rmtree(newFold)
    os.system("mkdir -p "+newFold)
    dateList = get_all_dates(foldAdd, nameIndex)
    dateList.sort()

    dateListMonths = [i[0:6] for i in dateList ]

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

        if oDate.strftime("%Y%m")  in dateListMonths:
            convert_to_month_average_data(foldAdd, nameIndex, dateList, newFold, month, year, monthCount)
            #dateListMonths.append(oDate.strftime("%Y%m"))
        else:
            print ("Missing data for : "+ oDate.strftime("%Y%m"))

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

    calculate_weighted_averge_prec(foldAdd, nameIndex, dateCountDic, newFold, year, month)

def calculate_weighted_averge_prec(foldAdd, nameIndex, dateCountDic, newFold, year, month):

    data , col, row, geoTrans, geoproj = readGeotiff ("mask_bolivia.tif")

    data3d = np.zeros((row, col, len (dateCountDic)))

    for i, key in enumerate(dateCountDic):
        daFold = os.path.join(foldAdd, key[0:4], key[4:6], key[6:8])
        fileName = os.path.join(daFold, nameIndex + "_" + key + ".tif")
        data , col, row, geoTrans, geoproj = readGeotiff (fileName)
        #simple_plot_index(data)
        data3d [:,:,i] = data


    data_mean = np.nanmean(data3d,axis=2)

    BandName="FAPAR_montly_mean"

    outFileName= os.path.join(newFold, nameIndex + "_" +"{:4d}{:02d}.tif".format(year, month))

    #simple_plot_index(data_mean)
    print (outFileName)
    writeGeotiffSingleBand(outFileName, geoTrans, geoproj, data_mean,nodata=np.nan, BandName=BandName)


def compute_statistics(foldAdd, fileNames, newFold, monthCount, monthStart, vmin, vmax):
    print("Create GeoTiff for {:d} months ending month {:02d}".
          format(monthCount, monthStart))

    # get first file name
    firstName = os.path.join(foldAdd, fileNames[0])
    dataSet = gdal.Open(firstName)
    geoTrans = dataSet.GetGeoTransform()
    col, row = dataSet.GetRasterBand(1).ReadAsArray().shape
    meanValue = []
    stdValue = []
    data = []
    for str in fileNames:
        file = os.path.join(foldAdd, str)
        dataSet = gdal.Open(file)
        arr = dataSet.GetRasterBand(1).ReadAsArray()
        data.append(arr)
        del dataSet

    for i in range(col):
        vmeanArr = []
        vstdArr = []
        for j in range(row):
            temp = []
            for k in range(len(data)):
                # control valid range
                val = data[k][i][j]  # !!!!!!!!!!!!!!!!!
                if vmin <= val <= vmax:
                    temp.append(val)
            if len(temp) > 1:
                tvmean = np.mean(temp)
                tvstd = np.std(temp)
            else:
                tvmean = np.nan
                tvstd = np.nan
            vmeanArr.append(tvmean)
            vstdArr.append(tvstd)
        meanValue.append(vmeanArr)
        stdValue.append(vstdArr)

    name = "FAPAR-statistics-{:02d}months-Month{:02d}.tif".format(monthCount, monthStart)
    name = os.path.join(newFold, name)
    dataSet = gdal.GetDriverByName('GTiff').Create(name, row, col, 2, gdal.GDT_Float32)
    dataSet.SetGeoTransform(geoTrans)
    dataSet.GetRasterBand(1).WriteArray(np.asarray(meanValue))
    dataSet.GetRasterBand(2).WriteArray(np.asarray(stdValue))
    dataSet.GetRasterBand(1).SetNoDataValue(np.nan)
    dataSet.GetRasterBand(2).SetNoDataValue(np.nan)
    dataSet.FlushCache()
    dataSet = None

def create_statistics(mainFoldAdd, newFold, nameIndex, monthCount, vmin, vmax):
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
        compute_statistics (mainFoldAdd, fileNames, newFold, monthCount, month, vmin, vmax)


def main(argv):
    with open('FAPAR_config.json') as jf:
        params = json.load(jf)

        # get FAPARFold tif files
        FAPARFold = params["FAPAR_folder"]
        if FAPARFold[-1] == os.path.sep:
            FAPARFold = FAPARFold[:-1]
        FAPARNameIndex = params["FAPAR_prefix"]
        # FAPARDates = get_all_dates(FAPARFold, FAPARNameIndex)

        monthlyFold = params["Monthly_folder"]
        statsFold = params["Stats_folder"]
        vmin = params["Valid_min"]
        vmax = params["Valid_max"]
        aggMonths = params["Agg_months"]

        stats = True

        opts, a1Args = getopt.getopt(argv,"hn",["help","nostats"])

        for opt, arg in opts:
            if opt in ("-n", "--nostats"):
                stats = False

        for nmonths in aggMonths:
        # monthly averages
            convert_to_monthly_data(FAPARFold, FAPARNameIndex, monthlyFold, nmonths)
        # compute min and max in given range
            monthsFold = os.path.join(monthlyFold, "{:d}-Month-Files".format(nmonths))

            if stats:
                create_statistics(monthsFold, statsFold, FAPARNameIndex, nmonths, vmin, vmax)

if __name__ == '__main__':
    argv=sys.argv[1:]
    main(argv)

else:
    pass