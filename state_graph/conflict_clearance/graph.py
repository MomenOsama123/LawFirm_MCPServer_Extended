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

def intake_node(state: ConflictState) -> dict:
    return {
        "status": "running_conflict_check",
    }

def running_conflict_check_node(state: ConflictState) -> dict:
    # Mock result for this milestone.
    return {
        "conflict_found": False,
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
    if state["conflict_found"]:
        return "rejected"

    return "awaiting_partner_signoff"

def route_after_signoff(state: ConflictState) -> str:
    if state["partner_approved"]:
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
    Conflict Clearance state flow:

        intake
          ↓
        running_conflict_check
          ↓
        awaiting_partner_signoff
          ↓
        cleared / rejected

    The partner sign-off node interrupts the graph and waits for
    an external resume operation.
    """

    builder = StateGraph(ConflictState)

    builder.add_node("intake", intake_node)
    builder.add_node(
        "running_conflict_check",
        running_conflict_check_node,
    )
    builder.add_node(
        "awaiting_partner_signoff",
        awaiting_partner_signoff_node,
    )
    builder.add_node("cleared", cleared_node)
    builder.add_node("rejected", rejected_node)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "running_conflict_check")

    builder.add_conditional_edges(
        "running_conflict_check",
        route_after_conflict,
        {
            "awaiting_partner_signoff": "awaiting_partner_signoff",
            "rejected": "rejected",
        },
    )

    builder.add_conditional_edges(
        "awaiting_partner_signoff",
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