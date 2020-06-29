import os
import csv
import jaydebeapi
import json
# import datetime
import calendar
from sq_class import *


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

def fetch_db_data(conn, sqlStr):
    cursor = conn.cursor()
    cursor.execute(sqlStr)
    return cursor.fetchall()

def get_valid_list(initList, q95tab):
    validList = []
#    line_count = 0
    good_codes = []
    for row in q95tab:
#        if line_count > 0:
        good_codes.append(row["code"])
#        line_count += 1
    for x in initList:
        #print(x)
        if x[0] in good_codes:
            if x not in validList:
                validList.append(x[0])
    return validList

def create_csv_events(sq, evFolder):
    fileName = os.path.join(evFolder, sq.code + "-LowFlowEvents.csv")
    with open(fileName, mode='w') as csvFile:
        writer = csv.writer(csvFile, delimiter=',')
        row = []
        row.append("Start")
        row.append("End")
        row.append("Dvol")
        row.append("LFI")
        writer.writerow(row)
        for tstart, tend, dV in zip(sq.tStartev, sq.tEndev, sq.dVev):
            row = []
            row.append(tstart)
            row.append(tend)
            row.append(dV)
            row.append(1 - numpy.exp(- sq.lambd_ev * dV))
            writer.writerow(row)
            # print(row)

def create_csv_latest(latestTable, latestCode, latestStart, latestEnd, latestLFI):
    with open(latestTable, mode='w') as csvFile:
        writer = csv.writer(csvFile, delimiter=',')
        row = []
        row.append("Code")
        row.append("Start")
        row.append("End")
        row.append("LFI")
        writer.writerow(row)
        for code, tstart, tend, LFI in zip(latestCode, latestStart, latestEnd, latestLFI):
            row = []
            row.append(code)
            row.append(tstart)
            row.append(tend)
            row.append(LFI)
            writer.writerow(row)
            print(row)

def create_reports(sq, destdLFI, destdQQQ, destdQ95, tstart, tend):
    tstartstr = "{:04d}".format(tstart.year) + "{:02d}".format(tstart.month) \
              + "{:02d}".format(tstart.day) + "0000"
    tendstr = "{:04d}".format(tend.year) + "{:02d}".format(tend.month) \
              + "{:02d}".format(tend.day) + "0000"
    fileName = os.path.join(destdLFI, "hydrograph_Bolivia_" + sq.code
                            + "_" + tendstr + ".txt")
    go_write_report(fileName, tstartstr, tendstr, sq.LFI_Rep, [])
    fileName = os.path.join(destdQQQ, "hydrograph_Bolivia_" + sq.code
                            + "_" + tendstr + ".txt")
    go_write_report(fileName, tstartstr, tendstr, sq.Q_Rep, sq.Q95_Rep)
    fileName = os.path.join(destdQ95, "hydrograph_Bolivia_" + sq.code
                            + "_" + tendstr + ".txt")
    go_write_report(fileName, tstartstr, tendstr, sq.Q95_Rep, [])

def go_write_report(fileName, tstartstr, tendstr, VV, V2):
    fid = open(fileName, 'w')
    fid.write("Procedure=LFI\n")
    fid.write("DateMeteoModel=" + tendstr + "\n")
    fid.write("DateStart=" + tstartstr + "\n")
    fid.write("Temp.Resolution=1440\n")
    fid.write("SscenariosNumber=1\n")
    if len(VV) > 0:
        Vstr = ""
        for i in range(0, len(VV)):
            Vstr = Vstr + "{:9.3f}".format(VV[i]) + " "
        fid.write(Vstr + "\n")
    if len(V2) > 0:
        Vstr = ""
        for i in range(0, len(V2)):
            Vstr = Vstr + "{:9.3f}".format(V2[i]) + " "
        fid.write(Vstr + "\n")
    fid.close()


