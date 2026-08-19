from .models import CaseAssignmentStateData


class CaseAssignmentGraph:

    def __init__(self, persistence):
        self.persistence = persistence

    async def run(
        self,
        state: CaseAssignmentStateData,
    ) -> CaseAssignmentStateData:
        return state