# Run: python -m agent.test_agent

import asyncio
from agent.agent import run_agent
from agent.mcp_client import LawFirmMCPClient
from agent.transports.streamable import HTTPMCPTransport


async def main():
    # 1. Create HTTP Transport pointing to your running MCP server
    transport = HTTPMCPTransport(
        url="http://127.0.0.1:8000/mcp"
    )

    # 2. Instantiate MCP client with HTTP transport
    mcp_client = LawFirmMCPClient(
        transport=transport
    )

    try:
        # 3. Execute agent work
        result = await run_agent(
            case_id="case-003",
            mcp_client=mcp_client,
        )

        print("\nFinal result:")
        print(result)

    finally:
        # 4. Clean up connection
        await mcp_client.close()


if __name__ == "__main__":
    asyncio.run(main())