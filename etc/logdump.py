#!/usr/bin/env python3
import requests
import time
import datetime as dt

print('last_api_request,populate_start_time,stream_count,load_1min,rate_limit_remaining')

while True:
    try:
        status = requests.get('https://nobody.live/stats.json')
        logline = f"{dt.datetime.utcfromtimestamp(status.json()['time_of_ratelimit']).strftime('%H:%M:%S')},{dt.datetime.utcfromtimestamp(status.json()['populate_started']).strftime('%H:%M:%S')},{status.json()['streams']},{status.json()['load'][0]},{status.json()['ratelimit_remaining']}"
        print(logline)
    except:
        pass
    time.sleep(2)
