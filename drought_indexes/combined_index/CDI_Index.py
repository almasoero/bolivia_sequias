__author__ = 'lauro'

from geotiff import *
import datetime
import os
from dateutil.relativedelta import *
import matplotlib.pylab as plt
import matplotlib as mpl
#from compressed_pickle import save, load
import numpy as np


def simple_plot_index(a,title="", min = -3,  max= 3,save_img=False,save_dir='.'):
    fig, ax = plt.subplots()
    #cmap='RdBu'
    cmap = mpl.colors.LinearSegmentedColormap.from_list("", ["red","orange","yellow","white","pink","violet", "#0f0f0f"])
    plt.title(title)
    im = plt.imshow(a, interpolation='none',cmap=cmap)
    plt.colormaps()
    # cbar = fig.colorbar(cax,ticks=[-1, 0, 1, 2, 10],orientation='vertical')
    cbar = fig.colorbar(im, orientation='vertical')
    plt.clim(min,max)
    # cbar.ax.set_yticklabels(['< -1', '0', 1, 2,'> 10'])# vertically oriented
    # colorbar
    #ax.format_coord = Formatter(im)
    if save_img:
        os.system("mkdir -p "+save_dir)
        plt.savefig(os.path.join(save_dir,title+'.png'))
    else:
        plt.show()

def main (oDateFrom,oDateTo):

    while (oDateFrom <= oDateTo):

        print (oDateFrom)

        ######## METEO 01

        if INDEX_METEO01=="SPI":
            METEO_prefix01= INDEX_METEO01 + accumulation_METEO01 + "-PERSIANN_"
        elif INDEX_METEO01=="SPEI":
            METEO_prefix01= INDEX_METEO01 + accumulation_METEO01 + "-PERSIANN-MODIS_"

        METEO_file01= os.path.join(products_dir,INDEX_METEO01,oDateFrom.strftime("%Y"),oDateFrom.strftime("%m"),METEO_prefix01+oDateFrom.strftime("%Y%m")+".tif")

        METEO01, xsize, ysize, geotransform, geoproj = readGeotiff(METEO_file01)


        ######## METEO 03

        if INDEX_METEO03=="SPI":
            METEO_prefix03= INDEX_METEO03 + accumulation_METEO03 + "-PERSIANN_"
        elif INDEX_METEO03=="SPEI":
            METEO_prefix03= INDEX_METEO03 + accumulation_METEO03 + "-PERSIANN-MODIS_"

        METEO_file03= os.path.join(products_dir,INDEX_METEO03,oDateFrom.strftime("%Y"),oDateFrom.strftime("%m"),METEO_prefix03+oDateFrom.strftime("%Y%m")+".tif")

        METEO03, xsize, ysize, geotransform, geoproj = readGeotiff(METEO_file03)

        ######## SOIL MOISTURE

        prefix_HUM= INDEX_HUM + accumulation_HUM + "-SMAP_"

        HUM_file= os.path.join(products_dir,INDEX_HUM,oDateFrom.strftime("%Y"),oDateFrom.strftime("%m"),prefix_HUM+oDateFrom.strftime("%Y%m")+".tif")

        HUM, xsize, ysize, geotransform, geoproj = readGeotiff(HUM_file)


        ######## VEGETATION

        prefix_VEG= INDEX_VEG + accumulation_VEG + "-MODIS_" #FAPAR e VHI have the same

        VEG_file= os.path.join(products_dir,INDEX_VEG,oDateFrom.strftime("%Y"),oDateFrom.strftime("%m"),prefix_VEG+oDateFrom.strftime("%Y%m")+".tif")

        VEG, col, row, geotransform, geoproj = readGeotiff(VEG_file)


        watch = (METEO03 < METEO_threshold03)*METEO03/METEO03+ (METEO01 < METEO_threshold01)*METEO01/METEO01

        #simple_plot_index(METEO01,"METEO01_"+oDateFrom.strftime("%Y%m"))
        #simple_plot_index(METEO03,"METEO03_"+oDateFrom.strftime("%Y%m"))
        #simple_plot_index(watch, "METEO01+METEO03_"+oDateFrom.strftime("%Y%m"))

        watch [watch>1] = 1

        warning = watch * (HUM < HUM_threshold) * 2 * HUM/HUM

        alert = watch * (VEG < VEG_threshold) * 3 * VEG/VEG

        data3d = np.zeros((row, col, 3))

        data3d [:,:,0] = watch
        data3d [:,:,1] = warning
        data3d [:,:,2] = alert

        combined = np.nanmax (data3d, axis=2)

        # PLOT combined
        save_img=False
        """
        fig, ax = plt.subplots()
        cmap = mpl.colors.LinearSegmentedColormap.from_list("", ["white","yellow","orange","red","violet"])
        im = plt.imshow(combined, interpolation='none',cmap=cmap)
        title = "CDI-"+INDEX_METEO01+"_"+oDateFrom.strftime("%Y%m")
        plt.title(title)
        cbar = fig.colorbar(im, orientation='vertical')
        plt.colormaps()
        plt.clim(0,4)
        if save_img:
            os.system ("mkdir -p "+png_dir)
            plt.savefig(os.path.join(png_dir,title+'.png'))
        else:
            plt.show()
        """

        # combined drought indicator

        combined_dir = products_dir+"/CDI/"+oDateFrom.strftime("%Y")+"/"+oDateFrom.strftime("%m")
        combined_file = combined_dir+"/CDI-"+INDEX_METEO01+"_"+oDateFrom.strftime("%Y%m")+".tif"

        os.system("mkdir -p " + combined_dir)

        #SAVE GEOTIFF
        writeGeotiff(combined_file, geotransform, geoproj, combined, nodata=np.nan, BandNames="CDI ("+METEO_prefix01+"-based)", globalDescr="Combined Drought Index")

        print(combined_file)

        oDateFrom = oDateFrom +relativedelta(months=+1)
    print('Process ended with success')



if __name__ == "__main__":

    #################################################################

    png_dir = "/home/sequia/drought/png/CDI"
    products_dir = "/home/sequia/drought/products"

    #################################################################

    sDateFrom = '201504'
    oDateFrom = datetime.datetime.strptime(sDateFrom,"%Y%m")

    sDateTo = '202005'
    oDateTo = datetime.datetime.strptime(sDateTo,"%Y%m")

    #################################################################

    INDEX_METEO01="SPEI"    ### SPI, SPEI
    accumulation_METEO01 = "01"
    METEO_threshold01 = -2

    INDEX_METEO03="SPEI"    ### SPI, SPEI
    accumulation_METEO03 = "03"
    METEO_threshold03 = -1

    INDEX_HUM="SSMI"     ### SMI, SWDI, PDSI
    accumulation_HUM = "01"
    HUM_threshold=-1

    INDEX_VEG="FAPAR"      ### FAPAR, VHI, ESI
    accumulation_VEG = "01"
    VEG_threshold=-1


    #################################################################

    main(oDateFrom,oDateTo)
    print('\n' + str(datetime.datetime.now()) + ' - Process ended.\n')
