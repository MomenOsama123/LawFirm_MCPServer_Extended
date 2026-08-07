# demo.py
import asyncio
import json
import logging
import os
from pathlib import Path
from google import genai
from google.genai import types

# Setup logging to monitor memory evictions and background consolidation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("IntegrationDemo")

# Import Memory Components
from mcp_server.memory.short_term import RollingBuffer
from mcp_server.memory.router import MemoryRouter
from mcp_server.memory.consolidation import MemoryConsolidator
from mcp_server.memory.scheduler import ConsolidationScheduler

# Import MCP Tools from your project
from mcp_server.tools import (
    database_health,
    get_client,
    get_case,
    get_conflict_checks,
    get_lawyer,
)


class GeminiMCPMemoryAgent:
    """
    Integrates Gemini 2.5 Flash with live MCP tool functions, 
    Short-Term Buffer, Router, and Background Consolidation.
    """
    def __init__(self, buffer_capacity: int = 4):
        # 1. Initialize Gemini Client
        self.client = genai.Client()
        self.model = "gemini-2.5-flash"

        # 2. Map Python functions directly as Gemini tools
        self.tools_list = [
            database_health,
            get_client,
            get_case,
            get_conflict_checks,
            get_lawyer,
        ]

        # 3. Initialize Memory Pipeline (small buffer capacity to trigger eviction demo easily)
        self.router = MemoryRouter()
        self.buffer = RollingBuffer(capacity=buffer_capacity, router=self.router)
        self.consolidator = MemoryConsolidator()

        # 4. Start Background Consolidation Scheduler (Runs every 10 seconds for demo)
        self.scheduler = ConsolidationScheduler(interval_seconds=10)
        self.scheduler.start()

    async def process_user_message(self, user_text: str) -> str:
        logger.info(f"\n--- USER INPUT: '{user_text}' ---")

        # 1. Push user message into short-term buffer (triggers eviction if full)
        evicted = self.buffer.add_message({"role": "user", "content": user_text})
        if evicted:
            logger.info(f"⚡ [Buffer Eviction -> Router]: {evicted['content']}")

        # 2. Build history from rolling buffer context
        raw_context = self.buffer.get_context()
        logger.info(f"🧠 [Active Buffer ({len(raw_context)} items)]: {[m['content'] for m in raw_context]}")

        # Convert memory buffer context to GenAI Content items
        contents = []
        for msg in raw_context:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # 3. Call Gemini with function calling (MCP tools enabled)
        config = types.GenerateContentConfig(
            system_instruction=(
                "You are an assistant connected to a legal firm database via MCP tools. "
                "Use the provided tools to fetch case, lawyer, and client data when needed."
            ),
            tools=self.tools_list,
            temperature=0.2,
        )

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=contents,
            config=config,
        )

        assistant_reply = response.text or "Completed request."

        # 4. Store Assistant response into rolling buffer
        evicted_ast = self.buffer.add_message({"role": "model", "content": assistant_reply})
        if evicted_ast:
            logger.info(f"⚡ [Buffer Eviction -> Router]: {evicted_ast['content']}")

        return assistant_reply

    def shutdown(self):
        """Cleanly stop background scheduler thread."""
        logger.info("Stopping Consolidation Scheduler...")
        self.scheduler.stop()


async def run_demo():
    print("\n==================================================")
    print(" 🚀 GEMINI 2.5 + MCP TOOLS + MEMORY PIPELINE DEMO")
    print("==================================================\n")

    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ ERROR: GEMINI_API_KEY environment variable is not set.")
        return

    agent = GeminiMCPMemoryAgent(buffer_capacity=4)

    try:
        # Turn 1: Database Health Check (Invokes database_health tool)
        reply1 = await agent.process_user_message("Check if the database connection and tables are working.")
        print(f"\n🤖 GEMINI: {reply1}\n")
        await asyncio.sleep(2)

        # Turn 2: Fact Entry
        reply2 = await agent.process_user_message("The client prefers updates sent via email only.")
        print(f"\n🤖 GEMINI: {reply2}\n")
        await asyncio.sleep(2)

        # Turn 3: Case Lookup (Invokes get_case tool)
        reply3 = await agent.process_user_message("Can you fetch details for case C101?")
        print(f"\n🤖 GEMINI: {reply3}\n")
        await asyncio.sleep(2)

        # Turn 4: More context (Forces buffer over capacity, pushing Turn 1 to router)
        reply4 = await agent.process_user_message("Note that initial consultations are scheduled for 30 minutes.")
        print(f"\n🤖 GEMINI: {reply4}\n")

        # Wait to observe the background Consolidation Scheduler execution
        print("\n⏳ Waiting 11 seconds for background Consolidation Scheduler pass...")
        await asyncio.sleep(11)

    finally:
        agent.shutdown()
        print("\n==================================================")
        print(" ✅ DEMO COMPLETE")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_demo())