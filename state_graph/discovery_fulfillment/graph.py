from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state_graph.discovery_fulfillment.state import DiscoveryState
from state_graph.discovery_fulfillment.nodes import task_decomposition_node, privilege_review_node
from state_graph.discovery_fulfillment.edges import route_next_step

memory_checkpointer = MemorySaver()

def build_discovery_fulfillment_graph():
    builder = StateGraph(DiscoveryState)
    
    builder.add_node("task_decomposition", task_decomposition_node)
    builder.add_node("privilege_review", privilege_review_node)
    
    builder.set_entry_point("task_decomposition")
    builder.add_edge("task_decomposition", "privilege_review")
    
    builder.add_conditional_edges(
        "privilege_review",
        route_next_step,
        {
            "trigger_ticket": END,
            "pause_hitl": END,
            "released": END,
            "withheld": END
        }
    )
    
    return builder.compile(checkpointer=memory_checkpointer)

discovery_graph = build_discovery_fulfillment_graph()