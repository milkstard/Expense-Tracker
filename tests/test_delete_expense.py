"""Tests for spec 09 -- Delete Expense.

Scenarios are derived from .claude/specs/09-delete-expense.md (Routes,
Database changes, Rules for implementation, Definition of done), exercised
against the seeded demo account (demo@spendly.com / demo123) whose eight
expenses are inserted in this order (ids assigned sequentially by
AUTOINCREMENT, see database/db.py:seed_db):

    id  category       amount    date         description
    1   Food            450.00   2026-08-02   Groceries - BigBasket
    2   Transport       180.00   2026-08-04   Uber to office
    3   Bills          1499.00   2026-08-05   Electricity bill
    4   Health          350.00   2026-08-08   Pharmacy - vitamins
    5   Entertainment   799.00   2026-08-10   Netflix subscription
    6   Shopping       2350.00   2026-08-12   New running shoes
    7   Food            620.50   2026-08-15   Dinner with friends
    8   Other           100.00   2026-08-18   Miscellaneous

Total: 6348.50, count 8.

Not covered here (out of reach of a Flask test client, which does not
execute JavaScript / has no DOM or browser):
- "Clicking Delete prompts for confirmation before anything happens"
- "Cancelling the confirmation leaves the expense untouched and the row
  unchanged"
These are pure client-side `main.js`/`window.confirm` behaviours from the
Definition of done; this suite instead verifies the server-rendered
`data-txn-delete` / `data-delete-url` attributes that `main.js` depends on
to build that behaviour, plus every server-side route/authorization/
persistence requirement in the spec.
"""

from conftest import DEMO_EMAIL, DEMO_PASSWORD


def _demo_user_id(db_module):
    return db_module.get_user_by_email(DEMO_EMAIL)["id"]


def _categories(breakdown):
    return {row["category"] for row in breakdown}


# ------------------------------------------------------------------ #
# Access control -- logged-in only                                   #
# ------------------------------------------------------------------ #

def test_post_delete_redirects_to_login_when_logged_out_and_does_not_delete(
    client, db_module
):
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)
    assert before is not None

    response = client.post("/expenses/1/delete")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    after = db_module.get_expense_by_id(1, demo_id)
    assert after is not None


# ------------------------------------------------------------------ #
# The route only accepts POST -- no GET handler                      #
# ------------------------------------------------------------------ #

def test_get_delete_returns_405_and_does_not_delete_when_logged_out(
    client, db_module
):
    demo_id = _demo_user_id(db_module)

    response = client.get("/expenses/1/delete")

    assert response.status_code == 405
    assert db_module.get_expense_by_id(1, demo_id) is not None


def test_get_delete_returns_405_and_does_not_delete_when_logged_in(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)

    response = client.get("/expenses/1/delete")

    assert response.status_code == 405
    assert db_module.get_expense_by_id(1, demo_id) is not None


# ------------------------------------------------------------------ #
# Ownership / existence -- 404, never reveal whether an id exists    #
# ------------------------------------------------------------------ #

def test_post_delete_nonexistent_id_returns_404_and_deletes_nothing(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)
    before_count = db_module.get_expense_summary(demo_id)["count"]

    response = client.post("/expenses/99999/delete")

    assert response.status_code == 404
    after_count = db_module.get_expense_summary(demo_id)["count"]
    assert after_count == before_count


def test_post_delete_other_users_expense_returns_404_and_does_not_delete(
    client, register_client, login_client, db_module
):
    # Expense id 1 belongs to the seeded demo user; a second user must not
    # be able to delete it by guessing/changing the id in a hand-crafted
    # POST.
    register_client("Second User", "second@example.com", "password123")
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)
    assert before is not None

    login_client("second@example.com", "password123")
    response = client.post("/expenses/1/delete")

    assert response.status_code == 404
    after = db_module.get_expense_by_id(1, demo_id)
    assert after is not None
    assert after["amount"] == before["amount"]
    assert after["category"] == before["category"]
    assert after["date"] == before["date"]
    assert after["description"] == before["description"]


# ------------------------------------------------------------------ #
# Profile page markup -- Delete control on every row                 #
# ------------------------------------------------------------------ #

def test_profile_shows_delete_control_on_every_row(client, login_client):
    login_client()
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert html.count("data-txn-delete") == 8
    assert 'data-delete-url="/expenses/1/delete"' in html


