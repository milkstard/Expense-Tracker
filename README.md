# Spendly

A Flask-based expense tracker — track every rupee. Built as a step-by-step learning exercise (Flask, SQLite, server-rendered Jinja2 templates).

**Live app:** https://expense-tracker-production-a170.up.railway.app/

## Features

- User registration and login (session-based auth, hashed passwords)
- Profile page with spending summary, category breakdown, and recent expenses
- Add, edit, and delete expenses
- Filter expenses by date range (bookmarkable via query params)

## Tech stack

- **Backend:** Flask (single-file app, no blueprints — all routes in `app.py`)
- **Database:** SQLite (`database/db.py`), created and seeded automatically at startup
- **Templates:** Jinja2 (`templates/`), extending a shared `base.html`
- **Styling:** vanilla CSS (`static/css/style.css`), no framework
- **Production server:** Gunicorn
- **Tests:** pytest + pytest-flask (`tests/`)

## Project structure

```
expense-tracker/
├── app.py                 # Flask app — all routes
├── database/
│   └── db.py               # get_db(), init_db(), seed_db(), CRUD helpers
├── templates/               # Jinja2 templates (extend base.html)
├── static/
│   ├── css/style.css        # global styles
│   └── js/                  # client-side JS
├── tests/                   # pytest suite
├── requirements.txt
└── Procfile                 # Railway/Gunicorn start command
```

## Routes

| Route | Methods | Description |
|---|---|---|
| `/` | GET | Landing page |
| `/register` | GET, POST | Create an account |
| `/login` | GET, POST | Log in |
| `/logout` | GET | Log out |
| `/profile` | GET | Spending summary, category breakdown, expense list, date filter |
| `/expenses/add` | GET, POST | Add an expense |
| `/expenses/<id>/edit` | GET, POST | Edit an expense |
| `/expenses/<id>/delete` | POST | Delete an expense |

## Database schema

**users**

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | autoincrement |
| name | TEXT | |
| email | TEXT | unique |
| password_hash | TEXT | |
| created_at | TEXT | defaults to now |

**expenses**

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | autoincrement |
| user_id | INTEGER | FK → users.id, cascades on delete |
| amount | REAL | |
| category | TEXT | |
| date | TEXT | |
| description | TEXT | optional |
| created_at | TEXT | defaults to now |

## Running locally

Requires Python 3 and a virtual environment.

```powershell
# create and activate the venv (if not already created)
python -m venv venv
venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# run the dev server (http://localhost:5001)
python app.py
```

The SQLite database (`expense_tracker.db`) is created and seeded automatically on first run — it's gitignored, so a fresh checkout starts with an empty/seeded DB.

### Running tests

```powershell
pytest
```

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask session signing key |
| `DB_PATH` | `<project root>/expense_tracker.db` | Path to the SQLite database file |

## Deployment

Deployed on [Railway](https://railway.com): **https://expense-tracker-production-a170.up.railway.app/**

- **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT` (see `Procfile`)
- **Persistence:** a Railway volume is mounted at `/data`, with `DB_PATH=/data/expense_tracker.db` set on the service so the SQLite database survives redeploys and restarts
- Push to `main` and redeploy via `railway up`, or connect the GitHub repo in the Railway dashboard for auto-deploys

## Notes

This project started as a guided learning scaffold — some pieces were intentionally left unimplemented as exercises (see `.claude/specs/` for the original step-by-step feature specs) and have since been built out incrementally.
