#!/usr/bin/env python3

import json
import os
import datetime
import functools
import random
import re
import subprocess
import sys

import redis

from flask import Flask, jsonify
app = Flask(__name__, static_url_path='', static_folder='static')
app.config['JSON_AS_ASCII'] = False

main_redis = redis.Redis(db=0)
stats_redis = redis.Redis(db=1)

script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
git_rev_fetch = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=script_path, stdout=subprocess.PIPE)
loaded_git_rev = git_rev_fetch.stdout.decode("ascii").rstrip()

# decorator to cache a result for a given time
# https://stackoverflow.com/a/50866968/1588786
def cache(ttl=datetime.timedelta(seconds=5)):
    def wrap(func):
        time, value = None, None
        @functools.wraps(func)
        def wrapped(*args, **kw):
            nonlocal time
            nonlocal value
            now = datetime.datetime.now()
            if not time or now - time > ttl:
                value = func(*args, **kw)
                time = now
            return value
        return wrapped
    return wrap

@cache(ttl=datetime.timedelta(seconds=1))
def get_sys_load():
    return os.getloadavg()

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

@app.route('/games_by_stream.json')
@cache(ttl=datetime.timedelta(seconds=30))
def get_games_by_stream():
    raw_list = main_redis.keys()
    games = {}

    for raw_game in raw_list:
        raw_name = raw_game.decode('utf-8').split('::')[1]
        if raw_name in games:
            games[raw_name] += 1
        else:
            games[raw_name] = 1

    collated_games = []
    for game, streams in games.items():
        collated_games.append({"game": game, "streams": streams})

    return jsonify(collated_games)

@app.route('/games_by_lang.json')
@cache(ttl=datetime.timedelta(seconds=30))
def get_games_by_lang():
    raw_list = main_redis.keys()
    games = {}

    for raw_game in raw_list:
        raw_name = raw_game.decode('utf-8').split('::')[2].replace('lang:', '')
        if raw_name in games:
            games[raw_name] += 1
        else:
            games[raw_name] = 1

    collated_games = []
    for game, streams in games.items():
        collated_games.append({"game": game, "streams": streams})

    return jsonify(collated_games)


@app.route('/motd')
@cache(ttl=datetime.timedelta(minutes=1))
def get_motd():
    try:
      with open('motd.txt', "r") as fh:
        return fh.read().strip()
    except IOError:
      return ('', 204)

if __name__ == "__main__":
    app.run()
