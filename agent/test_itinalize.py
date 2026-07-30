# عشان اتسيت  ال Capability negotiation 

import asyncio
from .agent import run_agent
from .mcp_client import LawFirmMCPClient
from .transports.stdio import StdioMCPTransport


async def main():

    # 1. Create the STDIO transport
    transport = StdioMCPTransport()

    # 2. Create the MCP client
    mcp_client = LawFirmMCPClient(
        transport=transport
    )

    try:
        # 3. Run the current Agent implementation
        result = await run_agent(
            case_id="case-003",
            mcp_client=mcp_client,
        )

        # 4. Display the result
        print("\nAgent result:")
        print(result)

    finally:
        # 5. Close the MCP connection
        await mcp_client.close()

        print("\nMCP connection closed.")


if __name__ == "__main__":
    asyncio.run(main())