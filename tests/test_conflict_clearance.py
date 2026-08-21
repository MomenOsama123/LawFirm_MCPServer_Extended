from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT_DIR / "db" / "schema.sql"

ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT_DIR)


def create_test_database(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def test_conflict_clearance_resumes_in_new_process(tmp_path):
    db_path = tmp_path / "case_intake_test.db"
    create_test_database(db_path)

    try:
        start = subprocess.run(
            [
                sys.executable,
                "tests/conflict_worker.py",
                str(db_path),
                "start",
            ],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
            env=ENV,
        )
    except subprocess.CalledProcessError as e:
        print("\n--- SUBPROCESS STDOUT ---")
        print(e.stdout)
        print("--- SUBPROCESS STDERR ---")
        print(e.stderr)
        raise e

    assert "awaiting_partner_signoff" in start.stdout

    conn = sqlite3.connect(db_path)
    checkpoint_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM graph_checkpoint
        WHERE thread_id = ?
        """,
        ("conflict-test-thread",),
    ).fetchone()[0]
    conn.close()

    assert checkpoint_count >= 3

    try:
        resume = subprocess.run(
            [
                sys.executable,
                "tests/conflict_worker.py",
                str(db_path),
                "resume",
            ],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
            env=ENV,
        )
    except subprocess.CalledProcessError as e:
        print("\n--- SUBPROCESS STDOUT ---")
        print(e.stdout)
        print("--- SUBPROCESS STDERR ---")
        print(e.stderr)
        raise e

    assert "cleared" in resume.stdout