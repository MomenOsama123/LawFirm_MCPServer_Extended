# Ashfords & Kane Law Firm — Intelligent Case Intake & Assignment System

> A secure, intelligent intake workflow for legal case intake and assignment, built around a Model Context Protocol (MCP) server that lets an AI agent assist intake staff through a narrow set of guarded tools — while keeping sensitive firm data inside a controlled permission boundary.

---

## Table of Contents

- [TL;DR](#tldr--what-this-repo-provides)
- [Problem & Approach](#problem--approach)
- [Features](#features)
- [Design Highlights & Rationale](#design-highlights--rationale)
- [Quick Start](#quick-start-developer)
- [Usage Notes & Common Commands](#usage-notes--common-commands)
- [Tools & Resources](#tools--resources-reference)
- [Architecture](#architecture)
- [Extending & Developing](#extending--developing)
- [Testing & Benchmarks](#testing--benchmarks)
- [Troubleshooting](#troubleshooting)
- [Important Files](#important-files-quick-links)
- [Contributing](#contributing)
- [Closing Summary](#closing-summary)

---

## TL;DR — What This Repo Provides

- A modular **MCP server** with:
  - Read-only and guarded write tools for intake, conflict checks, and assignments.
  - An explicit short-term / long-term **memory pipeline** (routing, episodic → semantic consolidation).
  - A pluggable **retrieval layer** (Naive, Hybrid, Agentic, Graph RAG).
  - A **context-evaluation harness** for strategy benchmarking.
- A small demo **Next.js front-end** for simple UI experiments.
- **DB scripts**, sample seed data, and a broad suite of unit/integration tests.

**Key folders** (open these for details):

| Folder | Purpose |
|---|---|
| `mcp_server` | MCP server, tools, and memory subsystem |
| `project_root/rag` | Retrieval strategies (Naive / Hybrid / Agentic / Graph) |
| `planning` | Planning artifacts and design notes |
| `context_eval` | Context-strategy benchmarking harness |
| `state_graph` | State/graph management |
| `db` | Schema, seed data, and DB init scripts |
| `lawfirm-ui` | Demo Next.js front-end |
| `tests` | Unit & integration tests |

---

## Problem & Approach

**Problem**

Traditional intake is manual, slow, and error-prone — and requires careful privacy controls, since direct LLM access to firm databases is unacceptable.

**Approach**

Use an MCP server as a controlled middle layer. The model calls small, audited tools (read-only and guarded writes), combined with:

- An explicit memory architecture (short-term buffer → routing → consolidation).
- Context-management strategies, with **ZonePruning** chosen as the production standard.
- Multi-strategy RAG for recovering evicted facts.

---

## Features

### 1. Secure Intake Assistance
The agent inspects intake via read-only tools, summarizes with structured prompts, and helps human reviewers reach decisions.

### 2. Conflict Awareness & Entity Graphs
Conflict checks and a small in-memory entity graph help detect relationships and conflict-of-interest chains.

### 3. Guarded Decision Tools
Write tools require required fields and elicitation, and abort automatically when required capabilities are missing.

### 4. Explicit Memory Architecture
- **Short-term:** `RollingBuffer` and `Scratchpad` — `mcp_server/memory/short_term.py`
- **Routing:** `MemoryRouter` decides forget vs. promote decisions and logs them — `mcp_server/memory/router.py`
- **Consolidation:** `MemoryConsolidator` promotes episodic facts into semantic memory, tracks contradictions, and preserves history — `mcp_server/memory/consolidation.py` (scheduled by `mcp_server/memory/scheduler.py`)

### 5. Multi-Strategy Retrieval (RAG)
`NaiveRAG`, `HybridRAG` (dense + BM25 + RRF), `AgenticRAG` (multi-hop), and `GraphRAG` implementations — see `project_root/rag` and the HNSW-backed `VectorStore`.

### 6. Context-Evaluation Suite
Benchmarks multiple context strategies (`FullContext`, `SlidingWindow`, `Masking`, `RecursiveSummary`, `ZonePruning`) against 10 real intake transcripts (`context_eval`), producing the comparisons used to choose ZonePruning.

### 7. Human-in-the-Loop Safety
Sensitive state-changing tools require human oversight and elicitation for missing fields; all routing/consolidation decisions are auditable.

---

## Design Highlights & Rationale

- **ZonePruning** was selected because it preserves system instructions and early rules while capping large intermediate tool outputs — the best balance of accuracy and token economy on the benchmark suite.
- The **Router** is conservative: it never writes directly to semantic memory, only decides forget vs. episodic, and logs every decision for audit.
- The **Consolidator** runs periodically, not per-turn: it groups events, detects contradictions, keeps versions, and marks expirations instead of deleting facts.

---

## Quick Start (Developer)

### Prerequisites
- Python 3.10+
- pip
- Node.js (only if running the UI)

### 1. Create & activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize the database (optional)
Inspect `db/schema.sql` and `db/seed_data.sql`, then run:
```bash
python db/init_db.py
```

### 4. Run the MCP server
```bash
python -m mcp_server.server
```
> This module exposes the LawFirm MCP server's exports and integrations used by tests and simple launchers. See `mcp_server/server.py` for exported helpers.

### 5. Run the context evaluation benchmark
```bash
python -m context_eval.run_eval
```
Results are saved to `context_eval/results/comparison.csv`.

### 6. Run the UI (optional)
```bash
cd lawfirm-ui
npm install
npm run dev
```
Open the dev server URL printed by Next.js (usually `http://localhost:3000`).

### 7. Run tests
```bash
pytest
```
Individual test suites exist for memory routing, consolidation, retrieval, and assignment flows:
- `mcp_server/memory/tests`
- `tests`

---

## Usage Notes & Common Commands

- **Run a one-off consolidation pass** (useful for development):
  ```bash
  python -m mcp_server.memory.scheduler
  ```
- **Inspect router logs and memory stores:**
  - `mcp_server/memory/episodic_store.json`
  - `mcp_server/memory/semantic_store.json`
  - `mcp_server/memory/logs/router_log.json`

---

## Tools & Resources (Reference)

**Read-only tools**
- `database_health`
- `get_client`
- `get_case`
- `get_conflict_checks`
- `get_lawyer`

**Write tools (guarded)**
- `accept_case`
- `reject_case`
- `assign_case_to_lawyer`

**Resources & prompts**
- `company://intake-policy`
- `company://case-types`
- `company://required-documents`
- `company://lawyers`
- `summarize_case` (structured summary prompt)

See `mcp_server/tools.py` for concrete implementations and usage contracts.

---

## Architecture

**Conversation flow**
```
Conversation turn → RollingBuffer (short-term)
                        │  (on overflow, router decisions logged)
                        ▼
                 MemoryRouter → forget | episodic_store.json
                                              │  (scheduled consolidation)
                                              ▼
                                     MemoryConsolidator
                                         │              │
                                         ▼              ▼
                              semantic_store.json   history_store.json
```

**Retrieval flow**
```
Agent query → Retrieval strategy (Naive | Hybrid | Agentic | Graph)
            → VectorStore / BM25 / Graph
            → returned chunks
            → summarization or decision step
```

---

## Extending & Developing

**Add a new retrieval strategy**
Implement it under `project_root/rag`, add unit tests, and add performance comparisons to `context_eval`.

**Change context strategy**
Edit or add a strategy in `context_eval/strategies`, then re-run:
```bash
python -m context_eval.run_eval
```

**Modify memory routing logic**
Update `mcp_server/memory/router.py` and add deterministic tests under `mcp_server/memory/tests`.

**Guidelines**
- Keep routing decisions auditable — always write to the router log.
- Consolidation must be idempotent and preserve history.
- Guard all write tools with elicitation and capability checks so no silent writes happen.

---

## Testing & Benchmarks

Run the entire test suite:
```bash
pytest
```

Run specific memory tests:
```bash
pytest mcp_server/memory/tests/test_router.py
pytest mcp_server/memory/tests/test_consolidation.py
```

Run context evaluation:
```bash
python -m context_eval.run_eval
```
Outputs: `context_eval/results/comparison.csv` and per-strategy result files.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `"Missing DB"` errors | Ensure the SQLite DB in `db/` exists, or run `db/init_db.py`. |
| `"Router not writing"` confusion | This is intentional — routing is restricted. Only the consolidator promotes to semantic memory. |
| Retrieval performance oddities | If `hnswlib` isn't available, the `VectorStore` falls back to a NumPy exact-search fallback. Check your environment for an `hnswlib` install. |

---

## Important Files (Quick Links)

- [`mcp_server/server.py`](mcp_server/server.py)
- [`mcp_server/tools.py`](mcp_server/tools.py)
- [`mcp_server/memory/short_term.py`](mcp_server/memory/short_term.py)
- [`mcp_server/memory/router.py`](mcp_server/memory/router.py)
- [`mcp_server/memory/consolidation.py`](mcp_server/memory/consolidation.py)
- [`context_eval/run_eval.py`](context_eval/run_eval.py)
- [`project_root/rag`](project_root/rag)
- [`db/schema.sql`](db/schema.sql)
- [`lawfirm-ui/README.md`](lawfirm-ui/README.md)

---

## Contributing

1. Describe the change in a concise PR and include unit tests for new behavior.
2. Run `pytest` locally, and re-run the context evaluation if your change affects context strategies or retrieval.
3. Preserve auditability when changing memory or routing behavior.

---

## Closing Summary

This repository demonstrates a safety-first integration pattern for applying LLMs to sensitive workflows: a small, audited tool interface (the MCP) plus an explicit memory/retrieval pipeline and a context-evaluation harness that guides production configuration. **ZonePruning + the memory subsystem + appropriate RAG selection** are the practical controls that let the system remain accurate and efficient while keeping sensitive client data secure.

> Need a different version? A more compact README for non-developer audiences, or a longer step-by-step developer guide with environment variables and example requests, can be produced — just specify the target audience and the sections to include.
