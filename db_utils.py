#!/usr/bin/env python3

import json
import time
import os

import psycopg2.extras

SCHEMA = """
CREATE TABLE IF NOT EXISTS streams (
    id   TEXT UNIQUE PRIMARY KEY,
    time INTEGER NOT NULL DEFAULT extract(epoch from now() at time zone 'utc'),
    game TEXT,
    lang TEXT,
    data TEXT
);

CREATE INDEX IF NOT EXISTS lowercase_game ON streams ((lower(game)));
CREATE INDEX IF NOT EXISTS lowercase_lang ON streams ((lower(lang)));

CREATE TABLE IF NOT EXISTS metadata (
    populate_started    INTEGER,
    time_of_ratelimit   INTEGER,
    ratelimit_limit     INTEGER,
    ratelimit_remaining INTEGER
);
"""

def get_cursor():
    conn = psycopg2.connect(f"dbname='{os.environ.get('NOBODY_DATABASE')}' user='{os.environ.get('NOBODY_USER')}' host='{os.environ.get('NOBODY_HOST')}' password='{os.environ.get('NOBODY_PASSWORD')}'")
    conn.autocommit = True
    return conn.cursor()

def get_dict_cursor():
    conn = psycopg2.connect(f"dbname='{os.environ.get('NOBODY_DATABASE')}' user='{os.environ.get('NOBODY_USER')}' host='{os.environ.get('NOBODY_HOST')}' password='{os.environ.get('NOBODY_PASSWORD')}'")
    conn.autocommit = True
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def migrate():
    cursor = get_cursor()
    print("Migrating schema")
    cursor.execute(SCHEMA)

    print("Dropping and reloading metadata row")
    cursor.execute("TRUNCATE metadata;")
    cursor.execute("INSERT INTO metadata VALUES (extract(epoch from now() at time zone 'utc'), extract(epoch from now() at time zone 'utc'), 0, 0);")

def bulk_insert_streams(cursor, streams):
    formatted_rows = [(stream['id'], stream['game_name'], stream['language'], json.dumps(stream)) for stream in streams]
    insert_query = """
        INSERT INTO streams (id, game, lang, data) values %s
        ON CONFLICT(id) DO UPDATE
            SET time=extract(epoch from now() at time zone 'utc');
    """
    psycopg2.extras.execute_values (
        cursor, insert_query, formatted_rows, template=None, page_size=100
    )

def set_populate_started(cursor):
    cursor.execute("UPDATE metadata SET populate_started = extract(epoch from now() at time zone 'utc')")

def set_ratelimit_data(cursor, ratelimit_limit, ratelimit_remaining):
    set_ratelimit_query = """UPDATE metadata SET
                    time_of_ratelimit = extract(epoch from now() at time zone 'utc'),
                    ratelimit_limit = %s,
                    ratelimit_remaining = %s;
    """
    cursor.execute(set_ratelimit_query, (ratelimit_limit, ratelimit_remaining))

def get_stats():
    cursor = get_dict_cursor()
    cursor.execute("SELECT * FROM metadata;")
    stats_dict = dict(cursor.fetchone())

    cursor.execute("SELECT count(*) as total FROM streams;")
    stats_dict['streams'] = cursor.fetchone()['total']

    return stats_dict

def get_n_games(cursor, count):
    games_query = """SELECT data FROM streams
                    ORDER BY RANDOM()
                    LIMIT %s"""
    cursor.execute(games_query, [count])
    return cursor.fetchall()

def get_n_games_filter_game(cursor, count, game):
    games_query = """SELECT data FROM streams
                    WHERE lower(game) LIKE %s
                    ORDER BY RANDOM()
                    LIMIT %s"""
    cursor.execute(games_query, [f"%{game.lower()}%", count])
    return cursor.fetchall()

def get_games_list(cursor):
    games_list_query = """SELECT game FROM streams
                    GROUP BY game"""
    cursor.execute(games_list_query)
    return cursor.fetchall()

def prune(cursor, max_age_secs):
    age = time.time() - max_age_secs
    delete_query = """DELETE FROM streams
                      WHERE time < %s;"""
    cursor.execute(delete_query, [age])
