#!/usr/bin/env python3

import json
import time
import os

from dateutil import parser
import psycopg2.extras

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS tsm_system_rows;

CREATE TABLE IF NOT EXISTS streams (
    id   TEXT UNIQUE PRIMARY KEY,
    time INTEGER NOT NULL DEFAULT extract(epoch from now() at time zone 'utc'),
    game TEXT,
    streamstart TIMESTAMP,
    lang TEXT,
    data TEXT
);

CREATE INDEX IF NOT EXISTS lowercase_game ON streams (lower(game));
CREATE INDEX IF NOT EXISTS lowercase_lang ON streams (lower(lang));
CREATE INDEX IF NOT EXISTS game_trgm ON streams USING gin (lower(game) gin_trgm_ops);
"""

conn = psycopg2.connect(f"dbname='{os.environ.get('NOBODY_DATABASE')}' user='{os.environ.get('NOBODY_USER')}' host='{os.environ.get('NOBODY_HOST')}' password='{os.environ.get('NOBODY_PASSWORD')}'")
conn.autocommit = True


def migrate():
    with conn.cursor() as cursor:
        print("Migrating schema")
        cursor.execute(SCHEMA)


def bulk_insert_streams(streams):
    formatted_rows = [(stream['id'], stream['game_name'], parser.parse(stream['started_at']), stream['language'], json.dumps(stream)) for stream in streams]
    insert_query = """
        INSERT INTO streams (id, game, streamstart, lang, data) values %s
        ON CONFLICT(id) DO UPDATE
        SET time=extract(epoch from now() at time zone 'utc');"""

    with conn.cursor() as cursor:
        psycopg2.extras.execute_values (
            cursor, insert_query, formatted_rows, template=None, page_size=100
        )


def prune(max_age_secs):
    age = time.time() - max_age_secs
    delete_query = """
        DELETE FROM streams
        WHERE time < %s;"""

    with conn.cursor() as cursor:
        cursor.execute(delete_query, [age])
