import sqlite3
from pathlib import Path
import pytest
from state_graph.checkpointer import DBCheckpointSaver
from langgraph.checkpoint.base import empty_checkpoint

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT_DIR / "db" / "schema.sql"


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Builds an isolated test database using the repository's schema.sql."""
    db_path = tmp_path / "case_intake_test.db"
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    
    return db_path


def test_checkpoint_is_stored_and_loaded(test_db: Path):
    saver = DBCheckpointSaver(str(test_db))
    checkpoint = empty_checkpoint()
    checkpoint_id = checkpoint["id"]

    config = {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "",
        }
    }

    stored_config = saver.put(
        config,
        checkpoint,
        {},
        {},
    )

    assert stored_config["configurable"]["checkpoint_id"] == checkpoint_id

    conn = sqlite3.connect(test_db)
    row = conn.execute(
        """
        SELECT checkpoint_id, thread_id
        FROM graph_checkpoint
        WHERE thread_id = ?
        """,
        ("thread-1",),
    ).fetchone()
    conn.close()

    assert row is not None
    assert row[0] == checkpoint_id
    assert row[1] == "thread-1"

    loaded = saver.get_tuple(stored_config)

    assert loaded is not None
    assert loaded.checkpoint["id"] == checkpoint_id