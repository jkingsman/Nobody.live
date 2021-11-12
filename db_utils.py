#!/usr/bin/env python3

import json
import time
import os

import psycopg2.extras

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION  IF NOT EXISTS tsm_system_rows;

CREATE TABLE IF NOT EXISTS streams (
    id   TEXT UNIQUE PRIMARY KEY,
    time INTEGER NOT NULL DEFAULT extract(epoch from now() at time zone 'utc'),
    game TEXT,
    lang TEXT,
    data TEXT
);

CREATE INDEX IF NOT EXISTS lowercase_game ON streams (lower(game));
CREATE INDEX IF NOT EXISTS lowercase_lang ON streams (lower(lang));
CREATE INDEX IF NOT EXISTS game_trgm ON streams USING gin (lower(game) gin_trgm_ops);

CREATE TABLE IF NOT EXISTS metadata (
    populate_started    INTEGER,
    time_of_ratelimit   INTEGER,
    ratelimit_limit     INTEGER,
    ratelimit_remaining INTEGER
);
"""

conn = psycopg2.connect(f"dbname='{os.environ.get('NOBODY_DATABASE')}' user='{os.environ.get('NOBODY_USER')}' host='{os.environ.get('NOBODY_HOST')}' password='{os.environ.get('NOBODY_PASSWORD')}'")
conn.autocommit = True

def migrate():
    with conn.cursor() as cursor:
        print("Migrating schema")
        cursor.execute(SCHEMA)

        print("Dropping and reloading metadata row")
        cursor.execute("TRUNCATE metadata;")
        cursor.execute("INSERT INTO metadata VALUES (extract(epoch from now() at time zone 'utc'), extract(epoch from now() at time zone 'utc'), 0, 0);")

def bulk_insert_streams(streams):
    formatted_rows = [(stream['id'], stream['game_name'], stream['language'], json.dumps(stream)) for stream in streams]
    insert_query = """
        INSERT INTO streams (id, game, lang, data) values %s
        ON CONFLICT(id) DO UPDATE
        SET time=extract(epoch from now() at time zone 'utc');"""

    with conn.cursor() as cursor:
        psycopg2.extras.execute_values (
            cursor, insert_query, formatted_rows, template=None, page_size=100
        )

def set_populate_started():
    with conn.cursor() as cursor:
        cursor.execute("UPDATE metadata SET populate_started = extract(epoch from now() at time zone 'utc')")

def set_ratelimit_data(ratelimit_limit, ratelimit_remaining):
    set_ratelimit_query = """
        UPDATE metadata SET
        time_of_ratelimit = extract(epoch from now() at time zone 'utc'),
        ratelimit_limit = %s,
        ratelimit_remaining = %s;"""

    with conn.cursor() as cursor:
        cursor.execute(set_ratelimit_query, (ratelimit_limit, ratelimit_remaining))

def get_games(count, include_list, exclude_list):
    if not include_list and not exclude_list:
        # if we have no criteria we can optimize
        games_query = f"""
            SELECT data FROM streams
            TABLESAMPLE system_rows(%s)"""

        with conn.cursor() as cursor:
            cursor.execute(games_query, [count])
            return cursor.fetchall()
    else:
        games_query = f"""
            SELECT data FROM streams
            WHERE 1=1
            {'AND lower(game) NOT LIKE %s ' * len(exclude_list)}
            {'AND lower(game) LIKE %s ' * len(include_list)}
            ORDER BY RANDOM()
            LIMIT %s"""

    wildcarded_exclusions = [f"%{exclude.lower()}%" for exclude in exclude_list]
    wildcarded_inclusions = [f"%{include.lower()}%" for include in include_list]

    with conn.cursor() as cursor:
        cursor.execute(games_query, [*wildcarded_exclusions, *wildcarded_inclusions, count])
        return cursor.fetchall()

def get_games_list_by_game():
    games_list_query = """
        SELECT game, count(*) FROM streams
        GROUP BY game"""

    with conn.cursor() as cursor:
        cursor.execute(games_list_query)
        return cursor.fetchall()

def get_stats():
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM metadata;")
        stats_dict = dict(cursor.fetchone())

        cursor.execute("SELECT count(*) as total FROM streams;")
        stats_dict['streams'] = cursor.fetchone()['total']

        return stats_dict

def get_stream_details(id):
    games_query = f"""
        SELECT * FROM streams
        WHERE id = %s"""

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(games_query, [id])
        return cursor.fetchone()

def prune(max_age_secs):
    age = time.time() - max_age_secs
    delete_query = """
        DELETE FROM streams
        WHERE time < %s;"""

    with conn.cursor() as cursor:
        cursor.execute(delete_query, [age])
