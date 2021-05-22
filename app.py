#!/usr/bin/env python3

import json
import os
import time
import random
import re
import subprocess
import sys

import redis

from flask import Flask, jsonify
app = Flask(__name__, static_url_path='', static_folder='static')
main_redis = redis.Redis(decode_responses=True, db=0)
stats_redis = redis.Redis(decode_responses=True, db=1)

script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
git_rev_fetch = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=script_path, stdout=subprocess.PIPE)
loaded_git_rev = git_rev_fetch.stdout.decode("ascii").rstrip()

cached_load = {'load': os.getloadavg(), 'retrieved_time': time.time()}
def get_sys_load():
    load_cache_time = 5

    if time.time() - cached_load['retrieved_time'] > load_cache_time:
        cached_load['load'] = os.getloadavg()
        cached_load['retrieved_time'] = time.time()
    return cached_load['load']

def normalize_and_escape_glob_term(glob):
    glob = glob.lower()
    glob = glob.replace('?', '\\?')
    glob = re.sub(r'([\[\]\?\*\^])', r'\\\1', glob)
    return glob

def get_streams(count=1, game=None):
    if game: # pylint: disable=no-else-return
        results = main_redis.keys(f"*{normalize_and_escape_glob_term(game)}*")

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
        for _i in range(int(count)):
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
    streams = get_streams(count=1, game=None)

    if streams:
        return streams[0]
    return '{}'

@app.route('/searchstream/<game>')
def get_single_game_stream(game):
    streams = get_streams(count=1, game=game)

    if streams:
        return streams[0]
    return '{}'

@app.route('/streams/<count>')
def get_streams_endpoint(count):
    streams = get_streams(count)

    if streams:
        return jsonify(streams)
    return '[]'

@app.route('/searchstreams/<game>/<count>')
def get_single_game_streams(game, count):
    streams = get_streams(count, game)

    if streams:
        return jsonify(streams)
    return '[]'

@app.route('/stats.json')
def get_stats_json():
    stats = json.loads(stats_redis.get('stats'))
    stats['streams'] = main_redis.dbsize()
    stats['load'] = get_sys_load()
    stats['rev'] = loaded_git_rev
    stats['populate_started'] = float(stats_redis.get('populate_started'))

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
