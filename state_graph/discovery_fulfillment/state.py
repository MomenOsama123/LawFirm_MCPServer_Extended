from typing import TypedDict, List, Dict, Any, Optional

class DiscoveryState(TypedDict):
    request_id: str
    instruction: str
    checklist: List[str]                  # Generated via Task Decomposition
    documents: List[Dict[str, Any]]        # Received document list
    flagged_docs: List[str]               # Documents flagged for privilege review
    court_deadline_passed: bool           # Trigger condition for unplanned Ticket
    attorney_approval: Optional[bool]     # HITL approval decision
    status: str                           # Current node/workflow status
    error_message: Optional[str]          # Error details if failure occurs