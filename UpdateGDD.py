'''
UpdateGDD.py
By Todd Dole

This script calls the AmbientWeather API, downloads the latest weather data, and then updates a Google Sheet

'''

from dotenv import load_dotenv
import os

import time
import pprint
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

def get_data(device, year, month, day):
    epoch = datetime(year=year, month=month, day=day, hour=23, minute=59, second=0)
    data = device.get_data(end_date=epoch)
    return data

def get_year(timestamp):
    dt_local = datetime.fromtimestamp(timestamp)
    return dt_local.year

def main():
    # load config file
    load_dotenv()

    # set up Google Sheets connection


    # set up the Ambient Weather connection
    from ambient_api.ambientapi import AmbientAPI
    api = AmbientAPI(log_level='CONSOLE')

    devices = api.get_devices()
    print(devices)



    device = devices[0]

    time.sleep(2)
    query_time = datetime(year=2026, month=1, day=28)

    data = get_data(device,  query_time.year, query_time.month, query_time.day)

    df = pd.DataFrame.from_records(data)

    # create datetime column, move to front

    df["datetime_utc"] =pd.to_datetime(df["dateutc"], unit="ms", utc=True)
    df["datetime_local"] = df["datetime_utc"].dt.tz_convert("America/Chicago")
    cols = list(df.columns)
    cols.pop(cols.index('datetime_local'))
    cols.insert(0, 'datetime_local')

    df = df[cols]
    df.drop(["datetime_utc"], axis=1, inplace=True)

    # reverse list order
    df = df.iloc[::-1]

    df.to_csv('output.csv')

'''
    for element in data:
        timestamp_s = element['dateutc'] / 1000
        dt_local = datetime.fromtimestamp(timestamp_s)
        print(str(dt_local) + " : " + str(element['tempf']))
'''

if __name__ == '__main__':
    main()