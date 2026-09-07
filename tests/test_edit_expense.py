"""Tests for spec 08 -- Edit Expense.

Scenarios are derived from .claude/specs/08-edit-expense.md (Routes,
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

Not covered here (out of reach of a Flask test client, which does not
execute JavaScript / has no DOM or browser):
- "Clicking Edit turns that row's cells into inputs ... with no page reload"
- "Only one row can be in edit mode at a time; opening a second row's
  editor closes the first"
- "Clicking Cancel restores the row to its original display state"
These are pure client-side `main.js` behaviours from the Definition of
done; this suite instead verifies the server-rendered data attributes
(`data-id`, `data-raw-date`, `data-raw-description`, `data-category`,
`data-raw-amount`, `data-edit-url`, `data-edit-id`, `data-categories`) that
`main.js` depends on to build that behaviour, plus every server-side
route/validation/authorization requirement in the spec.
"""

from conftest import DEMO_EMAIL, DEMO_PASSWORD


def _demo_user_id(db_module):
    return db_module.get_user_by_email(DEMO_EMAIL)["id"]


VALID_EDIT_FORM = {
    "amount": "999.99",
    "category": "Transport",
    "date": "2026-08-20",
    "description": "Weekend trip",
}


# ------------------------------------------------------------------ #
# Access control -- logged-in only                                   #
# ------------------------------------------------------------------ #

def test_get_edit_redirects_to_login_when_logged_out(client):
    response = client.get("/expenses/1/edit")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_post_edit_redirects_to_login_when_logged_out_and_does_not_update(
    client, db_module
):
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)

    response = client.post("/expenses/1/edit", data=VALID_EDIT_FORM)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    after = db_module.get_expense_by_id(1, demo_id)
    assert after["amount"] == before["amount"]
    assert after["category"] == before["category"]


# ------------------------------------------------------------------ #
# Ownership / existence -- 404, never reveal whether an id exists    #
# ------------------------------------------------------------------ #

def test_get_edit_nonexistent_id_returns_404(client, login_client):
    login_client()
    response = client.get("/expenses/99999/edit")
    assert response.status_code == 404


def test_post_edit_nonexistent_id_returns_404(client, login_client):
    login_client()
    response = client.post("/expenses/99999/edit", data=VALID_EDIT_FORM)
    assert response.status_code == 404


def test_get_edit_other_users_expense_returns_404(
    client, register_client, login_client
):
    # Expense id 1 belongs to the demo user (seeded); a second user must
    # not be able to reach its editor.
    register_client("Second User", "second@example.com", "password123")
    login_client("second@example.com", "password123")

    response = client.get("/expenses/1/edit")
    assert response.status_code == 404


def test_post_edit_other_users_expense_returns_404_and_does_not_update(
    client, register_client, login_client, db_module
):
    register_client("Second User", "second@example.com", "password123")
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)

    login_client("second@example.com", "password123")
    response = client.post("/expenses/1/edit", data=VALID_EDIT_FORM)

    assert response.status_code == 404
    after = db_module.get_expense_by_id(1, demo_id)
    assert after["amount"] == before["amount"]
    assert after["category"] == before["category"]
    assert after["date"] == before["date"]
    assert after["description"] == before["description"]


# ------------------------------------------------------------------ #
# GET /expenses/<id>/edit -- redirect into the profile editor        #
# ------------------------------------------------------------------ #

