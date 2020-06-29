import os
import json
import datetime
import scipy.stats as stat
import numpy as np
from dateutil.relativedelta import *
from calendar import monthrange
from geotiff import *

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

    #allFiles.sort()

    # get dates from file names
    count = len(nameIndex)
    result = []
    for str in allFiles:
        if len(str) > 0:
            for stf in str:
                if nameIndex in stf:
                    #if "200405" in stf:print(stf)
                    date=stf.split('_')[1].split(".")[0]
                    result.append(date)

    result.sort()
    return result

def get_same_values(first, second):
    same = [f for f in first if f in second]
    return same


def diff_date_str(curDate, refDate):
    dateVal = datetime.datetime.strptime(curDate, "%Y%m%d").date()
    refDateVal = datetime.datetime.strptime(refDate, "%Y%m%d").date()
    return (dateVal - refDateVal).days

def convert_to_monthly_data (snowFold, snowPrefix, indexFold, monthCount,indexPrefix):

    dateList = get_all_dates(snowFold, snowPrefix)
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
        year = oDate.strftime("%Y")
        month = oDate.strftime("%m")

        if oDate.strftime("%Y%m")  in dateListMonths:
            convert_to_month_average_data(indexFold,snowFold, snowPrefix, dateList, month, year, monthCount,indexPrefix)
            #dateListMonths.append(oDate.strftime("%Y%m"))
        else:
            print ("Missing data for : "+ oDate.strftime("%Y%m"))

        oDate = oDate +relativedelta(months=+1)

def convert_to_month_average_data(indexFold,snowFold, snowPrefix, dateList,month, year, monthCount, indexPrefix):
    dateCountDic = dict()
    for i in range(monthCount):
        yy = int(year)
        mm = int(month) - i
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

    calculate_monthly_average(indexFold, snowFold, snowPrefix, dateCountDic, year, month,indexPrefix,monthCount)

def calculate_monthly_average(indexFold, PETfold, PETprefix, dateCountDic, year, month,indexPrefix,monthCount):

    maskSnow , col, row, geoTrans, geoproj = readGeotiff ("mask_bolivia.tif")

    #maskSnow [maskSnow==0] =np.nan

    data3d = np.zeros((row, col, len (dateCountDic)))

    for i, key in enumerate(dateCountDic):
        #daFold = os.path.join(foldAdd, key[0:4], key[4:6], key[6:8])
        fileName = os.path.join(PETfold, key[0:4], key[4:6], key[6:8],PETprefix + "_" + key + ".tif")
        data , col, row, geoTrans, geoproj = readGeotiff (fileName)
        #simple_plot_index(data,key)
        data3d [:,:,i] = data

    data_mean = np.nanmean(data3d,axis=2)

    outFileNamePET= os.path.join(indexFold, year, month, PETprefix +"{:02d}_".format(monthCount)+year+month+".tif")

    data_mean [data_mean>1]=np.nan


    os.system("mkdir -p "+os.path.join(indexFold, year,month))

    #simple_plot_index(data_mean,"NSDI  mean")

    print (outFileNamePET)
    writeGeotiff(outFileNamePET, geoTrans, geoproj, data_mean,nodata=np.nan, BandNames="Soil_moisture",globalDescr="NDSI500m_monthly")


def create_statistics(indexFold, statFold, indexPrefix, monthCount,PETprefix):
    dateList = get_all_dates(indexFold, PETprefix+"{:02d}".format(monthCount))
    dateList.sort()
#    newFold = os.path.join(mainFoldAdd, "Normal PDF")
    if not(os.path.isdir(statFold)):
        os.system ("mkdir -p "+statFold)

    for month in range(1, 13):
        fileNames = []
        for date in dateList:
            yy = date[0:4]
            mm = date[4:6]
            if int(mm) == month:
                fileNames.append(os.path.join(indexFold,yy,mm,PETprefix+"{:02d}_".format(monthCount) + date + ".tif"))

        compute_statistics (indexFold, fileNames, statFold, monthCount, month,indexPrefix)


