"""Shared pytest fixtures for the Spendly test suite.

`app.py` has no application factory: at import time it creates the Flask
`app` object and immediately runs `init_db()` + `seed_db()` against the real
`expense_tracker.db` at the project root (inside `with app.app_context():`).
To keep tests from ever touching that file, every test gets its own throwaway
SQLite file: `database.db.DB_PATH` is repointed at a per-test temp path
*before* `app` (and the `database` package that feeds it) are (re)imported,
so `init_db()`/`seed_db()` run against the temp file instead. `get_db()`
opens a fresh connection and reads the module-level `DB_PATH` on every call,
so simply mutating that attribute before import is enough -- no per-function
patching is required.
"""

import os
import sys

import pytest

# Ensure the project root (parent of tests/) is importable regardless of how
# pytest is invoked, since app.py and the database package live there.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


def _purge_app_modules():
    """Drop app.py and the whole database package from the import cache.

    Forces a genuinely fresh import (and therefore a fresh init_db()/seed_db()
    run against whatever DB_PATH is set at that moment) for every test.
    """
    for name in list(sys.modules):
        if name == "app" or name == "database" or name.startswith("database."):
            del sys.modules[name]


@pytest.fixture
def app(tmp_path):
    """A fresh Flask app instance wired to a brand-new, seeded SQLite file."""
    db_path = tmp_path / "test_expense_tracker.db"

    _purge_app_modules()

    import database.db as db_module

    db_module.DB_PATH = str(db_path)

    import app as app_module  # noqa: F401  (import runs init_db()/seed_db())

    app_module.app.config.update(TESTING=True)

    yield app_module.app

    _purge_app_modules()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_module(app):
    """The database.db module, already reloaded against this test's temp DB."""
    import database.db as db

    return db


@pytest.fixture
def login_client(client):
    """Returns a callable that logs the test client in via POST /login."""

    def _login(email=DEMO_EMAIL, password=DEMO_PASSWORD):
        return client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    return _login


@pytest.fixture
def register_client(client):
    """Returns a callable that registers a new user via POST /register."""

    def _register(name, email, password):
        return client.post(
            "/register",
            data={"name": name, "email": email, "password": password},
            follow_redirects=True,
        )

    return _register


@pytest.fixture
def insert_expense(db_module):
    """Returns a callable that inserts an expense row directly via the DB.

    Used only for test setup that the spec's read-only date-filter feature
    doesn't itself provide a route for (there is no working expense-creation
    route yet -- /expenses/add is still an untouched Step 7 stub per this
    spec's Definition of done).
    """

    def _insert(user_id, amount, category, date, description=""):
        conn = db_module.get_db()
        try:
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, category, date, description),
            )
            conn.commit()
        finally:
            conn.close()

    return _insert
