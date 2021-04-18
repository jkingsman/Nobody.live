#!/usr/bin/env python3

import threading
import requests
import datetime as dt
import sys

if len(sys.argv) != 2:
    print("need a log filename")
    exit()

status = requests.get('https://nobody.live/stats.json')
with open(sys.argv[1], 'a') as logfile:
    logfile.write(f"{dt.datetime.utcfromtimestamp(status.json()['time_of_ratelimit']).strftime('%H:%M:%S')},{status.json()['streams']}\n")
