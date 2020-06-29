import os
import json
import osgeo
import gdal
import subprocess
import datetime
from shutil import copyfile, rmtree
import string
import numpy as np
from geotiff import *
from dateutil.relativedelta import *
from calendar import monthrange
import matplotlib.pylab as plt
import matplotlib as mpl


def simple_plot_index(a,title="", save_img=False,save_dir='.'):
    fig, ax = plt.subplots()
    #cmap='RdBu'
    cmap = mpl.colors.LinearSegmentedColormap.from_list("", ["red","orange","yellow","white","pink","violet", "#0f0f0f"])
    plt.title(title)
    im = plt.imshow(a, interpolation='none',cmap=cmap)
    plt.colormaps()
    # cbar = fig.colorbar(cax,ticks=[-1, 0, 1, 2, 10],orientation='vertical')
    cbar = fig.colorbar(im, orientation='vertical')
    #plt.clim(-3,3)
    # cbar.ax.set_yticklabels(['< -1', '0', 1, 2,'> 10'])# vertically oriented
    # colorbar
    #ax.format_coord = Formatter(im)
    if save_img:
        plt.savefig(os.path.join(save_dir,title+'.png'))
    else:
        plt.show()

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
    return year, month


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
    datasum = np.zeros((row, col ))
    for i, key in enumerate(dateCountDic):
        daFold = os.path.join(foldAdd, key[0:4], key[4:6], key[6:8])
        fileName = os.path.join(daFold, nameIndex + "_" + key + ".tif")
        data , col, row, geoTrans, geoproj = readGeotiff (fileName)
        #simple_plot_index(data)
        data3d [:,:,i] = data


    data_mean = np.nanmean(data3d,axis=2)

    BandName=nameIndex+"montly_mean"

    outFileName= os.path.join(newFold, nameIndex + "_" +"{:4d}{:02d}.tif".format(year, month))

    #simple_plot_index(data_mean)
    print (outFileName)
    writeGeotiffSingleBand(outFileName, geoTrans, geoproj, data_mean,nodata=np.nan, BandName=BandName)


def compute_extremes_inrange(foldAdd, fileNames, newFold, monthCount, month, vmin, vmax,indexPrefix):
    print("Create GeoTiff for {:d} months ending month {:02d}".
          format(monthCount, month))

    mask, col, row, geoTrans, geoproj=  readGeotiff("mask_bolivia.tif")

    data3d = np.zeros((row,col,len(fileNames)))

    for i, f in enumerate(fileNames):

        data , col, row, geoTrans, geoproj = readGeotiff (os.path.join(foldAdd,f))

        data3d [:,:,i]= data

    stats_param =np.zeros((row,col,3))* np.nan

    dataMin= np.nanmin(data3d,axis=2) * mask
    dataMin[dataMin<vmin]=np.nan

    dataMax= np.nanmax(data3d,axis=2) * mask

    dataMax[dataMax>vmax]=np.nan

    dataMean= np.nanmean (data3d,axis=2) * mask

    stats_param [:,:,0] = dataMin

    stats_param [:,:,1] = dataMax

    stats_param [:,:,2] = dataMean

    bandDescr = ["min","max","mean"]

    name = "Statistics-"+ indexPrefix +"-{:02d}months-Month{:02d}.tif".format(monthCount, month)
    name = os.path.join(newFold, name)

    writeGeotiff(name, geoTrans, geoproj, stats_param,nodata=np.nan, BandNames=bandDescr, globalDescr="Min_Max_values")

def create_extremes_inrange(mainFoldAdd, newFold, nameIndex, monthCount, vmin, vmax,indexPrefix):
    dateList = get_all_dates(mainFoldAdd, nameIndex)
    dateList.sort()

#    newFold = os.path.join(mainFoldAdd, "Normal PDF")
    if not(os.path.isdir(newFold)):
        os.mkdir(newFold)

    for month in range(1, 13):
        fileNames = []
        for str in dateList:
            yy, mm = get_date(str)
            if mm == month:
                fileNames.append(nameIndex + "_" + str + ".tif")
        compute_extremes_inrange(mainFoldAdd, fileNames, newFold, monthCount, month, vmin, vmax,indexPrefix)


def main():
    with open('VHI_config.json') as jf:
        params = json.load(jf)

        # get NDVIFold tif files
        LSTFold = params["LST_folder"]
        if LSTFold[-1] == os.path.sep:
            LSTFold = LSTFold[:-1]

        LSTNameIndex = params["LST_prefix"]

        monthlyFold = params["LST_Monthly_folder"]

        statsFold = params["LST_Stats_folder"]

        vmin = params["LST_valid_min"]
        vmax = params["LST_valid_max"]

        aggMonths = params["Agg_months"]

        for nmonths in aggMonths:
        # monthly averages
            convert_to_monthly_data(LSTFold, LSTNameIndex, monthlyFold, nmonths)

        # compute min and max in given range
            monthsFold = os.path.join(monthlyFold, "{:d}-Month-Files".format(nmonths))
            create_extremes_inrange(monthsFold, statsFold, LSTNameIndex, nmonths, vmin, vmax,LSTNameIndex)





if __name__ == '__main__':
    main()
else:
    pass