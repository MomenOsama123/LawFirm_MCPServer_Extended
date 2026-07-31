# Test connection between MCP client and server using the local STDIO transport.

import asyncio
from .mcp_client import LawFirmMCPClient
from .transports.streamable import (
    HTTPMCPTransport
)

# To run: python -m agent.test_mcp_client
# Test done

async def main():

    # 1. Create the local STDIO transport
    transport = HTTPMCPTransport(
        url="http://127.0.0.1:8000/mcp"
    )

    # ==================================
    # 2. CREATE THE MCP CLIENT
    # ==================================

    mcp_client = LawFirmMCPClient(
        transport=transport
    )

    # 2. Give the transport to the MCP client
    mcp_client = LawFirmMCPClient(transport=transport)

    try:

        # 3. Start the MCP connection
        await mcp_client.initialize()

        print("MCP client connected successfully.")

        # ==================================
        # 4. TEST SERVER CAPABILITIES
        # ==================================

        print("\nServer capabilities:")

        print(
            "Tools:",
            mcp_client.supports("tools")
        )

        print(
            "Resources:",
            mcp_client.supports("resources")
        )

        print(
            "Prompts:",
            mcp_client.supports("prompts")
        )

        # ==================================
        # 4. TEST MCP TOOLS
        # ==================================

        tools = await mcp_client.list_tools()

        print("\nAvailable MCP tools:")

        for tool in tools:
            print(f"- {tool}")

        # Test one MCP tool
        result = await mcp_client.call_tool(
            tool_name="database_health",
            arguments={},
        )

        print("\nDatabase health result:")

        print(result)

        # ==================================
        # 5. TEST MCP RESOURCE
        # ==================================

        intake_policy = await mcp_client.read_resource("company://intake-policy")

        print("\nIntake policy resource:")

        print(intake_policy[0].text)

        # ==================================
        # 6. TEST MCP PROMPT
        # ==================================

        case_prompt = await mcp_client.get_prompt(
            prompt_name="summarize_case",
            arguments={"case_details": ("A client has a " "residential lease dispute.")},
        )

        print("\nCase summary prompt:")

        print( case_prompt.messages[0].content.text)

    finally:

        # ==================================
        # 7. CLOSE MCP CONNECTION
        # ==================================

        await mcp_client.close()

        print("\nMCP connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
    print("FILE LOADED")