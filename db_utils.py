import sqlite3

DB_NAME = 'streams.db'

def get_connection():
    return sqlite3.connect(DB_NAME, isolation_level=None)

def migrate():
    conn = sqlite3.connect(DB_NAME, isolation_level=None)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS streams
                (id integer, time_loaded integer, game text, stream_data text)''')

    cur.execute('''CREATE INDEX IF NOT EXISTS idx_streams_time_loaded
                ON streams (time_loaded)''')

    cur.execute('''CREATE INDEX IF NOT EXISTS idx_streams_game
                ON streams (game)''')

    cur.close()
    conn.close()
