from context_eval.strategies.base import ContextStrategy

class FullContext(ContextStrategy):

    def prepare_messages(
        self,
        messages,
        llm_call=None,
    ):
        return messages