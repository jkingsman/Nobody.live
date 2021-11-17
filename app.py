#!/usr/bin/env python3

import json
import os
import datetime

from asyncpg import create_pool
from sanic import Sanic
from sanic.response import json as jsonify, text

app = Sanic(__name__)

@app.listener('before_server_start')
async def register_db(app, loop):
    app.config['pool'] = await create_pool(
        dsn=f"postgres://{os.environ.get('NOBODY_USER')}:{os.environ.get('NOBODY_PASSWORD')}@{os.environ.get('NOBODY_HOST')}/{os.environ.get('NOBODY_DATABASE')}",
        min_size=10,
        max_size=10,
        max_queries=1000,
        max_inactive_connection_lifetime=300,
        loop=loop)

@app.listener('after_server_stop')
async def close_connection(app, loop):
    pool = app.config['pool']
    async with pool.acquire() as conn:
        await conn.close()

app.static('/', './static/index.html')
app.static('/', './static')

@app.get('/stream')
async def get_streams(request):
    pool = request.app.config['pool']

    count = int(request.args.get('count', 1))
    include = request.args.get('include', '')
    exclude = request.args.get('exclude', '')

    # do a moderate approximation of not falling over
    if count > 64 or len(include) + len(exclude) > 64:
        return text('Filter too large! Please request fewer records.', 413)

    include_list = include.split()
    exclude_list = exclude.split()

    if not include_list and not exclude_list:
        # if we have no criteria we can optimize
        games_query = "SELECT data FROM streams TABLESAMPLE system_rows($1)"

        async with pool.acquire() as conn:
            streams = await conn.fetch(games_query, count)
    else:
        # this is so hacky but it looks like how we have to do things for asyncpg.
        # if anyone knows of an easier way to do LIKE on ALL elements of a list than this
        # please tell me
        query_arg_string = ''
        query_arg_index = 1
        for _exclusion in exclude_list:
            query_arg_string += f"AND lower(game) NOT LIKE ${query_arg_index} "
            query_arg_index += 1
        for _inclusion in include_list:
            query_arg_string += f"AND lower(game) LIKE ${query_arg_index} "
            query_arg_index += 1

        games_query = f"""
            SELECT data FROM streams
            WHERE 1=1
            {query_arg_string}
            ORDER BY RANDOM()
            LIMIT ${query_arg_index}"""

        wildcarded_exclusions = [f"%{exclude.lower()}%" for exclude in exclude_list]
        wildcarded_inclusions = [f"%{include.lower()}%" for include in include_list]

        async with pool.acquire() as conn:
            streams = await conn.fetch(games_query, *(wildcarded_exclusions + wildcarded_inclusions), count)

    if not streams:
        return jsonify([])

    extracted_streams = [json.loads(stream[0]) for stream in streams]
    return jsonify(extracted_streams)


@app.get('/stream/<id>')
async def get_stream_details(request, id):
    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        stream_details_query = f"SELECT * FROM streams WHERE id = $1"
        stream_details = await conn.fetch(stream_details_query, id)

        if not stream_details:
            return text('No such stream.', 410)

        twitch_data = json.loads(stream_details[0]['data'])

        now = datetime.datetime.now()
        scraped_at = datetime.datetime.fromtimestamp(stream_details[0]['time'])
        age = now - scraped_at

        twitch_data['scraped_at'] = stream_details[0]['time']
        twitch_data['scraped_at_seconds_ago'] = age.total_seconds()
        return jsonify(twitch_data)


if __name__ == "__main__":
    if os.environ.get('NOBODY_DEBUG'):
        app.run(host='0.0.0.0', port=5000, access_log=False, debug=True)
    else:
        app.run(host='0.0.0.0', port=8000, access_log=False, debug=False)
