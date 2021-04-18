#!/usr/bin/env python3

import json
import os
import time
import random
import redis

from flask import Flask, jsonify, request, send_from_directory
app = Flask(__name__, static_url_path='', static_folder='static')
main_redis = redis.Redis(decode_responses=True, db=0)
stats_redis = redis.Redis(decode_responses=True, db=1)

cached_load = {'load': os.getloadavg(), 'retrieved_time': time.time()}
def getSysLoad():
    load_cache_time = 5

    if time.time() - cached_load['retrieved_time'] > 5:
        cached_load['load'] = os.getloadavg()
        cached_load['retrieved_time'] = time.time()
    return cached_load['load']

def getStreams(count=1, game=None):
    if game:
        results = main_redis.keys(f"*{game.lower()}*")

        try:
            keys = random.sample(results, int(count))
        except ValueError:
            # likely have fewer keys than we want; just use what we have
            keys = results
        streams = list(map(lambda key: json.loads(main_redis.get(key)), keys))
        print(len(streams))
        return streams
    else:
        results = []
        for i in range(int(count)):
            key = main_redis.randomkey()

            if not key:
                return results

            stream = json.loads(main_redis.get(key))
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

@app.route('/searchstream/<game>')
def get_single_game_stream(game):
    streams = getStreams(count=1, game=game)

    if streams:
        return streams[0]
    return '{}'

@app.route('/streams/<count>')
def get_streams(count):
    streams = getStreams(count)

    if streams:
        return jsonify(streams)
    return '[]'

@app.route('/searchstreams/<game>/<count>')
def get_single_game_streams(game, count):
    streams = getStreams(count, game)

    if streams:
        return jsonify(streams)
    return '[]'

@app.route('/stats.json')
def get_stats_json():
    stats = json.loads(stats_redis.get('stats'))
    stats['streams'] = main_redis.dbsize()
    stats['load'] = getSysLoad()

    return jsonify(stats)

# @app.route('/games.json')
# def get_games_json():
#     raw_list = main_redis.keys()
#     games = set()
#
#     for raw_game in raw_list:
#         raw_name = raw_game.split('::')[1]
#         name_bytes = bytes(my_str, 'utf-8')
#         games.add(.decode('utf-8').title())
#
#     return json.dumps(sorted(list(games)))


if __name__ == "__main__":
    app.run()
