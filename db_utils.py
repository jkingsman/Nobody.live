import sqlite3

DB_NAME_FILE = 'streams.db'
DB_NAME_MEMORY = 'file:memory?cache=shared&mode=memory'

def get_connection():
    return sqlite3.connect(DB_NAME_MEMORY, uri=True)

def get_cursor():
    return get_connection().cursor()

def migrate():
    conn = sqlite3.connect(DB_NAME_MEMORY, uri=True)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS streams
                (id integer, time_loaded integer, game text, stream_data text)''')

    cur.execute('''CREATE INDEX IF NOT EXISTS idx_streams_time_loaded
                ON streams (time_loaded)''')

    cur.execute('''CREATE INDEX IF NOT EXISTS idx_streams_game
                ON streams (game)''')

    cur.close()
    conn.close()
