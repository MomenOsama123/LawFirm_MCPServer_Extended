from typing import List, Dict, Any, Callable, Optional
from context_eval.strategies.base import ContextStrategy


class ZonePruning(ContextStrategy):
    """
    Zone-Based Context Pruning Strategy.
    
    Segments conversation into 4 functional zones:
      - Zone 1 (System): System instructions & core agent constraints (Never pruned)
      - Zone 2 (Intent): Initial user request & explicit goals (Protected)
      - Zone 3 (Scratchpad): Middle turn history & tool outputs (Aggressively pruned)
      - Zone 4 (Active Memory): Most recent k turns (Preserved for local context)
    """

    def __init__(
        self,
        keep_recent: int = 6,
        max_tool_output_len: int = 200,
        keep_first_user_msg: bool = True,
        summarize_pruned_zone: bool = False,
    ):
        """
        Args:
            keep_recent: Number of most recent messages (Zone 4) to keep untouched.
            max_tool_output_len: Character cap for tool/observation payloads in Zone 3.
            keep_first_user_msg: Preserve the very first user message as Zone 2 intent.
            summarize_pruned_zone: Optional LLM-assisted mini-summary for removed Zone 3 items.
        """
        self.keep_recent = keep_recent
        self.max_tool_output_len = max_tool_output_len
        self.keep_first_user_msg = keep_first_user_msg
        self.summarize_pruned_zone = summarize_pruned_zone

    def prepare_messages(
        self,
        messages: List[Dict[str, Any]],
        llm_call: Optional[Callable[[List[Dict[str, Any]]], str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Prunes context by locking down structural bounds (System + Initial Intent + Recent Turns)
        and truncating/removing verbose tool calls inside the middle execution zone.
        """
        if len(messages) <= (self.keep_recent + 2):
            return messages

        # -------------------------------------------------------------
        # 1. Classify Zones
        # -------------------------------------------------------------
        zone_1_system: List[Dict[str, Any]] = []
        zone_2_intent: List[Dict[str, Any]] = []
        zone_3_scratchpad: List[Dict[str, Any]] = []
        zone_4_recent: List[Dict[str, Any]] = []

        idx = 0
        total_msgs = len(messages)

        # Extract Zone 1: Leading System Messages
        while idx < total_msgs and messages[idx].get("role") == "system":
            zone_1_system.append(messages[idx])
            idx += 1

        # Extract Zone 2: Initial User Intent (First user message after system)
        if self.keep_first_user_msg and idx < total_msgs:
            if messages[idx].get("role") == "user":
                zone_2_intent.append(messages[idx])
                idx += 1

        # Calculate splits for Zone 3 vs Zone 4
        recent_start_idx = max(idx, total_msgs - self.keep_recent)
        
        zone_3_scratchpad = messages[idx:recent_start_idx]
        zone_4_recent = messages[recent_start_idx:]

        # -------------------------------------------------------------
        # 2. Prune Zone 3 (Scratchpad / Tool Trajectory)
        # -------------------------------------------------------------
        pruned_zone_3: List[Dict[str, Any]] = []

        for msg in zone_3_scratchpad:
            role = msg.get("role")
            content = msg.get("content", "")

            # Mask tool/observation outputs inside Zone 3
            if role in ("tool", "observation") or "tool_calls" in msg:
                if isinstance(content, str) and len(content) > self.max_tool_output_len:
                    pruned_msg = msg.copy()
                    pruned_msg["content"] = (
                        f"{content[:self.max_tool_output_len]}... "
                        f"[ZonePruned: {len(content) - self.max_tool_output_len} chars omitted]"
                    )
                    pruned_zone_3.append(pruned_msg)
                else:
                    pruned_zone_3.append(msg)
            else:
                # Keep human/assistant dialogue turns in Zone 3
                pruned_zone_3.append(msg)

        # Optional LLM distillation of middle zone if llm_call provided
        if self.summarize_pruned_zone and llm_call and pruned_zone_3:
            summary_prompt = [
                {
                    "role": "system",
                    "content": "Briefly list key conclusions from intermediate tool calls in 2-3 sentences.",
                }
            ] + pruned_zone_3
            
            middle_summary = llm_call(summary_prompt)
            pruned_zone_3 = [
                {
                    "role": "system",
                    "content": f"[Pruned Scratchpad Summary]: {middle_summary}",
                }
            ]

        # -------------------------------------------------------------
        # 3. Assemble Output Context
        # -------------------------------------------------------------
        return zone_1_system + zone_2_intent + pruned_zone_3 + zone_4_recent