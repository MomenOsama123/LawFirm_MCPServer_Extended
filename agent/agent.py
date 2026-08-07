import os
import json
from typing import Any
from dotenv import load_dotenv
from google import genai

from tenacity import retry, stop_after_attempt, wait_fixed
from .config import REQUIRED_CASE_TOOLS, REQUIRED_RESOURCES, MODEL_NAME, MAX_STEPS
from .memory import ConversationMemory

from mcp_server.memory.short_term import RollingBuffer
from mcp_server.memory.router import MemoryRouter
from mcp_server.memory.consolidation import MemoryConsolidator
from mcp_server.memory.scheduler import ConsolidationScheduler

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# Initialize memory infrastructure
router = MemoryRouter(storage_dir="./mcp_server/memory")
buffer = RollingBuffer(capacity=10, router=router)
consolidator = MemoryConsolidator(storage_dir="./mcp_server/memory")

# Start background consolidation job
scheduler = ConsolidationScheduler(consolidator, interval_seconds=300)
scheduler.start()


async def process_user_turn(user_input: str, ctx=None) -> str:
    # 1. Add user message to short-term buffer
    evicted_user = buffer.add_message({"role": "user", "content": user_input})
    if evicted_user:
        router.route(evicted_user)

    # 2. Fetch context (combining rolling buffer + relevant semantic memory)
    current_context = buffer.get_context()

    # 3. Call model Gemini  with tool definitions
    response = await call_model(current_context)

    # 4. Add assistant response back to short-term buffer
    evicted_assistant = buffer.add_message({"role": "assistant", "content": response})
    if evicted_assistant:
        router.route(evicted_assistant)

    return response

# ==================================
# 3. AGENT SYSTEM PROMPT
# ==================================

SYSTEM_PROMPT = """
You are a constrained legal case intake agent.

Use only the MCP tools, resources, and prompts
provided in the conversation.

Rules:

* Never access the database directly.

* Never invent, rename, or use unavailable tools.

* Use exact MCP tool names and argument names.

* Retrieve case details before making a decision.

* Check conflicts before accepting a case.

* Analyze every tool result before selecting
  the next action.

* Use only the MCP tools listed in the most recent
  "Current MCP tools available for this step" message.

* Do not exceed MAX_STEPS.

* If information is insufficient or a conflict
  is unresolved, use "escalate".

Decision execution:

* If the case should be accepted:

  1. Call "accept_case".

  2. Review the current MCP tool list.

  3. If "assign_case_to_lawyer" is available,
     select a qualified active lawyer using the
     loaded lawyer information.

  4. Do not assign a lawyer whose current caseload
     is already at maximum capacity.

  5. Call "assign_case_to_lawyer".

  6. Use "final_answer" only after all required
     MCP tools succeed.

* If the case should be rejected:

  1. Call "reject_case".

  2. Use "final_answer" only after the tool succeeds.

* Never return "Accept Case" or "Reject Case"
  before executing the corresponding MCP write tool.

* The tools "accept_case" and "reject_case"
  perform the actual database updates.

Conflict rules:

* If a conflict is unresolved, use "escalate".

* If a conflict is confirmed, use "reject_case".

Return only valid JSON:

{
    "thought": "Short explanation of the next action.",
    "action": "An available MCP tool, final_answer, or escalate",
    "action_input": {},
    "final_decision": null
}

Examples:

Accept a case:

{
    "thought": "The case passed all required checks.",
    "action": "accept_case",
    "action_input": {
        "case_id": "...",
        "decided_by": "...",
        "decision_reason": "All intake requirements were satisfied."
    },
    "final_decision": null
}

Assign a lawyer:

{
    "thought": "The case was accepted and is ready for assignment.",
    "action": "assign_case_to_lawyer",
    "action_input": {
        "case_id": "...",
        "lawyer_id": "...",
        "assigned_by": "...",
        "role_on_case": "lead"
    },
    "final_decision": null
}

Finish after successful acceptance:

{
    "thought": "The case was accepted and assigned successfully.",
    "action": "final_answer",
    "action_input": {},
    "final_decision": "Accept Case"
}

Reject a case:

{
    "thought": "A confirmed conflict of interest was identified.",
    "action": "reject_case",
    "action_input": {
        "case_id": "...",
        "decided_by": "...",
        "decision_reason": "A confirmed conflict of interest was identified."
    },
    "final_decision": null
}

Finish after successful rejection:

{
    "thought": "The case was rejected successfully.",
    "action": "final_answer",
    "action_input": {},
    "final_decision": "Reject Case"
}
"""


