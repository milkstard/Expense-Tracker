import os
import sqlite3
from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    get_db,
    init_db,
    seed_db,
    create_user,
    create_expense,
    get_user_by_email,
    get_user_by_id,
    get_expense_summary,
    get_recent_expenses,
    get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def format_member_since(created_at):
    """Turn the users.created_at TEXT column into 'August 2026'."""
    if not created_at:
        return "—"
    try:
        return datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except (TypeError, ValueError):
        return "—"


def initials_for(name):
    """First letter of up to the first two name parts, e.g. 'Demo User' -> 'DU'."""
    parts = (name or "").split()
    return "".join(part[0] for part in parts[:2]).upper() or "?"


def format_inr(amount):
    """Render an amount as INR, e.g. 6348.5 -> '₹6,348.50'."""
    return f"₹{amount or 0:,.2f}"


def format_txn_date(date_str):
    """Turn an expenses.date TEXT column ('YYYY-MM-DD') into '18 Aug'."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b")
    except (TypeError, ValueError):
        return date_str


def clean_date_param(raw):
    """Validate a 'YYYY-MM-DD' date from the query string.

    Returns (value, malformed): absent/blank -> (None, False),
    unparseable -> (None, True).
    """
    raw = (raw or "").strip()
    if not raw:
        return None, False
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None, True
    return raw, False


def format_date_range(start_date, end_date):
    """Human-readable label for the active date range, e.g. '05 Aug – 12 Aug'."""
    if start_date and end_date:
        return f"{format_txn_date(start_date)} – {format_txn_date(end_date)}"
    if start_date:
        return f"From {format_txn_date(start_date)}"
    if end_date:
        return f"Until {format_txn_date(end_date)}"
    return "All time"


CATEGORY_TONES = {
    "food": "food",
    "transport": "transport",
    "bills": "bills",
    "health": "health",
    "entertainment": "entertainment",
    "shopping": "shopping",
    "other": "other",
}


def category_tone(category):
    """Map a category name to its pill/cat-bar tone slug, defaulting to 'other'."""
    return CATEGORY_TONES.get((category or "").strip().lower(), "other")


# Title-case options for the add-expense form, derived from CATEGORY_TONES so
# the dropdown can never drift out of sync with the pill/cat-bar tone map.
CATEGORIES = [slug.title() for slug in CATEGORY_TONES]


def clean_amount(raw):
    """Validate a rupee amount from a form field. Returns (value, error)."""
    raw = (raw or "").strip()
    if not raw:
        return None, "Please enter an amount."
    try:
        amount = float(raw)
    except ValueError:
        return None, "Amount must be a number."
    # Upper bound also rejects inf; NaN fails the lower comparison.
    if not 0 < amount < 10_000_000:
        return None, "Amount must be greater than zero."
    return round(amount, 2), None


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")

        password_hash = generate_password_hash(password)
        try:
            create_user(name, email, password_hash)
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with that email already exists.")

        return redirect(url_for("login", registered=1))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="All fields are required.")

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        return redirect(url_for("profile"))

    registered = request.args.get("registered")
    return render_template("login.html", registered=registered)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    row = get_user_by_id(user_id)
    if row is None:
        # Stale session pointing at a user that no longer exists.
        session.clear()
        return redirect(url_for("login"))

    # Build an explicit dict so password_hash can never reach the template.
    user = {
        "name": row["name"],
        "email": row["email"],
        "initials": initials_for(row["name"]),
        "member_since": format_member_since(row["created_at"]),
    }

    # Optional date filter — untrusted query-string input, validated here.
    start_date, start_bad = clean_date_param(request.args.get("start_date"))
    end_date, end_bad = clean_date_param(request.args.get("end_date"))

    error = None
    if start_bad or end_bad:
        error = "Please enter a valid date."
        start_date = end_date = None
    elif start_date and end_date and start_date > end_date:
        error = "Start date must be on or before the end date."
        start_date = end_date = None

    active = bool(start_date or end_date)
    filters = {
        "start_date": start_date or "",
        "end_date": end_date or "",
        "active": active,
    }

    raw_summary = get_expense_summary(user_id, start_date, end_date)
    summary = {
        "total": format_inr(raw_summary["total"]),
        "count": raw_summary["count"],
        "top_category": raw_summary["top_category"] or "—",
        "top_amount": format_inr(raw_summary["top_amount"]) if raw_summary["top_category"] else "",
        "scope": format_date_range(start_date, end_date),
        "count_hint": "In this range" if active else "Logged so far",
    }

    transactions = [
        {
            "date": format_txn_date(row["date"]),
            "description": row["description"] or "—",
            "category": row["category"],
            "tone": category_tone(row["category"]),
            "amount": format_inr(row["amount"]),
        }
        # A filtered view shows every match, so the table can't silently
        # disagree with the transaction count in the stat card above it.
        for row in get_recent_expenses(
            user_id, None if active else 8, start_date, end_date
        )
    ]

    breakdown = get_category_breakdown(user_id, start_date, end_date)
    peak = breakdown[0]["total"] if breakdown else 0
    categories = [
        {
            "name": row["category"],
            "tone": category_tone(row["category"]),
            "amount": format_inr(row["total"]),
            "pct": round(row["total"] / peak * 100) if peak else 0,
        }
        for row in breakdown
    ]

    return render_template(
        "profile.html",
        user=user,
        summary=summary,
        transactions=transactions,
        categories=categories,
        filters=filters,
        error=error,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        form = {
            "amount": request.form.get("amount", "").strip(),
            "category": request.form.get("category", "").strip(),
            "date": request.form.get("date", "").strip(),
            "description": request.form.get("description", "").strip(),
        }

        amount, error = clean_amount(form["amount"])

        if not error and form["category"] not in CATEGORIES:
            error = "Please choose a category."

        expense_date = None
        if not error:
            expense_date, malformed = clean_date_param(form["date"])
            if malformed or not expense_date:
                error = "Please enter a valid date."

        if error:
            return render_template(
                "add_expense.html", categories=CATEGORIES, form=form, error=error
            )

        create_expense(
            user_id, amount, form["category"], expense_date,
            form["description"] or None,
        )
        return redirect(url_for("profile"))

    form = {
        "amount": "",
        "category": "",
        "date": date.today().isoformat(),
        "description": "",
    }
    return render_template("add_expense.html", categories=CATEGORIES, form=form)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
