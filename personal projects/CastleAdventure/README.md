# Castle Adventure Flask App

This folder contains a small Flask game app called Castle Adventure. It includes a main landing page, a playable castle challenge page, instructions, and a leaderboard that stores player scores in a SQLite database.

## 1. Requirements

You need:

- macOS or another operating system with Python 3
- Python 3.10 or newer recommended
- A terminal
- `sqlite3` (already included with macOS)

## 2. Open the project in Terminal

Open the project in the integrated terminal.

## 3. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install the dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install Flask
```

## 5. Check the database

The app uses a SQLite database file named `app.db`.

When the application runs for the first time, it will create the database if it does not already exist. The table structure is defined in `schema.sql` and stores player results with:

- `name`
- `hp`
- `time_seconds`

## 6. Start the development server

```bash
python3 -m flask --app app run
```

Flask will print a local address, normally:

```text
http://127.0.0.1:5000
```

Open that address in your browser.

To stop the server, return to the terminal and press `Ctrl+C`.

## 7. Try the application

### Main pages

1. Open `/` to view the home screen.
2. Open `/castle_adventure` to play the main castle challenge.
3. Open `/instructions` to read the game instructions.
4. Open `/leaderboard` to view saved player results.

### How the game works

- Enter a player name when submitting a score.
- The game records the player's health points (`hp`) and completion time (`time_seconds`).
- Scores are saved to the database and displayed on the leaderboard.
- The leaderboard can be sorted by health points or time.

Useful pages:

- `/` - home page
- `/castle_adventure` - game page
- `/instructions` - game instructions
- `/leaderboard` - leaderboard
- `/submit_score` - route used to save scores

## 8. Reset the database

`schema.sql` creates the `results` table and resets the database structure for the app. This will remove existing leaderboard entries.

Stop the Flask server first, then run:

```bash
sqlite3 app.db < schema.sql
```

Then start the server again.

## Important files

- `app.py` - Flask routes and application logic
- `database.py` - SQLite connection setup
- `schema.sql` - database table definition
- `app.db` - SQLite database file for saved scores
- `templates/` - HTML pages for the game UI
- `static/` - CSS and JavaScript files
- `run.py` - CGI entry point for a compatible web server; not the recommended command for local development
