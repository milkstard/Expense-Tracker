# Spec: Profile Page Design

## Overview
Replace the `/profile` stub with a fully designed profile page. The goal is to
establish the complete UI layout — user info card, summary stats, transaction
history table, and category breakdown — before the expense queries exist.
Building the UI first lets the team isolate and validate the design and ensures
the templates are ready for the backend-connection steps.

The data is **hybrid**: the identity fields (name, email, member-since) come
from the real `users` row via `get_user_by_id()`, because that table already
exists and the signed-in user must see their own account. Everything derived
from expenses (stats, transaction rows, category totals) is **hardcoded** in
the template, because expense CRUD does not land until Steps 7–9. The
hardcoded figures mirror `seed_db()`'s sample expenses so the page reads as
plausible and lines up with real data later.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`,
  `users` table). Already complete on `main`.
- Step 3 — Login and Logout (`session["user_id"]` set on login, nav bar
  conditional on `session.user_id`). Already complete on `main`.

## Routes
- `GET /profile` — render the signed-in user's profile (name, email,
  member-since date) — logged-in only. If no `session["user_id"]` is
  set, redirect to `/login` instead of rendering.

No other new routes.

## Database changes
No schema changes. Uses the existing `users` table
(`id`, `name`, `email`, `password_hash`, `created_at`) and needs a way to
look up a user by id — add a `get_user_by_id(user_id)` function to
`database/db.py` alongside `get_db()` / `init_db()` / `seed_db()` /
`create_user()` / `get_user_by_email()`, following the same pattern
(parameterised query, connection closed in a `finally` block). Returns
the `sqlite3.Row` or `None`.

## Templates
- **Create:** `templates/profile.html` — extends `base.html`, fills
  `{% block title %}` and `{% block content %}`; displays:
  1. **Page header** — uppercase eyebrow + serif title with one italic
     accent word, matching the `.hero-title em` motif
  2. **Identity card** — avatar circle with initials, name, email, and a
     "Member since <Month Year>" pill (**live data** from the session user)
  3. **Summary stats row** — total spent, number of transactions, top
     category (hardcoded)
  4. **Transaction history table** — semantic `<table>` of recent expenses
     with date, description, category badge, amount (hardcoded rows)
  5. **Category breakdown** — per-category totals as progress-bar rows
     (hardcoded)
- **Create:** `templates/macros/profile.html` — Jinja macros for the pieces
  that repeat: `stat_card(label, value, hint)`, `pill(text, tone)`,
  `cat_row(name, pct, amount, tone)`
- **Modify:** none

## Files to change
- `app.py` — replace the `/profile` stub: guard on
  `session.get("user_id")` (redirect to `url_for("login")` if absent),
  otherwise look up the user via `get_user_by_id()` and render
  `profile.html` with the user data. If `get_user_by_id()` returns
  `None` (stale session referencing a deleted user), clear the session
  and redirect to `/login`. Pass an **explicit dict** (`name`, `email`,
  `initials`, `member_since`) rather than the `sqlite3.Row`, so
  `password_hash` structurally cannot reach the template. Add two
  module-level helpers: `format_member_since(created_at)` (parses the
  `created_at` TEXT column into "August 2026", falling back to an em dash
  on a missing/unparseable value) and `initials_for(name)`. Move
  `/profile` out of the "Placeholder routes" block, next to `/logout`.
- `database/db.py` — add `get_user_by_id(user_id)`
- `database/__init__.py` — export `get_user_by_id`
- `static/css/style.css` — add a mobile-first `/* Profile page */` section,
  plus new `:root` tokens the profile needs: `--cat-1` … `--cat-6` and
  their `-light` badge variants, and `--shadow-card`. Repoint
  `.mock-bar-3` / `.mock-bar-4` at `--cat-3` / `--cat-4` — they were raw
  hex, which the "no hardcoded hex" rule forbids. No other existing rule
  changes.

## Files to create
- `templates/profile.html`
- `templates/macros/profile.html`

## New dependencies
No new dependencies. (`datetime` from the standard library is imported in
`app.py` for the member-since formatting.)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not relevant to reads here, but the
  `password_hash` column must never be passed into the template context)
- Use CSS variables — never hardcode hex values outside the `:root` token
  block; new colors are added as tokens, not inlined at the use site
- All templates extend `base.html`
- Mobile-first: write the single-column layout first, then widen with
  `min-width` media queries. (The pre-existing rules in `style.css` are
  desktop-first — leave them as they are rather than rewriting working CSS.)
- No `!important`, no new dependencies, no CSS/JS framework
- Repeating markup goes in a Jinja macro, not copy-paste
- Icons follow the live house style (unicode glyphs like `◈ ◎ ₹`), not an
  SVG icon set — the project doesn't use one yet
- Currency renders as INR with the `₹` symbol

## Definition of done
**Route & data**
- [x] Visiting `/profile` while logged out redirects to `/login`
- [x] Logging in with the seeded demo credentials
      (`demo@spendly.com` / `demo123`) and visiting `/profile` shows
      "Demo User", "demo@spendly.com", and "Member since August 2026"
- [x] The avatar circle shows the initials derived from the user's name
      ("DU" for "Demo User")
- [x] The `password_hash` value never appears in the rendered HTML — the
      route passes an explicit dict, never the `sqlite3.Row`
- [x] Visiting `/profile` with a session pointing at a user id that no
      longer exists in `users` redirects to `/login` instead of erroring,
      and clears the stale session
- [x] A missing or unparseable `created_at` renders an em dash rather
      than raising

**Template structure**
- [x] `templates/profile.html` extends `base.html` and fills
      `{% block title %}` ("Profile — Spendly") and `{% block content %}`
- [x] All five sections render: page header, identity card, summary stats
      row, transaction history table, category breakdown
- [x] The repeating pieces come from `templates/macros/profile.html`
      (`stat_card`, `pill`, `cat_row`) — no duplicated markup
- [x] Transaction history uses a semantic `<table>` with `<thead>`/`<th
      scope="col">`, not `<div>` soup
- [x] Hardcoded expense figures match `seed_db()`'s sample data and are
      internally consistent (8 rows, category totals summing to the
      ₹6,348.50 shown in the stats, top category = Shopping ₹2,350.00)
- [x] Nav bar still shows "Sign out" while viewing `/profile` (unchanged
      from Step 3 behavior)

**Styling**
- [x] The profile CSS contains no hardcoded hex values; every category
      color is a `--cat-*` token. (One pre-existing hex remains elsewhere
      in the file — `.auth-error`'s `border: 1px solid #f5c6c2`, from
      Step 2. Out of scope here; worth tokenising in a later cleanup.)
- [x] The page uses the existing tokens (`--ink*`, `--paper*`, `--accent`,
      `--radius-*`, `--font-display`, `--font-body`) and reads as part of
      the same site as the landing and auth pages
- [x] No `!important` and no ad-hoc inline styles, except the dynamic
      `width: N%` on the category bars
- [x] Mobile-first: at 375px the page is one column and the transaction
      table scrolls inside its own container without the body scrolling
      horizontally
- [x] At ≥720px the summary stats become a 3-across grid
- [x] At ≥960px the transaction panel and category breakdown sit side by
      side in a 2fr / 1fr grid
- [x] Landing page is visually unchanged after the `.mock-bar-3/4` token
      refactor
