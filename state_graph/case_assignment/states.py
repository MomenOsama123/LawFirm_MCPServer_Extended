from enum import Enum

class CaseAssignmentState(str, Enum):
    PROPOSED = "proposed"
    AWAITING_ATTORNEY_RESPONSE = "awaiting_attorney_response"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REASSIGNING = "reassigning"
    ESCALATED = "escalated"  # HITL Pause
    TICKETED = "ticketed"    # Capacity/Failure Ticket