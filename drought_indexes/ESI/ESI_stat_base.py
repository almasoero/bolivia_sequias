import os, sys, getopt
import json
import gdal
import subprocess
import datetime
from shutil import rmtree
import string
import scipy.stats as stat
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
                    result.append(date)

    result.sort()
    return result


def get_same_values(first, second):
    same = [f for f in first if f in second]
    return same

def calculate_all_ratio(etFold, petFold, dates, etNameInd, petNameInd, outputFold, ratioNameInd):

    for dateStr in dates:
        daetFold = os.path.join(etFold, dateStr[0:4], dateStr[4:6], dateStr[6:8])
        dapetFold = os.path.join(petFold, dateStr[0:4], dateStr[4:6], dateStr[6:8])
        etFileName = os.path.join(daetFold, etNameInd + "_" + dateStr + ".tif")
        petFileName = os.path.join(dapetFold, petNameInd + "_" + dateStr + ".tif")
        ratioFileName = os.path.join(outputFold, ratioNameInd + "_" + dateStr + ".tif")
        calculate_one_ratio(etFileName, petFileName, ratioFileName)

def calculate_one_ratio_old(firstName, secondName, resultName):
    args = ["gdal_calc.py"]
    args.extend(["-A", firstName, "-B", secondName, "--outfile=" + resultName])
    # args.append("--calc=A/B")
    # args.append("--calc=A/((B==0) * A + (B>0) * B + (B<0) * B)")
    # args.append("--calc=A/((B==0) * A + ((B>0) + (B<0)) * B)")
    args.append("--calc= (A==0) * 0 + ((A > 0) + (A < 0)) *"
                " (A + (B==0)*1)/((B==0) * (A+1) + ((B>0) + (B<0)) * B)")

    print (args)
    subprocess.run(args)

def calculate_one_ratio(firstName, secondName, resultName):

    ET , col, row, geoTrans, geoproj = readGeotiff (firstName)
    PET, col, row, geoTrans, geoproj = readGeotiff (secondName)

    ratio = ET/PET

    ratio[ratio>1] = 1

    writeGeotiffSingleBand(resultName, geoTrans, geoproj, ratio,nodata=np.nan, BandName="ET_daily_ratio")
    print(resultName)

def diff_date_str(curDate, refDate):
    dateVal = datetime.datetime.strptime(curDate, "%Y%m%d").date()
    refDateVal = datetime.datetime.strptime(refDate, "%Y%m%d").date()
    return (dateVal - refDateVal).days

def convert_to_monthly_data(foldAdd, nameIndex, tempFold, monthCount):
    newFold = os.path.join(tempFold, "{:d}-Month-Files".format(monthCount))

    if os.path.isdir(newFold):    #!!!!!!!!!! DEBUG
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
        #daFold = os.path.join(foldAdd, key[0:4], key[4:6], key[6:8])
        fileName = os.path.join(foldAdd, nameIndex + "_" + key + ".tif")
        data , col, row, geoTrans, geoproj = readGeotiff (fileName)
        #simple_plot_index(data)
        data3d [:,:,i] = data

    data_mean = np.nanmean(data3d,axis=2)

    data_mean[data_mean>1]=1

    outFileName= os.path.join(newFold, nameIndex + "_" +"{:4d}{:02d}.tif".format(year, month))

    #simple_plot_index(data_mean)
    print (outFileName)
    writeGeotiffSingleBand(outFileName, geoTrans, geoproj, data_mean,nodata=np.nan, BandName="ET_monthly_ratio")


def calculate_weighted_averge(foldAdd, nameIndex, dateCountDic, newFold, year, month):
    alphabetList = list(string.ascii_uppercase)
    args = ["gdal_calc.py"]
    calcStr = "--calc=("
    sumValue = 0
    for i, key in enumerate(dateCountDic):
        fileName = os.path.join(foldAdd, nameIndex + "_" + key + ".tif")
        args.append("-" + alphabetList[i])
        args.append(fileName)
        calcStr += alphabetList[i] + "*" + str(dateCountDic[key])
        sumValue += dateCountDic[key]
        if i == len(dateCountDic) - 1:
            calcStr += ")"
        else:
            calcStr += "+"
    calcStr += "/" + str(sumValue*8) # original data unit measure mm / 8days
    print(calcStr)
    outFileName= os.path.join(newFold, nameIndex + "_" +
                              "{:4d}{:02d}.tif".format(year, month))
    args.append("--outfile=" + outFileName)
    args.append(calcStr)
    print (args)
    subprocess.run(args)


def refine_distribution_input(data):
    ok = False
    for i in range(1, len(data)):
        if data[i] != data[0]:
            ok = True
            break

    if not ok:
        ep = 0.00001
        for i in range(0, len(data)):
            if i % 2 == 0:
                data[i] -= ep
            else:
                data[i] += ep
            if data[i] <= 0:
                data[i] = ep / 2
            elif data[i] >= 1:
                data[i] = 1 - ep / 2

    return data

