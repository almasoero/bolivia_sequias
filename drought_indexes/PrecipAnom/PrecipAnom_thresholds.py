import os
import json
from shutil import copyfile
import numpy as np
from geotiff import *
from dateutil.relativedelta import *
import matplotlib.pylab as plt
import matplotlib as mpl
import scipy.stats as stat
from lmoments3 import distr

import matplotlib.pylab as plt
import matplotlib as mpl
import pandas as pd


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

def calculate_result(statsFold, monthCount):

    df_geo = pd.read_csv(os.path.join("../support_geofiles/MacroReg.csv"),delimiter=";")



    for SPI_level in [-2,-1.5,-1]:

        print ("Anomalia de precipitacion [mm/day] correspondiente a SPI = "+str(SPI_level))

        for month in range (1,13):

            month = "{:02d}".format(month)

            statsFileName = os.path.join(statsFold,"Statistics-PERSIANN-{:02d}months-Month".format(monthCount))+month+".tif"

            data3d, col, row, geoTrans, geoproj = readGeotiff (statsFileName)

            shape = data3d[:,:,0]
            loc = data3d[:,:,1]
            scale = data3d[:,:,2]
            P0 = data3d[:,:,3]

            SPI = np.ones((row,col)) * SPI_level

            probVal = stat.norm.cdf(SPI, loc=0, scale=1)

            if month in ["07","08"]:

                simple_plot_index(probVal,(month))
                print (np.nanmax(P0))

            probVal = (probVal- P0 / 2) / (1 - P0)

            probVal[probVal<=0]=0.0001

            if month in ["07","08"]: simple_plot_index(probVal,(month))
            if month in ["07","08"]: simple_plot_index(P0,"P0   "+(month))


            data = distr.gam.ppf(probVal, a=shape, loc=loc, scale=scale)

            mean = distr.gam.mean (a=shape, loc=loc, scale=scale)

            trhesholdAnom = data - mean


            #simple_plot_index(mean,str(month))

            geo_arr, col, row, geoTrans, geoproj=  readGeotiff("../support_geofiles/Macroregions_1_24.tif")

            anom_values =[]

            for idx, dGeo in enumerate(df_geo['ID']):

                index_mean = np.nanmean(trhesholdAnom[geo_arr == dGeo])
                anom_values.append(round(index_mean,2))

                #print (df_geo.at[idx,"MacroReg"]+": "+str(round(index_mean,2)))

            df_geo[str(month)] = anom_values

        df_geo.to_csv("SPI{:02d}_thresholds_".format(monthCount)+str(SPI_level)+".csv",index=False)

                # create geotiff for spei output
    #outFileName = os.path.join(dest_dir, indexPrefix+"{:02d}".format(monthCount)+"-"+PrecNameIndex+"_" +month +".tif")
   # ESI[data==1] = np.nan
    #writeGeotiffSingleBand (outFileName, geoTrans, geoproj,PrecAnom, nodata=np.nan, BandName="Precipitation_anomaly")
    #print ("saving... " + outFileName)

def main():

    with open('PrecipAnom_config.json') as jf:

        params = json.load(jf)

        statsFold = params["Stats_folder"]
        if statsFold[-1] == os.path.sep:
            statsFold = statsFold[:-1]


        aggMonths = params["Agg_months"]


        for monthCount in aggMonths:

                calculate_result(statsFold, monthCount)


if __name__ == '__main__':
    main()
else:
    pass
