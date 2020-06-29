import os
import calendar
from datetime import datetime, date
import numpy
import scipy
import jaydebeapi
import csv
import math

def new_db_connection(fileName):
    dirPath = os.path.dirname(os.path.realpath(__file__))
#    fullName = dirPath + "/" + fileName
    fullName = fileName
    accessAdd = dirPath + "/UCanAccess-5.0.0-bin"
    fileList = [
        accessAdd + "/ucanaccess-5.0.0.jar",
        accessAdd + "/lib/commons-lang3-3.8.1.jar",
        accessAdd + "/lib/commons-logging-1.2.jar",
        accessAdd + "/lib/hsqldb-2.5.0.jar",
        accessAdd + "/lib/jackcess-3.0.1.jar",
    ]

    classPath = ":".join(fileList)
    temp = "jdbc:ucanaccess://" + fullName

    conn = jaydebeapi.connect(
        "net.ucanaccess.jdbc.UcanaccessDriver",
        temp,
        ["", ""],
        classPath
    )
    return conn

def get_unique_list(initList):
    uniqueList = []
    for x in initList:
        #print(x)
        if x not in uniqueList:
            uniqueList.append(x)
    return uniqueList

def fetch_db_data(conn, sqlStr):
    cursor = conn.cursor()
    cursor.execute(sqlStr)
    return cursor.fetchall()

def count_finite_values(myList):
    count = 0
    for value in myList:
        if value is not None:
            count += 1
    return count


def sum_finite_values(myList):
    sum = 0
    for value in myList:
        if value is not None:
            sum += value
    return sum

def calculate_gamma_params(data):
    # alpha, loc, beta = stats.gamma.fit(data)
    # result = [alpha, loc, beta]
    # return result
    datapos = []
    for dd in data:
        if dd > 0:
            datapos.append(dd)
    p0 = 1 - len(datapos) / len(data)
    mean = numpy.mean(datapos)
    variance = numpy.var(datapos)
    alpha = mean * mean / variance
    beta = mean / variance
    teta = 1 / beta
    result = [alpha, 0, teta, p0]
    return result

