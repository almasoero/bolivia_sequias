import os

import csv
import sys

import scipy.stats as stats

import jaydebeapi
from datetime import datetime, date
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

def get_valid_list(initList, Stab):
    validList = []
    line_count = 0
    good_codes = []
    for row in Stab:
        if line_count > 0:
            good_codes.append(row["code"])
        line_count += 1
    for x in initList:
        #print(x)
        if x[0] in good_codes:
            if x not in validList:
                validList.append(x[0])
    return validList

def create_csv_SPI(spiTable, codesF, SPI01, SPI02, SPI03, SPI06, SPI12):
    with open(spiTable, mode='w') as csvFile:
        writer = csv.writer(csvFile, delimiter=',')
        row = []
        row.append("Code")
        row.append("SPI01")
        row.append("SPI02")
        row.append("SPI03")
        row.append("SPI06")
        row.append("SPI12")
        writer.writerow(row)
        for code, sp1, sp2, sp3, sp6, sp12 in zip(codesF, SPI01, SPI02, SPI03, SPI06, SPI12):
            row = []
            row.append(code)
            row.append(sp1)
            row.append(sp2)
            row.append(sp3)
            row.append(sp6)
            row.append(sp12)
            writer.writerow(row)
            print(row)


if __name__ == '__main__':
    # start main program
    print("Hello world")

    #jsoname = 'SPI_station_config.json'
    jsoname = sys.argv[1]
    with open(jsoname) as jf:
        params = json.load(jf)
        dbFileName = params["DataBase"]
        mdens = params["MinDataDens"]
        gamTableR = params["GamparsTableRoot"]
        startYear = params["StartYear4SPI"]
        startMonth = params["StartMonth4SPI"]
        indFold = params["Index_folder"]

    # adjust otuput folders
    desty = os.path.join(indFold, "{:04d}".format(startYear))
    if not (os.path.isdir(desty)):
        os.mkdir(desty)
    destm = os.path.join(desty, "{:02d}".format(startMonth))
    if not (os.path.isdir(destm)):
        os.mkdir(destm)
    destd = os.path.join(destm, "01")
    if not (os.path.isdir(destd)):
        os.mkdir(destd)

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

    # read statistics table first time to get codes
    gamTable = gamTableR + "-{:02d}months.csv".format(1)
    with open(gamTable, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        codes = get_valid_list(codes, csv_reader)
    print("total number of stations is ", len(codes))

    selection = "SELECT "
    startM = startMonth - 11
    startY = startYear
    if startM < 1:
        startM += 12
        startY -= 1
    tstart = datetime(startY, startM, 1).toordinal()
    mrange = calendar.monthrange(startYear, startMonth)
    tend = datetime(startYear, startMonth, mrange[1]).toordinal()
    codesF = []
    SPI01 = []
    SPI02 = []
    SPI03 = []
    SPI06 = []
    SPI12 = []
    for code in codes:
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
        sp.select_data_intimerange(tstart, tend)
        if sp.have_enough_data(startYear, startYear, mdens):
            sp.inherit_gamtable(gamTableR)
            sp.calculate_monthly_totals()
            sp.select_monthlydata_intimerange(tstart, tend)
            sp.calculate_SPI_values()
            codesF.append(code)
            SPI01.append(sp.SPI01)
            SPI02.append(sp.SPI02)
            SPI03.append(sp.SPI03)
            SPI06.append(sp.SPI06)
            SPI12.append(sp.SPI12)

    spiTable = os.path.join(destd, "SPI-station_{:04d}{:02d}01.csv".format(startYear, startMonth))
    create_csv_SPI(spiTable, codesF, SPI01, SPI02, SPI03, SPI06, SPI12)


