from abc import ABC, abstractmethod
from typing import Any


class BaseTransport(ABC):
    """
    Base interface for MCP transports.

    Every transport implementation must provide
    a method that creates the underlying transport.
    """

    @abstractmethod
    def create(self) -> Any:
        """
        Creates and returns an MCP transport.
        """

        raise NotImplementedError