import asyncio
from .mcp_client import LawFirmMCPClient
from .transports.stdio import StdioMCPTransport


async def main():

    # 1. Create the local STDIO transport
    transport = StdioMCPTransport()

    # 2. Give the transport to the MCP client
    mcp_client = LawFirmMCPClient(
        transport=transport
    )

    try:
        # 3. Start the MCP connection
        await mcp_client.initialize()

        print("MCP client connected successfully.")

        # 4. Get all tools exposed by the server
        tools = await mcp_client.list_tools()

        print("\nAvailable MCP tools:")

        for tool in tools:
            print(f"- {tool}")

        # 5. Test one MCP tool
        result = await mcp_client.call_tool(
            tool_name="database_health",
            arguments={},
        )

        print("\nDatabase health result:")
        print(result)

    finally:
        # 6. Always close the connection
        await mcp_client.close()

        print("\nMCP connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
print("FILE LOADED")

# ___________________________________________________________________________-
# import asyncio

# from .mcp_client import LawFirmMCPClient
# from .transports.stdio import StdioMCPTransport


# async def main():

#     print("MAIN STARTED")

#     transport = StdioMCPTransport()

#     print("TRANSPORT CREATED")

#     mcp_client = LawFirmMCPClient(
#         transport=transport
#     )

#     print("MCP CLIENT CREATED")

#     try:
#         print("CONNECTING...")

#         await mcp_client.initialize()

#         print("CONNECTED")

#         tools = await mcp_client.list_tools()

#         print("TOOLS:")
#         print(tools)

#         result = await mcp_client.call_tool(
#             tool_name="database_health",
#             arguments={},
#         )

#         print("RESULT:")
#         print(result)

#     except Exception as error:
#         print("ERROR:")
#         print(repr(error))
#         raise

#     finally:
#         await mcp_client.close()
#         print("CONNECTION CLOSED")


# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except Exception:
#         import traceback
#         traceback.print_exc()