# python -m planning.integration.experiment_test

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

from planning.decomposition.dynamic_decomposition import dynamic_decomposition

from planning.decomposition.dag import validate_and_sort

from ..llm import llm


# Ensure artifacts directory exists
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


async def run_experiment():

    print("=" * 60)
    print("LAW FIRM DECOMPOSITION EXPERIMENT")
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
    # RUN 1: Static Decomposition
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("RUNNING STATIC DECOMPOSITION")
    print("=" * 60)

    plan = decompose_goal(
        GOAL,
        llm,
    )

    print("\nGenerated static plan:")

    for task in plan.tasks:
        print(f"\n{task.id}")
        print(f"  Instruction : {task.instruction}")
        print(f"  Tool        : {task.tool_name}")
        print(f"  Arguments   : {task.arguments}")
        print(f"  Depends on  : {task.depends_on}")

    # --------------------------------------------------
    # Validate DAG BEFORE execution
    # --------------------------------------------------

    order = validate_and_sort(
        [task.model_dump() for task in plan.tasks]
    )

    print(f"\nValid DAG: {order}")

    static_outputs = await execute_plan(
        plan,
        llm,
        mcp_client,
    )

    static_final = final_output(
        plan,
        static_outputs,
    )

    static_trace = {
        "approach": "static_decomposition",
        "goal": GOAL.strip(),
        "case_id": CASE_ID,
        "client_id": CLIENT_ID,
        "decided_by": DECIDED_BY,
        "plan_dag": plan.model_dump(),
        "outputs": static_outputs,
        "final_output": static_final,
    }

    static_trace_path = ARTIFACTS_DIR / "static_trace.json"

    with static_trace_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            static_trace,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nStatic final result:")
    print(static_final)

    # --------------------------------------------------
    # RUN 2: Dynamic Decomposition
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("RUNNING DYNAMIC DECOMPOSITION")
    print("=" * 60)

    dynamic_history = await dynamic_decomposition(
        GOAL,
        llm,
        mcp_client,
        max_steps=6,
    )
    print("\nDynamic execution:")

    print("\nDynamic execution:")

    for entry in dynamic_history:
        print(f"\n--- STEP {entry['step']} ---")
        print(f"Task      : {entry['task']}")
        print(f"Tool      : {entry['tool_name']}")
        print(f"Arguments : {entry['arguments']}")
        print(f"Source    : {entry['source']}")
        print(f"Result    : {entry['result']}")

    dynamic_trace = {
        "approach": "dynamic_decomposition",
        "goal": GOAL.strip(),
        "case_id": CASE_ID,
        "client_id": CLIENT_ID,
        "decided_by": DECIDED_BY,
        "steps": dynamic_history,
    }

    dynamic_trace_path = ARTIFACTS_DIR / "dynamic_trace.json"

    with dynamic_trace_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            dynamic_trace,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------
    # Print Results
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)

    print(f"\nStatic trace saved to: {static_trace_path}")
    print(f"Dynamic trace saved to: {dynamic_trace_path}")

    # --------------------------------------------------
    # Close MCP connection
    # --------------------------------------------------

    await mcp_client.client.__aexit__(
        None,
        None,
        None,
    )

    print("\nMCP connection closed.")


if __name__ == "__main__":
    asyncio.run(run_experiment())