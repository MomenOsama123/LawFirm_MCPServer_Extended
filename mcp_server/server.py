from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import tools
from .mcp_instance import mcp
from .memory.runtime.registry import RuntimeToolRegistry

class LawFirmMCPServer:
    def __init__(self):
        self.registry = RuntimeToolRegistry(mcp)
        self._agent_tools: dict[str, set[str]] = {}

    def register_dynamic_tool(
        self,
        agent_id: str,
        tool: str | Callable[..., Any],
    ) -> bool:
        """Registers a new tool in the live MCP runtime."""
        tool_name = tool if isinstance(tool, str) else getattr(tool, "__name__", "")
        tool_function = getattr(tools, tool_name, tool) if isinstance(tool, str) else tool

        if not callable(tool_function):
            return False

        if not self.registry.is_registered(tool_name):
            self.registry.register_tool(tool_function, name=tool_name)

        self._agent_tools.setdefault(agent_id, set()).add(tool_name)
        return True

    def unregister_dynamic_tool(self, agent_id: str, tool_name: str) -> bool:
        """Unregisters a tool from the live MCP runtime."""
        agent_tools = self._agent_tools.get(agent_id)
        if not agent_tools or tool_name not in agent_tools:
            return False

        agent_tools.remove(tool_name)
        if not any(tool_name in names for names in self._agent_tools.values()):
            self.registry.unregister_tool(tool_name)
        return True

    def get_agent_tools(self, agent_id: str) -> list[str]:
        """Returns active tools registered for the given agent."""
        return sorted(self._agent_tools.get(agent_id, set()))

# Singleton Instance
mcp_server_instance = LawFirmMCPServer()

# Compatibility exports used by clients and tests.
accept_case = tools.accept_case
reject_case = tools.reject_case
get_conflict_checks = tools.get_conflict_checks