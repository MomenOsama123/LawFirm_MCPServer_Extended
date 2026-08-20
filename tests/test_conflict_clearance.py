# $env:PYTHONPATH="."
# pytest tests/test_checkpointer.py tests/test_conflict_clearance.py -v

from __future__ import annotations
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT_DIR / "db" / "schema.sql"
WORKER_FILE = ROOT_DIR / "tests" / "conflict_worker.py"


def create_test_database(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)

    conn.executescript(
        SCHEMA_FILE.read_text(encoding="utf-8")
    )

    conn.commit()
    conn.close()


def run_worker(
    db_path: Path,
    log_file: Path,
    mode: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    return subprocess.run(
        [
            sys.executable,
            str(WORKER_FILE),
            str(db_path),
            str(log_file),
            mode,
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        env=env,
    )


def test_conflict_clearance_recovers_after_process_kill(tmp_path):
    db_path = tmp_path / "case_intake_test.db"
    log_file = tmp_path / "nodes.log"

    create_test_database(db_path)

    # Process 1: run until running_conflict_check completes,
    # then kill the process at the next node.
    crashed = run_worker(
        db_path,
        log_file,
        "crash",
    )

    assert crashed.returncode == 42

    first_run_nodes = log_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert first_run_nodes == [
        "intake",
        "running_conflict_check",
        "awaiting_partner_signoff",
    ]

    # Confirm checkpoints exist directly in our database.
    conn = sqlite3.connect(db_path)

    checkpoint_count_before = conn.execute(
        """
        SELECT COUNT(*)
        FROM graph_checkpoint
        WHERE thread_id = ?
        """,
        ("conflict-test-thread",),
    ).fetchone()[0]

    conn.close()

    # We should have:
    # input checkpoint + intake checkpoint + conflict-check checkpoint.
    assert checkpoint_count_before >= 3

    # Process 2: resume from the latest saved checkpoint.
    recovered = run_worker(
        db_path,
        log_file,
        "recover",
    )

    assert recovered.returncode == 0
    assert "cleared" in recovered.stdout

    all_nodes = log_file.read_text(
        encoding="utf-8"
    ).splitlines()

    # intake and running_conflict_check were completed before the crash
    # and therefore must not execute again.
    assert all_nodes.count("intake") == 1
    assert all_nodes.count("running_conflict_check") == 1

    # awaiting_partner_signoff started once before the crash
    # and once after recovery.
    assert all_nodes.count("awaiting_partner_signoff") == 2

    # Recovery should have produced additional checkpoints.
    conn = sqlite3.connect(db_path)

    checkpoint_count_after = conn.execute(
        """
        SELECT COUNT(*)
        FROM graph_checkpoint
        WHERE thread_id = ?
        """,
        ("conflict-test-thread",),
    ).fetchone()[0]

    conn.close()

    assert checkpoint_count_after > checkpoint_count_before