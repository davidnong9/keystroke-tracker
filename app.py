from flask import Flask, jsonify, render_template, request
from tracker import KeystrokeTrackerBackend

app = Flask(__name__)
tracker = KeystrokeTrackerBackend()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify(tracker.get_status())

@app.route('/api/history')
def history():
    return jsonify(tracker.get_history())

@app.route('/api/start', methods=['POST'])
def start():
    tracker.start()
    return jsonify({'success': True, 'status': tracker.get_status()})

@app.route('/api/stop', methods=['POST'])
def stop():
    tracker.stop()
    return jsonify({'success': True, 'status': tracker.get_status(), 'history': tracker.get_history()})

@app.route('/api/keypress', methods=['POST'])
def keypress():
    data = request.get_json(silent=True) or {}
    key = data.get('key')
    if key is None:
        return jsonify({'success': False, 'error': 'Missing key'}), 400
    tracker.record_key(key)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
