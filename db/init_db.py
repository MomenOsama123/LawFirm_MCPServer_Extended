import sqlite3
from pathlib import Path

# Directory containing this file
DB_DIR = Path(__file__).resolve().parent

DB_FILE = DB_DIR / "case_intake.db"
SCHEMA_FILE = DB_DIR / "schema.sql"
SEED_FILE = DB_DIR / "seed_data.sql"


def main():
    # Start fresh each time this script runs
    if DB_FILE.exists():
        DB_FILE.unlink()
        print(f"Removed existing '{DB_FILE.name}' to start clean.")

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Load schema
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.commit()
    print(f"Schema loaded from '{SCHEMA_FILE.name}'.")

    # Load seed data
    if SEED_FILE.exists():
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        conn.commit()
        print(f"Seed data loaded from '{SEED_FILE.name}'.")
    else:
        print("No seed file found.")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)

    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"\nDatabase created at:\n{DB_FILE}\n")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        print(f"{table}: {cursor.fetchone()[0]} rows")

    conn.close()


if __name__ == "__main__":
    main()