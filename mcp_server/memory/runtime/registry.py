from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Any

from fastmcp import FastMCP


class RuntimeToolRegistry:
    """Manage MCP tools that can be added or removed at runtime."""

    def __init__(self, mcp: FastMCP) -> None:
        self._mcp = mcp
        self._registered_tools: dict[str, Any] = {}
        self._lock = RLock()

    def register_tool(
        self,
        tool: Callable[..., Any],
        *,
        name: str | None = None,
    ) -> Any:
        """Register a tool with the live MCP server.

        Returns the FastMCP tool object registered on the server.
        """
        tool_name = name or getattr(tool, "__name__", None)

        if not tool_name:
            raise ValueError("Tool must have a name")

        with self._lock:
            if tool_name in self._registered_tools:
                return self._registered_tools[tool_name]

            registered_tool = self._mcp.add_tool(tool)

            self._registered_tools[tool_name] = registered_tool

            return registered_tool

    def unregister_tool(self, name: str) -> bool:
        """Remove a tool from the live MCP server.

        Returns True if the tool was removed, False if it was not registered
        through this registry.
        """
        with self._lock:
            if name not in self._registered_tools:
                return False

            self._mcp.local_provider.remove_tool(name)
            del self._registered_tools[name]

            return True

    def is_registered(self, name: str) -> bool:
        """Return whether the registry currently owns the tool."""
        with self._lock:
            return name in self._registered_tools

    def list_registered_tools(self) -> tuple[str, ...]:
        """Return names of tools registered through this registry."""
        with self._lock:
            return tuple(self._registered_tools.keys())