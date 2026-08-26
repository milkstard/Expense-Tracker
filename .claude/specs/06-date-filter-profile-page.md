# Spec: Date Filter for Profile Page

## Overview
Step 5 replaced the `/profile` page's hardcoded stats, recent-transactions
table, and category breakdown with live queries against the `expenses`
table, but those queries always cover the user's entire expense history.
This step adds an optional date-range filter to `/profile` so a user can
narrow the stats, transactions table, and category breakdown down to a
specific window (e.g. "this month's spending"). It is a read-only filter on
existing data — it does not add the ability to create, edit, or delete
expenses, and does not touch the still-stubbed `/expenses/add`,
`/expenses/<id>/edit`, or `/expenses/<id>/delete` routes reserved for
Steps 7–9.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`,
  `expenses` table). Already complete on `main`.
- Step 3 — Login and Logout (`session["user_id"]`). Already complete on
  `main`.
- Step 5 — Profile backend implementation (`get_expense_summary`,
  `get_recent_expenses`, `get_category_breakdown`, and the `/profile` route
  that calls them). Already complete on `main`. This step extends those
  three functions and that route rather than replacing them.

## Routes
No new routes. Modifies the existing:
- `GET /profile` — now also reads optional `start_date` and `end_date`
  query-string parameters (`YYYY-MM-DD`, matching the `expenses.date`
  column format) and, when present and valid, scopes the summary stats,
  recent transactions, and category breakdown to that inclusive date range
  — logged-in only, unchanged access behavior from Steps 4–5.

## Database changes
No schema changes. Extends the three existing read-only query functions in
`database/db.py` with optional `start_date=None, end_date=None` keyword
arguments, following the existing pattern (parameterised query, connection
closed in a `finally` block):

- `get_expense_summary(user_id, start_date=None, end_date=None)`
- `get_recent_expenses(user_id, limit=8, start_date=None, end_date=None)`
- `get_category_breakdown(user_id, start_date=None, end_date=None)`

When `start_date` / `end_date` are provided, each function appends
`AND date >= ?` / `AND date <= ?` to its existing `WHERE user_id = ?`
clause (both bounds inclusive; either may be supplied independently).
`expenses.date` is stored as an ISO `YYYY-MM-DD` string, so a plain string
comparison in SQL sorts and filters correctly without a date function or
cast. All three still scope to `WHERE user_id = ?` — a user must only ever
see their own expenses, filtered or not.

## Templates
- **Create:** none
- **Modify:**
  - `templates/profile.html` — add a small filter form above the
    "Recent transactions" panel (or in the panel head) with two
    `<input type="date">` fields (`start_date`, `end_date`) and an
    "Apply" submit button, using a plain HTML `GET` on `/profile` (query
    params, not a POST — this keeps the filtered view bookmarkable/
    shareable and matches the read-only nature of the request). Repopulate
    both inputs with the current `start_date`/`end_date` values (via
    `value="{{ filters.start_date }}"`) so the filter stays visible after
    applying. Add a "Clear filter" link back to plain `/profile` shown only
    when a filter is active. When `start_date` is after `end_date`, show an
    inline error near the filter form (reusing the existing `error`
    template variable convention) instead of applying the filter. Update
    the empty-state copy so a filtered-with-zero-results view reads
    "No expenses in this date range." while an unfiltered zero-expense
    account still reads "No expenses yet."
  - `templates/macros/profile.html` — unchanged; `stat_card`, `pill`, and
    `cat_row` already take the right arguments for filtered data.

## Files to change
- `app.py` — in the `/profile` route: read `start_date`/`end_date` from
  `request.args`, validate both are well-formed `YYYY-MM-DD` dates and that
  `start_date <= end_date` when both are present (invalid/malformed values
  are treated as "no filter" plus an inline error message, not a 500), pass
  them through to `get_expense_summary`, `get_recent_expenses`, and
  `get_category_breakdown`, and pass a `filters` dict (`start_date`,
  `end_date`, `active`) plus any `error` string into `render_template`.
- `database/db.py` — extend `get_expense_summary`, `get_recent_expenses`,
  `get_category_breakdown` with the optional date-range parameters
  described above.
- `templates/profile.html` — add the filter form and updated empty-state
  copy (see Templates above).
- `static/css/style.css` — style the new filter form (inputs, button,
  "Clear filter" link, inline error) using the existing CSS variable
  tokens; no hardcoded hex values.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not relevant here — no password data
  touched by this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Every query function still scopes to the signed-in user
  (`WHERE user_id = ?`) even when a date range is also applied — never
  query or render another user's expenses
- Aggregate in SQL (`SUM`, `COUNT`, `GROUP BY`), not by pulling all rows
  into Python and summing/filtering there
- Date filter values arrive as untrusted query-string input — validate
  format and ordering server-side before using them in a query or
  reflecting them back into the `value="..."` attributes
- Repeating markup stays in the Step 4/5 Jinja macros (`stat_card`, `pill`,
  `cat_row`) — no copy-pasted markup for the filtered rows
- Currency renders as INR with the `₹` symbol, matching Steps 4–5

## Definition of done
- [ ] Visiting `/profile` with no query params behaves exactly as it does
      on `main` today (full history, unchanged stats/transactions/
      breakdown)
- [ ] Visiting `/profile?start_date=2026-08-05&end_date=2026-08-12` (with
      the seeded demo data) shows stats, a transactions table, and a
      category breakdown covering only the seeded expenses dated 05–12 Aug
      inclusive
- [ ] The `start_date` and `end_date` inputs are repopulated with the
      values from the query string after applying a filter
- [ ] A "Clear filter" control is visible when a filter is active and
      returns the user to the unfiltered `/profile` view
- [ ] Submitting `start_date` later than `end_date` shows an inline error
      and does not apply a broken/empty filter silently
- [ ] A malformed date query param (e.g. non-date text) does not raise a
      500 — it's treated as no filter, with an inline error shown
- [ ] A date range with zero matching expenses shows "No expenses in this
      date range." rather than an error, a broken table, or the unfiltered
      empty-state copy
- [ ] Visiting `/profile` while logged out still redirects to `/login`
      regardless of query params (unchanged from Steps 4–5)
- [ ] `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`
      remain untouched placeholder stubs — this step does not implement
      them
