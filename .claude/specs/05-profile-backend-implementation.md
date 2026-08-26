# Spec: Profile Backend Implementation

## Overview
Step 4 built the `/profile` page's visual design with the identity card wired
to live `users` data, but the summary stats, recent-transactions table, and
category breakdown were left hardcoded — a template comment marks them as
sample figures until "real expense queries land." This step replaces those
hardcoded blocks with real, read-only queries against the `expenses` table
that already exists and is already seeded. It does **not** add the ability to
create, edit, or delete expenses — those remain the stubbed `/expenses/add`,
`/expenses/<id>/edit`, and `/expenses/<id>/delete` routes reserved for Steps
7–9. This step is purely: read the signed-in user's expenses and render them
instead of the sample data.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`,
  `expenses` table, `seed_db()`'s sample expenses). Already complete on `main`.
- Step 3 — Login and Logout (`session["user_id"]`). Already complete on `main`.
- Step 4 — Profile page design (`templates/profile.html`,
  `templates/macros/profile.html`, the `/profile` route). Already complete on
  `main`. This step modifies that route and template rather than replacing
  them.

## Routes
No new routes. Modifies the existing:
- `GET /profile` — now also queries and renders the signed-in user's real
  expense data (stats, recent transactions, category breakdown) — logged-in
  only, unchanged access behavior from Step 4.

## Database changes
No schema changes. Adds new read-only query functions to `database/db.py`,
following the existing pattern (parameterised query, connection closed in a
`finally` block), operating on the existing `expenses` table
(`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`):

- `get_expense_summary(user_id)` — returns total spent, transaction count,
  and top category (name + amount) for the user, via aggregate SQL
  (`SUM`, `COUNT`, `GROUP BY category ORDER BY SUM(amount) DESC`) rather than
  summing in Python.
- `get_recent_expenses(user_id, limit=8)` — returns the user's most recent
  expenses ordered by `date DESC, id DESC`, capped at `limit`.
- `get_category_breakdown(user_id)` — returns per-category totals for the
  user (`category`, `total`), ordered by total descending, via
  `GROUP BY category`. The route computes each category's progress-bar width
  as a percentage of the **top category's** total (not the overall total) —
  this matches Step 4's hardcoded figures, where the largest category's bar
  is 100% and the rest scale relative to it (avoids doing percentage math in
  SQL/SQLite).

All three scope to `WHERE user_id = ?` — a user must only ever see their own
expenses.

## Templates
- **Create:** none
- **Modify:** `templates/profile.html` — remove the
  `{# Sample figures below... #}` comment block and the hardcoded
  `stat_card(...)` calls, `<tbody>` rows, and `cat_row(...)` calls; replace
  with `{% for %}` loops over the data passed from the route. Add an empty
  state (e.g. "No expenses yet") for a user with zero expenses, so the table
  and category panel don't render broken/empty when `get_recent_expenses`
  and `get_category_breakdown` return `[]`. `templates/macros/profile.html`
  is unchanged — `stat_card`, `pill`, and `cat_row` already take the right
  arguments for real data.

## Files to change
- `app.py` — in the `/profile` route, after loading the user, call
  `get_expense_summary`, `get_recent_expenses`, and `get_category_breakdown`
  for `session["user_id"]`, format the amounts as `₹#,##0.00` strings and
  dates as `"DD Mon"` (matching the existing hardcoded markup, e.g. "18 Aug"),
  map each category to the existing `pill`/`cat_row` tone name (reuse the
  category → tone mapping implied by the current hardcoded rows: Food,
  Transport, Bills, Health, Entertainment, Shopping, Other), and pass the
  results into `render_template("profile.html", ...)` alongside `user`. Add
  a small helper (e.g. `category_tone(category)`) rather than repeating the
  mapping inline.
- `database/db.py` — add `get_expense_summary`, `get_recent_expenses`,
  `get_category_breakdown`
- `database/__init__.py` — export the three new functions
- `templates/profile.html` — replace hardcoded sections with loops (see
  Templates above)

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not relevant here — no password data
  touched by this step)
- Use CSS variables — never hardcode hex values (no CSS changes are expected,
  but if a new category-tone/pill mapping needs a style, follow the existing
  `--cat-*` token pattern from Step 4 rather than inlining hex)
- All templates extend `base.html`
- Every new query function scopes to the signed-in user (`WHERE user_id = ?`)
  — never query or render another user's expenses
- Aggregate in SQL (`SUM`, `COUNT`, `GROUP BY`), not by pulling all rows into
  Python and summing in the view function
- Repeating markup stays in the Step 4 Jinja macros (`stat_card`, `pill`,
  `cat_row`) — no copy-pasted markup in the new loops
- Currency renders as INR with the `₹` symbol, matching Step 4's formatting

## Definition of done
- [ ] Logging in with the seeded demo credentials (`demo@spendly.com` /
      `demo123`) and visiting `/profile` shows real stats computed from the
      8 seeded expenses: total spent ₹6,348.50, 8 transactions, top category
      Shopping ₹2,350.00 — matching what was previously hardcoded, but now
      computed from the database
- [ ] The recent-transactions table lists the seeded expenses ordered
      newest-first (18 Aug down to 02 Aug), pulled from `get_recent_expenses`
      rather than hardcoded `<tr>` markup
- [ ] The category breakdown panel lists all 7 categories present in the
      seed data with correct totals and bar widths summing sensibly to 100%
      of the total spent, pulled from `get_category_breakdown` rather than
      hardcoded `cat_row(...)` calls
- [ ] A newly registered user (zero expenses) visiting `/profile` sees an
      empty state instead of an error, a blank table, or leftover demo-user
      figures
- [ ] `templates/profile.html` no longer contains the
      "Sample figures below" comment or any hardcoded expense amount,
      category, or transaction row
- [ ] All three new `database/db.py` functions use parameterised queries
      scoped to `user_id` and are exported from `database/__init__.py`
- [ ] Visiting `/profile` while logged out still redirects to `/login`
      (unchanged from Step 4)
- [ ] `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` remain
      untouched placeholder stubs — this step does not implement them
