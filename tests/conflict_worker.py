from __future__ import annotations
import sys
from langgraph.types import Command
from state_graph.checkpointer import DBCheckpointSaver
from state_graph.conflict_clearance.graph import build_graph


def main():
    db_path = sys.argv[1]
    mode = sys.argv[2]

    checkpointer = DBCheckpointSaver(db_path)
    graph = build_graph(checkpointer)

    config = {
        "configurable": {
            "thread_id": "conflict-test-thread",
        }
    }

    if mode == "start":
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

    elif mode == "resume":
        result = graph.invoke(
            Command(resume=True),
            config,
            durability="sync",
        )

        print(result)

    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()