from typing import TypedDict, Optional, List, Dict, Any
from .states import CaseAssignmentState

class CaseAssignmentGraphState(TypedDict, total=False):
    case_id: str
    current_candidate: str
    rejected_lawyers: List[str]
    current_state: CaseAssignmentState
    decline_count: int
    is_vip: bool
    assignment_status: Optional[Dict[str, Any]]
    escalation_reason: Optional[str]
    hitl_ticket_created: Optional[bool]