# ==================================
# 4. CALL GEMINI
# ==================================

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
def call_model(messages: list[dict[str, str]]) -> str:
    """
    Sends the current conversation to Gemini
    and returns the generated JSON response.
    """
    prompt = "\n\n".join(
        [f"{message['role'].upper()}:\n{message['content']}" for message in messages]
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    return {"text": response.text, "usage": response.usage_metadata}


# ==================================
# 5. START THE AGENT
# ==================================

async def run_agent( #===================== stratigies modification =====================
    case_id: str,
    mcp_client: Any,
    memory: ConversationMemory | None = None,
    strategy = None,
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
    11. Refresh dynamic MCP tools.
    12. Save tool results in memory.
    13. Continue reasoning until a final decision
        or MAX_STEPS is reached.
    """

    # ----------------------------------
    # 5.1 CREATE SESSION MEMORY
    # ----------------------------------
    if memory is None:
        memory = ConversationMemory()

    # ----------------------------------
    # ADD SYSTEM PROMPT
    # ----------------------------------
    memory.add_message(role="system", content=SYSTEM_PROMPT)

    # ----------------------------------
    # SAVE USER REQUEST
    # ----------------------------------
    memory.add_message(role="user", content=f"Evaluate legal case: {case_id}")

    # ----------------------------------
    # 5.2 CONNECT TO MCP SERVER
    # ----------------------------------
    await mcp_client.initialize()
    print("MCP connection initialized.")

    # ----------------------------------
    # 5.3 CHECK MCP CAPABILITIES
    # ----------------------------------
    server_capabilities = mcp_client.capabilities
    print("\nMCP server capabilities:")
    print(server_capabilities)

    # ----------------------------------
    # CHECK TOOL SUPPORT
    # ----------------------------------
    if not mcp_client.supports("tools"):
        error_message = "The MCP server does not support MCP tools."
        memory.add_message(role="assistant", content=error_message)
        return {
            "decision": "Unable to evaluate the case",
            "reason": error_message,
            "steps_taken": 0,
            "memory": memory.get_messages(),
        }

    print("\nMCP server supports tools.")

    # ----------------------------------
    # 5.4 GET AVAILABLE MCP TOOLS
    # ----------------------------------
    available_tools = await mcp_client.list_tools()
    print("\nAvailable MCP tools:")
    for tool in available_tools:
        print(f"- {tool}")

    # ----------------------------------
    # SAVE AVAILABLE TOOLS IN MEMORY
    # ----------------------------------
    memory.add_message(
        role="system",
        content="Initial MCP tools:\n" + "\n".join(available_tools),
    )

    # ----------------------------------
    # 5.5 VERIFY REQUIRED TOOLS
    # ----------------------------------
    missing_tools = [tool for tool in REQUIRED_CASE_TOOLS if tool not in available_tools]

    if missing_tools:
        error_message = (
            "The MCP server is missing required tools: " f"{', '.join(missing_tools)}"
        )
        memory.add_message(role="assistant", content=error_message)
        return {
            "decision": "Unable to evaluate the case",
            "reason": error_message,
            "steps_taken": 0,
            "memory": memory.get_messages(),
        }

    print("\nAll required MCP tools are available.")

    # ==================================
    # MCP RESOURCE SUPPORT
    # ==================================

    # ----------------------------------
    # 5.6 CHECK RESOURCE SUPPORT
    # ----------------------------------
    if not mcp_client.supports("resources"):
        error_message = "The MCP server does not support MCP resources."
        memory.add_message(role="assistant", content=error_message)
        return {
            "decision": "Unable to evaluate the case",
            "reason": error_message,
            "steps_taken": 0,
            "memory": memory.get_messages(),
        }

    print("\nMCP server supports resources.")

    # ----------------------------------
    # 5.7 LOAD REQUIRED RESOURCES
    # ----------------------------------
    loaded_resources: dict[str, str] = {}

    for resource_uri in REQUIRED_RESOURCES:
        try:
            resource_result = await mcp_client.read_resource(resource_uri)
            resource_text = "\n".join(
                item.text for item in resource_result if hasattr(item, "text")
            )
            loaded_resources[resource_uri] = resource_text
            print(f"Loaded resource: {resource_uri}")

        except Exception as error:
            error_message = (
                f"Failed to load MCP resource '{resource_uri}': {error}"
            )
            memory.add_message(role="assistant", content=error_message)
            return {
                "decision": "Unable to evaluate the case",
                "reason": error_message,
                "steps_taken": 0,
                "memory": memory.get_messages(),
            }

    # ----------------------------------
    # 5.8 SAVE RESOURCES IN MEMORY
    # ----------------------------------
    for resource_uri, resource_text in loaded_resources.items():
        memory.add_message(
            role="system",
            content=f"MCP Resource: {resource_uri}\n{resource_text}",
        )

    print("\nAll required MCP resources were loaded successfully.")

    # ==================================
    # MCP PROMPT SUPPORT
    # ==================================

    # ----------------------------------
    # 5.9 CHECK PROMPT SUPPORT
    # ----------------------------------
    if not mcp_client.supports("prompts"):
        error_message = "The MCP server does not support MCP prompts."
        memory.add_message(role="assistant", content=error_message)
        return {
            "decision": "Unable to evaluate the case",
            "reason": error_message,
            "steps_taken": 0,
            "memory": memory.get_messages(),
        }

    print("\nMCP server supports prompts.")

    # ----------------------------------
    # 5.10 LOAD MCP PROMPT
    # ----------------------------------
    prompt_name = "summarize_case"

    try:
        prompt_result = await mcp_client.get_prompt(
            prompt_name=prompt_name,
            arguments={"case_details": f"Legal case ID: {case_id}"},
        )

        prompt_text = "\n".join(
            message.content.text
            for message in prompt_result.messages
            if hasattr(message, "content") and hasattr(message.content, "text")
        )

        memory.add_message(
            role="system",
            content=f"MCP Prompt: {prompt_name}\n{prompt_text}",
        )

        print(f"Loaded MCP prompt: {prompt_name}")

    except Exception as error:
        error_message = f"Failed to load MCP prompt '{prompt_name}': {error}"
        memory.add_message(role="assistant", content=error_message)
        return {
            "decision": "Unable to evaluate the case",
            "reason": error_message,
            "steps_taken": 0,
            "memory": memory.get_messages(),
        }

    print("\nMCP prompt was loaded successfully.")

    # ==================================
    # 6. START REASONING LOOP
    # ==================================
    steps_taken = 0

    while steps_taken < MAX_STEPS:

        # ----------------------------------
        # GET CURRENT MCP TOOL LIST
        # ----------------------------------
        available_tools = mcp_client.available_tools

        # ----------------------------------
        # DISPLAY CURRENT STEP
        # ----------------------------------
        print("\n================================")
        print(f"REASONING STEP {steps_taken + 1}")
        print("================================")

        # ----------------------------------
        # UPDATE GEMINI WITH CURRENT TOOLS
        # ----------------------------------
        memory.add_message(
            role="system",
            content="Current MCP tools available for this step:\n"
            + "\n".join(available_tools),
        )

        # ----------------------------------
        # SEND CURRENT MEMORY TO GEMINI
        # ----------------------------------
        print("\nSending agent memory to Gemini...")

        try:
            messages = memory.get_messages()

            if strategy is not None:
                messages = strategy.prepare_messages(messages, llm_call=call_model)

            # call_model() returns:
            # {
            #     "text": "...",
            #     "usage": ...
            # }
            gemini_response = call_model(messages)
            response_text = gemini_response["text"]

            print("\nGemini response:")
            print(response_text)

        except Exception as error:
            error_message = f"Failed to get a response from Gemini: {error}"
            memory.add_message(role="assistant", content=error_message)
            return {
                "decision": "Unable to evaluate the case",
                "reason": error_message,
                "steps_taken": steps_taken,
                "memory": memory.get_messages(),
            }

            # ----------------------------------
            # PARSE GEMINI RESPONSE
            # ----------------------------------

        try:
            agent_response = json.loads(response_text)
            thought = agent_response.get("thought")
            action = agent_response.get("action")
            action_input = agent_response.get("action_input", {})
            final_decision = agent_response.get("final_decision")

        except (json.JSONDecodeError, AttributeError) as error:
            error_message = f"Gemini returned an invalid JSON response: {error}"
            memory.add_message(role="assistant", content=error_message)
            return {
                "decision": "Unable to evaluate the case",
                "reason": error_message,
                "steps_taken": steps_taken,
                "memory": memory.get_messages(),
            }

        # ----------------------------------
        # DISPLAY AGENT DECISION
        # ----------------------------------
        print("\nAgent thought:")
        print(thought)
        print("\nAgent selected action:")
        print(action)
        print("\nAction input:")
        print(action_input)

        # ----------------------------------
        # SAVE GEMINI RESPONSE
        # ----------------------------------
        memory.add_message(
            role="assistant",
            content=(
                f"Thought: {thought}\n"
                f"Action: {action}\n"
                f"Action Input: {action_input}\n"
                f"Final Decision: {final_decision}"
            ),
        )

        # ----------------------------------
        # INCREMENT STEP COUNT
        # ----------------------------------
        steps_taken += 1

        # ==================================
        # VALIDATE SELECTED ACTION
        # ==================================
        allowed_actions = set(available_tools) | {"final_answer", "escalate"}

        if action not in allowed_actions:
            error_message = (
                f"Gemini selected an action that is not currently available: {action}"
            )
            memory.add_message(role="assistant", content=error_message)
            return {
                "decision": "Unable to evaluate the case",
                "reason": error_message,
                "steps_taken": steps_taken,
                "memory": memory.get_messages(),
            }

        # ==================================
        # HANDLE FINAL ANSWER
        # ==================================
        if action == "final_answer":
            print("\nFinal decision:")
            print(final_decision)

            return {
                "decision": final_decision,
                "thought": thought,
                "action": action,
                "action_input": action_input,
                "final_decision": final_decision,
                "steps_taken": steps_taken,
                "loaded_resources": list(loaded_resources.keys()),
                "loaded_prompt": prompt_name,
                "memory": memory.get_messages(),
            }

        # ==================================
        # HANDLE ESCALATION
        # ==================================
        if action == "escalate":
            print("\nCase escalated for senior review.")

            return {
                "decision": "Escalate for Senior Review",
                "thought": thought,
                "action": action,
                "action_input": action_input,
                "final_decision": "Escalate for Senior Review",
                "steps_taken": steps_taken,
                "loaded_resources": list(loaded_resources.keys()),
                "loaded_prompt": prompt_name,
                "memory": memory.get_messages(),
            }

        # ==================================
        # EXECUTE MCP TOOL
        # ==================================
        try:
            print("\nExecuting MCP tool:")
            print(action)

            tool_result = await mcp_client.call_tool(
                tool_name=action, arguments=action_input
            )

            print("\nMCP tool result:")
            print(tool_result)

            # ----------------------------------
            # REFRESH DYNAMIC TOOLS
            # ----------------------------------
            if action == "accept_case":
                print("\nRefreshing MCP tools after case acceptance...")
                await mcp_client.refresh_tools()

        except Exception as error:
            error_message = f"Failed to execute MCP tool '{action}': {error}"
            memory.add_message(role="assistant", content=error_message)
            return {
                "decision": "Unable to evaluate the case",
                "reason": error_message,
                "steps_taken": steps_taken,
                "memory": memory.get_messages(),
            }

        # ==================================
        # SAVE TOOL RESULT IN MEMORY
        # ==================================
        memory.add_message(
            role="tool",
            content=(
                f"MCP Tool: {action}\n"
                f"Arguments: {action_input}\n"
                f"Result: {tool_result}"
            ),
        )

        print("\nMCP tool result was saved to agent memory.")

    # ==================================
    # MAXIMUM STEPS REACHED
    # ==================================
    error_message = (
        "The agent reached the maximum number of reasoning steps "
        "without reaching a final decision."
    )

    memory.add_message(role="assistant", content=error_message)
    print("\nMaximum reasoning steps reached.")

    return {
        "decision": "Escalate for Senior Review",
        "reason": error_message,
        "steps_taken": steps_taken,
        "loaded_resources": list(loaded_resources.keys()),
        "loaded_prompt": prompt_name,
        "memory": memory.get_messages(),
    }