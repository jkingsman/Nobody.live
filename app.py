#!/usr/bin/env python3

import json
import os
import datetime
import functools
import random
import re
import subprocess
import sys

import db_utils
cursor = db_utils.get_cursor()

from flask import Flask, jsonify, json
app = Flask(__name__, static_url_path='', static_folder='static')
app.config['JSON_AS_ASCII'] = False

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

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/stream')
def get_stream():
    stream = db_utils.get_n_games(cursor, 1)
    return jsonify(json.loads(stream[0][0]))

@app.route('/searchstream/<game>')
def get_single_game_stream(game):
    stream = db_utils.get_n_games_filter_game(cursor, 1, game)
    return jsonify(json.loads(stream[0][0]))

@app.route('/streams/<count>')
def get_streams_endpoint(count):
    streams = db_utils.get_n_games(cursor, min(int(count), 60))
    return jsonify([json.loads(stream[0]) for stream in streams])

@app.route('/searchstreams/<game>/<count>')
def get_single_game_streams(game, count):
    streams = db_utils.get_n_games_filter_game(cursor, min(int(count), 60), game)
    return jsonify([json.loads(stream[0]) for stream in streams])

@app.route('/stats.json')
def get_stats_json():
    stats = (db_utils.get_stats())
    stats['load'] = get_sys_load()
    stats['rev'] = loaded_git_rev

    return jsonify(stats)

@app.route('/games.json')
@cache(ttl=datetime.timedelta(seconds=30))
def get_games_json():
    games = [game[0] for game in db_utils.get_games_list(cursor)]
    return jsonify(sorted(games))


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
