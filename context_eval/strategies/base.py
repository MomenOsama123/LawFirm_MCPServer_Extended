from abc import ABC, abstractmethod

class ContextStrategy(ABC):

    @abstractmethod
    def prepare_messages(self, messages, llm_call=None):
        pass