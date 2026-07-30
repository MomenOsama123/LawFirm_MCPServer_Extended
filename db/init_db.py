import sqlite3
import os

DB_FILE = "case_intake.db"
SCHEMA_FILE = "schema.sql"
SEED_FILE = "seed_data.sql"


def main():
    # Start fresh each time this script runs, so the demo is repeatable.
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed existing '{DB_FILE}' to start clean.")

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")

    # 1. Build the schema (tables, constraints, indexes)
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    print(f"Schema loaded from '{SCHEMA_FILE}'.")

    # 2. Load the seed data (normal cases + edge cases), if present
    if os.path.exists(SEED_FILE):
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        print(f"Seed data loaded from '{SEED_FILE}'.")
    else:
        print(f"No '{SEED_FILE}' found — database created with empty tables.")

    # Quick sanity check: list tables and their row counts.
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    print(f"\n'{DB_FILE}' ready with {len(tables)} tables:")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        print(f"  - {table} ({count} rows)")
    conn.close()


if __name__ == "__main__":
    main()
