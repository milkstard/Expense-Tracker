# Spec: Add Expense

## Overview
This feature replaces the `/expenses/add` placeholder with a real form flow that lets a logged-in user record a new expense (amount, category, date, description). It is the first of the CRUD steps (Steps 7–9: add, edit, delete) that build directly on the `expenses` table and the summary/breakdown queries already powering the profile page. Once submitted, the new expense should be reflected in the profile page's totals, recent transactions, and category breakdown.

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db`)
- Step 02 — Registration (`users` table, password hashing pattern)
- Step 03 — Login/Logout (`session["user_id"]`, auth gate pattern used in `/profile`)
- Step 05 — Profile backend implementation (`get_expense_summary`, `get_recent_expenses`, `get_category_breakdown`, `format_inr`, `category_tone` helpers this feature's output will flow into)

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only
- `POST /expenses/add` — validate and insert the new expense, then redirect to `/profile` — logged-in only

If the user is not logged in, both should redirect to `/login` (same pattern as `/profile`).

## Database changes
No database changes. The existing `expenses` table (`database/db.py`) already has every column this feature needs: `user_id`, `amount`, `category`, `date`, `description`. A new `create_expense(user_id, amount, category, date, description)` function should be added to `database/db.py` following the existing style of `create_user` (open connection, parameterised `INSERT`, commit, close, return `lastrowid`).

## Templates
- **Create:** `templates/add_expense.html` — form with fields for amount, category (select, using the existing category set: Food, Transport, Bills, Health, Entertainment, Shopping, Other), date, description; server-rendered `error` block matching the `{% if error %}` pattern in `login.html`/`register.html`; extends `base.html`
- **Modify:** `templates/profile.html` — none required functionally, but verify the "Add Expense" nav/button (if present) already links to `/expenses/add` and needs no change

## Files to change
- `app.py` — implement `add_expense()` for GET/POST, add `session["user_id"]` auth gate, form validation, call `create_expense`, redirect to `/profile` on success
- `database/db.py` — add `create_expense(...)`
- `database/__init__.py` — export `create_expense` (matches how other db functions are exposed to `app.py`)

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not touched by this feature, but no regressions to login/session handling)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate on the server: amount must be a positive number, category must be non-empty, date must be a valid `YYYY-MM-DD` string, description is optional — reuse the existing `error` template-variable pattern rather than flash messages or client-side-only validation
- Category values should stay consistent with the existing `CATEGORY_TONES` map in `app.py` (food, transport, bills, health, entertainment, shopping, other) so new expenses render with the correct pill/cat-bar tone on the profile page
- Amounts are in INR — store as-entered numeric value (no currency symbol in the DB)

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in renders a form with amount, category, date, and description fields
- [ ] Submitting the form with a missing/invalid amount (blank, negative, non-numeric) re-renders the form with an error and does not insert a row
- [ ] Submitting the form with an invalid date re-renders the form with an error and does not insert a row
- [ ] Submitting a valid form inserts a new row into `expenses` for the logged-in user's `user_id` only
- [ ] After a successful submit, the user is redirected to `/profile`
- [ ] The new expense immediately appears in the profile page's recent transactions list, updates the total/count summary, and updates the category breakdown
- [ ] A logged-in user cannot cause an expense to be created under another user's `user_id` (no client-supplied `user_id` is trusted)
