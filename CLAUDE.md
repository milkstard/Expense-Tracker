# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"Spendly" is a Flask-based expense tracker built as a step-by-step learning exercise. The codebase is a **scaffold**: routes, templates, and static assets exist, but core functionality (database layer, auth, expense CRUD) is intentionally left as placeholders for the developer to implement incrementally. Route handlers and `database/db.py` contain comments like `# Students will implement this` / `# coming in Step N` marking unfinished work — check these before assuming a feature exists.

## Do not auto-implement placeholder steps

This is a **learning exercise** — the developer implements each numbered step themselves, and learns by doing so. Do not write the implementation for `database/db.py`, a stub route, or any other `# Students will implement this` / `# coming in Step N` placeholder unless the user has explicitly asked you to implement that specific piece in the current turn.

Organizational/prep actions are not implementation requests and must not be treated as one — in particular:
- Creating or checking out a git branch (e.g. `feature/database-setup`)
- Renaming the session (e.g. via `/rename`)
- Any other setup step that merely signals what's coming next

If it's ambiguous whether the user wants a given step implemented now, ask before writing code rather than inferring it from context like branch names.

## Commands

Windows venv is already created at `venv/`. Activate it before running anything:

```powershell
venv\Scripts\Activate.ps1
```

Run the dev server (listens on port 5001, debug mode on):
```powershell
python app.py
```

Run tests (pytest + pytest-flask are installed, but no test files exist yet):
```powershell
pytest
```

Install/update dependencies:
```powershell
pip install -r requirements.txt
```

There is no linter or build step configured in this project.

## Architecture

- **`app.py`** — single-file Flask app; all routes are defined here (no blueprints). Routes render Jinja templates from `templates/`. Two routes (`/expenses/<id>/edit`, `/expenses/<id>/delete`) are still stubs returning plain-text placeholder strings — they need real implementations (session handling, DB queries, form processing).
- **`database/db.py`** — intended to hold `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables via `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample data for dev). Currently empty/unimplemented — this is the foundation most other features depend on.
- **`templates/`** — Jinja2 templates extending `base.html`, which defines the shared nav/footer shell and `{% block title %}` / `{% block head %}` / `{% block content %}` / `{% block scripts %}` blocks. `login.html` and `register.html` POST to `/login` and `/register` respectively but the corresponding server-side handlers only support GET so far.
- **`static/css/style.css`** and **`static/js/main.js`** — global styles and client-side JS; `main.js` is currently empty, awaiting feature work.
- The SQLite database file (`expense_tracker.db`) is gitignored and created at runtime by `init_db()` once implemented — don't expect it to exist in a fresh checkout.

## Project map (source of truth)

```
Expense-Tracker/
├── app.py                 # single-file Flask app — ALL routes live here, no blueprints
├── CLAUDE.md              # project-level spec / conventions
├── database/              # get_db(), init_db(), seed_db(), SQLite helpers
├── templates/
│   ├── base.html          # shared shell: nav, footer, {% block %} hooks
│   └── *.html             # every page extends base.html
├── static/
│   ├── css/style.css      # the single global stylesheet
│   └── js/                # client-side JS (minimal)
└── requirements.txt
```

## Conventions in this codebase

- Currency/locale references (e.g. placeholder copy "Track every rupee") indicate INR is the target currency for expense amounts.
- Forms use plain HTML `POST` with server-rendered error messages via an `error` template variable (see the `{% if error %}` block in `login.html`/`register.html`) rather than client-side validation or flash messages.
