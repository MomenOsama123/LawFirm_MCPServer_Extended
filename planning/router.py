"""
planning/router.py

Router that uses `Task` from model.py and `llm` from llm.py
without modifying either of those files.
"""

from typing import Any, Dict, Optional

# Import directly from your existing model.py and llm.py
from planning.model import Task
from planning.llm import llm

# Import planning algorithms
from planning.algorithms.plan_and_solve import run_plan_and_solve
from planning.algorithms.tree_of_thoughts import run_tree_of_thoughts
from planning.algorithms.lats import run_lats


class TaskRouter:
    """
    Routes incoming `Task` objects to Plan-and-Solve (PS),
    Tree of Thoughts (ToT), or LATS based on task characteristics.
    """

    def __init__(self, llm_client: Optional[Any] = None, environment: Optional[Any] = None):
        # Default to the llm instance from llm.py
        self.llm_client = llm_client or llm
        self.environment = environment

    def route(self, task: Task, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Routing logic based on Task properties (instruction and tool_name).
        """
        instruction = task.instruction.lower()

        # High-stakes tasks requiring environment verification
        if task.tool_name is not None or "verify" in instruction or "check" in instruction:
            return "LATS"
        # Complex reasoning / multi-path tasks
        elif "analyze" in instruction or "prioritize" in instruction or "evaluate" in instruction:
            return "ToT"
        # Deterministic / logical default tasks
        else:
            return "PS"

    def execute_subtask(self, task: Task, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes the given Task using the routed algorithm.
        """
        selected_algorithm = self.route(task, context)
        print(f"\n[Router] Task '{task.id}' routed to ---> {selected_algorithm}")

        if selected_algorithm == "PS":
            return run_plan_and_solve(task, llm=self.llm_client, context=context)

        elif selected_algorithm == "ToT":
            return run_tree_of_thoughts(task, llm=self.llm_client, context=context)

        elif selected_algorithm == "LATS":
            return run_lats(task, llm=self.llm_client, env=self.environment, context=context)

        raise ValueError(f"Unknown algorithm: {selected_algorithm}")


# Local verification run using the official Task schema
if __name__ == "__main__":
    print("==================================================")
    print("        RUNNING ROUTER WITH MODEL & LLM           ")
    print("==================================================")

    router = TaskRouter()

    # Instantiating Tasks using your exact model.py schema
    tasks_to_test = [
        Task(
            id="task_1",
            instruction="Calculate slot duration for meetings based on available hours."
        ),
        Task(
            id="task_2",
            instruction="Analyze and prioritize conflicting appointment requests.",
            depends_on=["task_1"]
        ),
        Task(
            id="task_3",
            instruction="Verify calendar updates with external tools.",
            depends_on=["task_2"],
            tool_name="calendar_tool"
        )
    ]

    for t in tasks_to_test:
        chosen_algo = router.route(t)
        print(f"Task ID: {t.id:<8} | Strategy: {chosen_algo:<5} | Instruction: {t.instruction}")