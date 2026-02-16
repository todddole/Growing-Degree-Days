'''
UpdateGDD.py
By Todd Dole

This script calls the AmbientWeather API, downloads the latest weather data, and then updates a Google Sheet

'''
import ezsheets
from dotenv import load_dotenv
import os

import time
import pprint
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from pandas.core.tools.datetimes import DatetimeScalar
import math


def get_data(device, year, month, day):
    epoch = datetime(year=year, month=month, day=day, hour=23, minute=59, second=0)
    data = device.get_data(end_date=epoch)
    return data

def get_year(timestamp):
    dt_local = datetime.fromtimestamp(timestamp)
    return dt_local.year

def init_sheet(sheet_file):
    this_year = datetime.now().year

    # check if the sheet for this year exists
    if str(this_year) not in sheet_file.sheetTitles:
        sheet_file.createSheet(str(this_year), 0)
        new_sheet = sheet_file[0]
        new_sheet['A1'] = 'Date'
        new_sheet['B1'] = 'AVG Temp'
        new_sheet['C1'] = 'GDD'
        new_sheet['D1'] = 'CGDD'

    # check if the data sheet exists
    if 'Data' not in sheet_file.sheetTitles:
        sheet_file.createSheet('Data')
        new_sheet = sheet_file['Data']
        new_sheet['A1'] = 'datetime_local'
        new_sheet['B1'] = 'dateutc'
        new_sheet['C1'] = 'tempf'
        new_sheet['D1'] = 'humidity'
        new_sheet['E1'] = 'windspeedmph'
        new_sheet['F1'] = 'windgustmph'
        new_sheet['G1'] = 'maxdailygust'
        new_sheet['H1'] = 'winddir'
        new_sheet['I1'] = 'winddir_avg10m'
        new_sheet['J1'] = 'uv'
        new_sheet['K1'] = 'solarradiation'
        new_sheet['L1'] = 'hourlyrainin'
        new_sheet['M1'] = 'eventrainin'
        new_sheet['N1'] = 'dailyrainin'
        new_sheet['O1'] = 'weeklyrainin'
        new_sheet['P1'] = 'monthlyrainin'
        new_sheet['Q1'] = 'yearlyrainin'
        new_sheet['R1'] = 'battout'
        new_sheet['S1'] = 'tempinf'
        new_sheet['T1'] = 'humidityin'
        new_sheet['U1'] = 'baromrelin'
        new_sheet['V1'] = 'baromabsin'
        new_sheet['W1'] = 'battin'
        new_sheet['X1'] = 'feelsLike'
        new_sheet['Y1'] = 'dewPoint'
        new_sheet['Z1'] = 'feelsLikein'
        new_sheet['AA1'] = 'dewPointin'
        new_sheet['AB1'] = 'passkey'
        new_sheet['AC1'] = 'time'
        new_sheet['AD1'] = 'loc'
        new_sheet['AE1'] = 'date'

    # delete sheet1 if it exists
    if 'Sheet1' in sheet_file.sheetTitles:
        sheet_file['Sheet1'].delete()


def process_day(sheet, device, date):
    print(f'Processing day {date}')
    query_time = datetime(year=date.year, month=date.month, day=date.day)

    data = get_data(device, query_time.year, query_time.month, query_time.day)

    df = pd.DataFrame.from_records(data)

    # create datetime column, move to front

    df["datetime_utc"] = pd.to_datetime(df["dateutc"], unit="ms", utc=True)
    df["datetime_local"] = df["datetime_utc"].dt.tz_convert("America/Chicago").dt.strftime("%Y-%m-%d %H:%M")
    cols = list(df.columns)
    cols.pop(cols.index('datetime_local'))
    cols.insert(0, 'datetime_local')

    df = df[cols]
    df.drop(["datetime_utc"], axis=1, inplace=True)

    # reverse list order
    df = df.iloc[::-1]

    mean_temp = df["tempf"].mean()

    row_num = 1

    while sheet.getRow(row_num)[0] != '':
        row_num += 1

    rows = sheet.getRows()
    print("Before:")
    print(len(rows))
    # iterate through and update google sheet
    for row in df.itertuples(index=False):
        #print(f'Processing row {row_num}')
        values = list(row)
        # Need to clean nan values
        cleaned = [
            "nan" if isinstance(x, float) and math.isnan(x) else x
            for x in values
        ]

        rows.append(cleaned)

    print("After:")
    print(len(rows))

    sheet.updateRows(rows)
    return mean_temp




def main():
    # load config file
    load_dotenv()

    # set up Google Sheets connection
    import ezsheets
    # Note - follow ezsheets instructions to set up the connection.  You will need token-drive.pickle and token-sheets.pickle files in the folder to work

    s = ezsheets.Spreadsheet(os.getenv("SHEET_ID"))
    init_sheet(s)

    start_date = datetime.strptime(os.getenv('START_DATE'), '%m/%d/%Y')
    cur_date = start_date

    row = 2
    sheet = s[0]

    data = sheet.getRow(row)[0]

    while data !='':
        cur_date = datetime.strptime(data, '%Y-%m-%d')
        cur_date = cur_date + timedelta(days=1)
        if cur_date > start_date:
            start_date = cur_date
        row += 1
        data = sheet.getRow(row)[0]

    # set up the Ambient Weather connection
    from ambient_api.ambientapi import AmbientAPI
    api = AmbientAPI(log_level='CONSOLE')

    devices = api.get_devices()
    print(devices)

    device = devices[0]
    time.sleep(1)

    gdd_start = float(os.getenv('GDD_START'))

    while cur_date < (datetime.now() - timedelta(days=1)):
        mean_temp = process_day(s['Data'], device, cur_date)

        gdd = max(mean_temp-gdd_start, 0)
        if (row>2):
            cgdd = float(s[0].getRow(row-1)[3])
        else:
            cgdd = 0

        if gdd>0:
            cgdd+=gdd

        s[0].updateRow(row, [cur_date.strftime('%Y-%m-%d'), str(round(mean_temp, 2)), str(round(gdd, 2)), str(round(cgdd, 2))])
        row+=1
        time.sleep(1)
        cur_date = cur_date + timedelta(days=1)






'''
    for element in data:
        timestamp_s = element['dateutc'] / 1000
        dt_local = datetime.fromtimestamp(timestamp_s)
        print(str(dt_local) + " : " + str(element['tempf']))
'''

if __name__ == '__main__':
    main()