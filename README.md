# Keystroke Tracker

A web-based keystroke tracking app built with Flask, and a standalone desktop version built with Tkinter. Track how many keys you press, see your top 3 most-used keys in real time, and review your session history. Try it live: [Keystroke Tracker](https://top3-keystroke-tracker-3919d782d8aa.herokuapp.com/)

## Features

- Start/stop tracking sessions from the browser or desktop app
- Live keystroke count and session timer
- Top 3 most-pressed keys with bar and pie chart visualization
- Session history table with duration, keystrokes, and top keys per session
- Multi-user support via per-user session cookies (web app)

## Project Structure

```
├── app.py          # Flask web server and API routes
├── tracker.py      # Core tracking logic (shared by web and desktop)
├── main.py         # Standalone desktop app (Tkinter)
├── templates/
│   └── index.html  # Web UI
├── static/
│   └── style.css   # Styles
├── Procfile        # Heroku process definition
├── requirements.txt
└── runtime.txt     # (deprecated — replace with .python-version)
```

## Local Setup

**Requirements:** Python 3.11+

1. Clone the repo and install dependencies:

```bash
pip install -r requirements.txt
```

2. Set a secret key environment variable:

```bash
export SECRET_KEY=your-secret-key-here
```

3. Run the web app:

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

**Or run the desktop app instead:**

```bash
python main.py
```

## Global Keystroke Tracking (Desktop)

The web app can only capture keypresses while the browser tab is focused. If you want to track keystrokes system-wide — across all apps and windows — you need to run the desktop app (`main.py`) on your local machine.

### Setup

1. Make sure Python 3.11+ is installed — download from [python.org](https://python.org)

2. Install dependencies:

```bash
pip install pynput requests
```

3. Open `main.py` and confirm the server URL points to your hosted app:

```python
SERVER_URL = "https://top3-keystroke-tracker-3919d782d8aa.herokuapp.com"
```

4. Run it:

```bash
python main.py
```

5. Click **Start Tracking** — keystrokes will be captured system-wide and synced to the web app in real time. You can then view your stats in the browser from any device.

**Mac users:** You'll need to grant Accessibility permissions when prompted. Go to System Preferences → Privacy & Security → Accessibility and enable the terminal or app running `main.py`. This is required for `pynput` to read global keypresses.

### Who cannot use global tracking

Global keystroke tracking is not available in all situations. Users in the following cases are limited to browser-only tracking via the web app:

- **Chromebook / ChromeOS users** — no Python runtime available by default
- **iOS and Android users** — mobile operating systems do not allow apps to read keypresses from other apps
- **Users without install rights** — installing Python or running local scripts may be blocked on managed or corporate machines
- **Linux users without X11** — `pynput` requires an X display server and does not currently support Wayland natively
- **Mac users who decline Accessibility permissions** — without this permission, `pynput` cannot read global keypresses on macOS

These users can still use the web app fully — they just won't be able to capture keypresses made outside the browser tab.

## How It Works

**Web app:** The browser captures `keydown` events via JavaScript and sends each keypress to `/api/keypress`. The Flask backend stores all tracker state in a signed session cookie, keyed by a unique user ID. The UI polls `/api/status` every second to update the live count, timer, and chart.

**Desktop app:** The Tkinter UI uses `pynput` to listen for system-wide keypresses on a background thread. All UI updates are safely scheduled back on the main thread via `root.after()`.

**Shared backend:** Both apps use `KeystrokeTrackerBackend` from `tracker.py`, which handles counting, key frequency tracking, session recording, and duration formatting using a reentrant lock for thread safety.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/status` | Current session state (count, timer, top keys) |
| GET | `/api/history` | List of completed sessions |
| POST | `/api/start` | Start a new tracking session |
| POST | `/api/stop` | Stop the current session and save to history |
| POST | `/api/keypress` | Record a keypress `{ "key": "a" }` |

## Requirements

```
Flask==2.3.3
gunicorn==21.2.0
pynput==1.7.6
```