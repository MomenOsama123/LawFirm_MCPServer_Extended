import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "db" / "case_intake.db"


def get_connection(db_path: Path | str | None = None):
    path = Path(db_path) if db_path is not None else DB_PATH

    logger.info(f"Connecting to SQLite database: {path}")

    if not path.exists():
        raise FileNotFoundError(
            f"Database not found at:\n{path}\n"
            "Run: python db/init_db.py"
        )

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn