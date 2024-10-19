# nobody.live

## Architecture

A worker script (`scanner.py`) loops through the Twitch API's list of streams and spins until it inserts all streamers it finds matching the search criteria (default zero viewers), then it starts again. These stale streams are pruned after a fresh reload occurs on the assumption that someone will view them and then they won't have zero viewers any more so should not be served for too long; we'll pick them back up on the next load if they're still viewerless.

Environment variables needed for _both_ scanner and app:

* `NOBODY_HOST`: the database host
* `NOBODY_DATABASE`: the database name
* `NOBODY_USER`: the database user
* `NOBODY_PASSWORD`: the database password

Environment variables to be set for the scanner only:

* `CLIENT_ID`: Your Twitch application client ID (found at https://dev.twitch.tv/console)
* `CLIENT_SECRET`: Your Twitch application client secret (found at https://dev.twitch.tv/console)

Meanwhile, the Sanic app in `app.py` serves the index and the endpoint to get a random streamer.

*Note that the database schema makes use of slightly unusual extensions, namely `pg_trgm` (trigram indices) and `tsm_system_rows`. You may need to install your operating system's flavor of `postgresql-contrib` in order for them to work correctly. Also, you may need to grant your service user superuser permissions OR remove the extension creation calls from the `db_utils.py` migration block.*

## Getting Up and Running

* Install and start Postgres with a created database
* Run the stream fetcher (e.g. `python scanner.py`). This will need to run continuously. Be sure to include your database credentials in the environment variables. This also performs the initial database schema migration; additional modifications to the schema may require dropping tables/etc. See `db_utils.py` for the exact schema.
* Run the server app (`python app.py`). Be sure to include your database credentials in the environment variables.

This is obviously not production ready; you'll need to make sure all services are running as daemons (an example `supervisord` config is included in `etc`) and that your Sanic app is running safely (e.g. behind gunicorn/nginx/pick your poison).

## Dependencies

Update direct dependencies in `requirements.in`; use `pip-compile` to compile them down to `requirements.txt` if you update them.

## Components

* [Micromodal Copyright (c) 2017 Indrashish Ghosh](https://github.com/Ghosh/micromodal)
* Backgound image CC BY 4.0 [SVGBackgrounds.com](https://www.svgbackgrounds.com/)


## Cite this work

If you reference Nobody.live in a paper, check out the CITATION.cff file for the correct citation.

```bibtex
@misc{Nobody.live,
url={https://nobody.live/},
journal={Nobody.live},
publisher={Jack Kingsman},
author={Kingsman, Jack},
year={2020},
month={Nov},
note={{\url{https://github.com/jkingsman/Nobody.live}}}
}
```
