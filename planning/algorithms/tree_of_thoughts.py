"""
planning/algorithms/tree_of_thoughts.py

Implementation of Tree of Thoughts (ToT) Algorithm.
Generates candidate reasoning thoughts, evaluates each branch,
and selects/prunes paths to find the optimal solution.
"""

import time
from typing import Any, Dict, List, Optional


GENERATE_CANDIDATES_PROMPT = """\
You are solving a complex reasoning sub-task with multiple potential paths.
Generate {num_candidates} distinct strategies or initial approaches to solve this sub-task.

Sub-Task Instruction: {instruction}

Return each candidate strategy on a new line starting with "Candidate X:".
"""

EVALUATE_CANDIDATE_PROMPT = """\
Evaluate the viability of the following candidate strategy for the given sub-task.

Sub-Task Instruction: {instruction}
Candidate Strategy: {candidate}

Score the candidate strategy from 1 to 10 and give a short justification.
Output Format:
SCORE: <number>
REASON: <short text>
"""


class TreeOfThoughtsEngine:
    """Compatibility facade for callers using the earlier ToT API."""

    def select_next_best_attorney(
        self,
        case_id: Optional[str] = None,
        excluded_lawyers: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Return the next attorney candidate when one is supplied by the caller."""
        del case_id
        candidates = [candidate for candidate in (excluded_lawyers or []) if candidate]
        return candidates[0] if candidates else None


def _call_llm(llm: Any, prompt: str) -> str:
    """Helper function to handle both LangChain and simple LLM clients."""
    if hasattr(llm, "invoke"):
        return llm.invoke(prompt).content
    return llm.complete(prompt)


def run_tree_of_thoughts(sub_task: Any, llm: Any, context: Optional[Dict[str, Any]] = None, num_candidates: int = 3) -> Dict[str, Any]:
    """
    Executes a sub-task using the Tree of Thoughts strategy.
    """
    start_time = time.time()
    llm_calls = 0

    # Safely extract instruction from Task model or description
    instruction = getattr(sub_task, 'instruction', getattr(sub_task, 'description', str(sub_task)))

    # Step 1: Generate multiple candidates (Branching)
    gen_prompt = GENERATE_CANDIDATES_PROMPT.format(instruction=instruction, num_candidates=num_candidates)
    raw_candidates = _call_llm(llm, gen_prompt)
    llm_calls += 1
    
    candidates = [line.strip() for line in raw_candidates.strip().splitlines() if line.strip()]

    # Step 2: Evaluate candidates (Self-Evaluation / Pruning)
    best_candidate = None
    best_score = -1.0
    evaluations: List[Dict[str, Any]] = []

    for candidate in candidates:
        eval_prompt = EVALUATE_CANDIDATE_PROMPT.format(instruction=instruction, candidate=candidate)
        eval_response = _call_llm(llm, eval_prompt)
        llm_calls += 1
        
        # Parse score safely
        score = 5.0
        for line in eval_response.splitlines():
            if "SCORE:" in line.upper():
                try:
                    score = float(line.split(":")[1].strip())
                except ValueError:
                    pass

        evaluations.append({"candidate": candidate, "score": score, "eval_text": eval_response})

        if score > best_score:
            best_score = score
            best_candidate = candidate

    # Fallback if no candidate was parsed properly
    if not best_candidate and candidates:
        best_candidate = candidates[0]

    # Step 3: Execute selected best path
    final_prompt = f"Execute the following optimal strategy for the sub-task '{instruction}':\nStrategy: {best_candidate}"
    final_output = _call_llm(llm, final_prompt)
    llm_calls += 1

    latency = time.time() - start_time

    return {
        "status": "success",
        "algorithm": "ToT",
        "evaluated_branches": evaluations,
        "selected_branch": best_candidate,
        "output": final_output,
        "metrics": {
            "latency_seconds": round(latency, 3),
            "llm_calls": llm_calls
        }
    }