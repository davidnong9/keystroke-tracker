from flask import Flask, jsonify, render_template, request, session
from tracker import KeystrokeTrackerBackend
from datetime import datetime, timezone
import uuid
import os

app = Flask(__name__)
secret = os.environ.get('SECRET_KEY')
if not secret:
    raise RuntimeError("SECRET_KEY environment variable is required")
app.secret_key = secret

def get_user_tracker():
    """Get or create a tracker instance for the current user using Flask session."""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

    if 'tracker_data' not in session:
        session['tracker_data'] = {
            'count': 0,
            'key_counts': {},
            'running': False,
            'sessions': [],
            'session_start_count': 0,
            'session_start_time': None
        }

    tracker = KeystrokeTrackerBackend()
    data = session['tracker_data']
    tracker.count = data['count']
    tracker.key_counts = data['key_counts']
    tracker.running = data['running']
    tracker.sessions = data['sessions']
    tracker.session_start_count = data['session_start_count']

    # Deserialize session_start_time back to a timezone-aware datetime if present
    raw_time = data['session_start_time']
    if raw_time is None:
        tracker.session_start_time = None
    elif isinstance(raw_time, datetime):
        # Ensure it's timezone-aware
        if raw_time.tzinfo is None:
            tracker.session_start_time = raw_time.replace(tzinfo=timezone.utc)
        else:
            tracker.session_start_time = raw_time
    else:
        # Stored as an ISO string — parse it back to datetime
        tracker.session_start_time = datetime.fromisoformat(str(raw_time)).replace(tzinfo=timezone.utc)

    return tracker

def save_tracker_state(tracker):
    """Save tracker state back to Flask session."""
    session['tracker_data'] = {
        'count': tracker.count,
        'key_counts': tracker.key_counts,
        'running': tracker.running,
        'sessions': tracker.sessions,
        'session_start_count': tracker.session_start_count,
        # Store as ISO string so Flask can safely serialize/deserialize it
        'session_start_time': tracker.session_start_time.isoformat() if tracker.session_start_time else None,
    }
    session.modified = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify(get_user_tracker().get_status())

@app.route('/api/history')
def history():
    return jsonify(get_user_tracker().get_history())

@app.route('/api/start', methods=['POST'])
def start():
    tracker = get_user_tracker()
    tracker.start()
    save_tracker_state(tracker)
    return jsonify({'success': True, 'status': tracker.get_status()})

@app.route('/api/stop', methods=['POST'])
def stop():
    tracker = get_user_tracker()
    tracker.stop()
    save_tracker_state(tracker)
    return jsonify({'success': True, 'status': tracker.get_status(), 'history': tracker.get_history()})

@app.route('/api/keypress', methods=['POST'])
def keypress():
    data = request.get_json(silent=True) or {}
    key = data.get('key')
    if key is None:
        return jsonify({'success': False, 'error': 'Missing key'}), 400
    tracker = get_user_tracker()
    tracker.record_key(key)
    save_tracker_state(tracker)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)