# ------------------------------------------------------------------ #
# POST /expenses/<id>/delete -- successful deletion                  #
# ------------------------------------------------------------------ #

def test_post_delete_valid_owned_expense_redirects_to_profile(client, login_client):
    login_client()
    response = client.post("/expenses/1/delete")

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"


def test_post_delete_removes_row_from_expenses_table(client, login_client, db_module):
    login_client()
    demo_id = _demo_user_id(db_module)
    assert db_module.get_expense_by_id(3, demo_id) is not None

    client.post("/expenses/3/delete")

    assert db_module.get_expense_by_id(3, demo_id) is None


def test_post_delete_reflected_in_summary_and_category_breakdown(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)

    before_summary = db_module.get_expense_summary(demo_id)
    assert before_summary["count"] == 8
    assert before_summary["total"] == 6348.50

    # id 3 (Bills, 1499.00) is the only Bills expense, so deleting it must
    # remove "Bills" from the category breakdown entirely, not just reduce
    # its total.
    before_breakdown = db_module.get_category_breakdown(demo_id)
    assert "Bills" in _categories(before_breakdown)

    response = client.post("/expenses/3/delete")
    assert response.status_code == 302

    after_summary = db_module.get_expense_summary(demo_id)
    assert after_summary["count"] == 7
    assert after_summary["total"] == 6348.50 - 1499.00

    after_breakdown = db_module.get_category_breakdown(demo_id)
    assert "Bills" not in _categories(after_breakdown)


def test_post_delete_success_reflected_in_rendered_profile_page(
    client, login_client
):
    login_client()
    response = client.post("/expenses/3/delete", follow_redirects=True)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # New total: 6348.50 - 1499.00 = 4849.50
    assert "₹4,849.50" in html
    # The deleted row's description must no longer appear in the
    # transactions table.
    assert "Electricity bill" not in html


# ------------------------------------------------------------------ #
# Filter preservation across the delete flow                         #
# ------------------------------------------------------------------ #

def test_post_delete_redirect_preserves_active_date_filter(client, login_client):
    login_client()
    response = client.post(
        "/expenses/1/delete?start_date=2026-08-01&end_date=2026-08-20"
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith("/profile")
    assert "start_date=2026-08-01" in location
    assert "end_date=2026-08-20" in location
    assert "edit=" not in location


# ------------------------------------------------------------------ #
# Deleting the only expense left in the current (filtered) view      #
# ------------------------------------------------------------------ #

def test_post_delete_last_expense_in_filtered_view_shows_empty_state(
    client, login_client
):
    login_client()
    # Narrow the view to a single day that contains exactly one expense
    # (id 1, 2026-08-02), so deleting it empties the current view without
    # touching the other seven expenses.
    filter_qs = "start_date=2026-08-02&end_date=2026-08-02"

    pre_check = client.get(f"/profile?{filter_qs}")
    pre_html = pre_check.get_data(as_text=True)
    assert "Groceries - BigBasket" in pre_html

    response = client.post(
        f"/expenses/1/delete?{filter_qs}", follow_redirects=True
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "No expenses in this date range." in html
    assert "Groceries - BigBasket" not in html


def test_post_delete_only_expense_with_no_filter_shows_no_expenses_yet(
    client, register_client, login_client, insert_expense, db_module
):
    # A user with exactly one expense and no active date filter: deleting
    # it must fall back to the unfiltered "No expenses yet" empty state
    # (distinct from the filtered "No expenses in this date range." copy),
    # not a broken/empty table.
    register_client("Solo User", "solo@example.com", "password123")
    solo_id = db_module.get_user_by_email("solo@example.com")["id"]
    insert_expense(solo_id, 42.00, "Food", "2026-08-10", "Only expense")

    login_client("solo@example.com", "password123")
    solo_expense = db_module.get_expense_summary(solo_id)
    assert solo_expense["count"] == 1

    pre_check = client.get("/profile")
    assert "Only expense" in pre_check.get_data(as_text=True)

    expense_row = [
        row for row in db_module.get_recent_expenses(solo_id)
        if row["description"] == "Only expense"
    ][0]

    response = client.post(
        f"/expenses/{expense_row['id']}/delete", follow_redirects=True
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "No expenses yet." in html
    assert "No expenses in this date range." not in html
    assert "Only expense" not in html
    assert db_module.get_expense_summary(solo_id)["count"] == 0
