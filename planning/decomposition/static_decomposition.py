from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ConfigDict

from ..model import Plan

from agent.mcp_client import LawFirmMCPClient


PLANNER_SYSTEM = """You are a careful task-decomposition planner.
Produce a small executable DAG, not a prose checklist. Every task must make a concrete
contribution to the goal. Independent research or analysis tasks should be parallel.
The plan must end with exactly one synthesis task depending on every necessary branch.

CRITICAL: When choosing a 'tool_name', you MUST strictly pick from this list of available tools:
- database_health
- get_client
- get_case
- accept_case
- reject_case
- get_conflict_checks
- get_lawyer

get_client
Arguments:
- client_party_id: string

get_conflict_checks
Arguments:
- case_id: string

get_case
Arguments:
- case_id: string

reject_case
Arguments:
- case_id: string
- decided_by: string
- decision_reason: string

Use the argument names exactly as specified. Do not rename them.

If a step is an internal synthesis or reasoning task (no MCP tool required), set tool_name to "none" or "".
DO NOT invent tool names like 'get_client_info' or 'evaluate_rejection_criteria'.
"""


class PlannedTask(BaseModel):
    """A planned task that can be executed through an MCP tool."""

    model_config = ConfigDict(extra="forbid")

    id: str
    instruction: str
    tool_name: str
    arguments: dict[str, object] = {}
    depends_on: list[str] = []


class GeneratedPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str
    tasks: list[PlannedTask]


def decompose_goal(goal: str, llm: BaseChatModel) -> Plan:
    generated = llm.with_structured_output(
        GeneratedPlan,
        method="json_schema",
    ).invoke([
        ("system", PLANNER_SYSTEM),
        ("human", f"""Decompose this goal into 3-6 tasks: {goal!r}
Use short task ids such as t1. Dependencies may refer only to tasks in the plan.
Preserve the supplied goal exactly in the plan's goal field."""),
    ])
    # The caller's goal remains authoritative even if the model paraphrases it.
    payload = generated.model_dump()
    payload["goal"] = goal
    return Plan.model_validate(payload)


async def execute_plan(
    plan: Plan,
    llm: BaseChatModel,
    mcp_client: LawFirmMCPClient,
) -> dict[str, str]:

    outputs: dict[str, str] = {}

    for batch in plan.execution_batches():
        print(f"\nExecuting batch: {batch}")

        for task_id in batch:
            task = plan.task(task_id)

            # ==================================================
            # MCP TOOL TASK
            # ==================================================
            if task.tool_name != "none":
                try:
                    result = await mcp_client.call_tool(
                        task.tool_name,
                        task.arguments,
                    )

                    outputs[task_id] = str(result)

                    print(
                        f"✓ {task_id} "
                        f"({task.tool_name}) executed successfully"
                    )

                except Exception as exc:
                    raise RuntimeError(
                        f"Tool execution failed for "
                        f"{task_id} ({task.tool_name}): {exc}"
                    ) from exc

                continue

            # ==================================================
            # LLM SYNTHESIS TASK
            # ==================================================

            context = "\n\n".join(
                f"OUTPUT FROM {dependency}:\n"
                f"{outputs[dependency]}"
                for dependency in task.depends_on
            )

            try:
                response = llm.invoke(
                    [
                        (
                            "system",
                            "You are the final synthesis step of a "
                            "validated task DAG. Use only the outputs "
                            "provided by prerequisite tasks. Do not "
                            "invent facts or tool results.",
                        ),
                        (
                            "human",
                            f"""
Overall goal:
{plan.goal}

Current task:
{task.instruction}

Prerequisite outputs:
{context}

Provide a concise final result.
""",
                        ),
                    ],
                    temperature=0.2,
                )

                content = response.content

                # Gemini may return either a string or structured content.
                if isinstance(content, str):
                    text = content.strip()

                elif isinstance(content, list):
                    parts = []

                    for item in content:
                        if isinstance(item, dict):
                            value = item.get("text")
                            if value:
                                parts.append(str(value))

                    text = "\n".join(parts).strip()

                else:
                    text = str(content).strip()

                if not text:
                    raise RuntimeError(
                        "The chat model returned an empty response"
                    )

                outputs[task_id] = text

                print(
                    f"✓ {task_id} "
                    f"(LLM synthesis) completed successfully"
                )

            except Exception as exc:
                raise RuntimeError(
                    f"Synthesis failed for task {task_id}: {exc}"
                ) from exc

    return outputs


def final_output(plan: Plan, outputs: dict[str, str]) -> str:
    terminals = plan.terminal_tasks()
    if len(terminals) != 1:
        raise ValueError(f"Expected exactly one terminal synthesis task, found {terminals}")
    return outputs[terminals[0]]