class spClass:
    def __init__(self, code, name, X, Y, Z):
        self.code = code
        self.name = name
        self.X = X
        self.Y = Y
        self.Z = Z
        self.data = []
        self.time = []
        self.startYear = 0
        self.endYear = 0
        self.dens = 0
        self.timeM = []
        self.dataM = []
        self.dayCountInMonth = []
        self.M1GamPar = []
        self.M2GamPar = []
        self.M3GamPar = []
        self.M6GamPar = []
        self.M12GamPar = []

    def get_data(self, conn):
        sqlStr = "SELECT * FROM Dato_Numerico WHERE Cod_Param = 1 " + \
                 "AND Cod_Estacion=\'" + self.code + "\'"
        response = fetch_db_data(conn, sqlStr)
        data = []
        time = []
        for rowInd in range(len(response)):
            row = response[rowInd]
            year = row[1]
            # if year < 1990 or year > 2019:
            #     continue
            month = row[2]
            dayCount = calendar.monthrange(year, month)[1]
            for ind in range(dayCount):
                dbInd = ind + 4
                data.append(row[dbInd])
                day = ind + 1
                timeVal = date.toordinal(date(year, month, day))  # + 366
                time.append(timeVal)
        self.data = data
        self.time = time
        self.startYear = date.fromordinal(min(self.time)).year
        self.endYear = date.fromordinal(max(self.time)).year
        self.dens = count_finite_values(self.data) / (max(self.time) - min(self.time) + 1)
        # print(self.dens)

    def select_data_intimerange(self, tmin, tmax):
        select_Time = []
        select_Data = []
        for tt, dd in zip(self.time, self.data):
            if tmin <= tt <= tmax:
                select_Time.append(tt)
                select_Data.append(dd)
        self.data = select_Data
        self.time = select_Time
        self.dens = count_finite_values(self.data) / (max(self.time) - min(self.time) + 1)
        self.startYear = date.fromordinal(tmin).year
        self.endYear = date.fromordinal(tmax).year

    def select_monthlydata_intimerange(self, tmin, tmax):
        select_Time = []
        select_Data = []
        for tt, dd in zip(self.timeM, self.dataM):
            if tmin <= tt <= tmax:
                select_Time.append(tt)
                select_Data.append(dd)
        self.dataM = select_Data
        self.timeM = select_Time

    def have_enough_data(self, maxStart, minEnd, minDens):
        if self.startYear <= maxStart and\
         self.endYear >= minEnd and\
         self.dens >= minDens:
            return True
        else:
            return False

    def calculate_monthly_totals(self):
        yearsCount = self.endYear - self.startYear + 1
        for yInd in range(1, yearsCount + 1):
            yy = self.startYear + yInd - 1
            for mInd in range(1, 13):
                self.timeM.append(date.toordinal(date(yy, mInd, 1)))
                myList = []
                for i in range(len(self.data)):
                    if date.fromordinal(self.time[i]).month == mInd and\
                     date.fromordinal(self.time[i]).year == yy and\
                     self.data[i] is not None:
                        myList.append(i)
                self.dayCountInMonth.append(len(myList))
                val = None
                if len(myList) > 15:
                    sum = 0
                    for i in myList:
                        sum += self.data[i]
                    days = calendar.monthrange(yy, mInd)[1]
                    val = sum * days / len(myList)
                self.dataM.append(val)
                # print("station Name", self.name, "at year", yy, "and month", mInd, "have total", val)

    def calculate_cumulative_gamma_distribution(self):
        for i in range(1, 13):
            # calculate 1 month gamma fit parameters
            dataArray = self.calculate_data_for_gamma(i, 1)
            gamPar = calculate_gamma_params(dataArray)
            self.M1GamPar.append(gamPar)
            # print("Gamma Params (1-month) for", i, "month is ", gamPar)

            # calculate 2 month gamma fit parameters
            dataArray = self.calculate_data_for_gamma(i, 2)
            gamPar = calculate_gamma_params(dataArray)
            self.M2GamPar.append(gamPar)
            # print("Gamma Params (2-month) for", i, "month is ", gamPar)

            # calculate 3 month gamma fit parameters
            dataArray = self.calculate_data_for_gamma(i, 3)
            gamPar = calculate_gamma_params(dataArray)
            self.M3GamPar.append(gamPar)
            # print("Gamma Params (3-month) for", i, "month is ", gamPar)

            # calculate 6 month gamma fit parameters
            dataArray = self.calculate_data_for_gamma(i, 6)
            gamPar = calculate_gamma_params(dataArray)
            self.M6GamPar.append(gamPar)
            # print("Gamma Params (6-month) for", i, "month is ", gamPar)

            # calculate 12 month gamma fit parameters
            dataArray = self.calculate_data_for_gamma(i, 12)
            gamPar = calculate_gamma_params(dataArray)
            self.M12GamPar.append(gamPar)
            # print("Gamma Params (12-month) for", i, "month is ", gamPar)

    def calculate_data_for_gamma(self, monthInd, monthCount):
        result = []
        for yy in range(self.startYear, self.endYear + 1):
            # first find index of meaningful data
            myList = []
            totalDays = 0
            usedDays = 0
            for j in range(monthCount):
                year = yy
                temp = monthInd - j
                if (temp < 1):
                    temp += 12
                    year -= 1
                totalDays += calendar.monthrange(year, temp)[1]
                dateVal = date.toordinal(date(year, temp, 1))
                if dateVal in self.timeM:
                    ind = self.timeM.index(dateVal)
                    if self.dataM[ind] is not None:
                        myList.append(ind)
                        usedDays += calendar.monthrange(year, temp)[1]
            # now I have the list

            # lets use it to calculate accumulative value
            if len(myList) > 0:
                sum = 0
                for ind in myList:
                    sum += self.dataM[ind]
                value = sum / usedDays * totalDays
                result.append(value)

        # now return the calculated results
        return result

    def inherit_gamtable(self, gamTableR):
        for i in [1, 2, 3, 6, 12]:
            gamTable = gamTableR + "-{:02d}months.csv".format(i)
            with open(gamTable, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                skip1 = True
                for row in csv_reader:
                    if skip1:
                        skip1 = False
                        continue
                    else:
                        if self.code == row["code"]:
                            if i == 1:
                                self.M1GamPar = []
                            elif i == 2:
                                self.M2GamPar = []
                            elif i == 3:
                                self.M3GamPar = []
                            elif i == 6:
                                self.M6GamPar = []
                            elif i == 12:
                                self.M12GamPar = []
                            for month in range(1, 13):
                                G1 = float(row["GamP1_{0:02d}".format(month)])
                                G2 = float(row["GamP2_{0:02d}".format(month)])
                                P0 = float(row["P0_{0:02d}".format(month)])
                                if i == 1:
                                    self.M1GamPar.append([G1, 0, G2, P0])
                                elif i == 2:
                                    self.M2GamPar.append([G1, 0, G2, P0])
                                elif i == 3:
                                    self.M3GamPar.append([G1, 0, G2, P0])
                                elif i == 6:
                                    self.M6GamPar.append([G1, 0, G2, P0])
                                elif i == 12:
                                    self.M12GamPar.append([G1, 0, G2, P0])

    def calculate_SPI_values(self):
        refmonth = date.fromordinal(self.timeM[-1]).month
        for i in [1, 2, 3, 6, 12]:
            dataVal = 0
            # print(self.dataM)
            for j in range(i):
                # print(i)
                # print(j)
                # print(self.dataM[-(1+j)])
                val = self.dataM[-(1+j)]
                if val is not None:
                    dataVal += val
                else:
                    dataVal = math.nan
            # dataVal /= i
            if i == 1:
                shape_par = self.M1GamPar[refmonth][0]
                scale_par = self.M1GamPar[refmonth][2]
                P0 = self.M1GamPar[refmonth][3]
                probGam = P0 / 2 + (1 - P0) * scipy.stats.gamma.cdf(dataVal / scale_par, shape_par)
                self.SPI01 = scipy.stats.norm.isf(1 - probGam)
            elif i == 2:
                shape_par = self.M2GamPar[refmonth][0]
                scale_par = self.M2GamPar[refmonth][2]
                P0 = self.M2GamPar[refmonth][3]
                probGam = P0 / 2 + (1 - P0) * scipy.stats.gamma.cdf(dataVal / scale_par, shape_par)
                self.SPI02 = scipy.stats.norm.isf(1 - probGam)
            elif i == 3:
                shape_par = self.M3GamPar[refmonth][0]
                scale_par = self.M3GamPar[refmonth][2]
                P0 = self.M3GamPar[refmonth][3]
                probGam = P0 / 2 + (1 - P0) * scipy.stats.gamma.cdf(dataVal / scale_par, shape_par)
                self.SPI03 = scipy.stats.norm.isf(1 - probGam)
            elif i == 6:
                shape_par = self.M6GamPar[refmonth][0]
                scale_par = self.M6GamPar[refmonth][2]
                P0 = self.M6GamPar[refmonth][3]
                probGam = P0 / 2 + (1 - P0) * scipy.stats.gamma.cdf(dataVal / scale_par, shape_par)
                self.SPI06 = scipy.stats.norm.isf(1 - probGam)
            elif i == 12:
                shape_par = self.M12GamPar[refmonth][0]
                scale_par = self.M12GamPar[refmonth][2]
                P0 = self.M12GamPar[refmonth][3]
                probGam = P0 / 2 + (1 - P0) * scipy.stats.gamma.cdf(dataVal / scale_par, shape_par)
                self.SPI12 = scipy.stats.norm.isf(1 - probGam)

