from context_eval.strategies.base import ContextStrategy


class SlidingWindow(ContextStrategy):

    def __init__(self, max_messages=20):
        self.max_messages = max_messages

    def prepare_messages(self, conversation):
        return conversation[-self.max_messages:]