#!/usr/bin/env python3

import json
import logging
import os
import sys
import time

import redis
import requests

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# found at https://dev.twitch.tv/console
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    logging.error('CLIENT_ID or CLIENT_SECRET not set correctly! Exiting...')
    exit(1)

MAX_VIEWERS = 0  # number of viewers to be considered for inclusion
REQUEST_LIMIT = 1000  # number of API requests to stop at before starting a new search
SECONDS_BEFORE_RECORD_EXPIRATION = 180  # how many seconds a stream should stay in redis

r = redis.Redis()


def get_bearer_token(client_id, secret):
    payload = {'client_id': client_id,
               'client_secret': secret,
               'grant_type': 'client_credentials'}
    token_response = requests.post('https://id.twitch.tv/oauth2/token', params=payload)

    logging.debug(f"Issuing token request to {token_response.url}")

    try:
        logging.debug(f"Recieved {token_response.json()['access_token']}; expies in {token_response.json()['expires_in']}s")
        return(token_response.json()['access_token'])
    except KeyError:
        logging.error(f"Didn't find access token. Got '{token_response.text}'")
        return None


def get_stream_list_response(client_id, token, pagination_offset=None):
    headers = {'client-id': client_id,
               'Authorization': f'Bearer {token}'}

    url_params = {'first': '100',
                  'language': 'en'}
    if pagination_offset:
        url_params['after'] = pagination_offset

    stream_list = requests.get('https://api.twitch.tv/helix/streams', headers=headers, params=url_params)
    return stream_list


def populate_streamers():
    token = get_bearer_token(CLIENT_ID, CLIENT_SECRET)

    if not token:
        logging.error("There's no token; returning empty response")
        return []

    requests_sent = 1

    # eat page after page of API results until we hit our request limit
    stream_list = get_stream_list_response(CLIENT_ID, token)
    while requests_sent <= REQUEST_LIMIT:
        stream_list_data = stream_list.json()
        requests_sent += 1

        rate_limit_usage = round((1 - int(stream_list.headers['Ratelimit-Remaining']) / int(stream_list.headers['Ratelimit-Limit'])) * 100)

        # filter out streams with our desired count and inject into redis
        streams_found = list(filter(lambda stream: int(stream['viewer_count']) <= MAX_VIEWERS, stream_list_data['data']))
        for stream in streams_found:
            r.setex(json.dumps(stream), SECONDS_BEFORE_RECORD_EXPIRATION, time.time())

        if len(streams_found) > 0:
            logging.info(f"Inserted {len(streams_found)} streams")

        if requests_sent % 100 == 0:
            logging.info(f"{requests_sent} requests sent; API is {rate_limit_usage}% consumed")

        try:
            pagination_offset = stream_list_data['pagination']['cursor']
        except KeyError:
            # we hit the end of the list; no more keys
            break
        stream_list = get_stream_list_response(CLIENT_ID, token, pagination_offset)

while True:
    populate_streamers()
