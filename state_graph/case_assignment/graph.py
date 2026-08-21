from langgraph.graph import END, START, StateGraph

from .models import CaseAssignmentGraphState
from .states import CaseAssignmentState


def propose(state: CaseAssignmentGraphState) -> dict:
    return {
        "current_state": CaseAssignmentState.AWAITING_ATTORNEY_RESPONSE,
    }


def handle_attorney_response(
    state: CaseAssignmentGraphState,
) -> dict:
    return {}


def route_after_response(
    state: CaseAssignmentGraphState,
) -> str:
    current_state = state["current_state"]

    if current_state == CaseAssignmentState.ACCEPTED:
        return "accepted"

    if current_state == CaseAssignmentState.DECLINED:
        return "declined"

    return "awaiting_response"


def accepted(state: CaseAssignmentGraphState) -> dict:
    return {
        "current_state": CaseAssignmentState.ACCEPTED,
    }


def declined(state: CaseAssignmentGraphState) -> dict:
    return {
        "current_state": CaseAssignmentState.DECLINED,
    }


def build_case_assignment_graph():
    graph = StateGraph(CaseAssignmentGraphState)

    graph.add_node("propose", propose)
    graph.add_node("handle_attorney_response", handle_attorney_response)
    graph.add_node("accepted", accepted)
    graph.add_node("declined", declined)

    graph.add_edge(START, "propose")
    graph.add_edge("propose", "handle_attorney_response")

    graph.add_conditional_edges(
        "handle_attorney_response",
        route_after_response,
        {
            "accepted": "accepted",
            "declined": "declined",
            "awaiting_response": END,
        },
    )

    graph.add_edge("accepted", END)
    graph.add_edge("declined", END)

    return graph.compile()