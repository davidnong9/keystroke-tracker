import threading
from datetime import datetime


class KeystrokeTrackerBackend:
    def __init__(self):
        self.count = 0
        self.key_counts = {}
        self.running = False
        self.sessions = []
        self.session_start_count = 0
        self.session_start_time = None
        self.lock = threading.RLock()  # reentrant — safe to acquire from within the same thread

    def start(self):
        with self.lock:
            if self.running:
                return
            self.running = True
            self.count = 0  # Reset count for each new session
            self.session_start_count = 0
            self.key_counts = {}
            self.session_start_time = datetime.now()

    def stop(self):
        with self.lock:
            if not self.running:
                return
            self.running = False
            session_keystrokes = self.count - self.session_start_count
            duration_string = self._format_duration(self._get_duration_seconds())
            self.sessions.append({
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration': duration_string,
                'keystrokes': session_keystrokes,
                'top_keys': self._top_keys_str(),
            })
            self.session_start_time = None

    def record_key(self, key):
        with self.lock:
            if not self.running:
                return
            self.count += 1
            self.key_counts[key] = self.key_counts.get(key, 0) + 1

    def _top_keys_str(self, n=3):
        """Return a formatted string of the top n keys by press count."""
        sorted_keys = sorted(self.key_counts.items(), key=lambda x: x[1], reverse=True)[:n]
        return ', '.join(f"{k}({v})" for k, v in sorted_keys) if sorted_keys else 'None'

    def _top_keys_data(self, n=3):
        """Return top n keys as a list of dicts for the chart."""
        sorted_keys = sorted(self.key_counts.items(), key=lambda x: x[1], reverse=True)[:n]
        return [{'key': k, 'count': v} for k, v in sorted_keys]

    def _get_duration_seconds(self):
        if not self.session_start_time:
            return 0
        return int((datetime.now() - self.session_start_time).total_seconds())

    def _format_duration(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02}:{minutes:02}:{secs:02}"

    def get_status(self):
        with self.lock:
            return {
                'running': self.running,
                'count': self.count,
                'top_keys': self._top_keys_str(),
                'top_keys_data': self._top_keys_data(),
                'duration': self._format_duration(self._get_duration_seconds()) if self.running else '00:00:00',
            }

    def get_history(self):
        with self.lock:
            return list(self.sessions)