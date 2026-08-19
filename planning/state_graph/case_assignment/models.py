from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .states import CaseAssignmentState


@dataclass
class CaseAssignmentStateData:
    run_id: str
    case_id: str

    state: CaseAssignmentState = CaseAssignmentState.PROPOSED

    current_attorney_id: str | None = None
    candidate_attorney_ids: list[str] = field(default_factory=list)

    decline_count: int = 0
    is_vip: bool = False

    reason: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    metadata: dict[str, Any] = field(default_factory=dict)