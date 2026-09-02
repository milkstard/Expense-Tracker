import os
import sqlite3

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def create_user(name, email, password_hash):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def create_expense(user_id, amount, category, date, description):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def _date_range_sql(start_date, end_date):
    """Build the optional inclusive date-range clause for an expenses query.

    Returns (sql_fragment, params). The fragment is literal SQL only — the
    dates themselves always travel as bound parameters. expenses.date is an
    ISO 'YYYY-MM-DD' string, so plain string comparison filters correctly
    without a CAST or date() call.
    """
    fragment = ""
    params = []
    if start_date:
        fragment += " AND date >= ?"
        params.append(start_date)
    if end_date:
        fragment += " AND date <= ?"
        params.append(end_date)
    return fragment, params


def get_expense_summary(user_id, start_date=None, end_date=None):
    date_sql, date_params = _date_range_sql(start_date, end_date)
    conn = get_db()
    try:
        totals = conn.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total "
            "FROM expenses WHERE user_id = ?" + date_sql,
            (user_id, *date_params),
        ).fetchone()

        top = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ?" + date_sql + " GROUP BY category "
            "ORDER BY total DESC, category ASC LIMIT 1",
            (user_id, *date_params),
        ).fetchone()

        return {
            "count": totals["count"],
            "total": totals["total"],
            "top_category": top["category"] if top else None,
            "top_amount": top["total"] if top else None,
        }
    finally:
        conn.close()


def get_recent_expenses(user_id, limit=8, start_date=None, end_date=None):
    """Most recent expenses for a user, newest first. limit=None returns all."""
    date_sql, date_params = _date_range_sql(start_date, end_date)
    sql = (
        "SELECT id, amount, category, date, description FROM expenses "
        "WHERE user_id = ?" + date_sql + " ORDER BY date DESC, id DESC"
    )
    params = [user_id, *date_params]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    conn = get_db()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_category_breakdown(user_id, start_date=None, end_date=None):
    date_sql, date_params = _date_range_sql(start_date, end_date)
    conn = get_db()
    try:
        return conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ?" + date_sql + " GROUP BY category "
            "ORDER BY total DESC, category ASC",
            (user_id, *date_params),
        ).fetchall()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing > 0:
            return

        password_hash = generate_password_hash("demo123")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
        user_id = cur.lastrowid

        sample_expenses = [
            (user_id, 450.00, "Food", "2026-08-02", "Groceries - BigBasket"),
            (user_id, 180.00, "Transport", "2026-08-04", "Uber to office"),
            (user_id, 1499.00, "Bills", "2026-08-05", "Electricity bill"),
            (user_id, 350.00, "Health", "2026-08-08", "Pharmacy - vitamins"),
            (user_id, 799.00, "Entertainment", "2026-08-10", "Netflix subscription"),
            (user_id, 2350.00, "Shopping", "2026-08-12", "New running shoes"),
            (user_id, 620.50, "Food", "2026-08-15", "Dinner with friends"),
            (user_id, 100.00, "Other", "2026-08-18", "Miscellaneous"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            sample_expenses,
        )
        conn.commit()
    finally:
        conn.close()
