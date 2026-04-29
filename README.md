# Keystroke Tracker

A web-based keystroke tracking app built with Flask, and a standalone desktop version built with Tkinter. Track how many keys you press, see your top 3 most-used keys in real time, and review your session history.

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

## Deploying to Heroku

1. Create a Heroku app and set the required config var:

```bash
heroku config:set SECRET_KEY=your-long-random-secret --app your-app-name
```

You can generate a strong secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. Make sure your dynos are running:

```bash
heroku ps:scale web=1 --app your-app-name
```

3. Push to deploy:

```bash
git push heroku main
```

### Python Version

Heroku's `runtime.txt` is deprecated. Replace it with a `.python-version` file containing just:

```
3.11
```

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