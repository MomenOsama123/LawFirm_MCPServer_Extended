# inital version of the agent.py 
import os
import json
from typing import Any
from dotenv import load_dotenv
from google import genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
)

from .config import (
    REQUIRED_CASE_TOOLS,
    REQUIRED_RESOURCES,
    MODEL_NAME,
    MAX_STEPS,
)

from .memory import ConversationMemory


# ==================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==================================

load_dotenv()


# ==================================
# 2. CREATE GEMINI CLIENT
# ==================================

client = genai.Client(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)


# ==================================
# 3. AGENT SYSTEM PROMPT
# ==================================

SYSTEM_PROMPT = """
You are a constrained legal case intake agent.

Use only the MCP tools, resources, and prompts
provided in the conversation.

Rules:

* Never access the database directly.
* Never invent or rename tools.
* Use exact tool names and argument names.
* Retrieve case details before making a decision.
* Check conflicts before accepting a case.
* Analyze each tool result before choosing the next action.
* Do not exceed MAX_STEPS.
* If information is insufficient or a conflict is unresolved,
  use "escalate".

Tool arguments:

* get_case:
  {"case_id": "..."}
* get_conflict_checks:
  {"case_id": "..."}
* get_client:
  {"client_party_id": "..."}

Return only valid JSON:

{
"thought": "Short reasoning for the next step.",
"action": "MCP tool name, final_answer, or escalate",
"action_input": {},
"final_decision": null
}

When enough information is available:

{
"thought": "Short explanation of the decision.",
"action": "final_answer",
"action_input": {},
"final_decision": "Accept Case, Reject Case, Request More Information, or Escalate for Senior Review"
}
"""

# ==================================
# 4. CALL GEMINI
# ==================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
def call_model(
    messages: list[dict[str, str]],
) -> str:
    """
    Sends the current conversation to Gemini
    and returns the generated JSON response.
    """

    prompt = "\n\n".join(
        [
            f"{message['role'].upper()}:\n"
            f"{message['content']}"
            for message in messages
        ]
    )

    response = (
        client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type":
                    "application/json"
            },
        )
    )

    return response.text


# ==================================
# 5. START THE AGENT
# ==================================

