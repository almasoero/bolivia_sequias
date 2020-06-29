import os

import csv

import scipy.stats as stats

import jaydebeapi
from datetime import date
import operator
import json
import numpy
from sp_class import *


def create_header_row_gamtable():
    row = []
    row.append("code")
    row.append("start")
    row.append("end")
    row.append("dens")
    for month in range(1, 13):
        row.append("GamP1_{0:02d}".format(month))
        row.append("GamP2_{0:02d}".format(month))
        row.append("P0_{0:02d}".format(month))
    return row

def create_data_row_gamtable(sObj, gamPar):
    row = []
    row.append(sObj.code)
    row.append(sObj.startYear)
    row.append(sObj.endYear)
    row.append(sObj.dens)
    for i in range(12):
        row.append(gamPar[i][0])
        row.append(gamPar[i][2])
        row.append(gamPar[i][3])
    return row

def create_csv_gamtable(fileName, sList, monthCount):
    with open(fileName, mode='w') as csvFile:
        writer = csv.writer(csvFile, delimiter=',')
        writer.writerow(create_header_row_gamtable())
        for spObj in sList:
            dataRow = []
            if monthCount == 1:
                dataRow = create_data_row_gamtable(spObj, spObj.M1GamPar)
            elif monthCount == 2:
                dataRow = create_data_row_gamtable(spObj, spObj.M2GamPar)
            elif monthCount == 3:
                dataRow = create_data_row_gamtable(spObj, spObj.M3GamPar)
            elif monthCount == 6:
                dataRow = create_data_row_gamtable(spObj, spObj.M6GamPar)
            elif monthCount == 12:
                dataRow = create_data_row_gamtable(spObj, spObj.M12GamPar)
            writer.writerow(dataRow)


if __name__ == '__main__':
    # start main program
    print("Hello world")

    jsoname = 'SPI_station_config.json'
    with open(jsoname) as jf:
        params = json.load(jf)
        dbFileName = params["DataBase"]
        mstart = params["MaxStartYear"]
        mend = params["MinEndYear"]
        mdens = params["MinDataDens"]
        gamTableR = params["GamparsTableRoot"]

    # create database connection
    print("Trying to connect to the database : ", dbFileName)
    conn = new_db_connection(dbFileName)
    if conn is not None:
        print("connection to database is established successfully..")

    # get list of all stations
    print("getting list of all stations")
    sqlStr = "SELECT Cod_Estacion FROM Dato_Numerico"
    codes = fetch_db_data(conn, sqlStr)
    codes = get_unique_list(codes)
    print("total number of stations is ", len(codes))

    spList = []
    selection = "SELECT "
    for i in codes:
        code = i[0]
        print("get data of station No. ", code)
        fromWhere = " FROM Estacion WHERE Cod_Estacion=\'" + code + "\'"
        name = fetch_db_data(conn, selection + "Estacion" + fromWhere)[0][0]
        Gla = fetch_db_data(conn, selection + "Glatitud" + fromWhere)[0][0]
        Mla = fetch_db_data(conn, selection + "Mlatitud" + fromWhere)[0][0]
        Sla = fetch_db_data(conn, selection + "Slatitud" + fromWhere)[0][0]
        Glo = fetch_db_data(conn, selection + "Glongitud" + fromWhere)[0][0]
        Mlo = fetch_db_data(conn, selection + "Mlongitud" + fromWhere)[0][0]
        Slo = fetch_db_data(conn, selection + "Slongitud" + fromWhere)[0][0]
        X = -(Glo + Mlo / 60 + Slo / 3600)
        Y = -(Gla + Mla / 60 + Sla / 3600)
        Z = fetch_db_data(conn, selection + "Altura" + fromWhere)[0][0]
        sp = spClass(code, name, X, Y, Z)
        sp.get_data(conn)
        spList.append(sp)

    # select stations with enough data
    newList = []
    for spObj in spList:
        isOk = spObj.have_enough_data(mstart, mend, mdens)
        if isOk:
            newList.append(spObj)
    spList = newList
    print("Number of stations with enough data:", len(spList))

    # Monthly Totals
    print("calculate monthly total for each Station")
    for spObj in spList:
        print("Monthly Total for station No.", spObj.code)
        spObj.calculate_monthly_totals()

    # loop on each month of selected stations and calculate gamma distribution
    print("calculate gamma parameters")
    for spObj in spList:
        print("Gamma Distribution Fitting for Station No.", spObj.code)
        spObj.calculate_cumulative_gamma_distribution()

    for i in [1, 2, 3, 6, 12]:
        gamTable = gamTableR + "-{:02d}months.csv".format(i)
        print("Writing output table: " + gamTable)
        create_csv_gamtable(gamTable, spList, i)

