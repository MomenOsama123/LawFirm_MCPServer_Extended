from typing import Dict, Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from .models import CaseAssignmentGraphState
from .states import CaseAssignmentState

from planning.algorithms.tree_of_thoughts import TreeOfThoughtsEngine
from mcp_server.tools import assign_case_to_lawyer

MAX_RETRIES = 3  # Maximum number of reassignment attempts before escalation


def propose_node(state: CaseAssignmentGraphState) -> Dict[str, Any]:
    """
    Node responsible for proposing the case assignment to a specific lawyer
    using the real assignment tool.
    """
    candidate_lawyer = state.get("current_candidate")
    case_id = state.get("case_id")

    assignment_result = {
        "status": "proposed",
        "case_id": case_id,
        "lawyer_id": candidate_lawyer,
    }

    return {
        "current_state": CaseAssignmentState.AWAITING_ATTORNEY_RESPONSE,
        "assignment_status": assignment_result,
    }


def awaiting_response_node(
    state: CaseAssignmentGraphState
) -> Dict[str, Any]:
    """
    Node that uses interrupt to pause the State Graph execution
    while waiting for the lawyer's response.

    The graph can remain paused for hours or days and resume
    when the lawyer's response is received.
    """

    # Pause graph execution and return the required data to the interface
    user_response = interrupt({
        "message": (
            f"Waiting for lawyer {state.get('current_candidate')} "
            f"response on case {state.get('case_id')}"
        ),
        "case_id": state.get("case_id"),
        "lawyer_id": state.get("current_candidate"),
    })

    # The user response is received when the graph is resumed
    response_status = user_response.get("status")

    if response_status == "accepted":
        return {
            "current_state": CaseAssignmentState.ACCEPTED
        }

    elif response_status == "declined":
        decline_count = state.get("decline_count", 0) + 1

        return {
            "current_state": CaseAssignmentState.DECLINED,
            "decline_count": decline_count,
        }

    return {
        "current_state": CaseAssignmentState.AWAITING_ATTORNEY_RESPONSE
    }


def reassign_node(state: CaseAssignmentGraphState) -> Dict[str, Any]:
    """
    Uses Tree of Thoughts (ToT) to select the best alternative lawyer
    based on capacity, experience, and case suitability.
    """

    tot_engine = TreeOfThoughtsEngine()

    # Select the next best candidate using ToT
    next_candidate = tot_engine.select_next_best_attorney(
        case_id=state.get("case_id"),
        excluded_lawyers=state.get("rejected_lawyers", []),
    )

    if not next_candidate:
        # No suitable lawyers with available capacity
        # Escalate the case for human intervention
        return {
            "current_state": CaseAssignmentState.ESCALATED,
            "escalation_reason": "No capacity / No candidates available",
        }

    rejected_list = state.get("rejected_lawyers", [])
    rejected_list.append(state.get("current_candidate"))

    return {
        "current_candidate": next_candidate,
        "rejected_lawyers": rejected_list,
        "current_state": CaseAssignmentState.PROPOSED,
    }


def escalate_node(state: CaseAssignmentGraphState) -> Dict[str, Any]:
    """
    Escalates the case to a Human-in-the-Loop workflow,
    such as a Managing Partner or Admin Inbox.
    """

    return {
        "current_state": CaseAssignmentState.ESCALATED,
        "hitl_ticket_created": True,
    }


def route_after_response(state: CaseAssignmentGraphState) -> str:
    """
    Determines the next step after receiving the lawyer's response.
    """

    current_state = state.get("current_state")
    is_vip = state.get("is_vip", False)
    decline_count = state.get("decline_count", 0)

    if current_state == CaseAssignmentState.ACCEPTED:
        return "accepted"

    if current_state == CaseAssignmentState.DECLINED:
        if decline_count >= MAX_RETRIES or is_vip:
            return "escalate"

        return "reassign"

    return "awaiting_response"


def build_case_assignment_graph():
    """
    Builds and compiles the case assignment State Graph.
    """

    graph = StateGraph(CaseAssignmentGraphState)

    graph.add_node("propose", propose_node)
    graph.add_node("awaiting_response", awaiting_response_node)
    graph.add_node("reassign", reassign_node)
    graph.add_node("escalate", escalate_node)

    graph.add_edge(START, "propose")

    graph.add_edge(
        "propose",
        "awaiting_response"
    )

    graph.add_conditional_edges(
        "awaiting_response",
        route_after_response,
        {
            "accepted": END,
            "reassign": "reassign",
            "escalate": "escalate",
            "awaiting_response": "awaiting_response",
        },
    )

    # Connect the reassignment node back to the proposal node
    # so the newly selected candidate can be proposed.
    graph.add_conditional_edges(
        "reassign",
        lambda state: (
            "escalate"
            if state.get("current_state") == CaseAssignmentState.ESCALATED
            else "propose"
        ),
        {
            "propose": "propose",
            "escalate": "escalate",
        },
    )

    graph.add_edge(
        "escalate",
        END
    )

    return graph.compile(checkpointer=MemorySaver())

def propose_node(state: CaseAssignmentState) -> dict:
    lawyer_id = state.get("current_lawyer_id")
    case_id = state.get("case_id")
    
    # Execute actual tool call
    assignment_result = assign_case_to_lawyer(case_id=case_id, lawyer_id=lawyer_id)
    
    return {
        "status": "proposed",
        "assignment_result": assignment_result
    }