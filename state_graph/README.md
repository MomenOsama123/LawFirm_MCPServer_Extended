# State Graph Conventions

This repository defines guidelines and architectural patterns for building LangGraph state graphs within the Law Firm MCP Server ecosystem.

## State Management

Graphs should use standard Python `TypedDict` for state definitions.

```python
from typing import TypedDict


class ExampleState(TypedDict):
    case_id: str
    status: str
````

Nodes should return state updates (partial state dictionaries) rather than directly mutating shared state.

## MCP Integration

All external interactions and database operations must follow the MCP boundary architecture.

**Tool Access:** Graph nodes must access law-firm data exclusively through the existing MCP tools/client.

**Direct Access Prohibition:** Graph nodes must not access SQLite or the case database directly.

**Data Flow**

```text
Graph Node → MCP Tool → MCP Server → Database
```

## File & Naming Conventions

Maintain consistency across the codebase by following these conventions:

| Component            | Convention                      | Example                           |
| -------------------- | ------------------------------- | --------------------------------- |
| Graph implementation | `<feature>/graph.py`            | `case_review/graph.py`            |
| Graph tests          | `tests/test_<feature>_graph.py` | `tests/test_case_review_graph.py` |
| Node functions       | `<action>_node`                 | `validate_intake_node`            |

## Principles

* Keep graph state typed with `TypedDict`.
* Return partial state updates from nodes.
* Access data through MCP only.
* Never access SQLite or the case database directly from graph nodes.
* Keep file and function naming consistent.

## State Graph Engine

The project uses LangGraph's `StateGraph` as the shared workflow engine.

LangGraph was chosen instead of a hand-rolled graph runner because it provides the standard graph execution model, checkpointing, interrupts, and resume support required by the project.

LangGraph checkpoints are persisted in the application's SQLite database through a project-specific checkpointer, making paused workflow state durable and independently inspectable by the platform.

## Current Implementation

The shared LangGraph foundation is now implemented.

### Database-backed checkpoints

Two tables were added to `db/schema.sql`:

* `graph_checkpoint` — stores graph checkpoints and state metadata.
* `graph_checkpoint_write` — stores pending checkpoint writes.

This keeps workflow state in the application's own database rather than relying only on in-memory state or a separate checkpoint database.

### Custom checkpointer

`state_graph/checkpointer.py` contains `DBCheckpointSaver`, which connects LangGraph's checkpoint interface to the application's SQLite database.

It supports:

* saving checkpoints;
* saving pending writes;
* loading checkpoints by `thread_id`;
* listing checkpoints;
* deleting a thread's checkpoints.

Checkpoint rows can also be queried directly with SQLite without going through LangGraph.

### Conflict Clearance graph

`state_graph/conflict_clearance/graph.py` defines the first shared workflow using LangGraph's `StateGraph`:

```text
intake
  ↓
running_conflict_check
  ↓
awaiting_partner_signoff
  ↓
cleared / rejected
```

The partner-signoff state uses LangGraph's interrupt mechanism so execution can pause and later resume from the saved checkpoint.

For this milestone, the conflict result and partner decision use mock data. No real LLM calls or production workflow logic are implemented yet.

### Cross-process persistence

The implementation was verified using two separate Python processes.

The first process runs the graph until the partner-signoff interrupt and writes checkpoints to SQLite.

The second process uses the same `thread_id`, loads the saved checkpoint from the database, and resumes the workflow successfully.

Current verification:

```text
2 passed
```

Tests:

* `tests/test_checkpointer.py`
* `tests/test_conflict_clearance.py`
* `tests/conflict_worker.py`

## What This Solves

Previously, there was no shared durable workflow state for long-running case processes. A case could conceptually be waiting for a conflict check or partner approval without the workflow engine having an explicit state or durable checkpoint explaining where execution stopped.

The current foundation provides:

```text
LangGraph StateGraph
        ↓
Workflow State
        ↓
DBCheckpointSaver
        ↓
Application SQLite Database
        ↓
Inspectable Checkpoint
        ↓
New Process Can Resume
```

This gives all future graphs one execution model and one durable checkpoint mechanism.

## Next Steps

The current implementation is only the shared foundation. Future issues can build on it without creating another graph engine or checkpoint system.

Next work should focus on:

1. Connecting graph nodes to the existing MCP tools instead of mock data.
2. Expanding the Conflict Clearance workflow with the real case and conflict logic.
3. Adding the remaining workflow states and human/partner approval behavior required by the application.
4. Reusing the same `StateGraph` and `DBCheckpointSaver` architecture for the other team graphs.
5. Adding platform-level checkpoint inspection using the existing database.

Future graph implementations should build on this foundation rather than introducing separate graph runners or checkpoint stores.

