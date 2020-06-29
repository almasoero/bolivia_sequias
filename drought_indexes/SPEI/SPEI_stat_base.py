import os, sys, getopt
import json
import datetime
from shutil import copyfile, rmtree
import numpy as np
from dateutil.relativedelta import *
from calendar import monthrange
from geotiff import *
from lmoments3 import distr
import scipy.stats as stat


def get_all_dates(foldAdd, nameIndex):
    # remove path separator from end of folder address
    if foldAdd[-1] == os.path.sep:
        foldAdd = foldAdd[:-1]

    # get list of all files
    allFiles = [x[2] for x in os.walk(foldAdd)]

    print (allFiles)

    # get dates from file names
    count = len(nameIndex)
    result = []
    for str in allFiles:
        if len(str) > 0:
            for stf in str:
                if nameIndex in stf:
                    date=stf.split('_')[1].split(".")[0]
                    #date = stf[count+1:count+9]
                    print(stf)
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

    return dateListMonths

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

    # do not use "calculate_weighted_average" because it is

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

    if nameIndex == "MODIS-PET":
        data_mean = np.nanmean(data3d,axis=2)/8
        BandName="Potential_Evap"
    else:
        data_mean = np.nanmean(data3d,axis=2)
        BandName="Prec_accumulation"
    outFileName= os.path.join(newFold, nameIndex + "_" +"{:4d}{:02d}.tif".format(year, month))

    #simple_plot_index(data_mean)
    print (outFileName)
    writeGeotiffSingleBand(outFileName, geoTrans, geoproj, data_mean,nodata=np.nan, BandName=BandName)


def create_statistics(mainFoldAdd, newFold, nameIndex, monthCount):
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
        compute_statistics (mainFoldAdd, fileNames, newFold, monthCount, month)


def compute_statistics(foldAdd, fileNames, newFold, monthCount, monthStart):
    print("Create statistics GeoTiff for {:d} months from month {:02d}".
          format(monthCount, monthStart))

    mask, col, row, geoTrans, geoproj=  readGeotiff("mask_bolivia.tif")

    data3d = np.zeros((row,col,len(fileNames)))*np.nan

    print ("Loading monthly data of P/PET ratio ..." )

    for i, f in enumerate(fileNames):

        data , col, row, geoTrans, geoproj = readGeotiff (os.path.join(foldAdd,f))
        data3d [:,:,i]= data

    distr_param =np.zeros((row,col,3))*np.nan

    invalid_pixels = 0

    for i in range(row):
        for j in range(col):

            array = data3d[i,j,:]
            array = array[np.logical_not(np.isnan(array))]
            #fit = stat.genextreme.fit(data3d[i,j,:], loc=0, scale = 1)  #loc initial guess
            if len(array) < 4:
                continue
            fit_dict = distr.gev.lmom_fit(data3d[i,j,:])
            fit = (fit_dict['c'],fit_dict['loc'],fit_dict['scale'])
            #print (fit)
            max_distance, p_value = stat.kstest(array,"genextreme",args=fit)
            #print("Kolmogorov-Smirnov test for goodness of fit: "+str(round(p_value*100))+"%, max distance: "+str(max_distance))
            if p_value < 0.5:
                invalid_pixels += 1
                continue
#
            distr_param [i,j,0]  = fit[0]
            distr_param [i,j,1]  = fit[1]
            distr_param [i,j,2]  = fit[2]

    print ("Invalid pixels: " + str(round(invalid_pixels/(row*col)*100))+"%")

    name = "Statistics-Prec-PET-{:02d}months-Month{:02d}.tif".format(monthCount, monthStart)
    name = "Statistics-Prec-PET-{:02d}months-Month{:02d}.tif".format(monthCount, monthStart)
    fileStatsOut = os.path.join(newFold, name)

    writeGeotiff(fileStatsOut,geoTrans, geoproj,distr_param, nodata=np.nan, BandNames=list(fit_dict.keys()),globalDescr = "SPEI_distr_param_c_loc_scale")



def get_same_values(first, second):
    same = [f for f in first if f in second]
    return same

