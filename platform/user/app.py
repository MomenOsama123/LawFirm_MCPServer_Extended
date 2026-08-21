from typing import Dict, Any, List

class UserPlatformService:
    def __init__(self):
        self.available_agents = [
            "memory_rag_agent",
            "planning_decomposition_agent",
            "case_assignment_agent",
            "conflict_clearance_agent",
            "discovery_fulfillment_agent"
        ]

    def switch_agent(self, selected_agent: str) -> Dict[str, Any]:
        """Handles agent switching across the unified chat surface."""
        if selected_agent not in self.available_agents:
            raise ValueError(f"Agent '{selected_agent}' is not available.")
        
        return {
            "status": "success",
            "active_agent": selected_agent,
            "message": f"Successfully switched context to {selected_agent}"
        }

    def dispatch_chat_message(self, agent_id: str, message: str, thread_id: str) -> Dict[str, Any]:
        """Routes chat prompts to the targeted agent instance."""
        if agent_id == "discovery_fulfillment_agent":
            config = {"configurable": {"thread_id": thread_id}}
            initial_input = {"instruction": message, "court_deadline_passed": False}
            
            from state_graph.discovery_fulfillment.graph import discovery_graph
            result = discovery_graph.invoke(initial_input, config=config)
            return {"agent": agent_id, "output": result}
        
        return {"agent": agent_id, "output": "Message routed to standard agent endpoint."}