def calculate_beta_distribution(foldAdd, fileNames, newFold, monthCount, monthStart, fit_Type,nameIndex):


    print("Create GeoTiff for {:d} months from month {:02d}".
          format(monthCount, monthStart))

    betaDistAlpha = []
    betaDistBeta = []
    data = []


    for str in fileNames:
        file = os.path.join(foldAdd, str)
        dataSet = gdal.Open(file)
        #arr = dataSet.GetRasterBand(1).ReadAsArray()
        arr , col, row, geoTrans, geoproj = readGeotiff (file)
        data.append(arr)
        del dataSet


    ep = 0.001
    for i in range(row):
        alphaArr = []
        betaArr = []
        for j in range(col):
            temp = []
            for k in range(len(data)):
                # refine data if required
                val = data[k][i][j]
                if val <= 0:
                    val = 0 + ep
                elif val >= 1:
                    val = 1 - ep
                temp.append(val)

            temp = refine_distribution_input(temp)
#            print(temp)
            if "M" in fit_Type:

                tmea = np.nanmean(temp)
                tvar = np.nanvar(temp)
                ab = tmea * (1 - tmea) / tvar - 1
                alpha = tmea * ab
                beta = (1 - tmea) * ab
            else:
                result = stat.beta.fit(temp, floc=0, fscale=1)
                alpha = result[0]
                beta = result[1]
            alphaArr.append(alpha)
            betaArr.append(beta)
        betaDistAlpha.append(alphaArr)
        betaDistBeta.append(betaArr)

    name = "Beta-ETratio-{:02d}months-Month{:02d}.tif".format(monthCount, monthStart)
    name = os.path.join(newFold, name)

    betaDist = np.zeros((row,col,2))
    betaDist[:,:,0]= np.asarray(betaDistAlpha)
    betaDist[:,:,1]= np.asarray(betaDistBeta)

    bandsNames = ["alpha","beta"]

    writeGeotiff(name, geoTrans, geoproj, betaDist,nodata=np.nan, BandNames=bandsNames, globalDescr="Beta_distribution")

def create_beta_distribution(mainFoldAdd, newFold, ratioName, monthCount, fit_Type,nameIndex):
    dateList = get_all_dates(mainFoldAdd, ratioName)
    dateList.sort()

#    newFold = os.path.join(mainFoldAdd, "Normal PDF")
    if not(os.path.isdir(newFold)):
        os.mkdir(newFold)

    for month in range(1, 13):
        fileNames = []
        for str in dateList:
            mm = int(str[4:6])
            if mm == month:
                fileNames.append(ratioName + "_" + str + ".tif")
        calculate_beta_distribution(mainFoldAdd, fileNames, newFold, monthCount, month, fit_Type, nameIndex)


def main(argv):
    with open('ESI_config.json') as jf:
        params = json.load(jf)

        # get ET tif files
        etFold = params["ET_folder"]
        if etFold[-1] == os.path.sep:
            etFold = etFold[:-1]
        etNameIndex = params["ET_prefix"]
        etDates = get_all_dates(etFold, etNameIndex)

        # get PET tif files
        petFold = params["PET_folder"]
        if petFold[-1] == os.path.sep:
            petFold = petFold[:-1]
        petNameIndex = params["PET_prefix"]
        petDates = get_all_dates(petFold, petNameIndex)

        # get shared dates
        sameDates = get_same_values(petDates, etDates)
        print("Total number of tif files with same dates is", len(sameDates))

        # create path  values
        monthlyFold = params["Monthly_folder"]
        if monthlyFold[-1] == os.path.sep:
            monthlyFold = monthlyFold[:-1]

        ratioFold = params["Ratio_folder"]
        if ratioFold[-1] == os.path.sep:
            ratioFold = ratioFold[:-1]
        os.system("mkdir -p "+ratioFold)

        aggMonths = params["Agg_months"]
        statsFold = params["Stats_folder"]
        fit_Type = params["Fit_type"]

        ratioName = params["Ratio_name"]

        stats = True

        opts, a1Args = getopt.getopt(argv,"hn",["help","nostats"])

        for opt, arg in opts:
            if opt in ("-n", "--nostats"):
                stats = False

        # calculate ET/PET
        calculate_all_ratio(etFold, petFold, sameDates, etNameIndex,petNameIndex, ratioFold, ratioName)


        for nmonths in aggMonths:

            # monthly averages
            convert_to_monthly_data(ratioFold, ratioName , monthlyFold, nmonths)

            monthsFold = os.path.join(monthlyFold, "{:d}-Month-Files".format(nmonths))

            # fit Beta distribution
            if stats:
                create_beta_distribution(monthsFold, statsFold, ratioName, nmonths, fit_Type, nameIndex="ESI")

if __name__ == '__main__':
    argv=sys.argv[1:]
    main(argv)
else:
    pass