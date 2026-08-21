# python -m planning.integration.case_review_test

import asyncio
import json
from pathlib import Path

from agent.mcp_client import LawFirmMCPClient
from agent.transports.streamable import HTTPMCPTransport

from planning.decomposition.static_decomposition import (
    decompose_goal,
    execute_plan,
    final_output,
)

from ..llm import llm


ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)


CASE_ID = "case-003"
CLIENT_ID = "party-004"
DECIDED_BY = "staff-003"


GOAL = f"""
Review case {CASE_ID} for client {CLIENT_ID}.

Retrieve the client's information and all conflict checks for the case.
Determine whether the case should be rejected based on the available
information. If the rejection conditions are satisfied, reject the case
using staff member {DECIDED_BY} and provide an appropriate decision reason.
"""


async def main():
    print("=" * 60)
    print("LAW FIRM CASE REVIEW - STATIC DECOMPOSITION TEST")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Connect to the real MCP server
    # --------------------------------------------------

    transport = HTTPMCPTransport(
        url="http://127.0.0.1:8000/mcp"
    )

    mcp_client = LawFirmMCPClient(
        transport=transport
    )

    await mcp_client.initialize()

    print("\nConnected to MCP server.")

    print("\nAvailable MCP tools:")
    for tool in mcp_client.available_tools:
        print(f"  - {tool}")

    # --------------------------------------------------
    # 2. Generate the COMPLETE plan
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("GENERATING COMPLETE PLAN")
    print("=" * 60)

    plan = decompose_goal(
        GOAL,
        llm,
    )

    print("\nGenerated plan:")

    for task in plan.tasks:
        print(f"\n{task.id}")
        print(f"  Instruction : {task.instruction}")
        print(f"  Tool        : {task.tool_name}")
        print(f"  Arguments   : {task.arguments}")
        print(f"  Depends on  : {task.depends_on}")

    # --------------------------------------------------
    # 3. Execute the validated DAG using real MCP tools
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("EXECUTING PLAN")
    print("=" * 60)

    outputs = await execute_plan(
        plan,
        llm,
        mcp_client,
    )

    for task_id, output in outputs.items():
        print(f"\n--- {task_id} ---")
        print(output)

    # --------------------------------------------------
    # 4. Produce final output
    # --------------------------------------------------

    result = final_output(
        plan,
        outputs,
    )

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(result)

    # --------------------------------------------------
    # 5. Save trace
    # --------------------------------------------------

    trace = {
        "goal": GOAL.strip(),
        "case_id": CASE_ID,
        "client_id": CLIENT_ID,
        "decided_by": DECIDED_BY,
        "plan": plan.model_dump(),
        "node_outputs": outputs,
        "final_output": result,
    }

    trace_path = ARTIFACTS_DIR / "case_review_trace.json"

    with trace_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            trace,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 60)
    print(f"TRACE SAVED: {trace_path}")
    print("=" * 60)

    # --------------------------------------------------
    # 6. Close MCP connection
    # --------------------------------------------------

    await mcp_client.client.__aexit__(
        None,
        None,
        None,
    )

    print("\nMCP connection closed.")


if __name__ == "__main__":
    asyncio.run(main())