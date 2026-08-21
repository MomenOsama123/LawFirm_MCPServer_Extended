from typing import Any, TypedDict

from .states import CaseAssignmentState


class CaseAssignmentGraphState(TypedDict, total=False):
    case_id: str
    case_value: float
    is_vip: bool

    assigned_attorney_id: str | None
    declined_attorney_ids: list[str]

    decline_count: int

    current_state: CaseAssignmentState

    hitl_reason: str | None

    ticket_id: str | None
    ticket_status: str | None

    metadata: dict[str, Any]