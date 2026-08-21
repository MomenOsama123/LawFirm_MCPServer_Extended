from typing import Dict, List, Set, Any

from .mcp_instance import mcp
from .tools import accept_case, get_conflict_checks, reject_case

class MCPServer:
    def __init__(self):
        self.agent_tools: Dict[str, Set[str]] = {}

    def register_tool(self, agent_id: str, tool_name: str) -> Dict[str, Any]:
        """Dynamically binds a tool to a specific agent at runtime."""
        if agent_id not in self.agent_tools:
            self.agent_tools[agent_id] = set()
        self.agent_tools[agent_id].add(tool_name)
        return {
            "status": "success",
            "agent_id": agent_id,
            "active_tools": list(self.agent_tools[agent_id])
        }

    def unregister_tool(self, agent_id: str, tool_name: str) -> Dict[str, Any]:
        """Dynamically removes a tool from a specific agent at runtime."""
        if agent_id in self.agent_tools and tool_name in self.agent_tools[agent_id]:
            self.agent_tools[agent_id].remove(tool_name)
        return {
            "status": "success",
            "agent_id": agent_id,
            "active_tools": list(self.agent_tools.get(agent_id, []))
        }

    def get_agent_tools(self, agent_id: str) -> List[str]:
        """Returns active whitelisted tools for an agent."""
        return list(self.agent_tools.get(agent_id, []))

mcp_server_instance = MCPServer()


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)