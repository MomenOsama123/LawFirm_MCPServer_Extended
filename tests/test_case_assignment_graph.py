import pytest
from langgraph.types import Command
from state_graph.case_assignment.graph import build_case_assignment_graph
from state_graph.case_assignment.states import CaseAssignmentState

def test_case_assignment_accepted_flow():
    app = build_case_assignment_graph()
    
    # 1. Start execution -> should pause at awaiting_response via interrupt
    initial_state = {
        "case_id": "CASE-101",
        "current_candidate": "lawyer_a",
        "decline_count": 0,
        "is_vip": False
    }
    
    thread_config = {"configurable": {"thread_id": "test_thread_1"}}
    
    # Run until interrupt
    events = app.invoke(initial_state, config=thread_config)
    
    # Check that it interrupted and asks for user response
    state = app.get_state(thread_config)
    assert state.next[0] == "awaiting_response"

    # 2. Resume execution with 'accepted' response
    final_state = app.invoke(Command(resume={"status": "accepted"}), config=thread_config)
    assert final_state["current_state"] == CaseAssignmentState.ACCEPTED


def test_case_assignment_escalation_flow():
    app = build_case_assignment_graph()
    
    # VIP case should escalate immediately on decline
    initial_state = {
        "case_id": "CASE-VIP-99",
        "current_candidate": "lawyer_a",
        "decline_count": 0,
        "is_vip": True
    }
    
    thread_config = {"configurable": {"thread_id": "test_thread_2"}}
    
    app.invoke(initial_state, config=thread_config)
    
    # Resume with decline -> should escalate due to VIP status
    final_state = app.invoke(Command(resume={"status": "declined"}), config=thread_config)
    assert final_state["current_state"] == CaseAssignmentState.ESCALATED
    assert final_state.get("hitl_ticket_created") is True