def test_get_edit_owned_expense_redirects_to_profile_with_edit_query_param(
    client, login_client
):
    login_client()
    response = client.get("/expenses/1/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/profile?edit=1"


def test_get_edit_redirect_preserves_active_date_filter(client, login_client):
    login_client()
    response = client.get(
        "/expenses/1/edit?start_date=2026-08-01&end_date=2026-08-20"
    )
    assert response.status_code == 302
    location = response.headers["Location"]
    assert "edit=1" in location
    assert "start_date=2026-08-01" in location
    assert "end_date=2026-08-20" in location


def test_following_get_edit_redirect_opens_that_rows_editor(client, login_client):
    login_client()
    response = client.get("/expenses/3/edit", follow_redirects=True)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-edit-id="3"' in html


def test_profile_edit_query_param_opens_matching_rows_editor_directly(
    client, login_client
):
    # GET /profile?edit=<id> directly (not via the /expenses/<id>/edit
    # redirect) must also auto-open that row's editor.
    login_client()
    response = client.get("/profile?edit=5")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-edit-id="5"' in html


# ------------------------------------------------------------------ #
# Profile page markup -- Actions column and per-row data attributes  #
# ------------------------------------------------------------------ #

def test_profile_shows_edit_control_on_every_row(client, login_client):
    login_client()
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert html.count("data-txn-edit") == 8
    assert 'href="/expenses/1/edit"' in html


def test_profile_row_carries_data_attributes_for_inline_editor(client, login_client):
    login_client()
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert 'data-id="1"' in html
    assert 'data-raw-date="2026-08-02"' in html
    assert 'data-raw-description="Groceries - BigBasket"' in html
    assert 'data-category="Food"' in html
    assert 'data-raw-amount="450.00"' in html
    assert 'data-edit-url="/expenses/1/edit"' in html


def test_profile_table_carries_data_categories_json(client, login_client):
    login_client()
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert "data-categories=" in html
    for category in (
        "Food", "Transport", "Bills", "Health",
        "Entertainment", "Shopping", "Other",
    ):
        assert category in html


def test_profile_no_edit_param_leaves_data_edit_id_empty(client, login_client):
    login_client()
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert 'data-edit-id=""' in html


# ------------------------------------------------------------------ #
# POST /expenses/<id>/edit -- server-side validation (reuses         #
# add_expense's rules)                                                #
# ------------------------------------------------------------------ #

def test_post_edit_blank_amount_shows_error_and_does_not_update(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)

    response = client.post(
        "/expenses/1/edit",
        data={"amount": "", "category": "Food", "date": "2026-08-02",
              "description": "Groceries - BigBasket"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Please enter an amount." in html
    assert 'data-edit-id="1"' in html
    after = db_module.get_expense_by_id(1, demo_id)
    assert after["amount"] == before["amount"]


def test_post_edit_negative_amount_shows_error_and_does_not_update(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)

    response = client.post(
        "/expenses/1/edit",
        data={"amount": "-50", "category": "Food", "date": "2026-08-02",
              "description": "Groceries - BigBasket"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Amount must be greater than zero." in html
    after = db_module.get_expense_by_id(1, demo_id)
    assert after["amount"] == before["amount"]


def test_post_edit_non_numeric_amount_shows_error_and_does_not_update(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)

    response = client.post(
        "/expenses/1/edit",
        data={"amount": "abc", "category": "Food", "date": "2026-08-02",
              "description": "Groceries - BigBasket"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Amount must be a number." in html
    after = db_module.get_expense_by_id(1, demo_id)
    assert after["amount"] == before["amount"]


def test_post_edit_invalid_date_shows_error_and_does_not_update(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)

    response = client.post(
        "/expenses/1/edit",
        data={"amount": "450.00", "category": "Food", "date": "not-a-date",
              "description": "Groceries - BigBasket"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Please enter a valid date." in html
    after = db_module.get_expense_by_id(1, demo_id)
    assert after["date"] == before["date"]


def test_post_edit_invalid_category_shows_error_and_does_not_update(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)
    before = db_module.get_expense_by_id(1, demo_id)

    response = client.post(
        "/expenses/1/edit",
        data={"amount": "450.00", "category": "Not A Category",
              "date": "2026-08-02", "description": "Groceries - BigBasket"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Please choose a category." in html
    after = db_module.get_expense_by_id(1, demo_id)
    assert after["category"] == before["category"]


def test_post_edit_failure_reopens_editor_with_submitted_values(
    client, login_client
):
    login_client()
    response = client.post(
        "/expenses/1/edit",
        data={"amount": "not-a-number", "category": "Food",
              "date": "2026-08-02", "description": "Submitted but unsaved"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-edit-id="1"' in html
    # The row being re-edited shows what was just typed, not the DB value,
    # so the user doesn't lose their in-progress edit.
    assert 'data-raw-description="Submitted but unsaved"' in html
    assert "Groceries - BigBasket" not in html


def test_post_edit_error_rendered_server_side_via_form_error_block(
    client, login_client
):
    login_client()
    response = client.post(
        "/expenses/1/edit",
        data={"amount": "", "category": "Food", "date": "2026-08-02",
              "description": ""},
    )
    html = response.get_data(as_text=True)

    assert 'class="form-error"' in html


# ------------------------------------------------------------------ #
# POST /expenses/<id>/edit -- successful update                      #
# ------------------------------------------------------------------ #

def test_post_edit_valid_data_redirects_to_profile(client, login_client):
    login_client()
    response = client.post("/expenses/1/edit", data=VALID_EDIT_FORM)
    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"


def test_post_edit_valid_data_updates_existing_row_not_insert_new(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)
    before_count = db_module.get_expense_summary(demo_id)["count"]

    client.post("/expenses/1/edit", data=VALID_EDIT_FORM)

    after_count = db_module.get_expense_summary(demo_id)["count"]
    assert after_count == before_count  # no row inserted

    updated = db_module.get_expense_by_id(1, demo_id)
    assert updated is not None  # same id still exists
    assert updated["amount"] == 999.99
    assert updated["category"] == "Transport"
    assert updated["date"] == "2026-08-20"
    assert updated["description"] == "Weekend trip"
    assert updated["user_id"] == demo_id


def test_post_edit_success_reflected_in_summary_transactions_and_breakdown(
    client, login_client
):
    login_client()
    client.post("/expenses/1/edit", data=VALID_EDIT_FORM)

    response = client.get("/profile")
    html = response.get_data(as_text=True)

    # Total: 6348.50 - 450.00 (old) + 999.99 (new) = 6898.49
    assert "₹6,898.49" in html
    # Updated row's new values show up in the transactions table.
    assert "Weekend trip" in html
    assert "20 Aug" in html
    # Category breakdown reflects the move from Food to Transport:
    # Food now only has the 620.50 expense (id 7); Transport now has
    # 180.00 (id 2) + 999.99 (edited id 1) = 1179.99.
    assert "₹620.50" in html
    assert "₹1,179.99" in html


def test_post_edit_can_clear_optional_description(
    client, login_client, db_module
):
    login_client()
    demo_id = _demo_user_id(db_module)

    response = client.post(
        "/expenses/2/edit",
        data={"amount": "180.00", "category": "Transport",
              "date": "2026-08-04", "description": ""},
    )
    assert response.status_code == 302

    updated = db_module.get_expense_by_id(2, demo_id)
    assert not updated["description"]


# ------------------------------------------------------------------ #
# Filter preservation across the edit flow                           #
# ------------------------------------------------------------------ #

def test_post_edit_success_redirect_preserves_active_date_filter(
    client, login_client
):
    login_client()
    response = client.post(
        "/expenses/1/edit?start_date=2026-08-01&end_date=2026-08-20",
        data=VALID_EDIT_FORM,
    )
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith("/profile")
    assert "start_date=2026-08-01" in location
    assert "end_date=2026-08-20" in location
    assert "edit=" not in location


def test_post_edit_failure_preserves_active_date_filter(client, login_client):
    login_client()
    response = client.post(
        "/expenses/1/edit?start_date=2026-08-01&end_date=2026-08-20",
        data={"amount": "not-a-number", "category": "Food",
              "date": "2026-08-02", "description": "Groceries - BigBasket"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'value="2026-08-01"' in html
    assert 'value="2026-08-20"' in html
    assert "Clear filter" in html
    assert 'data-edit-id="1"' in html
