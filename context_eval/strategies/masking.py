from context_eval.strategies.base import ContextStrategy

class Masking(ContextStrategy):

    def __init__(self, keep_recent=3):
        self.keep_recent = keep_recent

    def prepare_messages(
        self,
        messages,
        llm_call=None,
    ):
        messages = [m.copy() for m in messages]

        tool_indexes = [
            i
            for i, m in enumerate(messages)
            if m["role"] == "tool"
        ]

        to_mask = tool_indexes[:-self.keep_recent]

        for i in to_mask:
            messages[i]["content"] = (
                "[tool output omitted]"
            )

        return messages