def compute_statistics(indexFold, fileNames, statFold, monthCount, month, indexPrefix):
    print("Create statistics GeoTiff for {:d} months from month {:02d}".
          format(monthCount, month))


    maskSnow , col, row, geoTrans, geoproj = readGeotiff ("mask_bolivia.tif")

    data3d = np.zeros((row,col,len(fileNames))) * np.nan

    for i, f in enumerate(fileNames):

        data , col, row, geoTrans, geoproj = readGeotiff (os.path.join(indexFold,f))

        data3d [:,:,i]= data

        #simple_plot_index(data)

    distr_param =np.zeros((row,col,4))*np.nan

    nameParams  = [None] * 4

    invalid_pixels = 0

    data_mean = np.nanmean(data3d, axis=2, dtype=np.float32)
    data_var = np.nanvar(data3d, axis=2, dtype=np.float32)

    """
    ra = data_max - data_min
    mu = (data_mean - data_min)/ra
    va = data_var/ra/ra
    ab = mu*(1 - mu)/va - 1
    fit_alpha = mu*ab
    fit_beta = (1 - mu)*ab
    """

    fit_alpha  = (data_mean*data_mean) * (1 - data_mean) / data_var  - data_mean

    fit_beta = (data_mean * (1-data_mean) / data_var - 1 ) * (1 - data_mean)

    distr_param[:,:,0] = fit_alpha
    distr_param[:,:,1] = fit_beta
    distr_param[:,:,2] = np.zeros_like(fit_beta)
    distr_param[:,:,3] = np.zeros_like(fit_beta)+1

    ks_test = True

    if ks_test:

        for i in range(row):
            for j in range(col):

                if sum(np.isnan(data3d[i,j,:])) ==len(fileNames):
                    continue

                d1d = data3d[i,j,:]

                dpd = d1d[np.where(d1d> 0)]  # only non null values

                try:
                    #print (dpd)
                    fit = (fit_alpha[i,j], fit_beta[i,j] , 0, 1)
                    max_distance, p_value = stat.kstest(dpd,"beta",args=fit)
                    #print("Kolmogorov-Smirnov test for goodness of fit: "+str(round(p_value*100))+"%, max distance: "+str(max_distance))

                except:
                    print("Distribution fitting failed... ")
                    continue


                if p_value < 0.6:

                    invalid_pixels += 1

                    fit_alpha[i,j] = np.nan

                    fit_beta[i,j]  = np.nan

                    #print("Kolmogorov-Smirnov test for goodness of fit: "+str(round(p_value*100))+"%, max distance: "+str(max_distance))

    nameParams [0]= "a"
    nameParams [1]= "b"
    nameParams [2]= "loc"
    nameParams [3]= "scale"


    print ("Invalid pixel: " + str(round(invalid_pixels/(row*col)*100))+"%")
    name = "Statistics-"+ indexPrefix +"-{:02d}months-Month{:02d}.tif".format(monthCount, month)
    fileStatsOut = os.path.join(statFold, name)

    writeGeotiff(fileStatsOut,geoTrans, geoproj,distr_param, nodata=np.nan, BandNames=nameParams
                 ,globalDescr = "NDSI_distr_param_a_b_loc_scale_P0")


def main():


    with open('SSMI-SMAP_config.json') as jf:
        params = json.load(jf)

        # get PET tif files
        snowFold = params["Snow_folder"]
        if snowFold[-1] == os.path.sep:
            snowFold = snowFold[:-1]

        snowPrefix = params["Snow_prefix"]

        indexFold = params["Index_folder"]
        if indexFold[-1] == os.path.sep:
            indexFold = indexFold[:-1]

        indexPrefix = params["Index_prefix"]

        statFold = params["Stats_folder"]
        if statFold[-1] == os.path.sep:
            statFold = statFold[:-1]

        aggMonths = params["Agg_months"]


        for monthCount in aggMonths:

                convert_to_monthly_data(snowFold, snowPrefix, indexFold, monthCount,indexPrefix)

                create_statistics(indexFold, statFold, indexPrefix, monthCount, snowPrefix)


if __name__ == '__main__':
    main()
else:
    pass