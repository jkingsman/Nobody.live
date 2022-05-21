#!/usr/bin/env python3

import logging
import os
import sys
import time

import requests

import db_utils

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# found at https://dev.twitch.tv/console
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    logging.error("CLIENT_ID or CLIENT_SECRET not set correctly! Exiting...")
    sys.exit(1)

MAX_VIEWERS = 1  # number of viewers to be considered for inclusion
REQUEST_LIMIT = 1500  # number of API requests to stop at before starting a new search
MINIMUM_STREAMS_TO_GET = 50  # if REQUEST_LIMIT streams doesn't capture at least this many zero viewer streams, keep going

SECONDS_BEFORE_TAG_REFRESH = (
    600  # seconds between refreshes of the tag UUID=>name lookup object (~4s API call)
)

tag_id_and_name = {
    "data": {},
    "generation_time": 0,
}  # global object to resolve tags from


def get_bearer_token(client_id, secret):
    payload = {
        "client_id": client_id,
        "client_secret": secret,
        "grant_type": "client_credentials",
    }
    token_response = requests.post(
        "https://id.twitch.tv/oauth2/token", params=payload, timeout=4
    )

    logging.debug(f"Issuing token request to {token_response.url}")

    try:
        logging.debug(
            f"Recieved {token_response.json()['access_token']}; expires in {token_response.json()['expires_in']}s"
        )
        return token_response.json()["access_token"]
    except KeyError:
        logging.error(f"Didn't find access token. Got '{token_response.text}'")
        return None


def get_stream_list_response(session, client_id, token, pagination_offset=None):
    headers = {"client-id": client_id, "Authorization": f"Bearer {token}"}

    url_params = {"first": "100", "language": "en"}
    if pagination_offset:
        url_params["after"] = pagination_offset

    stream_list = session.get(
        "https://api.twitch.tv/helix/streams",
        headers=headers,
        params=url_params,
        timeout=4,
    )
    return stream_list


def load_tag_list(session, client_id, token):
    time_since_load = time.time() - tag_id_and_name["generation_time"]
    if time_since_load > SECONDS_BEFORE_TAG_REFRESH:
        logging.info(
            f"{time_since_load}s since tag refresh -- {time_since_load}s > {SECONDS_BEFORE_TAG_REFRESH}s; refreshing now..."
        )
        tag_id_and_name["generation_time"] = time.time()
    else:
        return

    headers = {"client-id": client_id, "Authorization": f"Bearer {token}"}
    url_params = {"first": "100"}

    tag_id_and_name["data"] = {}

    while True:
        tag_response = session.get(
            "https://api.twitch.tv/helix/tags/streams",
            headers=headers,
            params=url_params,
            timeout=4,
        ).json()

        for tag in tag_response["data"]:
            tag_id_and_name["data"][tag["tag_id"]] = tag["localization_names"]["en-us"]

        if "cursor" not in tag_response["pagination"]:  # on the last page
            break
        url_params["after"] = tag_response["pagination"]["cursor"]

    logging.info(f"{len(tag_id_and_name['data'])} tags loaded")


def resolve_tag_ids_to_names_in_stream_object(stream):
    # handle possible empty tag lists or unexpectedly missing tag field
    if "tag_ids" not in stream or not stream["tag_ids"]:
        stream["tags"] = []
        return stream

    resolved_tags = []
    for tag_id in stream["tag_ids"]:
        try:
            resolved_tags.append(tag_id_and_name["data"][tag_id])
        except KeyError:
            logging.error(f"Unknown tag '{tag_id}'!")
            continue

    stream["tags"] = resolved_tags
    return stream


def populate_streamers(client_id, client_secret, generation):
    token = get_bearer_token(client_id, client_secret)
    requests_session = requests.Session()

    if not token:
        logging.error("There's no token! Halting.")
        return

    load_tag_list(requests_session, client_id, token)

    requests_sent = 1
    streams_grabbed = 0

    # eat page after page of API results until we hit our request limit
    stream_list = get_stream_list_response(requests_session, client_id, token)
    while requests_sent <= REQUEST_LIMIT or streams_grabbed < MINIMUM_STREAMS_TO_GET:
        stream_list_data = stream_list.json()
        requests_sent += 1

        # filter out streams with our desired count and inject into the db
        raw_streams = list(
            filter(
                lambda stream: int(stream["viewer_count"]) <= MAX_VIEWERS,
                stream_list_data["data"],
            )
        )
        tag_resolved_streams = list(
            map(resolve_tag_ids_to_names_in_stream_object, raw_streams)
        )
        db_utils.bulk_insert_streams(tag_resolved_streams, generation)
        streams_grabbed += len(tag_resolved_streams)

        # report on what we inserted
        if len(tag_resolved_streams) > 0:
            logging.debug(f"Inserted {len(tag_resolved_streams)} streams")

        # sleep on rate limit token utilization
        rate_limit_usage = round(
            (
                1
                - int(stream_list.headers["Ratelimit-Remaining"])
                / int(stream_list.headers["Ratelimit-Limit"])
            )
            * 100
        )
        if rate_limit_usage > 60:
            logging.warning(
                f"Rate limiting is at {rate_limit_usage}% utilized; sleeping for 30s"
            )
            time.sleep(30)

        # drop a status every now and again
        if requests_sent % 10 == 0:
            logging.info(
                (
                    f"{requests_sent} requests sent ({streams_grabbed} streams found); "
                    f"{stream_list.headers['Ratelimit-Remaining']} of {stream_list.headers['Ratelimit-Limit']} "
                    f"API tokens remaining ({rate_limit_usage}% utilized)"
                )
            )
            time.sleep(1)

        # aaaaand do it again
        try:
            pagination_offset = stream_list_data["pagination"]["cursor"]
        except KeyError:
            # we hit the end of the list; no more keys
            logging.warning("Hit end of search results")
            break
        stream_list = get_stream_list_response(
            requests_session, client_id, token, pagination_offset
        )


if __name__ == "__main__":
    db_utils.migrate()
    while True:
        current_generation = int(time.time())
        populate_streamers(CLIENT_ID, CLIENT_SECRET, current_generation)
        db_utils.prune_all_but_generation(current_generation)
