from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class ConflictClearanceState(TypedDict, total=False):
    case_id: str
    status: str
    conflict_found: bool
    partner_approved: bool


def check_conflict(state: ConflictClearanceState) -> dict[str, str]:
    if state.get("conflict_found"):
        return {"status": "conflict_flagged"}
    return {"status": "awaiting_partner_signoff"}


def await_partner_signoff(state: ConflictClearanceState) -> dict[str, str | bool]:
    interrupt("Partner signoff required")
    return {"partner_approved": True, "status": "cleared"}


def build_graph(checkpointer: BaseCheckpointSaver):
    graph = StateGraph(ConflictClearanceState)
    graph.add_node("check_conflict", check_conflict)
    graph.add_node("await_partner_signoff", await_partner_signoff)
    graph.add_edge(START, "check_conflict")
    graph.add_conditional_edges(
        "check_conflict",
        lambda state: "flagged" if state.get("conflict_found") else "signoff",
        {"flagged": END, "signoff": "await_partner_signoff"},
    )
    graph.add_edge("await_partner_signoff", END)
    return graph.compile(checkpointer=checkpointer)
