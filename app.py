from flask import Flask, jsonify, render_template, request, session
from tracker import KeystrokeTrackerBackend
from datetime import datetime, timezone
import uuid
import os
import psycopg2
import psycopg2.extras
import json

app = Flask(__name__)
secret = os.environ.get('SECRET_KEY')
if not secret:
    raise RuntimeError("SECRET_KEY environment variable is required")
app.secret_key = secret

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

# Heroku provides postgres:// but psycopg2 requires postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)


def get_db():
    """Open a new database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_user_id():
    """Get or create a unique user_id stored in the session cookie."""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']


def get_user_tracker(user_id):
    """Load tracker state for a user from Postgres."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tracker_state WHERE user_id = %s", (user_id,))
            row = cur.fetchone()

        tracker = KeystrokeTrackerBackend()
        if row:
            tracker.count = row['count']
            tracker.key_counts = row['key_counts'] or {}
            tracker.running = row['running']
            tracker.session_start_count = row['session_start_count']

            raw_time = row['session_start_time']
            if raw_time is None:
                tracker.session_start_time = None
            elif isinstance(raw_time, datetime):
                tracker.session_start_time = raw_time.replace(tzinfo=timezone.utc) if raw_time.tzinfo is None else raw_time
            else:
                tracker.session_start_time = datetime.fromisoformat(str(raw_time)).replace(tzinfo=timezone.utc)

            # Load session history
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT time, duration, keystrokes, top_keys FROM sessions WHERE user_id = %s ORDER BY id ASC",
                    (user_id,)
                )
                tracker.sessions = [dict(r) for r in cur.fetchall()]
        return tracker
    finally:
        conn.close()


def save_tracker_state(user_id, tracker):
    """Upsert tracker state and session history for a user into Postgres."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Upsert live tracker state
            cur.execute("""
                INSERT INTO tracker_state (user_id, count, key_counts, running, session_start_count, session_start_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    count = EXCLUDED.count,
                    key_counts = EXCLUDED.key_counts,
                    running = EXCLUDED.running,
                    session_start_count = EXCLUDED.session_start_count,
                    session_start_time = EXCLUDED.session_start_time
            """, (
                user_id,
                tracker.count,
                json.dumps(tracker.key_counts),
                tracker.running,
                tracker.session_start_count,
                tracker.session_start_time.isoformat() if tracker.session_start_time else None,
            ))

            # Sync session history — delete and re-insert to keep it simple
            cur.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
            for s in tracker.sessions:
                cur.execute("""
                    INSERT INTO sessions (user_id, time, duration, keystrokes, top_keys)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, s['time'], s['duration'], s['keystrokes'], s['top_keys']))

        conn.commit()
    finally:
        conn.close()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify(get_user_tracker(get_user_id()).get_status())

@app.route('/api/history')
def history():
    return jsonify(get_user_tracker(get_user_id()).get_history())

@app.route('/api/start', methods=['POST'])
def start():
    user_id = get_user_id()
    tracker = get_user_tracker(user_id)
    tracker.start()
    save_tracker_state(user_id, tracker)
    return jsonify({'success': True, 'status': tracker.get_status()})

@app.route('/api/stop', methods=['POST'])
def stop():
    user_id = get_user_id()
    tracker = get_user_tracker(user_id)
    tracker.stop()
    save_tracker_state(user_id, tracker)
    return jsonify({'success': True, 'status': tracker.get_status(), 'history': tracker.get_history()})

@app.route('/api/keypress', methods=['POST'])
def keypress():
    data = request.get_json(silent=True) or {}
    key = data.get('key')
    if key is None:
        return jsonify({'success': False, 'error': 'Missing key'}), 400
    user_id = get_user_id()
    tracker = get_user_tracker(user_id)
    tracker.record_key(key)
    save_tracker_state(user_id, tracker)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)