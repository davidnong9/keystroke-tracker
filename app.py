from flask import Flask, jsonify, render_template, request, session
from tracker import KeystrokeTrackerBackend
import uuid

app = Flask(__name__)
app.secret_key = 'keystroke-tracker-secret-key'

# Store each user's tracker instance
user_trackers = {}

def get_user_tracker():
    """Get or create a tracker instance for the current user"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    user_id = session['user_id']
    if user_id not in user_trackers:
        user_trackers[user_id] = KeystrokeTrackerBackend()
    
    return user_trackers[user_id]

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
    return jsonify({'success': True, 'status': tracker.get_status()})

@app.route('/api/stop', methods=['POST'])
def stop():
    tracker = get_user_tracker()
    tracker.stop()
    return jsonify({'success': True, 'status': tracker.get_status(), 'history': tracker.get_history()})

@app.route('/api/keypress', methods=['POST'])
def keypress():
    data = request.get_json(silent=True) or {}
    key = data.get('key')
    if key is None:
        return jsonify({'success': False, 'error': 'Missing key'}), 400
    get_user_tracker().record_key(key)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