def convertPrec_to_monthly_data (PrecFold, PrecNameIndex, PrecmonthlyFold, nmonths):

    dateListPrec = get_all_dates(PrecFold, PrecNameIndex)

    oDateFrom = datetime.datetime.strptime(dateListPrec[0],"%Y%m%d")
    oDateTo =   datetime.datetime.strptime(dateListPrec[-1],"%Y%m%d")

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

    return dateListMonths

    return dateListPrec

def computePrec_PET (dateListSPEI, Prec_PETmonthlyFold , PETmonthlyFold,  PrecmonthlyFold, PETNameIndex, PrecNameIndex, nmonths):

    for date in dateListSPEI:
        filePET = os.path.join (PETmonthlyFold, "{:d}-Month-Files".format(nmonths), PETNameIndex+ "_" + date + ".tif")
        filePrec = os.path.join (PrecmonthlyFold, "{:d}-Month-Files".format(nmonths), PrecNameIndex+ "_" + date + ".tif")

        PET , col, row, geoTrans, geoproj = readGeotiff (filePET)

        Prec , col, row, geoTrans, geoproj = readGeotiff (filePrec)

        Prec_PET = Prec - PET

        months_file_dir = os.path.join (Prec_PETmonthlyFold, "{:d}-Month-Files".format(nmonths))

        os.system("mkdir -p "+months_file_dir)

        filePrec_PET = os.path.join (months_file_dir, "Prec-PET"+ "_" + date + ".tif")

        writeGeotiffSingleBand (filePrec_PET, geoTrans, geoproj, Prec_PET,nodata=np.nan, BandName="Prec_accumulation")
        print("saving:  "+filePrec_PET)

    return


def main(argv):
    with open('SPEI_config.json') as jf:
        params = json.load(jf)

        # get FAPARFold tif files
        PETFold = params["PET_folder"]
        if PETFold[-1] == os.path.sep:
            PETFold = PETFold[:-1]

        PrecFold = params["Prec_folder"]
        if PrecFold[-1] == os.path.sep:
            PrecFold = PrecFold[:-1]

        IndexFold = params["Index_folder"]
        if PrecFold[-1] == os.path.sep:
            PrecFold = PrecFold[:-1]

        SPEINameIndex = params["Index_prefix"]
        PETNameIndex = params["PET_prefix"]
        PrecNameIndex = params["Prec_prefix"]

        PrecPETNameIndex = params["Prec-PET_prefix"]

        statsFold = params["Stats_folder"]

        aggMonths = params["Agg_months"]
        
        stats = True

        opts, a1Args = getopt.getopt(argv,"hn",["help","nostats"])

        for opt, arg in opts:
            if opt in ("-n", "--nostats"):
                stats = False
        
        PETmonthlyFold = os.path.join(IndexFold,PETNameIndex+"-Monthly-Files")
        PrecmonthlyFold = os.path.join(IndexFold,PrecNameIndex+"-Monthly-Files")
        PrecPETmonthlyFold = os.path.join (IndexFold,PrecPETNameIndex+"-Monthly-Files")

        for nmonths in aggMonths:

            # monthly averages

            convert_to_monthly_data(PETFold, PETNameIndex, PETmonthlyFold, nmonths)#,PETNameIndex)

            convert_to_monthly_data(PrecFold, PrecNameIndex, PrecmonthlyFold, nmonths)#,PrecNameIndex)

            dateListPET = get_all_dates(os.path.join(PETmonthlyFold,str(nmonths)+"-Month-Files"),PETNameIndex)

            dateListPrec = get_all_dates(os.path.join(PrecmonthlyFold,str(nmonths)+"-Month-Files"),PrecNameIndex)

            dateListSPEI = get_same_values(dateListPET,dateListPrec)

            computePrec_PET (dateListSPEI, PrecPETmonthlyFold , PETmonthlyFold,  PrecmonthlyFold, PETNameIndex, PrecNameIndex, nmonths)

            monthsFold = os.path.join(PrecPETmonthlyFold, "{:d}-Month-Files".format(nmonths))

            if stats:

            	create_statistics(monthsFold, statsFold, PrecPETNameIndex, nmonths)

if __name__ == '__main__':
    argv=sys.argv[1:]
    main(argv)
else:
    pass