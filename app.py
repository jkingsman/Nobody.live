#!/usr/bin/env python3

import json
import os.path
import datetime
import redis

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
app = Flask(__name__, static_url_path='', static_folder='static')
# TODO: Revisit best practices for CORS
CORS(app)
cors = CORS(app, resources={
    r"/*": {
        "origins": "*"
    }
})
main_redis = redis.Redis(decode_responses=True, db=0)
stats_redis = redis.Redis(decode_responses=True, db=1)


def getStreams(count = 1):
    results = []
    for i in range(int(count)):
        key = main_redis.randomkey()

        if not key:
            return results

        stream = json.loads(key)
        stream['fetched'] = main_redis.get(key)
        stream['ttl'] = main_redis.ttl(key)
        results.append(stream)
    return results

@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/stream')
def get_stream():
    streams = getStreams()

    if streams:
        return streams[0]
    return '{}'

@app.route('/streams', defaults={'count': 20}, methods=['GET'])
@app.route('/streams/<count>')
def get_streams(count):
    streams = getStreams(count)

    if streams:
        return jsonify(streams)
    return '[]'


@app.route('/stats/json')
@app.route('/stats.json')
def get_stats_json():
    stats = json.loads(stats_redis.get('stats'))
    stats['streams'] = main_redis.dbsize()

    return jsonify(stats)


@app.route('/status')
@app.route('/stats')
@app.route('/stats.txt')
def get_stats_human():
    stats = json.loads(stats_redis.get('stats'))

    return (f"{int(stats['ratelimit_remaining'])}/{int(stats['ratelimit_limit'])} API tokens left "
            f"({round((1 - int(stats['ratelimit_remaining']) / int(stats['ratelimit_limit'])) * 100, 2)}% spent). "
            f"{main_redis.dbsize() - 1} streams loaded."
    )


if __name__ == "__main__":
    app.run()
