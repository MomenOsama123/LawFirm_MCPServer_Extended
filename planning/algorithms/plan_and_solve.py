"""
planning/algorithms/plan_and_solve.py

Implementation of Plan-and-Solve (PS) Algorithm.
Generates an explicit execution plan for deterministic/logical sub-tasks
and executes it sequentially in a single pass.
"""

import time
from typing import Any, Dict, Optional


PLAN_PROMPT = """\
You are an expert planner. Break down the following sub-task into clear, sequential execution steps.

Sub-Task Instruction: {instruction}
Context: {context}

Provide a numbered list of concrete steps.
"""

EXECUTE_PROMPT = """\
You are an expert task executor. Execute the following plan sequentially and provide the final solution.

Sub-Task Instruction: {instruction}
Plan:
{plan}

Provide the final output clearly.
"""


def _call_llm(llm: Any, prompt: str) -> str:
    """Helper function to handle both LangChain and simple LLM clients."""
    if hasattr(llm, "invoke"):
        return llm.invoke(prompt).content
    return llm.complete(prompt)


def run_plan_and_solve(sub_task: Any, llm: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Executes a sub-task using the Plan-and-Solve strategy.
    """
    start_time = time.time()
    
    # Safely extract instruction from Task model or description
    instruction = getattr(sub_task, 'instruction', getattr(sub_task, 'description', str(sub_task)))
    ctx_str = str(context) if context else "None"

    # Step 1: Planning Phase
    plan_prompt = PLAN_PROMPT.format(instruction=instruction, context=ctx_str)
    plan_response = _call_llm(llm, plan_prompt)

    # Step 2: Execution Phase
    exec_prompt = EXECUTE_PROMPT.format(instruction=instruction, plan=plan_response)
    final_output = _call_llm(llm, exec_prompt)

    latency = time.time() - start_time

    return {
        "status": "success",
        "algorithm": "PS",
        "plan": plan_response,
        "output": final_output,
        "metrics": {
            "latency_seconds": round(latency, 3),
            "llm_calls": 2
        }
    }