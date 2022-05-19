#!/usr/bin/env python3

from functools import partial
import json
import os
import datetime
import pprint

from asyncpg import create_pool
from sanic import Sanic
from sanic.response import json as sanic_json, text

app = Sanic(__name__)
app.ctx.cached_responses = {}

# the optimized query flow not guaranteed to return enough results
# how many queries should we make to try to hit our requested count before giving up
QUERY_FILL_LIMIT = 5

# use builtin json with unicode instead of sanic's
json_dumps = partial(json.dumps, separators=(",", ":"), ensure_ascii=False)

def get_from_dict_as_int_or_default(obj, key, default=0):
    try:
        return int(obj.get(key, default))
    except ValueError:
        return default

@app.listener('before_server_start')
async def register_db(app_handle, loop):
    app_handle.config['pool'] = await create_pool(
        dsn=f"postgres://{os.environ.get('NOBODY_USER')}:{os.environ.get('NOBODY_PASSWORD')}@{os.environ.get('NOBODY_HOST')}"
            f"/{os.environ.get('NOBODY_DATABASE')}",
        min_size=10,
        max_size=10,
        max_queries=1000,
        max_inactive_connection_lifetime=300,
        loop=loop)

@app.listener('after_server_stop')
async def close_connection(app_handle):
    pool = app_handle.config['pool']
    async with pool.acquire() as conn:
        await conn.close()

app.static('/', './static/index.html')
app.static('/static', './static')

# pylint: disable=too-many-statements,too-many-locals
@app.get('/stream')
async def get_streams(request):
    pool = request.app.config['pool']

    count = get_from_dict_as_int_or_default(request.args, 'count', 1)
    max_viewers = get_from_dict_as_int_or_default(request.args, 'max_viewers', 0)
    min_age = get_from_dict_as_int_or_default(request.args, 'min_age', 0)

    # include and exclude to handle comma separated values
    include = request.args.get('include', '').replace(',', ' ')
    exclude = request.args.get('exclude', '').replace(',', ' ')
    operator = request.args.get('search_operator', 'all')

    # do a moderate approximation of not falling over
    if count > 20 or len(include) + len(exclude) > 64:
        return text('Filter too large! Please request fewer records.', 413)

    include_list = include.split()
    exclude_list = exclude.split()

    if not include_list and not exclude_list and min_age == 0:
        # if we have no criteria we can optimize
        # select a large enough sample
        games_query = "SELECT data FROM streams TABLESAMPLE system_rows(250) WHERE viewer_count <= $1"

        async with pool.acquire() as conn:
            query_count = 1
            streams = await conn.fetch(games_query, max_viewers)
            extracted_streams = [json.loads(stream[0]) for stream in streams]

            # TABLESAMPLE not guaranteed to return enough rows, especially (mainly) after filtering
            # Issue additional queries up to QUERY_FILL_LIMIT to attempt to meet our quota
            # If not done, give up and return what we have
            while len(extracted_streams) < count and query_count < QUERY_FILL_LIMIT:
                new_streams = await conn.fetch(games_query, max_viewers)
                extracted_streams += [json.loads(stream[0]) for stream in new_streams]
                query_count += 1

            extracted_streams = extracted_streams[:count]
    else:
        # this is so hacky but it looks like how we have to do things for asyncpg.
        # if anyone knows of an easier way to do LIKE on ALL elements of a list (and inverse)
        # than this please tell me
        query_arg_string = ''
        query_arg_index = 1
        query_arg_list = []

        for exclusion in exclude_list:
            query_arg_string += f"AND lower(title_block) NOT LIKE ${query_arg_index} "
            query_arg_index += 1
            query_arg_list.append(f"%{exclusion.lower()}%")

        if min_age:
            query_arg_string += f"AND streamstart < (NOW() - interval '1 minute' * ${query_arg_index}) "
            query_arg_index += 1
            query_arg_list.append(min_age)

        query_arg_string += f"AND viewer_count <= ${query_arg_index} "
        query_arg_index += 1
        query_arg_list.append(max_viewers)

        if operator == "any":
            # dummy always-false value that lets us prefix with "or" without special-casing the first entry
            query_arg_string += "AND (1=2 "
            for inclusion in include_list:
                query_arg_string += f"OR lower(title_block) LIKE ${query_arg_index} "
                query_arg_index += 1
                query_arg_list.append(f"%{inclusion.lower()}%")
            query_arg_string += ") "
        else:
            # operator == "all"; include all search terms
            for inclusion in include_list:
                query_arg_string += f"AND lower(title_block) LIKE ${query_arg_index} "
                query_arg_index += 1
                query_arg_list.append(f"%{inclusion.lower()}%")

        query_arg_list.append(count)

        # 1=1 is dummy always-true value that lets us prefix with "and" without special-casing the first entry
        games_query = f"""
            SELECT data FROM streams
            WHERE 1=1
            {query_arg_string}
            ORDER BY RANDOM()
            LIMIT ${query_arg_index}"""

        async with pool.acquire() as conn:
            streams = await conn.fetch(games_query, *query_arg_list)
            extracted_streams = [json.loads(stream[0]) for stream in streams]

    if not streams:
        return sanic_json([], dumps=json_dumps)

    return sanic_json(extracted_streams, dumps=json_dumps)


