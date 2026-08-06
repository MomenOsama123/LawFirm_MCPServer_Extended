from typing import List, Dict, Any, Callable, Optional
from context_eval.strategies.base import ContextStrategy

class RecursiveSummary(ContextStrategy):
    COMPACT_PROMPT = """
    Summarize the conversation below.

    Preserve:
    - decisions made
    - unresolved issues
    - key findings

    Discard:
    - redundant tool output
    - superseded reasoning
    """

    def __init__(self, keep_recent: int = 6):
        self.keep_recent = keep_recent
    
    def prepare_messages(
        self,
        messages,
        llm_call=None,
    ):

        old = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent:]

        summary_messages = [
            {
                "role": "system",
                "content": self.COMPACT_PROMPT,
            }
        ] + old

        summary = llm_call(summary_messages)

        return [
            {
                "role": "system",
                "content": "[Conversation Summary]\n" + summary,
            }
        ] + recent

