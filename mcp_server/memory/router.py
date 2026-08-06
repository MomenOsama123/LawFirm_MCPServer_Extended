from datetime import datetime
from pathlib import Path
import json
from typing import Literal, Optional
from pydantic import BaseModel


class MemoryRoutingDecision(BaseModel):
    """
    Represents a decision made by the memory router regarding
    where an evicted message should go.
    """

    destination: Literal["forget", "episodic"]
    reasoning: str

    # Populated only if destination == "episodic"
    event_summary: Optional[str] = None
    context: Optional[str] = None
    outcome: Optional[str] = None


class MemoryRouter:
    """
    Routes items evicted from the rolling buffer.

    NOTE:
    This router NEVER writes to semantic memory.
    It only decides whether to:
      - forget
      - promote to episodic memory
    """

    LOG_DIR = Path(__file__).parent / "logs"
    LOG_FILE = LOG_DIR / "router_log.json"

    def route(self, item: dict) -> MemoryRoutingDecision:
        """
        Decide whether to forget the item or promote it
        to episodic memory.
        """

        content = item.get("content", "").lower()

        # Temporary heuristic.
        # Later this can be replaced by an LLM call.
        if "my" in content:
            decision = MemoryRoutingDecision(
                destination="episodic",
                reasoning="Contains possible user-specific information.",
                event_summary=item.get("content")
            )
        else:
            decision = MemoryRoutingDecision(
                destination="forget",
                reasoning="No long-term value detected."
            )

        self.log_decision(item, decision)

        return decision

    def log_decision(
        self,
        item: dict,
        decision: MemoryRoutingDecision
    ) -> None:
        """
        Store every routing decision in a JSON file so it can
        be inspected without reading application logs.
        """

        self.LOG_DIR.mkdir(exist_ok=True)

        try:
            with open(self.LOG_FILE, "r", encoding="utf-8") as file:
                logs = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append({
            "timestamp": datetime.now().isoformat(),
            "item": item,
            "decision": decision.destination,
            "reasoning": decision.reasoning
        })

        with open(self.LOG_FILE, "w", encoding="utf-8") as file:
            json.dump(logs, file, indent=4, ensure_ascii=False)