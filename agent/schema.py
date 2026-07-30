# ______________________________________________
from typing import Any, Literal
from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    """
    Represents one validated step selected
    by the constrained legal case agent.
    """

    thought: str = Field(
        description=(
            "Short explanation of why the "
            "next action is required."
        )
    )

    action: Literal[
        # Read-only MCP tools
        "database_health",
        "get_case",
        "get_client",
        "get_conflict_checks",
        "get_lawyer",

        # MCP tools that modify data
        "accept_case",
        "reject_case",
        "assign_case_to_lawyer",

        # Agent control actions
        "final_answer",
        "escalate",
    ]

    action_input: dict[str, Any] = Field(
        default_factory=dict
    )

    final_decision: str | None = None