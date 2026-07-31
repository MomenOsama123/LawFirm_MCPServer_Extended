# test initial version of the agent with the MCP client
# to run: python -m agent.test_itinalize
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

        # ==================================
        # 4. DISPLAY FINAL RESULT
        # ==================================

        print(
            "\n"
            + "=" * 50
        )

        print(
            "FINAL AGENT RESULT"
        )

        print(
            "=" * 50
        )

        print(
            "\nDecision:"
        )

        print(
            result.get(
                "decision",
                "Not available",
            )
        )

        print(
            "\nReasoning:"
        )

        print(
            result.get(
                "thought",
                "Not available",
            )
        )

        print(
            "\nFinal Action:"
        )

        print(
            result.get(
                "action",
                "Not available",
            )
        )

        print(
            "\nSteps Taken:"
        )

        print(
            result.get(
                "steps_taken",
                0,
            )
        )

        # ----------------------------------
        # DISPLAY LOADED RESOURCES
        # ----------------------------------

        loaded_resources = (
            result.get(
                "loaded_resources",
                [],
            )
        )

        print(
            "\nLoaded Resources:"
        )

        if loaded_resources:

            for resource in (
                loaded_resources
            ):

                print(
                    f"- {resource}"
                )

        else:

            print(
                "No resources loaded."
            )

        # ----------------------------------
        # DISPLAY LOADED PROMPT
        # ----------------------------------

        print(
            "\nLoaded Prompt:"
        )

        print(
            result.get(
                "loaded_prompt",
                "Not available",
            )
        )

        # ----------------------------------
        # DISPLAY ERROR IF IT EXISTS
        # ----------------------------------

        if result.get(
            "reason"
        ):

            print(
                "\nError:"
            )

            print(
                result.get(
                    "reason"
                )
            )

        print(
            "\n"
            + "=" * 50
        )

    finally:

        # 5. Close the MCP connection
        await mcp_client.close()

        print(
            "\nMCP connection closed."
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )