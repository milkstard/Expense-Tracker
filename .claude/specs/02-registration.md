# Spec: Registration

## Overview
Implement account creation for Spendly. The `/register` route currently only
supports `GET` (renders `register.html`, which already POSTs to `/register`
with `name`, `email`, `password` fields). This step adds the `POST` handler:
validate input, hash the password, insert a new row into `users`. On success
the user is redirected to `/login` with a success message shown there
("Account created — please sign in."). Registration itself does **not**
create a session — Login (Step 3) is where session-based auth gets
established; this step only needs to lay the groundwork (a reusable
`create_user()` helper) that Login will read back against.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`,
  `users` table). Already complete on `main`.

## Routes
- `POST /register` — create a new user account from form data, redirect to
  `/login?registered=1` on success — public
- `GET /register` — unchanged, already implemented
- `GET /login` — modified to show a success banner when `registered=1` is
  present in the query string (see Templates below) — public

No other new routes. `/logout` and `/profile` stay stubs (Steps 3–4).
Session creation (`session["user_id"]`) is out of scope here and belongs to
Login (Step 3).

## Database changes
No schema changes. Uses the existing `users` table from `database/db.py`
(`id`, `name`, `email`, `password_hash`, `created_at`).

Add a reusable `create_user(name, email, password_hash)` function to
`database/db.py`, alongside `get_db()` / `init_db()` / `seed_db()`, so
Login (Step 3) and any future admin/seed tooling can reuse it instead of
routes writing raw INSERTs directly. It should:
- Insert via a parameterised query and return the new user's `id`
- Rely on the existing `email UNIQUE NOT NULL` constraint rather than a
  separate SELECT-then-INSERT check (avoids a check/insert race) — let
  `sqlite3.IntegrityError` propagate and have the `/register` route catch
  it to render the duplicate-email error

## Templates
- **Create:** none
- **Modify:**
  - `templates/register.html` — no field/markup changes needed; already
    posts the correct fields and renders `{% if error %}`
  - `templates/login.html` — add a success banner shown when
    `request.args.get("registered")` is truthy (e.g. "Account created —
    please sign in."), styled with a new `.auth-success` class parallel to
    the existing `.auth-error` one

## Files to change
- `app.py` — add `POST` handling to the `/register` route (form validation,
  password hashing, insert via `create_user()`, catch duplicate-email
  `IntegrityError`, redirect to `/login?registered=1`); add `registered`
  handling to the `/login` GET route so it can pass a success flag to the
  template
- `database/db.py` — add `create_user(name, email, password_hash)`
- `templates/login.html` — render the success banner
- `static/css/style.css` — add `.auth-success` (parallel to `.auth-error`)
  and a `--success` / `--success-light` pair in `:root` (no `--success*`
  variables exist yet — don't hardcode hex the way `.auth-error`'s border
  currently does)

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate required fields server-side and re-render `register.html` with
  `error` set on failure (matches the existing `{% if error %}` convention —
  no client-side validation, no flash messages)
- Enforce a minimum password length of 8 characters server-side (the
  template already promises this via its placeholder — "Min. 8 characters"
  — but nothing currently enforces it)
- Catch the duplicate-email `IntegrityError` from `create_user()` and
  re-render `register.html` with a clear `error` message
- The success message on `/login` follows the same server-rendered
  convention as `error` — no flash messages, no client-side JS

## Definition of done
- [ ] Submitting the register form with a new name/email/password creates a
      row in the `users` table with a hashed (not plaintext) password
- [ ] After successful registration the browser is redirected to
      `/login?registered=1`, no session cookie/`session["user_id"]` is set,
      and the login page displays a success message
- [ ] Submitting with an email that already exists in `users` re-renders
      `register.html` with an `error` message and does not insert a row
- [ ] Submitting with a missing required field re-renders `register.html`
      with an `error` message and does not insert a row
- [ ] Submitting a password shorter than 8 characters re-renders
      `register.html` with an `error` message and does not insert a row
- [ ] Re-running the app and registering the same demo/seed email
      (`demo@spendly.com`) is rejected as a duplicate
- [ ] Visiting `/login` normally (no `registered` param) shows no success
      banner
- [ ] App starts and `/register` GET still renders normally