async def run_agent(
    case_id: str,
    mcp_client: Any,
    memory: ConversationMemory | None = None,
) -> dict[str, Any]:
    """
    Runs the constrained legal case intake agent.

    Responsibilities:

    1. Create or reuse session memory.
    2. Connect to the MCP server.
    3. Check server capabilities.
    4. Retrieve available MCP tools.
    5. Verify required tools.
    6. Load required MCP resources.
    7. Load the MCP prompt.
    8. Send memory to Gemini.
    9. Validate Gemini's action.
    10. Execute MCP tools.
    11. Save tool results in memory.
    12. Continue reasoning until a final decision
        or MAX_STEPS is reached.
    """

    # ----------------------------------
    # 5.1 CREATE SESSION MEMORY
    # ----------------------------------

    if memory is None:

        memory = (
            ConversationMemory()
        )

    # ----------------------------------
    # ADD SYSTEM PROMPT
    # ----------------------------------

    memory.add_message(
        role="system",
        content=SYSTEM_PROMPT,
    )

    # ----------------------------------
    # SAVE USER REQUEST
    # ----------------------------------

    memory.add_message(
        role="user",
        content=(
            f"Evaluate legal case: "
            f"{case_id}"
        ),
    )

    # ----------------------------------
    # 5.2 CONNECT TO MCP SERVER
    # ----------------------------------

    await mcp_client.initialize()

    print(
        "MCP connection initialized."
    )

    # ----------------------------------
    # 5.3 CHECK MCP CAPABILITIES
    # ----------------------------------

    server_capabilities = (
        mcp_client.capabilities
    )

    print(
        "\nMCP server capabilities:"
    )

    print(
        server_capabilities
    )

    # ----------------------------------
    # CHECK TOOL SUPPORT
    # ----------------------------------

    if not mcp_client.supports(
        "tools"
    ):

        error_message = (
            "The MCP server does not "
            "support MCP tools."
        )

        memory.add_message(
            role="assistant",
            content=error_message,
        )

        return {

            "decision": (
                "Unable to evaluate "
                "the case"
            ),

            "reason": (
                error_message
            ),

            "steps_taken": 0,

            "memory": (
                memory.get_messages()
            ),

        }

    print(
        "\nMCP server supports tools."
    )

    # ----------------------------------
    # 5.4 GET AVAILABLE MCP TOOLS
    # ----------------------------------

    available_tools = (
        await mcp_client.list_tools()
    )

    print(
        "\nAvailable MCP tools:"
    )

    for tool in available_tools:

        print(
            f"- {tool}"
        )

    # ----------------------------------
    # SAVE AVAILABLE TOOLS IN MEMORY
    # ----------------------------------

    memory.add_message(
        role="system",
        content=(
            "Available MCP tools:\n"
            + "\n".join(
                available_tools
            )
        ),
    )

    # ----------------------------------
    # 5.5 VERIFY REQUIRED TOOLS
    # ----------------------------------

    missing_tools = [

        tool

        for tool

        in REQUIRED_CASE_TOOLS

        if tool

        not in available_tools

    ]

    if missing_tools:

        error_message = (
            "The MCP server is missing "
            "required tools: "
            f"{', '.join(
                missing_tools
            )}"
        )

        memory.add_message(
            role="assistant",
            content=error_message,
        )

        return {

            "decision": (
                "Unable to evaluate "
                "the case"
            ),

            "reason": (
                error_message
            ),

            "steps_taken": 0,

            "memory": (
                memory.get_messages()
            ),

        }

    print(
        "\nAll required MCP tools "
        "are available."
    )

    # ==================================
    # MCP RESOURCE SUPPORT
    # ==================================

    # ----------------------------------
    # 5.6 CHECK RESOURCE SUPPORT
    # ----------------------------------

    if not mcp_client.supports(
        "resources"
    ):

        error_message = (
            "The MCP server does not "
            "support MCP resources."
        )

        memory.add_message(
            role="assistant",
            content=error_message,
        )

        return {

            "decision": (
                "Unable to evaluate "
                "the case"
            ),

            "reason": (
                error_message
            ),

            "steps_taken": 0,

            "memory": (
                memory.get_messages()
            ),

        }

    print(
        "\nMCP server supports "
        "resources."
    )

    # ----------------------------------
    # 5.7 LOAD REQUIRED RESOURCES
    # ----------------------------------

    loaded_resources: dict[
        str,
        str,
    ] = {}

    for resource_uri in (
        REQUIRED_RESOURCES
    ):

        try:

            resource_result = (
                await (
                    mcp_client
                    .read_resource(
                        resource_uri
                    )
                )
            )

            resource_text = (
                "\n".join(
                    item.text

                    for item

                    in resource_result

                    if hasattr(
                        item,
                        "text",
                    )
                )
            )

            loaded_resources[
                resource_uri
            ] = resource_text

            print(
                "Loaded resource: "
                f"{resource_uri}"
            )

        except Exception as error:

            error_message = (
                "Failed to load MCP "
                "resource "
                f"'{resource_uri}': "
                f"{error}"
            )

            memory.add_message(
                role="assistant",
                content=error_message,
            )

            return {

                "decision": (
                    "Unable to evaluate "
                    "the case"
                ),

                "reason": (
                    error_message
                ),

                "steps_taken": 0,

                "memory": (
                    memory.get_messages()
                ),

            }

    # ----------------------------------
    # 5.8 SAVE RESOURCES IN MEMORY
    # ----------------------------------

    for (
        resource_uri,
        resource_text,
    ) in (
        loaded_resources.items()
    ):

        memory.add_message(
            role="system",
            content=(
                "MCP Resource: "
                f"{resource_uri}\n"
                f"{resource_text}"
            ),
        )

    print(
        "\nAll required MCP "
        "resources were loaded "
        "successfully."
    )

    # ==================================
    # MCP PROMPT SUPPORT
    # ==================================

    # ----------------------------------
    # 5.9 CHECK PROMPT SUPPORT
    # ----------------------------------

    if not mcp_client.supports(
        "prompts"
    ):

        error_message = (
            "The MCP server does not "
            "support MCP prompts."
        )

        memory.add_message(
            role="assistant",
            content=error_message,
        )

        return {

            "decision": (
                "Unable to evaluate "
                "the case"
            ),

            "reason": (
                error_message
            ),

            "steps_taken": 0,

            "memory": (
                memory.get_messages()
            ),

        }

    print(
        "\nMCP server supports "
        "prompts."
    )

    # ----------------------------------
    # 5.10 LOAD MCP PROMPT
    # ----------------------------------

    prompt_name = (
        "summarize_case"
    )

    try:

        prompt_result = (
            await (
                mcp_client
                .get_prompt(
                    prompt_name=(
                        prompt_name
                    ),
                    arguments={
                        "case_details": (
                            "Legal case ID: "
                            f"{case_id}"
                        )
                    },
                )
            )
        )

        prompt_text = (
            "\n".join(

                message.content.text

                for message

                in prompt_result.messages

                if hasattr(
                    message,
                    "content",
                )

                and hasattr(
                    message.content,
                    "text",
                )

            )
        )

        memory.add_message(
            role="system",
            content=(
                "MCP Prompt: "
                f"{prompt_name}\n"
                f"{prompt_text}"
            ),
        )

        print(
            "Loaded MCP prompt: "
            f"{prompt_name}"
        )

    except Exception as error:

        error_message = (
            "Failed to load MCP "
            "prompt "
            f"'{prompt_name}': "
            f"{error}"
        )

        memory.add_message(
            role="assistant",
            content=error_message,
        )

        return {

            "decision": (
                "Unable to evaluate "
                "the case"
            ),

            "reason": (
                error_message
            ),

            "steps_taken": 0,

            "memory": (
                memory.get_messages()
            ),

        }

    print(
        "\nMCP prompt was loaded "
        "successfully."
    )

    # ==================================
    # 6. START REASONING LOOP
    # ==================================

    steps_taken = 0

    while steps_taken < MAX_STEPS:

        print(
            "\n"
            "================================"
        )

        print(
            f"REASONING STEP "
            f"{steps_taken + 1}"
        )

        print(
            "================================"
        )

        # ------------------------------
        # SEND CURRENT MEMORY TO GEMINI
        # ------------------------------

        print(
            "\nSending agent memory "
            "to Gemini..."
        )

        try:

            gemini_response = (
                call_model(
                    memory.get_messages()
                )
            )

            print(
                "\nGemini response:"
            )

            print(
                gemini_response
            )

        except Exception as error:

            error_message = (
                "Failed to get a response "
                "from Gemini: "
                f"{error}"
            )

            memory.add_message(
                role="assistant",
                content=error_message,
            )

            return {

                "decision": (
                    "Unable to evaluate "
                    "the case"
                ),

                "reason": (
                    error_message
                ),

                "steps_taken": (
                    steps_taken
                ),

                "memory": (
                    memory.get_messages()
                ),

            }

        # ------------------------------
        # PARSE GEMINI RESPONSE
        # ------------------------------

        try:

            agent_response = (
                json.loads(
                    gemini_response
                )
            )

            thought = (
                agent_response.get(
                    "thought"
                )
            )

            action = (
                agent_response.get(
                    "action"
                )
            )

            action_input = (
                agent_response.get(
                    "action_input",
                    {},
                )
            )

            final_decision = (
                agent_response.get(
                    "final_decision"
                )
            )

        except (
            json.JSONDecodeError,
            AttributeError,
        ) as error:

            error_message = (
                "Gemini returned an "
                "invalid JSON response: "
                f"{error}"
            )

            memory.add_message(
                role="assistant",
                content=error_message,
            )

            return {

                "decision": (
                    "Unable to evaluate "
                    "the case"
                ),

                "reason": (
                    error_message
                ),

                "steps_taken": (
                    steps_taken
                ),

                "memory": (
                    memory.get_messages()
                ),

            }

        # ------------------------------
        # DISPLAY AGENT DECISION
        # ------------------------------

        print(
            "\nAgent thought:"
        )

        print(
            thought
        )

        print(
            "\nAgent selected action:"
        )

        print(
            action
        )

        print(
            "\nAction input:"
        )

        print(
            action_input
        )

        # ------------------------------
        # SAVE GEMINI RESPONSE
        # ------------------------------

        memory.add_message(
            role="assistant",
            content=(
                f"Thought: {thought}\n"
                f"Action: {action}\n"
                f"Action Input: "
                f"{action_input}\n"
                f"Final Decision: "
                f"{final_decision}"
            ),
        )

        # ------------------------------
        # INCREMENT STEP COUNT
        # ------------------------------

        steps_taken += 1

        # ==================================
        # VALIDATE SELECTED ACTION
        # ==================================

        allowed_actions = (

            set(
                available_tools
            )

            | {
                "final_answer",
                "escalate",
            }

        )

        if action not in (
            allowed_actions
        ):

            error_message = (
                "Gemini selected an "
                "action that is not "
                "allowed: "
                f"{action}"
            )

            return {

                "decision": (
                    "Unable to evaluate "
                    "the case"
                ),

                "reason": (
                    error_message
                ),

                "steps_taken": (
                    steps_taken
                ),

                "memory": (
                    memory.get_messages()
                ),

            }

        # ==================================
        # HANDLE FINAL ANSWER
        # ==================================

        if action == (
            "final_answer"
        ):

            print(
                "\nFinal decision:"
            )

            print(
                final_decision
            )

            return {

                "decision": (
                    final_decision
                ),

                "thought": (
                    thought
                ),

                "action": (
                    action
                ),

                "action_input": (
                    action_input
                ),

                "final_decision": (
                    final_decision
                ),

                "steps_taken": (
                    steps_taken
                ),

                "loaded_resources": list(
                    loaded_resources.keys()
                ),

                "loaded_prompt": (
                    prompt_name
                ),

                "memory": (
                    memory.get_messages()
                ),

            }

        # ==================================
        # HANDLE ESCALATION
        # ==================================

        if action == (
            "escalate"
        ):

            print(
                "\nCase escalated "
                "for senior review."
            )

            return {

                "decision": (
                    "Escalate for "
                    "Senior Review"
                ),

                "thought": (
                    thought
                ),

                "action": (
                    action
                ),

                "action_input": (
                    action_input
                ),

                "final_decision": (
                    "Escalate for "
                    "Senior Review"
                ),

                "steps_taken": (
                    steps_taken
                ),

                "loaded_resources": list(
                    loaded_resources.keys()
                ),

                "loaded_prompt": (
                    prompt_name
                ),

                "memory": (
                    memory.get_messages()
                ),

            }

        # ==================================
        # EXECUTE MCP TOOL
        # ==================================

        try:

            print(
                "\nExecuting MCP tool:"
            )

            print(
                action
            )

            tool_result = (
                await (
                    mcp_client
                    .call_tool(
                        tool_name=action,
                        arguments=(
                            action_input
                        ),
                    )
                )
            )

            print(
                "\nMCP tool result:"
            )

            print(
                tool_result
            )

        except Exception as error:

            error_message = (
                "Failed to execute MCP "
                "tool "
                f"'{action}': "
                f"{error}"
            )

            memory.add_message(
                role="assistant",
                content=error_message,
            )

            return {

                "decision": (
                    "Unable to evaluate "
                    "the case"
                ),

                "reason": (
                    error_message
                ),

                "steps_taken": (
                    steps_taken
                ),

                "memory": (
                    memory.get_messages()
                ),

            }

        # ==================================
        # SAVE TOOL RESULT IN MEMORY
        # ==================================

        memory.add_message(
            role="tool",
            content=(
                f"MCP Tool: {action}\n"
                f"Arguments: "
                f"{action_input}\n"
                f"Result: "
                f"{tool_result}"
            ),
        )

        print(
            "\nMCP tool result was "
            "saved to agent memory."
        )

    # ==================================
    # MAXIMUM STEPS REACHED
    # ==================================

    error_message = (
        "The agent reached the maximum "
        "number of reasoning steps "
        "without reaching a final "
        "decision."
    )

    memory.add_message(
        role="assistant",
        content=error_message,
    )

    print(
        "\n"
        "Maximum reasoning steps "
        "reached."
    )

    return {

        "decision": (
            "Escalate for "
            "Senior Review"
        ),

        "reason": (
            error_message
        ),

        "steps_taken": (
            steps_taken
        ),

        "loaded_resources": list(
            loaded_resources.keys()
        ),

        "loaded_prompt": (
            prompt_name
        ),

        "memory": (
            memory.get_messages()
        ),

    }