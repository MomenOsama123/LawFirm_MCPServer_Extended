#لسه مستخدمتهوش 
import asyncio
from .agent import run_agent
from .mcp_client import LawFirmMCPClient
from .transports.stdio import StdioMCPTransport


async def main():

    transport = StdioMCPTransport()

    mcp_client = LawFirmMCPClient(
        transport=transport
    )

    try:

        result = await run_agent(
            case_id="case-003",
            mcp_client=mcp_client,
        )

        print("\nFinal result:")

        print(result)

    finally:

        await mcp_client.close()


if __name__ == "__main__":

    asyncio.run(
        main()
    )