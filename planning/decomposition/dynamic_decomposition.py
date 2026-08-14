from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ConfigDict, Field

from agent.mcp_client import LawFirmMCPClient


DYNAMIC_TOOLS_DOC = """
Available MCP tools you may call:
- database_health
- get_client (client_party_id)
- get_case (case_id)
- get_conflict_checks (case_id)
- get_lawyer (lawyer_id)
- accept_case (case_id, decided_by, decision_reason)
- reject_case (case_id, decided_by, decision_reason)

Use exact argument names above.

If a step is pure reasoning with no tool call needed,
set tool_name to "none".
"""


class DynamicDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    done: bool
    next_task: str
    tool_name: str
    arguments: dict[str, object] = Field(default_factory=dict)


async def dynamic_decomposition(
    goal: str,
    llm: BaseChatModel,
    mcp_client: LawFirmMCPClient,
    max_steps: int = 6,
) -> list[dict]:

    history: list[dict] = []

    for step in range(max_steps):

        observation = (
            "\n".join(
                f"{h['task']} -> {h['result']}"
                for h in history
            )
            or "None"
        )

        # --------------------------------------------------
        # Ask Gemini to choose the next action
        # --------------------------------------------------

        planner = llm.with_structured_output(
            DynamicDecision,
            method="json_schema",
        )

        decision = planner.invoke([
            (
                "system",
                "You are an adaptive planner for a law firm "
                "intake system. Decide the single best next step "
                "based on prior observations, which may include "
                "real database results that contradict your "
                "assumptions.\n"
                + DYNAMIC_TOOLS_DOC,
            ),
            (
                "human",
                f"""Goal: {goal}

Completed work and observations so far:
{observation}

Decide the single best next step.

Set done to true only when a final accept/reject decision
has actually been recorded via a tool call.

When done is true, use:
- next_task = ""
- tool_name = "none"
""",
            ),
        ])

        # --------------------------------------------------
        # Goal completed
        # --------------------------------------------------

        if decision.done:

            history.append({
                "step": step + 1,
                "task": "done",
                "tool_name": "none",
                "arguments": {},
                "result": "Planner marked goal complete.",
                "source": "planner",
            })

            break

        # --------------------------------------------------
        # Validate planner output
        # --------------------------------------------------

        task = decision.next_task.strip()

        if not task:
            raise ValueError(
                f"Dynamic planner omitted next_task "
                f"at step {step + 1}"
            )

        tool_name = (
            decision.tool_name or "none"
        ).strip()

        # --------------------------------------------------
        # Execute MCP tool
        # --------------------------------------------------

        if tool_name != "none":

            try:
                tool_result = await mcp_client.call_tool(
                    tool_name,
                    decision.arguments,
                )

                result_text = str(tool_result)
                source = "tool"

            except Exception as exc:

                result_text = {
                    "error": f"Tool call failed: {exc}"
                }

                result_text = str(result_text)
                source = "tool_error"

        # --------------------------------------------------
        # Pure reasoning step
        # --------------------------------------------------

        else:

            response = llm.invoke([
                (
                    "system",
                    "Execute the next adaptive sub-task using "
                    "only the observations provided. "
                    "Do not invent tool results.",
                ),
                (
                    "human",
                    f"""Goal: {goal}

Next task:
{task}

Prior observations:
{observation}
""",
                ),
            ])

            result_text = response.content

            if isinstance(result_text, list):

                text_parts = []

                for block in result_text:

                    if isinstance(block, str):
                        text_parts.append(block)

                    elif isinstance(block, dict):
                        text = block.get("text")

                        if isinstance(text, str):
                            text_parts.append(text)

                result_text = "\n".join(text_parts)

            if (
                not isinstance(result_text, str)
                or not result_text.strip()
            ):
                raise RuntimeError(
                    "The chat model returned an empty "
                    "or unsupported response"
                )

            result_text = result_text.strip()
            source = "llm_reasoning"

        # --------------------------------------------------
        # Save observation
        # --------------------------------------------------

        history.append({
            "step": step + 1,
            "task": task,
            "tool_name": tool_name,
            "arguments": decision.arguments,
            "result": result_text,
            "source": source,
        })

    return history