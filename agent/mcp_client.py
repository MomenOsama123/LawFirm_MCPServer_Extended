# from typing import Any
# from fastmcp import Client
# from .transports.base import BaseTransport


# class LawFirmMCPClient:
#     """
#     MCP client used by the legal case agent.

#     The client is independent of the transport type.
#     It can work with STDIO during development and
#     Streamable HTTP after deployment.
#     """

#     def __init__(
#         self,
#         transport: BaseTransport,
#     ) -> None:

#         self.transport = transport.create()

#         self.client = Client(
#             self.transport
#         )

#         self.connected = False

#     async def initialize(self) -> None:
#         """
#         Opens the MCP connection.
#         MCP initialization is performed automatically

#         """

#         if self.connected:
#             return

#         await self.client.__aenter__()

#         self.connected = True

#     async def list_tools(self) -> list[str]:
#         """
#         Returns the tools available on the MCP server.
#         """

#         if not self.connected:
#             raise RuntimeError(
#                 "MCP client is not connected."
#             )

#         tools = await self.client.list_tools()

#         return [
#             tool.name
#             for tool in tools
#         ]

#     async def call_tool(
#         self,
#         tool_name: str,
#         arguments: dict[str, Any] | None = None,
#     ) -> Any:
#         """
#         Calls a tool on the connected MCP server.
#         """

#         if not self.connected:
#             raise RuntimeError(
#                 "MCP client is not connected."
#             )

#         return await self.client.call_tool(
#             tool_name,
#             arguments or {},
#         )
        



    

#     async def close(self) -> None:
#         """
#         Closes the MCP connection.
#         """

#         if self.connected:

#             await self.client.__aexit__(
#                 None,
#                 None,
#                 None,
#             )

#             self.connected = False


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

    async def initialize(self) -> None:
        """
        Opens the MCP connection.
        MCP initialization is performed automatically

        """

        if self.connected:
            return

        await self.client.__aenter__()

        self.connected = True

    async def list_tools(self) -> list[str]:
        """
        Returns the tools available on the MCP server.
        """

        if not self.connected:
            raise RuntimeError(
                "MCP client is not connected."
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