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
    viewer_count INTEGER,
    title_block TEXT,
    game TEXT,
    generation INTEGER,
    streamstart TIMESTAMP,
    data TEXT
);

ALTER TABLE streams ADD COLUMN IF NOT EXISTS title_block text;
ALTER TABLE streams ADD COLUMN IF NOT EXISTS generation INTEGER;

CREATE INDEX IF NOT EXISTS viewer_count ON streams (viewer_count);
CREATE INDEX IF NOT EXISTS lowercase_title_block ON streams (lower(title_block));
CREATE INDEX IF NOT EXISTS title_block_trgm ON streams USING gin (lower(title_block) gin_trgm_ops);
"""

conn = psycopg2.connect(f"dbname='{os.environ.get('NOBODY_DATABASE')}' user='{os.environ.get('NOBODY_USER')}' "
                        f"host='{os.environ.get('NOBODY_HOST')}' password='{os.environ.get('NOBODY_PASSWORD')}'")
conn.autocommit = True


def migrate():
    with conn.cursor() as cursor:
        print("Migrating schema")
        cursor.execute(SCHEMA)

def bulk_insert_streams(streams, generation):
    if streams:
        formatted_rows = [(
            stream['id'],
            stream['game_name'],
            f"{stream['game_name']} {' '.join(stream['tags']).strip()}",
            stream['viewer_count'],
            generation,
            parser.parse(stream['started_at']),
            json.dumps(stream)) for stream in streams]

        insert_query = """
            INSERT INTO streams (id, game, title_block, viewer_count, generation, streamstart, data) values %s
            ON CONFLICT(id) DO UPDATE
            SET time=extract(epoch from now() at time zone 'utc');"""

        with conn.cursor() as cursor:
            psycopg2.extras.execute_values (
                cursor, insert_query, formatted_rows, template=None, page_size=100
            )

def prune_all_but_generation(generation):
    delete_query = """
        DELETE FROM streams
        WHERE generation != %s;"""

    with conn.cursor() as cursor:
        cursor.execute(delete_query, [generation])
