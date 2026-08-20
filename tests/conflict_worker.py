from __future__ import annotations
import os
import sys
from langgraph.types import Command
from state_graph.checkpointer import DBCheckpointSaver
from state_graph.conflict_clearance import graph as conflict_graph


THREAD_ID = "conflict-test-thread"


def record_node(node_name: str, log_file: str) -> None:
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(node_name + "\n")


def install_test_hooks(log_file: str, mode: str) -> None:
    original_intake = conflict_graph.intake_node
    original_conflict = conflict_graph.running_conflict_check_node
    original_signoff = conflict_graph.awaiting_partner_signoff_node

    def intake_hook(state):
        record_node("intake", log_file)
        return original_intake(state)

    def conflict_hook(state):
        record_node("running_conflict_check", log_file)
        return original_conflict(state)

    def signoff_hook(state):
        record_node("awaiting_partner_signoff", log_file)

        if mode == "crash":
            # running_conflict_check has already completed and its
            # checkpoint should already be durable.
            os._exit(42)

        if mode == "recover":
            # Simulate the partner approving after the process restarted.
            return {
                "partner_approved": True,
                "status": "cleared",
            }

        return original_signoff(state)

    conflict_graph.intake_node = intake_hook
    conflict_graph.running_conflict_check_node = conflict_hook
    conflict_graph.awaiting_partner_signoff_node = signoff_hook


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: conflict_worker.py <db_path> <log_file> <mode>"
        )

    db_path = sys.argv[1]
    log_file = sys.argv[2]
    mode = sys.argv[3]

    if mode not in {"crash", "recover", "normal"}:
        raise ValueError(f"Unknown mode: {mode}")

    install_test_hooks(log_file, mode)

    checkpointer = DBCheckpointSaver(db_path)
    graph = conflict_graph.build_graph(checkpointer)

    config = {
        "configurable": {
            "thread_id": THREAD_ID,
        }
    }

    if mode == "crash":
        graph.invoke(
            {
                "case_id": "case-test",
                "status": "intake",
                "conflict_found": False,
                "partner_approved": False,
            },
            config,
            durability="sync",
        )

    elif mode == "recover":
        result = graph.invoke(
            None,
            config,
            durability="sync",
        )
        print(result)

    else:
        result = graph.invoke(
            {
                "case_id": "case-test",
                "status": "intake",
                "conflict_found": False,
                "partner_approved": False,
            },
            config,
            durability="sync",
        )
        print(result)


if __name__ == "__main__":
    main()