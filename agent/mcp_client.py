from typing import Any
import mcp.types
from fastmcp import Client
from fastmcp.client.messages import MessageHandler
from .transports.base import BaseTransport


# ==================================================
# MCP NOTIFICATION HANDLER
# ==================================================
class ToolListChangedHandler(MessageHandler):
    """
    Receives MCP notifications when the server's
    available tool list changes.
    """

    def __init__(
        self,
        mcp_client: "LawFirmMCPClient",
    ) -> None:

        self.mcp_client = mcp_client

    async def on_tool_list_changed(
        self,
        notification: mcp.types.ToolListChangedNotification,
    ) -> None:

        await self.mcp_client.handle_tools_list_changed()


# ==================================================
# MCP CLIENT
# ==================================================
class LawFirmMCPClient:
    """
    MCP client used by the legal case agent.
    The client is independent of the transport type.
    It can work with STDIO during development and
    Streamable HTTP after deployment.
    """

    def __init__(
        self,
        transport: BaseTransport,
    ) -> None:

        # Create the selected MCP transport.
        self.transport = transport.create()

        # Create the notification handler.
        # It receives tools/list_changed notifications
        # from the MCP server.
        self.message_handler = ToolListChangedHandler(
            self
        )

        # Create the FastMCP client and register
        # the notification handler.
        self.client = Client(
            self.transport,
            message_handler=self.message_handler,
        )

        self.connected = False

        # Stores the capabilities declared by the MCP
        # server during the initialization handshake.
        self.capabilities: dict[str, bool] = {
            "tools": False,
            "resources": False,
            "prompts": False,
        }

        # Stores the tools currently available
        # during this MCP connection.
        self.available_tools: list[str] = []

    # ==================================================
    # INITIALIZATION
    # ==================================================

    async def initialize(self) -> None:
        """
        Opens the MCP connection.

        MCP initialization is performed automatically
        when the FastMCP client enters its context.
        """

        if self.connected:
            return

        await self.client.__aenter__()

        self.connected = True

        # Read the capabilities declared by the MCP
        # server during the initialization handshake.
        server_capabilities = (
            self.client.session.get_server_capabilities()
        )

        self.capabilities = {
            "tools": (
                server_capabilities.tools is not None
            ),
            "resources": (
                server_capabilities.resources is not None
            ),
            "prompts": (
                server_capabilities.prompts is not None
            ),
        }

        # Load and cache the initial tool list.
        if self.supports("tools"):
            await self.list_tools()

    # ==================================================
    # CAPABILITY CHECK
    # ==================================================

    def supports(
        self,
        capability: str,
    ) -> bool:
        """
        Checks whether the connected MCP server supports
        a requested capability.
        """

        if not self.connected:
            raise RuntimeError(
                "MCP client is not connected."
            )

        if capability not in self.capabilities:
            raise ValueError(
                f"Unknown capability: {capability}"
            )

        return self.capabilities[capability]

    # ==================================================
    # TOOLS
    # ==================================================

    async def list_tools(self) -> list[str]:
        """
        Returns and stores the tools currently
        available on the MCP server.
        """

        if not self.connected:
            raise RuntimeError(
                "MCP client is not connected."
            )

        if not self.supports("tools"):
            raise RuntimeError(
                "The MCP server does not support tools."
            )

        tools = await self.client.list_tools()

        self.available_tools = [
            tool.name
            for tool in tools
        ]

        return self.available_tools

    async def refresh_tools(self) -> list[str]:
        """
        Refreshes the local tool list after the MCP
        server reports that its tools have changed.
        """

        updated_tools = await self.list_tools()

        print(
            "\nMCP tools changed. "
            "Local tool list was updated."
        )

        print(
            "Current MCP tools:"
        )

        for tool_name in updated_tools:
            print(
                f"- {tool_name}"
            )

        return updated_tools

    async def handle_tools_list_changed(
        self,
    ) -> list[str]:
        """
        Handles the MCP tools/list_changed notification.

        The server notifies the client that the
        available tool set changed. The client then
        refreshes its local tool list.
        """

        print(
            "\nReceived MCP notification: "
            "tools/list_changed"
        )

        return await self.refresh_tools()

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> Any:
        """
        Calls a tool on the connected MCP server.
        """

        if not self.connected:
            raise RuntimeError(
                "MCP client is not connected."
            )

        if not self.supports("tools"):
            raise RuntimeError(
                "The MCP server does not support tools."
            )

        return await self.client.call_tool(
            tool_name,
            arguments or {},
        )

    # ==================================================
    # RESOURCES
    # ==================================================

    async def read_resource(
        self,
        uri: str,
    ) -> Any:
        """
        Reads a resource from the connected MCP server.
        """

        if not self.connected:
            raise RuntimeError(
                "MCP client is not connected."
            )

        if not self.supports("resources"):
            raise RuntimeError(
                "The MCP server does not support resources."
            )

        return await self.client.read_resource(
            uri
        )

    # ==================================================
    # PROMPTS
    # ==================================================

    async def get_prompt(
        self,
        prompt_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> Any:
        """
        Retrieves a prompt from the connected MCP server.
        """

        if not self.connected:
            raise RuntimeError(
                "MCP client is not connected."
            )

        if not self.supports("prompts"):
            raise RuntimeError(
                "The MCP server does not support prompts."
            )

        return await self.client.get_prompt(
            prompt_name,
            arguments or {},
        )

    # ==================================================
    # CLOSE CONNECTION
    # ==================================================

    async def close(self) -> None:
        """
        Closes the MCP connection.
        """

        if self.connected:

            await self.client.__aexit__(
                None,
                None,
                None,
            )

            self.connected = False

            # Reset the cached tool list.
            self.available_tools = []

            # Reset capabilities after closing
            # the connection.
            self.capabilities = {
                "tools": False,
                "resources": False,
                "prompts": False,
            }