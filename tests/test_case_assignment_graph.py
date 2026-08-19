from state_graph.case_assignment.graph import build_case_assignment_graph
from state_graph.case_assignment.states import CaseAssignmentState


def test_case_assignment_graph_proposes_attorney():
    graph = build_case_assignment_graph()

    result = graph.invoke(
        {
            "case_id": "CASE-001",
            "current_state": CaseAssignmentState.PROPOSED,
        }
    )

    assert (
        result["current_state"]
        == CaseAssignmentState.AWAITING_ATTORNEY_RESPONSE
    )