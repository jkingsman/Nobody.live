# nodbody.live

## PainfulSines Notes

This fork and branch are an experement, where I am trying to recreate the front-end of Nobody[dot]live but with CSS grid, the file I am messing with is in the folder ```static/test/```, I am in no way garenteeing that this will work in production or in any way, as it is more of my own personal exploration of CSS grid, if you would like you can use the code I wrote here, just don't blame me if doing so leads directly to thermonuclear war...

## Architecture

A worker script (`scanner.py`) loops through the Twitch API's list of streams and spins until it inserts all streamers it finds matching the search criteria (default zero viewers), then it starts again. These streamers are pruned after a set number of seconds (`SECONDS_BEFORE_RECORD_EXPIRATION`) on the assumption that someone will view them and then they won't have zero viewers any more so should not be served for too long.

Environment variables needed for both scanner and app:

* `NOBODY_HOST`: the database host
* `NOBODY_DATABASE`: the database name
* `NOBODY_USER`: the database user
* `NOBODY_PASSWORD`: the database password

Environment variables to be set for the scanner only:

* `CLIENT_ID`: Your Twitch application client ID (found at https://dev.twitch.tv/console)
* `CLIENT_SECRET`: Your Twitch application client secret (found at https://dev.twitch.tv/console)

Meanwhile, the Flask app in `app.py` serves the index and the endpoint to get a random streamer.

## Getting Up and Running

* Install and start Postgres with a created database
* Run the stream fetcher (e.g. `CLIENT_ID=xxxxxx CLIENT_SECRET=xxxxxx scanner.py`). This will need to run continuously. Be sure to include your database credentials.
* Run the flask app (`flask run`). Be sure to include your database credentials.

This is obviously not production ready; you'll need to make sure all services are running as daemons (some config files are included in `etc`) and that your flask app is running safely (e.g. behind gunicorn/nginx/pick your poison).

## Dependencies

Update direct dependencies in `requirements.in`; use `pip-compile` to compile them down to `requirements.txt` if you update them.

## Components

* [Loading throbber Copyright (c) 2014 Sam Herbert](https://github.com/SamHerbert/SVG-Loaders)
* [Micromodal Copyright (c) 2017 Indrashish Ghosh](https://github.com/Ghosh/micromodal)
