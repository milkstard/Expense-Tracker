# Spec: Login and Logout

## Overview
Implement session-based authentication for Spendly. The `/login` route
currently only supports `GET` (renders `login.html`, which already POSTs to
`/login` with `email` and `password` fields, and already shows the
`registered=1` success banner from Step 2). This step adds the `POST`
handler: look up the user by email, verify the password hash, and establish
a session on success. `/logout` is currently a stub returning plain text —
this step replaces it with a real handler that clears the session and
redirects to the landing page. The shared nav in `base.html` is updated to
reflect signed-in state (show "Sign out" instead of "Sign in" / "Get
started") since every subsequent step (Profile, Expenses) depends on
knowing whether a user is logged in.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`,
  `users` table). Already complete on `main`.
- Step 2 — Registration (`create_user()`, `login.html`'s `registered`
  success banner, `.auth-success` / `.auth-error` styling). Already
  complete on `main`.

## Routes
- `POST /login` — verify email + password against `users`, set
  `session["user_id"]` on success, redirect to `/profile` — public
- `GET /login` — unchanged, already implemented (still handles
  `registered=1`)
- Both `GET` and `POST /login` — if `session.get("user_id")` is already
  set, redirect straight to `/` (landing) before touching the form or
  request body — an already-authenticated user has no reason to see or
  resubmit the login form
- `GET /logout` — clear the session and redirect to `/` — logged-in
  (safe to call even if no session exists; just no-ops)

No other new routes. `/profile` stays a stub (Step 4) — Login only needs to
redirect there, not implement it. `/expenses/*` stay stubs (Steps 7–9).

## Database changes
No schema changes. Uses the existing `users` table
(`id`, `name`, `email`, `password_hash`, `created_at`) and needs a way to
look up a user by email — add a `get_user_by_email(email)` function to
`database/db.py` alongside `get_db()` / `init_db()` / `seed_db()` /
`create_user()`, following the same pattern (parameterised query, connection
closed in a `finally` block). Returns the `sqlite3.Row` or `None`.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — no field/markup changes needed; already posts
    `email` + `password` and renders `{% if error %}`
  - `templates/base.html` — nav links become conditional on whether
    `session.get("user_id")` is set: logged out shows the existing "Sign
    in" / "Get started" links; logged in shows a "Sign out" link
    (`{{ url_for('logout') }}`) instead. `session` is available in Jinja
    templates by default in Flask, no context processor needed.

## Files to change
- `app.py` — set `app.secret_key` (required for Flask sessions — read from
  an env var with a hardcoded dev fallback, since there's no `.env`
  handling in this project yet); add `POST` handling to the `/login` route
  (look up user via `get_user_by_email()`, verify password with
  `check_password_hash`, set `session["user_id"]`, redirect to `/profile`;
  on failure re-render `login.html` with a generic `error` — do not reveal
  whether the email or the password was wrong); guard the top of the
  `/login` view with `if session.get("user_id"): return
  redirect(url_for("landing"))`, before branching on `request.method`, so
  it covers both `GET` and `POST`; replace the `/logout` stub with a
  handler that calls `session.clear()` and redirects to `landing`
- `database/db.py` — add `get_user_by_email(email)`
- `database/__init__.py` — export `get_user_by_email`
- `templates/base.html` — make nav links conditional on `session.user_id`

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`check_password_hash` against the stored
  `password_hash` — never compare plaintext)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate required fields server-side and re-render `login.html` with
  `error` set on failure (matches the existing `{% if error %}` convention
  — no client-side validation, no flash messages)
- Use one generic error message ("Invalid email or password.") for both
  "no such user" and "wrong password" cases — don't leak which one it was
- `/logout` must work via `GET` (matches the existing stub's method and the
  plain `<a href="...">` nav link pattern already used for `/login`;
  no CSRF-token infrastructure exists in this project to protect a POST-only
  logout)

## Definition of done
- [ ] Submitting the login form with the seeded demo credentials
      (`demo@spendly.com` / `demo123`) sets a session and redirects to
      `/profile`
- [ ] Submitting the login form with a correct email but wrong password
      re-renders `login.html` with an `error` message and does not set a
      session
- [ ] Submitting the login form with an email that doesn't exist in `users`
      re-renders `login.html` with the same generic `error` message (not a
      distinct "user not found" message) and does not set a session
- [ ] Submitting with a missing required field re-renders `login.html` with
      an `error` message
- [ ] After logging in, the nav bar shows "Sign out" instead of "Sign in" /
      "Get started" on every page (landing, login, register, profile stub)
- [ ] Visiting `/logout` while logged in clears the session and redirects
      to `/`, after which the nav bar reverts to "Sign in" / "Get started"
- [ ] Visiting `/logout` while not logged in does not error — it just
      redirects to `/`
- [ ] App starts and `/login` GET still renders normally, including the
      `registered=1` success banner from Step 2
- [ ] While logged in, visiting `GET /login` redirects to `/` instead of
      rendering the form
- [ ] While logged in, submitting `POST /login` also redirects to `/`
      rather than re-processing the credentials
