from __future__ import annotations
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from state_graph.checkpointer import DBCheckpointSaver
from project_root.rag.policy_retriever import retrieve_policy_docs
import sqlite3
import uuid
from mcp_server.database import get_connection

RISK_SCORE_THRESHOLD = 0.70
# Conflicts above 0.70 require human partner review.
# The threshold intentionally prevents the agent from unilaterally
# clearing cases where the conflict evidence is sufficiently risky.

class ConflictState(TypedDict):
    case_id: str
    status: str
    conflict_found: bool
    risk_score: float
    partner_approved: bool
    check_list: list[str]
    search_results: list[str]
    evaluation: str
    policy_docs: list[dict]
    memo: str


def intake_node(state: ConflictState) -> dict:
    return {
        "status": "running_conflict_check",
    }


def decompose_conflict_check_node(state: ConflictState) -> dict:
    check_list = ["search", "evaluate", "draft_memo"]
    return {
        "check_list": check_list,
        "status": "running_conflict_check",
    }


def search_node(state: ConflictState) -> dict:
    return {
        "search_results": ["No conflicting party found."],
    }


def evaluate_node(state: ConflictState) -> dict:
    risk_score = 0.85

    return {
        "conflict_found": risk_score > 0,
        "risk_score": risk_score,
        "evaluation": f"Conflict risk score: {risk_score:.2f}",
    }

def retrieve_policy_node(state: ConflictState) -> dict:
    """Pull relevant conflict-of-interest policy docs via the shared RAG stack."""
    query = "conflict of interest policy evaluation rules for case review"
    docs = retrieve_policy_docs(query, top_k=2)
    return {"policy_docs": docs}


def draft_memo_node(state: ConflictState) -> dict:
    policy_docs = state.get("policy_docs", [])
    if policy_docs:
        policy_section = "\n\n".join(
            f"[{doc['metadata'].get('source', 'policy')}]\n{doc['content']}"
            for doc in policy_docs
        )
    else:
        policy_section = "No policy documents retrieved."

    result_text = "Conflict identified." if state.get("conflict_found") else "No conflict identified."

    memo = (
        "Conflict search completed. "
        f"{result_text}\n\n"
        "Relevant policy:\n"
        f"{policy_section}"
    )
    return {"memo": memo, "status": "partner_signoff"}



def partner_signoff_node(state: ConflictState, config) -> dict:
    risk_score = state["risk_score"]

    if risk_score <= RISK_SCORE_THRESHOLD:
        return {
            "partner_approved": True,
            "status": "cleared",
        }

    task_id = str(uuid.uuid4())
    thread_id = config["configurable"]["thread_id"]
    db_path = config["configurable"]["db_path"]

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO hitl_tasks (
                task_id,
                thread_id,
                case_id,
                task_type,
                risk_score,
                status
            )
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (
                task_id,
                thread_id,
                state["case_id"],
                "partner_signoff",
                risk_score,
            ),
        )
        conn.commit()

    decision = interrupt(
        {
            "task_id": task_id,
            "type": "partner_signoff",
            "case_id": state["case_id"],
            "risk_score": risk_score,
        }
    )

    if not isinstance(decision, dict):
        raise ValueError("Invalid HITL decision.")

    action = decision.get("decision")
    decided_by = decision.get("decided_by")

    if action not in {"approve", "reject"}:
        raise ValueError("HITL decision must be 'approve' or 'reject'.")

    if not decided_by:
        raise ValueError("HITL decision requires decided_by.")

    status = "approved" if action == "approve" else "rejected"

    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE hitl_tasks
            SET
                status = ?,
                decision_by = ?,
                decision_at = datetime('now'),
                updated_at = datetime('now')
            WHERE task_id = ?
            """,
            (
                status,
                decided_by,
                task_id,
            ),
        )
        conn.commit()

    return {
        "partner_approved": action == "approve",
        "status": "cleared" if action == "approve" else "rejected",
    }


def route_after_conflict(state: ConflictState) -> str:
    if state.get("conflict_found"):
        return "rejected"

    return "partner_signoff"


def route_after_signoff(state: ConflictState) -> str:
    if state.get("partner_approved"):
        return "cleared"

    return "rejected"


def cleared_node(state: ConflictState) -> dict:
    return {
        "status": "cleared",
    }


def rejected_node(state: ConflictState) -> dict:
    return {
        "status": "rejected",
    }


def build_graph(checkpointer: DBCheckpointSaver):
    """
    Conflict Clearance workflow:

        intake
          ↓
        decompose_conflict_check
          ↓
        search
          ↓
        evaluate
          ↓
        draft_memo
          ↓
        partner_signoff
          ↓
        cleared / rejected
    """

    builder = StateGraph(ConflictState)

    builder.add_node("intake", intake_node)
    builder.add_node(
        "decompose_conflict_check",
        decompose_conflict_check_node,
    )
    builder.add_node("search", search_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("partner_signoff",partner_signoff_node,)
    builder.add_node("retrieve_policy", retrieve_policy_node)
    builder.add_node("draft_memo", draft_memo_node)
    builder.add_node("cleared", cleared_node)
    builder.add_node("rejected", rejected_node)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "decompose_conflict_check")
    builder.add_edge("decompose_conflict_check", "search")
    builder.add_edge("search", "evaluate")
    builder.add_edge("evaluate", "retrieve_policy")
    builder.add_edge("retrieve_policy", "draft_memo")
    builder.add_edge("draft_memo", "partner_signoff")

    builder.add_conditional_edges(
        "partner_signoff",
        lambda state: (
            "cleared"
            if state["partner_approved"]
            else "rejected"
        ),
        {
            "cleared": "cleared",
            "rejected": "rejected",
        },
    )

    builder.add_edge("cleared", END)
    builder.add_edge("rejected", END)

    return builder.compile(checkpointer=checkpointer)