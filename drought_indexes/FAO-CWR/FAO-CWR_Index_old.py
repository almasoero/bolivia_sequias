import os
import json
import datetime
import numpy as np
from dateutil.relativedelta import *
from calendar import monthrange
from geotiff import *
import calendar
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

def convert_to_monthly_data (oDateFrom, oDateTo,PETfold, PETprefix, indexFold, monthCount,indexPrefix,sourcePrefix):

    """ in this case we don't use monthly fold

    monthlyFoldAggr = os.path.join(indexFold, PETprefix+"-Monthly-Files", "{:d}-Month-Files".format(monthCount))

    if os.path.isdir(monthlyFoldAggr):
        rmtree(monthlyFoldAggr)

    os.system("mkdir -p "+monthlyFoldAggr)

    """

    dateList = get_all_dates(PETfold, PETprefix)
    dateList.sort()

    dateListMonths = [i[0:6] for i in dateList ]

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
            convert_to_month_average_data(indexFold,PETfold, PETprefix, dateList, month, year, monthCount,indexPrefix,sourcePrefix)
            #dateListMonths.append(oDate.strftime("%Y%m"))
        else:
            print ("Missing data for : "+ oDate.strftime("%Y%m"))

        oDate = oDate +relativedelta(months=+1)

def convert_to_month_average_data(indexFold,PETfold, PETprefix, dateList,month, year, monthCount, indexPrefix,sourcePrefix):
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

    calculate_monthly_PET_FAOCWR(indexFold, PETfold, PETprefix, dateCountDic, year, month,indexPrefix,monthCount,sourcePrefix)

def calculate_monthly_PET_FAOCWR(indexFold, PETfold, PETprefix, dateCountDic, year, month,indexPrefix,monthCount,sourcePrefix):

    maskPotato , col, row, geoTrans, geoproj = readGeotiff ("../support_geofiles/potatos_bolivia500m.tif")

    maskPotato [maskPotato==0] =np.nan

    data3d = np.zeros((row, col, len (dateCountDic)))

    for i, key in enumerate(dateCountDic):
        #daFold = os.path.join(foldAdd, key[0:4], key[4:6], key[6:8])
        fileName = os.path.join(PETfold, key[0:4], key[4:6], key[6:8],PETprefix + "_" + key + ".tif")
        data , col, row, geoTrans, geoproj = readGeotiff (fileName)
        #simple_plot_index(data,key)
        data3d [:,:,i] = data

    data_mean = np.nanmean(data3d,axis=2)/8


    #simple_plot_index(data_mean,"MEAN")

    factor = 1.1 / 1.2

    FAOCWR_mm = data_mean * factor * maskPotato

    totDaysInMonth = calendar.monthrange(int(year),int(month))[1]

    # conver daily FAOCWR [mm] into monthly cumulate FAOCWR [m3/ha]

    FAOCWR_m3_ha = FAOCWR_mm  * 10 # *totDaysInMonth

    os.system("mkdir -p "+os.path.join(indexFold, year, month))

    #simple_plot_index(FAOCWR_m3_ha,"FAO - Crop Water Requirement [m3/ha] - "+year+ month)

    outFileNamePET= os.path.join(indexFold,year, month, PETprefix + "{:02d}-".format(monthCount)+sourcePrefix+"_"+year+month+".tif")

    outFileNameFAO= os.path.join(indexFold,year, month, indexPrefix + "{:02d}-".format(monthCount)+sourcePrefix+"_"+year+ month+".tif")

    print (outFileNamePET)
    writeGeotiff(outFileNamePET, geoTrans, geoproj, data_mean,nodata=np.nan, BandNames="PET500m_monthly",globalDescr="PET500m_monthly")

    print (outFileNameFAO)
    writeGeotiff(outFileNameFAO, geoTrans, geoproj, FAOCWR_m3_ha, nodata=np.nan, BandNames="FAO_CWR_500m_monthly",globalDescr="PET500m_monthly")


def main():


    with open('FAO-CWR_config.json') as jf:
        params = json.load(jf)

        # get PET tif files
        PETfold = params["PET_folder"]
        if PETfold[-1] == os.path.sep:
            PETfold = PETfold[:-1]

        PETprefix = params["PET_prefix"]

        indexFold = params["Index_folder"]
        if indexFold[-1] == os.path.sep:
            indexFold = indexFold[:-1]

        indexPrefix = params["Index_prefix"]

        sDateFrom = params["StartDate"]
        sDateTo = params["EndDate"]

        sourcePrefix = params["Source_prefix"]

        aggMonths = params["Agg_months"]

        oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m")
        oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m")

        while (oDateFrom <= oDateTo):

            for monthCount in aggMonths:

            # monthly averages
                convert_to_monthly_data(oDateFrom, oDateTo, PETfold, PETprefix, indexFold, monthCount,indexPrefix,sourcePrefix)

            oDateFrom = oDateFrom +relativedelta(months=+1)

if __name__ == '__main__':
    main()
else:
    pass