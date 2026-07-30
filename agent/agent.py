# لسه اول جزء تجريبي  من الايجنت
import os
from typing import Any
from dotenv import load_dotenv
from google import genai
from tenacity import retry, stop_after_attempt, wait_fixed
from .config import (
    REQUIRED_CASE_TOOLS,
    MODEL_NAME
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
    api_key=os.getenv("GEMINI_API_KEY")
)

# ==================================
# 3. AGENT SYSTEM PROMPT
# ==================================
SYSTEM_PROMPT = """
You are a constrained legal case intake agent.
Your responsibility is to evaluate legal cases by using only
the tools, resources, and prompts provided by the connected
Law Firm MCP Server.
You must follow these rules:
Never access the database directly.
Never invent a tool name.
Use only tools returned by the MCP server.
Use MCP resources as the firm's source of policies and rules.
Do not make a final decision before retrieving the case details.
Check conflict information before accepting a case.
Do not exceed the maximum number of reasoning steps.
If the available information is insufficient, choose "escalate".
Respond only with valid JSON matching the required schema.
The JSON response must follow this structure:
{
"thought": "Short reasoning for the next step.",
"action": "MCP tool name, final_answer, or escalate",
"action_input": {},
"final_decision": null
}
When you need information, select an available MCP tool.
When enough information is available, use:
{
"thought": "Short explanation of the final decision.",
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

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        },
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
    Current responsibilities:

    1. Create or reuse session memory.
    2. Connect to the MCP server.
    3. Check the server capabilities.
    4. Retrieve the available MCP tools.
    5. Verify that the required tools exist.

    The reasoning loop will be added later.
    """

    # ----------------------------------
    # 5.1 CREATE SESSION MEMORY
    # ----------------------------------

    if memory is None:
        memory = ConversationMemory()

    # Save the user's request in memory
    memory.add_message(
        role="user",
        content=f"Evaluate legal case: {case_id}",
    )

    # ----------------------------------
    # 5.2 CONNECT TO MCP SERVER
    # ----------------------------------

    await mcp_client.initialize()

    print("MCP connection initialized.")

    # ----------------------------------
    # 5.3 CHECK MCP SERVER CAPABILITIES
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

    # Check whether the server supports tools
    if not mcp_client.supports("tools"):

        error_message = (
            "The MCP server does not support "
            "MCP tools."
        )

        memory.add_message(
            role="assistant",
            content=error_message,
        )

        return {
            "decision": "Unable to evaluate the case",
            "reason": error_message,
            "steps_taken": 0,
            "memory": memory.get_messages(),
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
    # 5.5 VERIFY REQUIRED TOOLS
    # ----------------------------------

    missing_tools = [
        tool
        for tool in REQUIRED_CASE_TOOLS
        if tool not in available_tools
    ]

    if missing_tools:

        error_message = (
            "The MCP server is missing "
            "required tools: "
            f"{', '.join(missing_tools)}"
        )

        memory.add_message(
            role="assistant",
            content=error_message,
        )

        return {
            "decision": "Unable to evaluate the case",
            "reason": error_message,
            "steps_taken": 0,
            "memory": memory.get_messages(),
        }

    print(
        "\nAll required MCP tools are available."
    )

    # ----------------------------------
    # TEMPORARY RETURN
    # ----------------------------------

    # This return is temporary.
    # It will be replaced after adding:
    # - MCP Resources
    # - MCP Prompt
    # - Reasoning Loop
    # - Tool execution
    # - Final decision

    return {
        "decision": "Agent initialization completed",
        "steps_taken": 0,
        "memory": memory.get_messages(),
    }