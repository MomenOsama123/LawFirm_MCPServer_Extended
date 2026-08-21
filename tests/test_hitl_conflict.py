from __future__ import annotations
import sqlite3
from pathlib import Path
from langgraph.types import Command
from state_graph.checkpointer import DBCheckpointSaver
from state_graph.conflict_clearance import graph as conflict_graph


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT_DIR / "db" / "schema.sql"
SEED_FILE = ROOT_DIR / "db" / "seed_data.sql"


class TestDB:
    __test__ = False

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def __call__(self, db_path=None):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def create_test_database(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)

    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript(
        SCHEMA_FILE.read_text(encoding="utf-8")
    )

    conn.executescript(
        SEED_FILE.read_text(encoding="utf-8")
    )

    conn.commit()
    conn.close()


def initial_state() -> dict:
    return {
        "case_id": "case-003",
        "thread_id": "hitl-test-thread",
        "status": "intake",
        "conflict_found": False,
        "risk_score": 0.0,
        "partner_approved": False,
        "checklist": [],
        "search_results": [],
        "evaluation": "",
        "memo": "",
    }


def build_test_graph(tmp_path: Path):
    db_path = tmp_path / "case_intake_test.db"

    create_test_database(db_path)

    # Make the real graph code use our isolated test database.
    conflict_graph.get_connection = TestDB(db_path)

    checkpointer = DBCheckpointSaver(str(db_path))
    graph = conflict_graph.build_graph(checkpointer)

    return graph, db_path


def get_hitl_task(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT
            task_id,
            thread_id,
            case_id,
            task_type,
            risk_score,
            status,
            decision_by,
            decision_at
        FROM hitl_tasks
        WHERE thread_id = ?
        ORDER BY rowid DESC
        LIMIT 1
        """,
        ("hitl-test-thread",),
    ).fetchone()

    conn.close()

    return row


def test_risky_conflict_creates_hitl_task_and_pauses(tmp_path):
    graph, db_path = build_test_graph(tmp_path)

    config = {
        "configurable": {
            "thread_id": "hitl-test-thread",
            "db_path": str(db_path),
        }
    }

    result = graph.invoke(
        initial_state(),
        config,
        durability="sync",
    )

    # LangGraph should stop at the HITL interrupt.
    assert "__interrupt__" in result

    task = get_hitl_task(db_path)

    assert task is not None
    assert task["thread_id"] == "hitl-test-thread"
    assert task["case_id"] == "case-003"
    assert task["task_type"] == "partner_signoff"
    assert task["risk_score"] > 0.70
    assert task["status"] == "pending"
    assert task["decision_by"] is None


def test_admin_approval_resumes_to_cleared(tmp_path):
    graph, db_path = build_test_graph(tmp_path)

    config = {
        "configurable": {
            "thread_id": "hitl-test-thread",
            "db_path": str(db_path),
        }
    }

    # First run pauses for HITL.
    result = graph.invoke(
        initial_state(),
        config,
        durability="sync",
    )

    assert "__interrupt__" in result

    # Resume with an explicit admin decision.
    resumed = graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "decided_by": "staff-003",
            }
        ),
        config,
        durability="sync",
    )

    assert resumed["status"] == "cleared"
    assert resumed["partner_approved"] is True

    task = get_hitl_task(db_path)

    assert task is not None
    assert task["status"] == "approved"
    assert task["decision_by"] == "staff-003"
    assert task["decision_at"] is not None


def test_admin_rejection_resumes_to_rejected(tmp_path):
    graph, db_path = build_test_graph(tmp_path)

    config = {
        "configurable": {
            "thread_id": "hitl-test-thread",
            "db_path": str(db_path),
        }
    }

    # First run pauses for HITL.
    result = graph.invoke(
        initial_state(),
        config,
        durability="sync",
    )

    assert "__interrupt__" in result

    # Resume with an explicit rejection.
    resumed = graph.invoke(
        Command(
            resume={
                "decision": "reject",
                "decided_by": "staff-003",
            }
        ),
        config,
        durability="sync",
    )

    assert resumed["status"] == "rejected"
    assert resumed["partner_approved"] is False

    task = get_hitl_task(db_path)

    assert task is not None
    assert task["status"] == "rejected"
    assert task["decision_by"] == "staff-003"
    assert task["decision_at"] is not None