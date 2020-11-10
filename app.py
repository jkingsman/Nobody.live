#!/usr/bin/env python3

import json
import os.path
import datetime
import redis

from flask import Flask, jsonify, send_from_directory
app = Flask(__name__, static_url_path='', static_folder='static')
r = redis.Redis(decode_responses=True)

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/stream')
def get_stream():
    key = r.randomkey()

    # if someone gets our stats key, try again up to ten times
    tries = 0
    while key == 'stats' or tries > 10:
        key = r.randomkey()

    if not key or key == 'stats':
        return "{}"

    response = json.loads(key)
    response['fetched'] = r.get(key)
    response['ttl'] = r.ttl(key)
    return response

@app.route('/streams', defaults={'count': 20})
@app.route('/streams/<count>')
def get_streams(count):
    streams = []
    for i in range(int(count)):
        key = r.randomkey()
        tries = 0
        while key == 'stats' or tries > 10:
            key = r.randomkey()

        if not key or key == 'stats':
            return "[]"

        stream = json.loads(key)
        stream['fetched'] = r.get(key)
        stream['ttl'] = r.ttl(key)

        if key != 'stats':
            streams.append(stream)

    return jsonify(streams)

@app.route('/stats/json')
def get_stats_json():
    stats = json.loads(r.get('stats'))
    stats['streams'] = r.dbsize()

    return jsonify(stats)

@app.route('/stats')
def get_stats_human():
    stats = json.loads(r.get('stats'))

    return f"{int(stats['ratelimit_remaining'])}/{int(stats['ratelimit_limit'])} API tokens left ({round((1 - int(stats['ratelimit_remaining']) / int(stats['ratelimit_limit'])) * 100, 2)}% spent). {r.dbsize() - 1} streams loaded."

if __name__ == "__main__":
    app.run()
