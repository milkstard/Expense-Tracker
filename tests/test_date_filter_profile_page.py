"""Tests for spec 06 -- Date Filter for Profile Page.

Scenarios are derived from .claude/specs/06-date-filter-profile-page.md
(Routes, Database changes, Rules for implementation, Definition of done),
exercised against the seeded demo account (demo@spendly.com / demo123) whose
eight expenses span 2026-08-02 .. 2026-08-18 (see database/db.py:seed_db).
"""

from conftest import DEMO_EMAIL


# ------------------------------------------------------------------ #
# Access control (unchanged from Steps 4-5)                          #
# ------------------------------------------------------------------ #

def test_profile_redirects_to_login_when_logged_out(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_redirects_to_login_when_logged_out_with_query_params(client):
    response = client.get("/profile?start_date=2026-08-05&end_date=2026-08-12")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# No filter: behaviour must be unchanged from before this step       #
# ------------------------------------------------------------------ #

def test_profile_no_filter_shows_full_unfiltered_history(client, login_client):
    login_client()
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # All 8 seeded expenses, and their combined total.
    assert html.count('class="txn-date"') == 8
    assert "₹6,348.50" in html
    # No filter is active, so there is nothing to clear.
    assert "Clear filter" not in html
    assert "No expenses yet." not in html
    assert "No expenses in this date range." not in html


def test_profile_unfiltered_empty_state_for_brand_new_user(
    client, register_client, login_client
):
    register_client("New User", "newuser@example.com", "password123")
    login_client("newuser@example.com", "password123")

    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "No expenses yet." in html
    assert "No expenses in this date range." not in html


# ------------------------------------------------------------------ #
# Applying a valid date range                                        #
# ------------------------------------------------------------------ #

def test_profile_date_range_filters_stats_transactions_and_breakdown(
    client, login_client
):
    login_client()
    response = client.get("/profile?start_date=2026-08-05&end_date=2026-08-12")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # Only the 4 expenses dated 05-12 Aug inclusive: Bills, Health,
    # Entertainment, Shopping (450/180/620.50/100 from outside the range
    # must be excluded).
    assert html.count('class="txn-date"') == 4
    assert "₹4,998.00" in html

    for category in ("Bills", "Health", "Entertainment", "Shopping"):
        assert f'<span class="cat-name">{category}</span>' in html
    for category in ("Food", "Transport", "Other"):
        assert f'<span class="cat-name">{category}</span>' not in html


def test_profile_filter_with_only_start_date(client, login_client):
    login_client()
    response = client.get("/profile?start_date=2026-08-15")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.count('class="txn-date"') == 2
    assert "₹720.50" in html


def test_profile_filter_with_only_end_date(client, login_client):
    login_client()
    response = client.get("/profile?end_date=2026-08-04")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.count('class="txn-date"') == 2
    assert "₹630.00" in html


def test_profile_filter_inputs_repopulated_with_query_values(client, login_client):
    login_client()
    response = client.get("/profile?start_date=2026-08-05&end_date=2026-08-12")
    html = response.get_data(as_text=True)

    assert 'value="2026-08-05"' in html
    assert 'value="2026-08-12"' in html


def test_profile_clear_filter_shown_when_active_and_links_to_plain_profile(
    client, login_client
):
    login_client()
    response = client.get("/profile?start_date=2026-08-05&end_date=2026-08-12")
    html = response.get_data(as_text=True)

    assert "Clear filter" in html
    assert 'href="/profile"' in html

    # Following the "Clear filter" link's target returns the full,
    # unfiltered view.
    cleared = client.get("/profile")
    cleared_html = cleared.get_data(as_text=True)
    assert cleared_html.count('class="txn-date"') == 8
    assert "Clear filter" not in cleared_html


# ------------------------------------------------------------------ #
# Invalid input handling                                             #
# ------------------------------------------------------------------ #

def test_profile_start_after_end_shows_inline_error_and_keeps_full_history(
    client, login_client
):
    login_client()
    response = client.get("/profile?start_date=2026-08-12&end_date=2026-08-05")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="filter-error"' in html
    # The broken range must not be silently applied -- full history shows.
    assert html.count('class="txn-date"') == 8
    assert "Clear filter" not in html


def test_profile_malformed_date_does_not_500_and_is_treated_as_no_filter(
    client, login_client
):
    login_client()
    response = client.get("/profile?start_date=not-a-date")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="filter-error"' in html
    assert html.count('class="txn-date"') == 8


def test_profile_sql_injection_style_date_is_treated_as_malformed_not_500(
    client, login_client
):
    login_client()
    response = client.get(
        "/profile?start_date=2026-08-01%27%20OR%20%271%27%3D%271"
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="filter-error"' in html
    assert html.count('class="txn-date"') == 8


def test_profile_date_range_with_zero_matching_expenses_shows_filtered_empty_state(
    client, login_client
):
    login_client()
    response = client.get("/profile?start_date=2026-01-01&end_date=2026-01-02")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "No expenses in this date range." in html
    assert "No expenses yet." not in html
    assert html.count('class="txn-date"') == 0


# ------------------------------------------------------------------ #
# Cross-user isolation (Rules for implementation)                    #
# ------------------------------------------------------------------ #

def test_profile_date_filter_never_shows_another_users_expenses(
    client, register_client, login_client, insert_expense, db_module
):
    other_email = "isolation@example.com"
    register_client("Isolation User", other_email, "password123")
    other_user = db_module.get_user_by_email(other_email)
    insert_expense(
        other_user["id"], 555.00, "Food", "2026-08-06", "Isolation test lunch"
    )

    login_client(other_email, "password123")
    response = client.get("/profile?start_date=2026-08-05&end_date=2026-08-12")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # Only the second user's own expense in range shows up...
    assert html.count('class="txn-date"') == 1
    assert "₹555.00" in html
    # ...and none of the demo user's amounts in that same window leak in.
    assert "₹1,499.00" not in html
    assert "₹2,350.00" not in html
    assert "₹350.00" not in html
    assert "₹799.00" not in html


# ------------------------------------------------------------------ #
# Database layer -- get_expense_summary / get_recent_expenses /      #
# get_category_breakdown extended with start_date/end_date           #
# ------------------------------------------------------------------ #

def _demo_user_id(db_module):
    return db_module.get_user_by_email(DEMO_EMAIL)["id"]


def test_get_expense_summary_no_filter_matches_full_history(db_module):
    user_id = _demo_user_id(db_module)
    summary = db_module.get_expense_summary(user_id)
    assert summary["count"] == 8
    assert summary["total"] == 6348.50


def test_get_expense_summary_filters_by_inclusive_date_range(db_module):
    user_id = _demo_user_id(db_module)
    summary = db_module.get_expense_summary(
        user_id, start_date="2026-08-05", end_date="2026-08-12"
    )
    assert summary["count"] == 4
    assert summary["total"] == 4998.00
    assert summary["top_category"] == "Shopping"
    assert summary["top_amount"] == 2350.00


def test_get_expense_summary_with_only_start_date(db_module):
    user_id = _demo_user_id(db_module)
    summary = db_module.get_expense_summary(user_id, start_date="2026-08-15")
    assert summary["count"] == 2
    assert summary["total"] == 720.50


def test_get_expense_summary_with_only_end_date(db_module):
    user_id = _demo_user_id(db_module)
    summary = db_module.get_expense_summary(user_id, end_date="2026-08-04")
    assert summary["count"] == 2
    assert summary["total"] == 630.00


def test_get_recent_expenses_filters_by_date_range_and_orders_newest_first(
    db_module,
):
    user_id = _demo_user_id(db_module)
    rows = db_module.get_recent_expenses(
        user_id, limit=None, start_date="2026-08-05", end_date="2026-08-12"
    )
    assert [row["category"] for row in rows] == [
        "Shopping",
        "Entertainment",
        "Health",
        "Bills",
    ]


def test_get_category_breakdown_filters_by_date_range_and_orders_by_total_desc(
    db_module,
):
    user_id = _demo_user_id(db_module)
    rows = db_module.get_category_breakdown(
        user_id, start_date="2026-08-05", end_date="2026-08-12"
    )
    assert [(row["category"], row["total"]) for row in rows] == [
        ("Shopping", 2350.00),
        ("Bills", 1499.00),
        ("Entertainment", 799.00),
        ("Health", 350.00),
    ]


def test_query_functions_scope_to_user_id_even_with_date_range(
    db_module, register_client, insert_expense
):
    demo_id = _demo_user_id(db_module)

    register_client("Isolation User", "isolation-db@example.com", "password123")
    other = db_module.get_user_by_email("isolation-db@example.com")
    insert_expense(other["id"], 999.00, "Food", "2026-08-06", "Other user's lunch")

    # Filtering demo's own summary/recent/breakdown over a range that
    # contains the other user's expense must never include it.
    summary = db_module.get_expense_summary(
        demo_id, start_date="2026-08-05", end_date="2026-08-12"
    )
    assert summary["total"] == 4998.00
    assert summary["count"] == 4

    recent = db_module.get_recent_expenses(
        demo_id, limit=None, start_date="2026-08-05", end_date="2026-08-12"
    )
    assert all(row["category"] != "Food" for row in recent)
    assert len(recent) == 4

    breakdown = db_module.get_category_breakdown(
        demo_id, start_date="2026-08-05", end_date="2026-08-12"
    )
    assert all(row["category"] != "Food" for row in breakdown)


# ------------------------------------------------------------------ #
# Still-stubbed routes untouched by this step                        #
# ------------------------------------------------------------------ #

def test_add_expense_route_is_still_an_untouched_stub(client, login_client, db_module):
    login_client()
    user_id = _demo_user_id(db_module)
    before = db_module.get_expense_summary(user_id)["count"]

    response = client.get("/expenses/add")

    assert response.status_code == 200
    # A real page would extend base.html; the stub is plain text.
    assert "<html" not in response.get_data(as_text=True).lower()
    after = db_module.get_expense_summary(user_id)["count"]
    assert after == before
