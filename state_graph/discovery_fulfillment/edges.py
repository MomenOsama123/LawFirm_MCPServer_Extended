from typing import Literal
from state_graph.discovery_fulfillment.state import DiscoveryState

def route_next_step(state: DiscoveryState) -> Literal["trigger_ticket", "pause_hitl", "released", "withheld"]:
    """Determines transition path based on court deadlines, HITL triggers, and attorney feedback."""
    
    if state.get("court_deadline_passed", False):
        return "trigger_ticket"
    
    flagged = state.get("flagged_docs", [])
    approval = state.get("attorney_approval")
    
    if len(flagged) > 0 and approval is None:
        return "pause_hitl"
    
    if approval is False:
        return "withheld"
        
    return "released"