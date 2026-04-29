"""
Run this once to create the required tables in your Heroku Postgres database.

    heroku run python init_db.py --app top3-keystroke-tracker-3919d782d8aa
"""
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

conn = psycopg2.connect(DATABASE_URL)
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracker_state (
            user_id            TEXT PRIMARY KEY,
            count              INTEGER NOT NULL DEFAULT 0,
            key_counts         JSONB NOT NULL DEFAULT '{}',
            running            BOOLEAN NOT NULL DEFAULT FALSE,
            session_start_count INTEGER NOT NULL DEFAULT 0,
            session_start_time TIMESTAMPTZ
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES tracker_state(user_id) ON DELETE CASCADE,
            time        TEXT NOT NULL,
            duration    TEXT NOT NULL,
            keystrokes  INTEGER NOT NULL,
            top_keys    TEXT NOT NULL
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions(user_id);")
conn.commit()
conn.close()
print("Database tables created successfully.")