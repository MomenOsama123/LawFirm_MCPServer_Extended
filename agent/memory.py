#____________________
from dataclasses import dataclass, field

@dataclass
class ConversationMemory:
    """
    Stores the conversation history for one agent session.
    The memory keeps:
    - User requests
    - Agent reasoning steps
    - MCP tool results
    - Final decisions
    """

    messages: list[dict[str, str]] = field(
        default_factory=list
    )

    def add_message(
        self,
        role: str,
        content: str,
    ) -> None:
        """
        Adds one message to the conversation memory.
        """

        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    def get_messages(self) -> list[dict[str, str]]:
        """
        Returns a copy of the stored conversation.
        """

        return self.messages.copy()

    def clear(self) -> None:
        """
        Removes all messages from the current session.
        """

        self.messages.clear()