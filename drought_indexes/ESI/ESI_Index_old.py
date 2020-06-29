import os
import json
import gdal
from shutil import copyfile
import scipy.stats as stat
import numpy
import numpy as np
from geotiff import *
import datetime
from dateutil.relativedelta import *




def calculate_esi_result(fileName, distFileName, destFold, year, month, monthCount):
    # adjust destination folder
    dest_dir = os.path.join(destFold, year, month)
    os.system("mkdir -p "+dest_dir)

    # first copy file to new folder
    newFileName = os.path.join(dest_dir, "ETratio-{:02d}_".format(monthCount)+year+month+".tif"
                               .format(monthCount))
    copyfile(fileName, newFileName)

    # estimate probability corresponding to our distribution and calculate ESI Index

    data3d, col, row, geoTrans, geoproj = readGeotiff (distFileName)
    Alpha = data3d[:,:,0]
    Beta = data3d[:,:,1]

    data, col, row, geoTrans, geoproj = readGeotiff (fileName)

    mask, col, row, geoTrans, geoproj=  readGeotiff("mask_bolivia.tif")

    data = data*mask
    data [data==1] = np.nan

    probVal = stat.beta.cdf(data, Alpha, Beta)
    probVal [probVal==0] = 0.0000001
    probVal [probVal==1] = 0.9999999
    ESI = stat.norm.ppf(probVal, loc=0, scale=1)

    probFileName = os.path.join(dest_dir, "ETratioProb-{:02d}_".format(monthCount) +year+month+ ".tif")
    #probVal[data==1] = np.nan
    writeGeotiffSingleBand(probFileName, geoTrans, geoproj, probVal, nodata=np.nan, BandName="ESI_probability")

    # create geotiff for spei output
    ESIFileName = os.path.join(dest_dir, "ESI{:02d}".format(monthCount)+"-MODIS_" +year+month +".tif")
   # ESI[data==1] = np.nan

    writeGeotiffSingleBand (ESIFileName, geoTrans, geoproj,ESI, nodata=np.nan, BandName="Standardized_ESI")
    print(ESIFileName)

def main():

    with open('ESI_config.json') as jf:
        params = json.load(jf)
        statsFold = params["Stats_folder"]
        if statsFold[-1] == os.path.sep:
            statsFold = statsFold[:-1]
        indexFold = params["Index_folder"]
        if indexFold[-1] == os.path.sep:
            indexFold = indexFold[:-1]
        foldAdd = params["Monthly_folder"]
        if foldAdd[-1] == os.path.sep:
            foldAdd = foldAdd[:-1]
        aggMonths = params["Agg_months"]
        sDateFrom = params["StartDate"]
        sDateTo = params["EndDate"]

        ratioName = params["Ratio_name"]

        oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m")
        oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m")

        while (oDateFrom <= oDateTo):

            year=oDateFrom.strftime("%Y")
            month=oDateFrom.strftime("%m")

            for monthCount in aggMonths:
                fileName = os.path.join(foldAdd, "{:d}-Month-Files".format(monthCount),
                                        ratioName + "_" + oDateFrom.strftime("%Y%m")+".tif")

                distFileName = os.path.join(statsFold, "Beta-ETratio-{:02d}months-Month".format(monthCount)+month+".tif")
                calculate_esi_result(fileName, distFileName, indexFold, year, month, monthCount)

            oDateFrom = oDateFrom +relativedelta(months=+1)


if __name__ == '__main__':
    main()
else:
    pass
