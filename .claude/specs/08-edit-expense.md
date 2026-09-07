# Spec: Edit Expense

## Overview
This feature replaces the `/expenses/<id>/edit` placeholder with a real update flow that lets a logged-in user edit an expense they own (amount, category, date, description) directly from the profile page. It is the second of the CRUD steps (Steps 7–9: add, edit, delete). Once submitted, the updated expense should be reflected in the profile page's totals, recent transactions, and category breakdown — exactly like a new expense does today.

**Design note:** an earlier draft of this spec described a separate `templates/edit_expense.html` page mirroring `add_expense.html` (like a second `add_expense` route). That was replaced with **inline row editing** in the profile transactions table: clicking Edit turns that row's cells into inputs in place, with no navigation to a separate page. This is the first client-side JavaScript in the app (`static/js/main.js`, previously an empty placeholder).

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db`)
- Step 02 — Registration (`users` table, password hashing pattern)
- Step 03 — Login/Logout (`session["user_id"]`, auth gate pattern used in `/profile`)
- Step 05 — Profile backend implementation (`get_expense_summary`, `get_recent_expenses`, `get_category_breakdown`, `format_inr`, `category_tone` helpers this feature's output flows into)
- Step 07 — Add expense (`clean_amount`, `clean_date_param`, `CATEGORIES`, and the same server-side validation rules this feature reuses)

## Routes
- `GET /expenses/<int:id>/edit` — redirects to `/profile?edit=<id>` (plus any active date filter), so a typed or bookmarked edit URL still lands on the profile page with that row's editor already open — logged-in only, and only if the expense belongs to the current user
- `POST /expenses/<int:id>/edit` — validates and updates the expense. On success, redirects to `/profile` (preserving the active date filter). On validation failure, re-renders the profile page with that row's editor reopened, holding the submitted values and an inline error — logged-in only, and only if the expense belongs to the current user

If the user is not logged in, both redirect to `/login` (same pattern as `/profile` and `/expenses/add`). If `id` does not exist or belongs to a different user, respond with a 404 (via `flask.abort(404)`) rather than revealing whether the expense exists — no client-supplied `id` should be trusted as proof of ownership.

`GET /profile` gains an optional `?edit=<id>` query param: when present and it names a transaction on the page, that row's editor opens automatically on load.

## Database changes
No schema changes. The existing `expenses` table (`database/db.py`) already has every column this feature needs. Two new functions were added to `database/db.py`, following the existing style (open connection, parameterised query, commit where needed, close):
- `get_expense_by_id(expense_id, user_id)` — `SELECT * FROM expenses WHERE id = ? AND user_id = ?`, returns the row or `None`. The `user_id` filter is what makes ownership checks safe.
- `update_expense(expense_id, user_id, amount, category, date, description)` — `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?`. The `WHERE ... AND user_id = ?` clause is the enforcement point — it must never be dropped, even though the route also checks ownership before calling this.

## Templates
- **Create:** none.
- **Modify:** `templates/profile.html` — the `txn-table` gains a fifth "Actions" column with an Edit link per row; each `<tr>` carries `data-id`, `data-raw-date`, `data-raw-description`, `data-category`, `data-raw-amount`, and `data-edit-url` attributes that `main.js` reads to build the inline editor; the table itself carries `data-edit-id` (which row, if any, should open automatically) and `data-categories` (the category list as JSON, for the in-row `<select>`); the transactions panel gained an `{% if edit_error %}` block for inline-save errors.

## Files to change
- `app.py`:
  - Import `abort` from `flask`.
  - Extract the profile page's data-building logic out of `profile()` into `render_profile(user_id, edit_id=None, edit_form=None, edit_error=None)`, so both `GET /profile` and a failed `POST /expenses/<id>/edit` can render the same summary/transactions/category-breakdown view. `edit_id` opens a row's editor; `edit_form` (set only after a failed save) overrides that one row's displayed values with what was submitted, so the user doesn't lose their edit.
  - `profile()` now reads `?edit=` from the query string and passes it through.
  - Each transaction dict gained raw fields (`raw_date`, `raw_description`, `raw_amount`) alongside the existing formatted ones (`date`, `description`, `amount`), since the inline editor needs unformatted values to populate its inputs.
  - Replace the `edit_expense(id)` stub with a real `GET`/`POST` implementation: session auth gate, ownership lookup via `get_expense_by_id` (`abort(404)` if `None`), GET redirects to `/profile?edit=<id>`, POST reuses `clean_amount`/`clean_date_param`/`CATEGORIES` validation exactly as `add_expense` does, calls `update_expense` on success and redirects to `/profile`, or calls `render_profile(..., edit_error=...)` on failure.
- `database/db.py` — add `get_expense_by_id(...)` and `update_expense(...)`.
- `database/__init__.py` — export `get_expense_by_id` and `update_expense`.
- `templates/profile.html` — Actions column, per-row data attributes, `edit_error` block, as described above.
- `static/js/main.js` — was an empty placeholder; now holds the inline-editor logic (open/close a row's editor, submit a real POST via a detached form, auto-open the row named by `data-edit-id`).
- `static/css/style.css` — additions only, all existing CSS variables: `.txn-actions`, `.txn-action`, `.txn-input`, `.btn-sm`, `.txn-row--editing`, and a bumped `.txn-table` `min-width` (480px → 620px) to fit the new column.

## Files to create
None.

## New dependencies
No new dependencies. (`main.js` is plain vanilla JS — no framework.)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not touched by this feature, but no regressions to login/session handling)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate on the server using the same rules as `add_expense`: amount must be a positive number, category must be one of `CATEGORIES`, date must be a valid `YYYY-MM-DD` string, description is optional — the error is rendered server-side (via the profile page's `edit_error`), never client-side-only
- Category values must stay consistent with the existing `CATEGORY_TONES` map in `app.py` so an edited expense still renders with the correct pill/cat-bar tone
- Amounts are in INR — store as-entered numeric value (no currency symbol in the DB)
- Every DB read/write for a specific expense (`get_expense_by_id`, `update_expense`) must filter by both `id` and the session's `user_id` — never trust the `id` in the URL alone as proof of ownership
- `main.js` must never build HTML by string-concatenating user data (no `innerHTML = "..." + value`). Build editor inputs with `document.createElement` and assign `.value`/`.textContent`; restoring a row's original cells from previously-rendered (already-escaped) markup is fine

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for an expense that doesn't exist, or belongs to another user, returns a 404
- [ ] Visiting `/expenses/<id>/edit` for an expense you own redirects to `/profile?edit=<id>` with that row's editor already open
- [ ] The profile page's transactions table shows an Edit control on every row
- [ ] Clicking Edit turns that row's Date/Description/Category/Amount cells into inputs, prefilled with the row's current values, with no page reload
- [ ] Only one row can be in edit mode at a time; opening a second row's editor closes the first
- [ ] Clicking Cancel restores the row to its original display state
- [ ] Submitting the form with a missing/invalid amount (blank, negative, non-numeric) re-renders the profile page with that row's editor reopened, an inline error, and does not change the row
- [ ] Submitting the form with an invalid date behaves the same way
- [ ] Submitting a valid edit updates the existing row in `expenses` (same `id`, same `user_id`) rather than inserting a new one, and redirects to `/profile`
- [ ] After a successful update, the row's new values, the total/count summary, and the category breakdown all reflect the change
- [ ] A logged-in user cannot edit another user's expense by guessing/changing the `id` in the URL or in a hand-crafted POST
- [ ] An active date-range filter on the profile page survives opening a row's editor and both the success and failure paths of saving it
