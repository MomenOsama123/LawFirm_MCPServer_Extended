from __future__ import annotations
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from state_graph.checkpointer import DBCheckpointSaver

class ConflictState(TypedDict):
    case_id: str
    status: str
    conflict_found: bool
    partner_approved: bool
    check_list: list[str]
    search_results: list[str]
    evaluation: str
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
    conflict_found = False
    return {
        "conflict_found": conflict_found,
        "evaluation": "No conflict identified.",
    }


def draft_memo_node(state: ConflictState) -> dict:
    return {
        "memo": (
            "Conflict search completed. "
            "No conflict identified."
        ),
        "status": "awaiting_partner_signoff",
    }


def awaiting_partner_signoff_node(state: ConflictState) -> dict:
    approved = interrupt("Waiting for partner sign-off.")

    return {
        "partner_approved": bool(approved),
        "status": (
            "cleared"
            if approved
            else "rejected"
        ),
    }


def route_after_conflict(state: ConflictState) -> str:
    if state.get("conflict_found"):
        return "rejected"

    return "awaiting_partner_signoff"


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
        awaiting_partner_signoff
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
    builder.add_node("draft_memo", draft_memo_node)
    builder.add_node(
        "awaiting_partner_signoff",
        awaiting_partner_signoff_node,
    )
    builder.add_node("cleared", cleared_node)
    builder.add_node("rejected", rejected_node)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "decompose_conflict_check")
    builder.add_edge("decompose_conflict_check", "search")
    builder.add_edge("search", "evaluate")
    builder.add_edge("evaluate", "draft_memo")
    builder.add_edge("draft_memo", "awaiting_partner_signoff")

    builder.add_conditional_edges(
        "awaiting_partner_signoff",
        lambda state: (
            "cleared"
            if state.get("partner_approved")
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