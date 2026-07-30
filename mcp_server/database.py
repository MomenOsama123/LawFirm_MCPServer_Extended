import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "db" / "case_intake.db"


def get_connection():
    logger.info(f"Connecting to SQLite database: {DB_PATH}")

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at:\n{DB_PATH}\n"
            "Run: python db/init_db.py"
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn