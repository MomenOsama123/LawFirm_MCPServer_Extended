from .states import CaseAssignmentState
from .models import CaseAssignmentStateData

class CaseAssignmentGraph:
    def __init__(self, persistence_layer):
        self.persistence = persistence_layer

    def check_hitl_escalation(self, state_data: CaseAssignmentStateData) -> bool:
        """
        HITL Trigger Condition:
        1. Case is VIP or High-Value (e.g., value > $100,000)
        2. Repeated declines (decline_count >= 2)
        """
        if state_data.is_vip or state_data.case_value >= 100000.0:
            state_data.hitl_reason = "Escalated to Managing Partner: VIP / High-Value Case Reassignment"
            return True
        
        if state_data.decline_count >= 2:
            state_data.hitl_reason = f"Escalated to Managing Partner: Repeated attorney declines ({state_data.decline_count} declines)"
            return True

        return False

    def handle_attorney_decline(self, state_data: CaseAssignmentStateData, candidate_attorneys_available: list):
        """
        Handles transition on attorney decline:
        - Checks for capacity (Ticket System trigger if empty)
        - Checks for HITL conditions before reassigning via Tree of Thoughts
        """
        state_data.decline_count += 1
        
        # 1. Failure Path: No available capacity across all attorneys -> Create Ticket
        if not candidate_attorneys_available:
            state_data.current_state = CaseAssignmentState.TICKETED
            state_data.ticket_status = "open"
            state_data.ticket_id = f"TICKET-{state_data.case_id}"
            
            # Persist checkpoint at moment of failure
            self.persistence.save_checkpoint(state_data.case_id, state_data.model_dump())
            return state_data

        # 2. HITL Escalation Path: Pause graph for Managing Partner approval
        if self.check_hitl_escalation(state_data):
            state_data.current_state = CaseAssignmentState.ESCALATED
            
            # Persist paused state for Admin UI pickup
            self.persistence.save_checkpoint(state_data.case_id, state_data.model_dump())
            return state_data

        # 3. Normal Reassignment Loop -> Return to PROPOSED / Tree of Thoughts
        state_data.current_state = CaseAssignmentState.REASSIGNING
        self.persistence.save_checkpoint(state_data.case_id, state_data.model_dump())
        return state_data

    def resume_from_hitl_or_ticket(self, case_id: str, admin_decision: dict) -> CaseAssignmentStateData:
        """
        Resumes process from durable checkpoint after Admin resolves HITL task or Ticket
        """
        raw_state = self.persistence.get_checkpoint(case_id)
        state_data = CaseAssignmentStateData(**raw_state)

        if admin_decision.get("approved_attorney_id"):
            state_data.assigned_attorney_id = admin_decision["approved_attorney_id"]
            state_data.current_state = CaseAssignmentState.ACCEPTED
        elif admin_decision.get("action") == "resolve_ticket":
            state_data.ticket_status = "resolved"
            state_data.current_state = CaseAssignmentState.PROPOSED

        self.persistence.save_checkpoint(case_id, state_data.model_dump())
        return state_data