#!/usr/bin/env python3

import threading
import requests
import datetime as dt
import sys



status = requests.get('https://nobody.live/stats.json')
#status = requests.get('http://127.0.0.1:5000/stats.json')
logline = f"{dt.datetime.utcfromtimestamp(status.json()['time_of_ratelimit']).strftime('%H:%M:%S')},{dt.datetime.utcfromtimestamp(status.json()['populate_started']).strftime('%H:%M:%S')},{status.json()['streams']}"

print(logline)
