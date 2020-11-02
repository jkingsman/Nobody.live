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

    # if someone gets our stats key, try again
    if key == 'stats':
        key = r.randomkey()

    if not key:
        return "{}"

    time_fetched = r.get(key)
    ttl = r.ttl(key)

    response = json.loads(key)
    response['fetched'] = time_fetched
    response['ttl'] = ttl
    return response

@app.route('/stats')
def get_stats():
    streamcount = r.dbsize()
    stats = json.loads(r.get('stats'))

    return jsonify(
        streams=streamcount,
        ratelimit_usage=stats['ratelimit_usage'],
        time=stats['time_of_ratelimit']
    )

if __name__ == "__main__":
    app.run()
