# Spec: Delete Expense

## Overview
This feature replaces the `/expenses/<id>/delete` placeholder with a real delete flow that lets a logged-in user permanently remove an expense they own, directly from the profile page's transactions table. It is the third and final CRUD step (Steps 7–9: add, edit, delete). Once an expense is deleted, it should immediately disappear from the profile page's totals, recent transactions, and category breakdown — exactly as if it had never been added.

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db`)
- Step 02 — Registration (`users` table, password hashing pattern)
- Step 03 — Login/Logout (`session["user_id"]`, auth gate pattern used in `/profile`)
- Step 05 — Profile backend implementation (`get_expense_summary`, `get_recent_expenses`, `get_category_breakdown` — the queries this feature's removal is reflected in)
- Step 08 — Edit expense (`render_profile` helper, the `txn-actions` column and per-row `data-*` attributes on `templates/profile.html`, the `get_expense_by_id` ownership-check pattern this feature reuses, and `static/js/main.js` as the file this feature's JS is added to)

## Routes
- `POST /expenses/<int:id>/delete` — deletes the expense if it belongs to the current user, then redirects to `/profile` (preserving the active date filter) — logged-in only, and only if the expense belongs to the current user.

If the user is not logged in, redirect to `/login` (same pattern as `/profile`, `/expenses/add`, and `/expenses/<id>/edit`). If `id` does not exist or belongs to a different user, respond with a 404 (via `flask.abort(404)`) rather than revealing whether the expense exists — no client-supplied `id` should be trusted as proof of ownership.

The route only accepts `POST` — deleting via a plain `GET` link would let a prefetch, crawler, or pasted URL destroy data as a side effect, so no `GET` handler is defined.

## Database changes
No schema changes. The existing `expenses` table (`database/db.py`) already supports this. One new function is added to `database/db.py`, following the existing style (open connection, parameterised query, commit, close):
- `delete_expense(expense_id, user_id)` — `DELETE FROM expenses WHERE id = ? AND user_id = ?`, returns rows deleted (0 or 1). The `WHERE ... AND user_id = ?` clause is the enforcement point — it must never be dropped, even though the route also checks ownership via `get_expense_by_id` before calling this.

## Templates
- **Create:** none.
- **Modify:** `templates/profile.html` — the `txn-actions` cell in each row gains a Delete control alongside the existing Edit link, wired to a hidden POST form (via `data-txn-delete` + `data-delete-url` on the row, mirroring the existing `data-edit-url` pattern) that `main.js` submits after a confirmation prompt.

## Files to change
- `app.py`:
  - Replace the `delete_expense(id)` stub with a real `POST`-only implementation: session auth gate (redirect to `/login`), ownership lookup via `get_expense_by_id` (`abort(404)` if `None`), call `delete_expense` on the DB layer, then redirect to `/profile` preserving the active date filter (same `filter_args` pattern used in `edit_expense`).
- `database/db.py` — add `delete_expense(expense_id, user_id)`.
- `database/__init__.py` — export `delete_expense`.
- `templates/profile.html` — add the Delete control to the `txn-actions` cell, plus the `data-txn-delete` / `data-delete-url` attributes on each row.
- `static/js/main.js` — add a click handler for `[data-txn-delete]` that shows a `window.confirm` prompt (naming the expense's description/amount if available) and, only on confirmation, builds and submits a hidden POST form to the row's `data-delete-url` — reusing the existing `submitEdit`-style hidden-form pattern already in this file rather than duplicating it wholesale.
- `static/css/style.css` — additions only, all existing CSS variables: a `.txn-action--danger` (or similar) modifier so the Delete control is visually distinct from Edit, using an existing error/danger color variable if one exists, otherwise reusing `.txn-action` as-is with no new color.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not touched by this feature, but no regressions to login/session handling)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- The delete route must only accept `POST` — no `GET` handler, so a bare navigation or link click cannot trigger a delete
- Every DB write for a specific expense (`delete_expense`) must filter by both `id` and the session's `user_id` — never trust the `id` in the URL alone as proof of ownership
- The client must confirm before deleting (`window.confirm` or equivalent) — a single accidental click must not destroy data
- `main.js` must never build HTML by string-concatenating user data (no `innerHTML = "..." + value`), consistent with the existing rule from Step 08

## Definition of done
- [ ] Submitting `POST /expenses/<id>/delete` while logged out redirects to `/login`
- [ ] Submitting `POST /expenses/<id>/delete` for an expense that doesn't exist, or belongs to another user, returns a 404 and does not delete anything
- [ ] Sending a `GET` request to `/expenses/<id>/delete` does not delete the expense (405, since only `POST` is registered)
- [ ] The profile page's transactions table shows a Delete control on every row, alongside Edit
- [ ] Clicking Delete prompts for confirmation before anything happens
- [ ] Cancelling the confirmation leaves the expense untouched and the row unchanged
- [ ] Confirming the delete removes the row from `expenses` and redirects to `/profile`
- [ ] After a successful delete, the total/count summary and the category breakdown no longer include the deleted expense
- [ ] A logged-in user cannot delete another user's expense by guessing/changing the `id` in a hand-crafted POST
- [ ] An active date-range filter on the profile page survives a delete (the redirect preserves `start_date`/`end_date`)
- [ ] Deleting the last remaining expense in the current view shows the existing "No expenses yet" / "No expenses in this date range" empty state, not a broken table
