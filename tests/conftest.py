from pathlib import Path
import sqlite3
import platform as stdlib_platform

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
stdlib_platform.__path__ = [str(ROOT_DIR / "platform")]
DB_FILE = ROOT_DIR / "db" / "case_intake.db"
SCHEMA_FILE = ROOT_DIR / "db" / "schema.sql"
SEED_FILE = ROOT_DIR / "db" / "seed_data.sql"


@pytest.fixture(scope="session", autouse=True)
def reset_shared_database():
    """Keep tests that use the shared database independent of test order."""
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        tables = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for (table_name,) in tables:
            connection.execute(f'DELETE FROM "{table_name}"')
        connection.executescript(SEED_FILE.read_text(encoding="utf-8"))
        connection.execute("PRAGMA foreign_keys = ON")
        connection.commit()

    yield
