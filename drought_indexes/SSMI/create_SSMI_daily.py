__author__ = 'lauro'

from geotiff import *
import datetime
import os
from dateutil.relativedelta import *
import numpy as np

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

def create_SSMI_daily  (data_dir, sDateFrom, sDateTo, VAR):


    oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m%d")

    oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m%d")

    #VAR = ["snow_mass"]

    #VAR = ["land_fraction_snow_covered","snow_depth","snow_mass"]

    #SMAP_L4_SM_gph_20200101T0130_Vv4030_001_land_fraction_snow_covered

    while (oDateFrom <= oDateTo):


            #print (oDateFrom)

            yy=oDateFrom.strftime("%Y")
            mm=oDateFrom.strftime("%m")
            dd=oDateFrom.strftime("%d")

            for i in range(0, len(VAR)):


                folder = os.path.join(data_dir,yy,mm,dd)

                #allFiles = [x[2] for x in os.walk(folder)]

                if not os.path.exists(folder):

                    print ("Missing: "+folder)

                    continue

                allFiles = os.listdir(folder)

                data, col, row, geoTrans, geoproj = readGeotiff ("mask_bolivia.tif")

                data3d = np.zeros((row, col, 8)) *np.nan

                ii=0

                for file in allFiles:

                    if file.endswith(VAR[i]+".tif"):

                        try:

                            data, col, row, geoTrans, geoproj = readGeotiff (os.path.join(data_dir, yy,mm,dd,file))

                        except:

                            print ("problems in reading: "+ os.path.join(data_dir, yy,mm,dd,file))

                            continue

                        data3d [:,:,ii] = data

                        #simple_plot_index(data)

                        ii += 1

                if ii>0:

                    data_mean = np.nanmean(data3d,axis=2)

                    #simple_plot_index(data_mean)

                    os.system("mkdir -p "+os.path.join(data_dir, "daily", yy,mm,dd))

                    outFileName= os.path.join(data_dir, "daily", yy,mm,dd,"SMAP-"+VAR[i].replace("_", "-") +"_"+yy+mm+dd+".tif")

                    print (outFileName)

                    writeGeotiffSingleBand(outFileName, geoTrans, geoproj, data_mean,nodata=np.nan, BandName="Daily_SMAP_"+VAR[i])

                    ii=0

            oDateFrom = oDateFrom + relativedelta(days=+1)


if __name__ == '__main__':
    #argv=sys.argv[1:]
    #main(argv)

    #data_dir = "/home/sequia/drought/data/SMAP/processed/snow"
    #data_dir = "/Users/lauro/Downloads/drought/data/SMAP/processed/snow"

    sDateFrom = '20191201'
    oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m%d")

    sDateTo = '20200101'
    oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m%d")

    VAR = ["snow_mass"]


    create_SSMI_daily  (products_dir, sDateFrom, sDateTo, VAR)

else:
    pass