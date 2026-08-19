from abc import ABC, abstractmethod

from .models import CaseAssignmentStateData


class CaseAssignmentPersistence(ABC):

    @abstractmethod
    async def save_checkpoint(
        self,
        state: CaseAssignmentStateData,
    ) -> None:
        pass

    @abstractmethod
    async def load_checkpoint(
        self,
        run_id: str,
    ) -> CaseAssignmentStateData | None:
        pass

    @abstractmethod
    async def update_checkpoint(
        self,
        state: CaseAssignmentStateData,
    ) -> None:
        pass