if __name__ == '__main__':
    # start main program
    print("Hello world")

    jsoname = 'LFI_config.json'
    with open(jsoname) as jf:
        params = json.load(jf)
        dbFileName = params["DataBase"]
        q95Table = params["Q95Table"]
        indFold = params["Index_folder"]
        QQQFold = params["Qday_folder"]
        Q95Fold = params["Q95_folder"]
        startYear = params["StartYear4LFI"]
        startMonth = params["StartMonth4LFI"]
        endYear = params["EndYear4LFI"]
        endMonth = params["EndMonth4LFI"]
        startRepYear = params["StartYearReport"]
        startRepMonth = params["StartMonthReport"]
        endRepYear = params["EndYearReport"]
        endRepMonth = params["EndMonthReport"]
        mdens = params["MinDataDens"]


    # adjust otuput folders
    desty = os.path.join(indFold, "{:04d}".format(endRepYear))
    if not (os.path.isdir(desty)):
        os.mkdir(desty)
    destm = os.path.join(desty, "{:02d}".format(endRepMonth))
    if not (os.path.isdir(destm)):
        os.mkdir(destm)
    destd = os.path.join(destm,
                         "{:02d}".format(calendar.monthrange(endRepYear, endRepMonth)[1]))
    if not (os.path.isdir(destd)):
        os.mkdir(destd)

    evFolder = os.path.join(destd, "Events")
    if not (os.path.isdir(evFolder)):
        os.mkdir(evFolder)

    desty = os.path.join(QQQFold, "{:04d}".format(endRepYear))
    if not (os.path.isdir(desty)):
        os.mkdir(desty)
    destm = os.path.join(desty, "{:02d}".format(endRepMonth))
    if not (os.path.isdir(destm)):
        os.mkdir(destm)
    destdRepQQQ = os.path.join(destm,
                               "{:02d}".format(calendar.monthrange(endRepYear, endRepMonth)[1]))
    if not (os.path.isdir(destdRepQQQ)):
        os.mkdir(destdRepQQQ)

    desty = os.path.join(Q95Fold, "{:04d}".format(endRepYear))
    if not (os.path.isdir(desty)):
        os.mkdir(desty)
    destm = os.path.join(desty, "{:02d}".format(endRepMonth))
    if not (os.path.isdir(destm)):
        os.mkdir(destm)
    destdRepQ95 = os.path.join(destm,
                               "{:02d}".format(calendar.monthrange(endRepYear, endRepMonth)[1]))
    if not (os.path.isdir(destdRepQ95)):
        os.mkdir(destdRepQ95)

    # create database connection
    print("Trying to connect to the database : ", dbFileName)
    conn = new_db_connection(dbFileName)
    if conn is not None:
        print("connection to database is established successfully..")

    # get list of all stations
    print("getting list of all stations")
    sqlStr = "SELECT Id_Station FROM Debits"
    codes = fetch_db_data(conn, sqlStr)
    codes = get_unique_list(codes)

    # read statistics (Q95 table)
    with open(q95Table, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        codes = get_valid_list(codes, csv_reader)
    print("total number of stations is ", len(codes))
    selection = "SELECT "

    latestCode = []
    latestStart = []
    latestEnd = []
    latestLFI = []

    for code in codes:

        print("get data of station No. ", code)
        fromWhere = " FROM Stations_Base WHERE Id_Station=\'" + code + "\'"
        name = fetch_db_data(conn, selection + "Nom" + fromWhere)[0][0]
        river = fetch_db_data(conn, selection + "Riviere" + fromWhere)[0][0]
        x = fetch_db_data(conn, selection + "Longitude" + fromWhere)[0][0]
        y = fetch_db_data(conn, selection + "Latitude" + fromWhere)[0][0]
        z = fetch_db_data(conn, selection + "Altitude" + fromWhere)[0][0]
        sq = sqClass(code, x, y, z, name, river)
        fromWhere = "  FROM Debits WHERE Id_Station=\'" + code + "\'"
        Time = fetch_db_data(conn, selection + "Date" + fromWhere)
        Data = fetch_db_data(conn, selection + "Valeur" + fromWhere)
        select_Time = []
        select_Data = []
        tstart = datetime(startYear, startMonth, 1).toordinal()
        mrange = calendar.monthrange(endYear, endMonth)
        tend = datetime(endYear, endMonth, mrange[1]).toordinal()
        tstartRep = datetime(startRepYear, startRepMonth, 1).toordinal()
        tstartRepT = datetime(startRepYear, startRepMonth, 1)
        mrange = calendar.monthrange(endRepYear, endRepMonth)
        tendRep = datetime(endRepYear, endRepMonth, mrange[1]).toordinal()
        tendRepT = datetime(endRepYear, endRepMonth, mrange[1])
        for tt, dd in zip(Time, Data):
            tdata = datetime.strptime((tt[0]), '%Y-%m-%d %H:%M:%S').date().toordinal()
            if tstart <= tdata <= tend:
                select_Time.append(tt)
                select_Data.append(dd)
        sq.set_data(select_Data, select_Time)
        if sq.has_enough_data(startYear, endYear, mdens):
            sq.inherit_DC(q95Table)
            sq.find_events(tstartRep, tendRep)
            create_csv_events(sq, evFolder)
            create_reports(sq, destd, destdRepQQQ, destdRepQ95, tstartRepT, tendRepT)
            latestCode.append(sq.code)
            if len(sq.tStartev) > 0:
                latestStart.append(sq.tStartev[-1])
                latestEnd.append(sq.tEndev[-1])
                latestLFI.append(1 - numpy.exp(- sq.lambd_ev * sq.dVev[-1]))
            else:
                latestStart.append("0000-00-00")
                latestEnd.append("0000-00-00")
                latestLFI.append(-99999)
    latestTable = os.path.join(destd, "LFI-latest_{:04d}{:02d}010000.csv".format(endYear, endMonth))
    create_csv_latest(latestTable, latestCode, latestStart, latestEnd, latestLFI)



