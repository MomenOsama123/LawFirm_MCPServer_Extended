# $env:PYTHONPATH="."; pytest tests/test_case_tools.py -v

import sqlite3
from pathlib import Path
import pytest
from mcp_server.server import accept_case, reject_case, get_conflict_checks
from mcp_server import tools

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT_DIR / "db" / "schema.sql"
SEED_FILE = ROOT_DIR / "db" / "seed_data.sql"

class DummyContext:
    async def enable_components(self, **kwargs):
        pass

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Build a fresh test database using the project's real schema.sql
    and seed_data.sql, but keep it isolated from db/case_intake.db.
    """

    db_file = tmp_path / "case_intake_test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.executescript(
    SEED_FILE.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()

    def get_test_connection():
        connection = sqlite3.connect(db_file)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    monkeypatch.setattr(tools, "get_connection", get_test_connection)

    return db_file

@pytest.mark.asyncio
async def test_accept_case_updates_real_schema(test_db):
    result = await accept_case(
        DummyContext(),
        case_id="case-002",
        decided_by="staff-003",
        decision_reason="Conflict review completed successfully.",
    )
    assert result["success"] is True
    assert result["status"] == "accepted"
    conn = sqlite3.connect(test_db)

    row = conn.execute(""" SELECT
    status, decision_reason, decided_by, decision_at, updated_at
    FROM "case"
    WHERE case_id = ? """, ("case-002",),).fetchone()

    conn.close()

    assert row is not None
    assert row[0] == "accepted"
    assert row[1] == "Conflict review completed successfully."
    assert row[2] == "staff-003"
    assert row[3] is not None
    assert row[4] is not None


@pytest.mark.asyncio
async def test_reject_case_updates_real_schema(test_db):
    result = await reject_case(
        DummyContext(),
        case_id="case-002",
        decided_by="staff-003",
        decision_reason="Conflict detected during review.",
    )

    assert result["success"] is True
    assert result["status"] == "rejected"

    conn = sqlite3.connect(test_db)

    row = conn.execute(
        """
        SELECT status, decision_reason, decided_by, decision_at, updated_at
        FROM "case"
        WHERE case_id = ? """, ("case-002",),).fetchone()

    conn.close()

    assert row is not None
    assert row[0] == "rejected"
    assert row[1] == "Conflict detected during review."
    assert row[2] == "staff-003"
    assert row[3] is not None
    assert row[4] is not None

    def test_get_conflict_checks_reads_real_seed_data(test_db):
        result = get_conflict_checks("case-003")

        assert isinstance(result, list)
        assert len(result) == 1

        conflict = result[0]

        assert conflict["check_id"] == "check-001"
        assert conflict["case_id"] == "case-003"
        assert conflict["batch_job_id"] == "batch-001"
        assert conflict["matched_party_id"] == "party-003"
        assert conflict["match_type"] == "fuzzy_name_match"
        assert conflict["confidence_score"] == 0.87
        assert conflict["resolution"] == "unresolved"


@pytest.mark.asyncio
async def test_accept_case_missing_case_returns_error(test_db):
    result = await accept_case(
        DummyContext(),
        case_id="does-not-exist",
        decided_by="staff-003",
        decision_reason="Test",
    )

    assert result["success"] is False
    assert result["code"] == "CASE_NOT_FOUND"


@pytest.mark.asyncio
async def test_reject_case_missing_staff_returns_error(test_db):
    result = await reject_case(
        DummyContext(),
        case_id="case-002",
        decided_by="does-not-exist",
        decision_reason="Test",
    )

    assert result["success"] is False
    assert result["code"] == "STAFF_NOT_FOUND"


def test_get_conflict_checks_missing_case_returns_error(test_db):
    result = get_conflict_checks("does-not-exist")

    assert result["success"] is False
    assert result["code"] == "CASE_NOT_FOUND"


@pytest.mark.asyncio
async def test_accept_case_invalid_staff_does_not_modify_case(test_db):
    result = await accept_case(
        DummyContext(),
        case_id="case-002",
        decided_by="does-not-exist",
        decision_reason="Should fail",
    )

    assert result["success"] is False
    assert result["code"] == "STAFF_NOT_FOUND"

    conn = sqlite3.connect(test_db)

    status = conn.execute(
        'SELECT status FROM "case" WHERE case_id = ?',
        ("case-002",),
    ).fetchone()[0]

    conn.close()

    assert status == "under_review"