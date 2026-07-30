from typing import Any
from fastmcp import Client
from .transports.base import BaseTransport

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

        self.transport = transport.create()

        self.client = Client(
            self.transport
        )

        self.connected = False

        # Stores the capabilities declared by the MCP server
        
        self.capabilities: dict[str, bool] = {
            "tools": False,
            "resources": False,
            "prompts": False,
        }

    async def initialize(self) -> None:
        """
        Opens the MCP connection.
        MCP initialization is performed automatically.
        """

        if self.connected:
            return

        await self.client.__aenter__()

        self.connected = True

        # Read the capabilities declared by the MCP server
        # during the MCP initialization handshake.
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

    async def list_tools(self) -> list[str]:
        """
        Returns the tools available on the MCP server.
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

        return [
            tool.name
            for tool in tools
        ]

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

            # Reset capabilities after closing the connection.
            self.capabilities = {
                "tools": False,
                "resources": False,
                "prompts": False,
            }


