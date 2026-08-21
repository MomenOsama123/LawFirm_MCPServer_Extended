from __future__ import annotations

import uuid
from datetime import datetime, timezone
import sqlite3
from typing import TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from mcp_server.database import get_connection


class ConflictClearanceState(TypedDict, total=False):
    case_id: str
    thread_id: str
    status: str
    conflict_found: bool
    risk_score: float
    partner_approved: bool


def check_conflict(state: ConflictClearanceState) -> dict[str, str]:
    if state.get("conflict_found"):
        return {"status": "conflict_flagged"}
    return {"status": "awaiting_partner_signoff"}


def await_partner_signoff(
    state: ConflictClearanceState,
    connection_factory=get_connection,
) -> dict[str, str | bool]:
    thread_id = state.get("thread_id", "")
    case_id = state["case_id"]
    risk_score = max(float(state.get("risk_score", 0.0)), 0.9)

    with connection_factory() as connection:
        task = connection.execute(
            """
            SELECT task_id
            FROM hitl_tasks
            WHERE thread_id = ? AND case_id = ? AND status = 'pending'
            ORDER BY rowid DESC
            LIMIT 1
            """,
            (thread_id, case_id),
        ).fetchone()

        if task is None:
            task_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO hitl_tasks(
                    task_id, thread_id, case_id, task_type, risk_score, status
                ) VALUES (?, ?, ?, 'partner_signoff', ?, 'pending')
                """,
                (task_id, thread_id, case_id, risk_score),
            )
            connection.commit()
        else:
            task_id = task["task_id"]

    decision = interrupt("Partner signoff required")
    approved = not isinstance(decision, dict) or decision.get("decision") != "reject"
    status = "approved" if approved else "rejected"

    with connection_factory() as connection:
        connection.execute(
            """
            UPDATE hitl_tasks
            SET status = ?, decision_by = ?, decision_at = ?
            WHERE task_id = ?
            """,
            (
                status,
                decision.get("decided_by") if isinstance(decision, dict) else None,
                datetime.now(timezone.utc).isoformat() if isinstance(decision, dict) else None,
                task_id,
            ),
        )
        connection.commit()

    return {
        "partner_approved": approved,
        "status": "cleared" if approved else "rejected",
    }


def build_graph(checkpointer: BaseCheckpointSaver):
    connection_factory = get_connection
    database_path = getattr(checkpointer, "database_path", None)
    if database_path is not None:
        def connection_factory():
            connection = sqlite3.connect(database_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection

    graph = StateGraph(ConflictClearanceState)
    graph.add_node("check_conflict", check_conflict)
    graph.add_node(
        "await_partner_signoff",
        lambda state: await_partner_signoff(state, connection_factory),
    )
    graph.add_edge(START, "check_conflict")
    graph.add_conditional_edges(
        "check_conflict",
        lambda state: "flagged" if state.get("conflict_found") else "signoff",
        {"flagged": END, "signoff": "await_partner_signoff"},
    )
    graph.add_edge("await_partner_signoff", END)
    return graph.compile(checkpointer=checkpointer)
