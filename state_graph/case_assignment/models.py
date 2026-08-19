from typing import List, Optional
from pydantic import BaseModel
from .states import CaseAssignmentState

class CaseAssignmentStateData(BaseModel):
    case_id: str
    case_value: float = 0.0
    is_vip: bool = False
    assigned_attorney_id: Optional[str] = None
    declined_attorney_ids: List[str] = []
    decline_count: int = 0
    current_state: CaseAssignmentState = CaseAssignmentState.PROPOSED
    hitl_reason: Optional[str] = None
    ticket_id: Optional[str] = None
    ticket_status: Optional[str] = None # "open", "investigating", "resolved"