@app.get('/stream/<stream_id>')
async def get_stream_details(request, stream_id):
    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        stream_details_query = "SELECT * FROM streams WHERE id = $1"
        stream_details = await conn.fetch(stream_details_query, stream_id)

        if not stream_details:
            return text('No such stream.', 410)

        twitch_data = json.loads(stream_details[0]['data'])

        now = datetime.datetime.now()
        scraped_at = datetime.datetime.fromtimestamp(stream_details[0]['time'])
        age = now - scraped_at
        start_age = now - stream_details[0]['streamstart']

        twitch_data['scraped_at_mins_ago'] = str(round(age.total_seconds() / 60, 2))
        twitch_data['streamstart_mins_ago'] = str(round(start_age.total_seconds() / 60, 2))
        return text(pprint.pformat(twitch_data))

@app.get('/stats/games')
async def get_stats_streams_by_game(request):
    now = datetime.datetime.now().timestamp()
    cache_key = 'streams_by_game'
    cache_max_age = 60

    if cache_key not in app.ctx.cached_responses:
        app.ctx.cached_responses[cache_key] = {
            'cached-since': 0,
            'max_age': cache_max_age,
            'response': None
        }
    if (now - app.ctx.cached_responses[cache_key]['cached-since']) < app.ctx.cached_responses[cache_key]['max_age']:
        return text(app.ctx.cached_responses[cache_key]['response'], headers={"x-cached-since": app.ctx.cached_responses[cache_key]['cached-since']})
    else:
        # continue with the function and capture the result at the end
        pass

    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        games_list_query = """
        SELECT s0.game,
            s0.streams_zero_viewer,
            s1.streams_one_viewer
        FROM   (SELECT game,
                    Count(*) AS streams_zero_viewer
                FROM   streams
                WHERE  viewer_count = 0
                GROUP  BY game) s0
            LEFT JOIN (SELECT game,
                                Count(*) AS streams_one_viewer
                        FROM   streams
                        WHERE  viewer_count = 1
                        GROUP  BY game) s1
                    ON ( s0.game = s1.game )
        ORDER BY s0.game DESC"""
        games_list_query = await conn.fetch(games_list_query)
        games_list_dict = {}
        for game in games_list_query:
            games_list_dict[game['game']] = {
              'one_viewer': game['streams_one_viewer'] or 0,
              'zero_viewer': game['streams_zero_viewer'] or 0}

        response = pprint.pformat(games_list_dict, sort_dicts=False)
        app.ctx.cached_responses[cache_key]['cached-since'] = now
        app.ctx.cached_responses[cache_key]['response'] = response

        return text(response, headers={"x-cached-since": now})

@app.get('/stats/counts')
async def get_stats_counts(request):
    now = datetime.datetime.now().timestamp()
    cache_key = 'counts'
    cache_max_age = 60

    if cache_key not in app.ctx.cached_responses:
        app.ctx.cached_responses[cache_key] = {
            'cached-since': 0,
            'max_age': cache_max_age,
            'response': None
        }
    if (now - app.ctx.cached_responses[cache_key]['cached-since']) < app.ctx.cached_responses[cache_key]['max_age']:
        return text(app.ctx.cached_responses[cache_key]['response'], headers={"x-cached-since": app.ctx.cached_responses[cache_key]['cached-since']})
    else:
        # continue with the function and capture the result at the end
        pass

    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        counts_query = """
        SELECT *
        FROM   (SELECT Count(*) AS zero_viewer_count
                FROM   streams
                WHERE  viewer_count = 0) AS zero,
            (SELECT Count(*) AS single_viewer_count
                FROM   streams
                WHERE  viewer_count = 1) AS one,
            (SELECT Count(*) AS total_count
                FROM   streams) AS total,
            (SELECT Count(DISTINCT game) AS unique_games
                FROM   streams) unique_games;
        """
        counts_query = dict(await conn.fetchrow(counts_query))

        response = pprint.pformat(counts_query, sort_dicts=False)
        app.ctx.cached_responses[cache_key]['cached-since'] = now
        app.ctx.cached_responses[cache_key]['response'] = response
        return text(response, headers={"x-cached-since": now})

@app.get('/stats/tags')
async def get_stats_tags(request):
    now = datetime.datetime.now().timestamp()
    cache_key = 'tags'
    cache_max_age = 60

    if cache_key not in app.ctx.cached_responses:
        app.ctx.cached_responses[cache_key] = {
            'cached-since': 0,
            'max_age': cache_max_age,
            'response': None
        }
    if (now - app.ctx.cached_responses[cache_key]['cached-since']) < app.ctx.cached_responses[cache_key]['max_age']:
        return text(app.ctx.cached_responses[cache_key]['response'], headers={"x-cached-since": app.ctx.cached_responses[cache_key]['cached-since']})
    else:
        # continue with the function and capture the result at the end
        pass

    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        data_query = "SELECT data from streams;"
        data_query = await conn.fetch(data_query)
        stream_data_list = [json.loads(stream['data']) for stream in data_query]

        tag_count = {}
        for stream in stream_data_list:
            for tag in stream['tags']:
                if tag in tag_count:
                    tag_count[tag] = tag_count[tag] + 1
                else:
                    tag_count[tag] = 1

        sorted_tag_count = dict(sorted(tag_count.items(), key=lambda item: item[1], reverse=True))

        response = pprint.pformat(sorted_tag_count, sort_dicts=False)
        app.ctx.cached_responses[cache_key]['cached-since'] = now
        app.ctx.cached_responses[cache_key]['response'] = response
        return text(response, headers={"x-cached-since": now})


if __name__ == "__main__":
    if os.environ.get('NOBODY_DEBUG'):
        app.run(host='0.0.0.0', port=5000, access_log=False, debug=True, auto_reload=True)
    else:
        app.run(host='0.0.0.0', port=8000, access_log=False, debug=False, fast=True)
