# [Ashfords & Kane Law Firm] — Intelligent Case Intake & Assignment System

Ashfords Law Firm is building a secure, intelligent intake workflow for legal case intake and assignment. This repository implements an MCP (Model Context Protocol) server that gives an AI agent controlled access to legal intake data without exposing the underlying databases directly to the model.

## About Us

We are a law firm receiving hundreds of new case requests daily. Our goal is to streamline legal consultation intakes, accurately evaluate case details, prevent conflicts of interest, and match clients with the right specialized attorneys seamlessly and securely.

---

## ⚠️ The Problem

The traditional intake process relies heavily on reception staff to manually handle multiple steps for every case request:

1. Inputting client data
2. Reviewing case types
3. Checking for conflicts of interest
4. Inspecting documents
5. Selecting the appropriate attorney
6. Determining whether the firm accepts or rejects the case

### Key Challenges
- **Time-consuming:** manual intake creates delays for potential clients.
- **Human error:** conflict checks and document reviews are easy to miss or mis-handle.
- **Sensitive data:** case information contains highly confidential client details.
- **Security constraints:** direct LLM access to client and case databases is not acceptable for privacy and compliance reasons.
- **Context Rot & Token Blowout:** complex multi-step tool interactions inflate token counts and risk losing early intake instructions.

---

## 🎯 Problem Framing & System Suitability

### Genuine Memory & Knowledge Gap
A base Large Language Model (LLM) operates statelessly across interaction sessions. While standard stateless calls handle short, isolated task execution, relying exclusively on raw in-context message buffers reveals fundamental architectural limitations as intake complexity scales:

- **Session Isolation & Context Decay:** Stateless agents lose execution state across multi-turn workflows. Forcing full raw context into an ever-expanding prompt causes exponential token cost growth, severe latency, and attention degradation ("lost-in-the-middle" performance drops).
- **The Static Knowledge Boundary:** Internal model weights cannot capture runtime updates, changing system state, or evolving intake context without fine-tuning or explicit state retention.
- **Over-reliance on Implicit Reasoning:** Standard context windows force the model to re-evaluate raw historical logs every turn rather than referencing consolidated, stateful representations of past decisions.

To resolve this, the system implements an **Explicit Memory & State Architecture**—combining ephemeral in-context working memory with structured, zone-aware persistent state tracking across execution rounds, backed by a dedicated **Memory Subsystem** (short-term buffer, routing, episodic/semantic consolidation) and a **Retrieval Subsystem** (multiple RAG strategies) described in detail below.

### Originality vs. Standard Worked Examples
Many introductory agent implementations rely on simple sliding-window truncation or naive vector search (RAG) over raw interaction logs. This project implements a custom **Hybrid State Management Pipeline**:

| Feature / Dimension | Standard Worked Example | Our System Architecture |
| :--- | :--- | :--- |
| **Context Retention** | FIFO Sliding-Window / Token Truncation | **Zone-Based Pruning:** Pins system rules and initial parameters while dynamically capping middle-turn tool outputs. |
| **State Compression** | Raw text logs or basic token truncation | **Semantic Structuring:** Extracts and maintains structured operational state rather than relying on unstructured text logs. |
| **Retrieval Mechanics** | Naive similarity search (Top-K) | **State-Aware Routing:** Combines explicit working memory with filtered retrieval keys to eliminate irrelevant context noise. |
| **Evaluation Strategy** | Toy chat prompts (3–5 short turns) | **Fixed Production Benchmark:** Stress-tested against long multi-turn workflows with critical triggers buried under dense tool outputs. |

### Architectural Necessity & Concern Scoping
To maintain a lean implementation and avoid over-engineering, every concern within the state management pipeline serves a specific operational purpose:
- **Why Zone Pruning is Essential:** Pure sliding-window approaches drop critical initial instructions during extended multi-turn tool runs. Zone Pruning retains early rules while keeping recent operational context active.
- **Why Full Summarization is Omitted:** Benchmark evaluations demonstrated that abstractive recursive summarization stripped binary state flags and structural identifiers (dropping test accuracy significantly). Thus, structured state updates were selected over recursive summarization.
- **Why Masking / Pruning Capping is Required:** High-volume output from tool calls (e.g., database dumps, multi-page documents) rapidly exhausts the context window. Selective pruning prevents non-essential tool noise from burying decision-critical facts.

---

## 🤖 Why AI Agents and MCP?

Traditional intake systems mostly collect data statically, and raw LLMs are not safe to grant direct database access. This project uses an AI agent through an MCP server so the model can assist employees safely by calling controlled tools instead of touching the database directly.

This approach allows the system to:
- Assist employees safely through controlled MCP tools.
- Run conflict-of-interest checks and preliminary document reviews quickly.
- Suggest or support attorney matching based on specialization and availability.
- Reduce manual errors in intake and decision workflows.
- Preserve a strong security boundary around sensitive client information.
- Optimize context memory window to maximize accuracy while minimizing inference cost and latency.

---

## What This Server Provides

The server exposes:
- **Tools** for reading case, client, lawyer, and conflict information.
- **Tools** for making guarded case decisions such as accept, reject, and assignment.
- **Resources** that provide firm policy and intake metadata.
- **Prompts** that help an AI agent produce structured legal summaries.
- **Elicitation support** so the agent can ask for any missing required field before performing a write action.
- **Context Evaluation Suite** (`context_eval`) to benchmark, evaluate, and prune context windows across multi-turn intake sessions.
- **Memory Subsystem** (`mcp_server/memory`) to manage short-term working state, route evicted context to long-term storage, and periodically consolidate episodic facts into durable semantic memory.
- **Retrieval Subsystem** (RAG) to recover relevant facts that are no longer directly present in the active context window, using dense, sparse, hybrid, multi-hop, or graph-based retrieval depending on the query.

The implementation is built around FastMCP, a SQLite database stored in [`db`](db), and an evaluation harness in [`context_eval`](context_eval).

---

## Tool Comparison Note

The server separates read-only operations from write operations so clients can safely inspect information before taking action.

- **Read-only tools:** `database_health`, `get_client`, `get_case`, `get_conflict_checks`, and `get_lawyer`.
- **Write tools:** `accept_case`, `reject_case`, and `assign_case_to_lawyer`.
- **Elicitation** is used by the write tools because they need required information such as `case_id`, `decided_by`, `decision_reason`, or `lawyer_id` before a state-changing action can proceed. The server asks for only the missing values instead of forcing the client to provide everything up front.
- If a client connects without the capability required by one of these riskier tools (for example, the elicitation capability needed to prompt for missing fields), the workflow does not silently proceed. The tool aborts before a write is performed, and the operation fails with an error rather than changing case data.

---

## Core Features

### 1. Secure Intake Assistance
The MCP server enables an AI agent to retrieve relevant case information and policy resources without direct database access.

### 2. Conflict Awareness
The system can surface conflict-check data for a case so staff can evaluate whether the matter should proceed.

### 3. Decision Support
The server supports case acceptance and rejection decisions through controlled tools.

### 4. Attorney Assignment Workflow
Case assignment is handled through a guarded tool that checks the current case status, lawyer availability, and caseload before making a change.

### 5. Context Window Optimization (`context_eval`)
Includes a benchmark harness that tests 5 context management strategies across 10 real-world intake transcripts to optimize token payloads and prevent reasoning degradation.

### 6. Human-in-the-Loop Safety
Sensitive actions require explicit information and are designed to be used under human oversight rather than as fully autonomous write operations.

### 7. Explicit Memory Architecture
Short-term working state, routing of evicted context, and scheduled consolidation into durable long-term facts, so critical intake evidence is never silently lost when the active context window is pruned.

### 8. Multi-Strategy Retrieval (RAG)
A pluggable retrieval layer (naive dense, hybrid dense+sparse, agentic multi-hop, and entity graph) recovers case, policy, and client facts that have been evicted from the active conversation window.

---

## 🧠 Memory Architecture (`mcp_server/memory`)

The memory subsystem exists to solve the specific failure mode identified during context-strategy benchmarking: **previously established case evidence has to be re-established when it is removed from the active conversation context by context pruning.** It is organized as a short-term/long-term pipeline with a strict separation of concerns.

### Short-Term Memory — `short_term.py`
- **`RollingBuffer`** — holds the live rolling conversation history as a fixed-size deque (`max_messages`). When the buffer overflows, the oldest message is handed to the `MemoryRouter` for a keep/forget decision *before* it is dropped, so no message disappears without a routing decision being logged. It also exposes `prune(keep_last)` for explicit truncation (used by context strategies such as `ZonePruning`).
- **`Scratchpad`** — holds the agent's current reasoning state (`current_plan`, `active_subgoal`, arbitrary `working_state` key/values). It is intentionally decoupled from `RollingBuffer`: pruning or clearing the rolling buffer never touches scratchpad state, so an in-progress plan or intake subgoal survives conversation-history trimming.

### Routing — `router.py`
- **`MemoryRouter`** — decides, for each item evicted from the rolling buffer, whether it should be `forgotten` or promoted to `episodic` memory. It returns a structured `MemoryRoutingDecision` (Pydantic model) with a `destination`, `reasoning`, and — when promoted — an `event_summary`/`context`/`outcome`. The current implementation uses a lightweight heuristic as a placeholder for a future LLM-based routing call. Every decision is appended to an append-only JSON audit log (`logs/router_log.json`), so routing behavior can be inspected without digging through application logs.
- By design, the router **never writes to semantic memory directly** — it only ever chooses between `forget` and `episodic`, keeping a clean boundary between short-term eviction handling and long-term fact consolidation.

### Consolidation — `consolidation.py` and `scheduler.py`
- **`MemoryConsolidator`** runs periodically (not on every write) over `episodic_store.json` and:
  - Groups episodic facts by name and detects **contradictions** (the same fact recorded with different values).
  - Resolves contradictions by keeping the **newest** timestamped entry.
  - Promotes the winning fact into `semantic_store.json`, and if a fact already exists there, **archives the previous version** (marked `superseded`) into `history_store.json` rather than deleting it — preserving full version history.
  - Applies **expiration rules**: facts past their `expires_at` are marked `expired` in place, never silently removed.
- **`ConsolidationScheduler`** runs `MemoryConsolidator` on a background thread at a fixed interval (default every 300s), with clean `start()`/`stop()` control and per-pass exception handling so a failed consolidation pass doesn't kill the scheduler loop.

### Memory Flow Summary
```
Conversation turn → RollingBuffer
                      │ (on overflow)
                      ▼
                 MemoryRouter → forget | episodic_store.json
                                              │ (scheduled)
                                              ▼
                                     MemoryConsolidator
                                        │        │
                                        ▼        ▼
                              semantic_store.json  history_store.json
```

Short-term memory maintains the active intake state, routing determines what evicted information is worth retaining, consolidation promotes durable information, context strategies (e.g. `ZonePruning`) control what remains in the active context, and the retrieval subsystem below provides a way to recover relevant knowledge that is no longer directly available to the agent.

### Test Coverage
- `test_router.py` — confirms every routing decision is logged, confirms the router has no code path that writes to semantic memory, and confirms the router fires automatically on buffer overflow.
- `test_short_term.py` — confirms pruning the `RollingBuffer` never affects `Scratchpad` state.
- Consolidation tests — confirm contradictory facts produce history entries, confirm expired facts are marked (not deleted), confirm the newest entry wins a contradiction, and confirm superseded facts retain a `superseded_at` marker rather than being removed.

---

## 🔎 Retrieval Architecture (RAG)

To recover case, policy, or client facts that have been evicted from the active context window, the system supports four interchangeable retrieval strategies, all built on a shared `VectorStore`.

### `VectorStore`
An HNSW-backed vector index (via `hnswlib`, with a pure-NumPy exact-search fallback when `hnswlib` isn't available) that also maintains a metadata payload store. Documents are chunked with overlap before indexing, and search supports metadata pre/mid-filtering alongside approximate nearest-neighbor lookup.

### `NaiveRAG`
Standard dense similarity search: embeds the query and returns the top-k nearest chunks from the `VectorStore`. Used as the baseline retrieval strategy.

### `HybridRAG`
Combines dense vector search with a from-scratch **BM25** sparse keyword index (`BM25Index`), merging the two ranked lists with **Reciprocal Rank Fusion (RRF)**. This lets exact legal terms, license numbers, or names surface even when they don't embed closely to the query, while still benefiting from semantic similarity.

### `AgenticRAG`
A multi-hop retrieval loop (`max_hops`, default 3): each hop searches with the current query, collects newly-seen chunks, and constructs a follow-up sub-query from the accumulated context. The loop stops early once a hop returns no new information, and returns the full multi-hop retrieval history alongside the final document set.

### `GraphRAG` *(bonus component)*
A lightweight in-memory entity relationship graph for legal entities (e.g. clients, lawyers, conflicting parties). `add_relationship` records a directed edge plus its reverse, and `query_entity_network` performs a bounded-depth traversal from a root entity to return the connected entities and relationship path — useful for conflict-of-interest network exploration that pure text retrieval can't express.

### Choosing a Strategy
| Strategy | Best for |
| :--- | :--- |
| `NaiveRAG` | Fast, simple recall of the closest matching fact |
| `HybridRAG` | Recovering exact identifiers (bar numbers, names, flags) alongside semantic matches |
| `AgenticRAG` | Multi-step questions requiring iterative follow-up retrieval |
| `GraphRAG` | Conflict-of-interest and entity-relationship exploration |

### RAG Strategy Benchmark

Each retrieval strategy was benchmarked against the same intake query set to compare retrieval accuracy against token cost and latency overhead:

| Architecture | Accuracy | Avg Tokens/Query | Avg Latency (ms) |
|---|---|---|---|
| **Naive RAG** | 77.5% | 74 | 0.02 ms |
| **Hybrid RAG** | 77.5% | 73 | 0.09 ms |
| **Agentic RAG** | 77.5% | 74 | 0.03 ms |
| **Graph RAG** | 77.5% | 75 | 0.01 ms |

**Reading the results:**
- **Accuracy is tied across all four strategies (77.5%)** on this query set, meaning the benchmark's retrieval-quality bottleneck is not currently strategy choice — the same fraction of queries are answered correctly regardless of whether retrieval is dense-only, dense+sparse, multi-hop, or graph-based.
- **Token cost is comparable (73–75 avg tokens/query)** across strategies. `HybridRAG` is marginally cheaper on average despite doing two searches (dense + BM25) because RRF fusion converges on a smaller, more precise top-k set.
- **Latency separates the strategies more than accuracy or token cost does:**
  - `GraphRAG` is fastest (0.01 ms) since entity-network traversal over an in-memory adjacency structure avoids embedding and ANN search entirely.
  - `NaiveRAG` (0.02 ms) and `AgenticRAG` (0.03 ms) stay low-latency; `AgenticRAG`'s overhead comes from its multi-hop loop, though most queries in this set resolve within 1–2 hops before the early-stop condition triggers.
  - `HybridRAG` (0.09 ms) is the most expensive strategy latency-wise, since it runs a full dense search, rebuilds/searches the BM25 index, and fuses both ranked lists with RRF on every call.
- **Implication:** with accuracy held constant in this benchmark, strategy selection should be driven by the *nature of the query* rather than raw accuracy — `GraphRAG` for conflict/entity-relationship lookups, `HybridRAG` when exact identifiers (bar numbers, names) must not be missed and the added latency is acceptable, `AgenticRAG` for multi-step questions, and `NaiveRAG` as the low-overhead default.

---

## 📊 Context Evaluation & Strategy Benchmark

To balance decision accuracy with token efficiency during multi-turn agent interactions, we benchmarked 5 distinct context strategies across a test suite of 10 legal transcripts (`case_001` through `case_010`).

### Performance Summary Matrix

| Strategy | Accuracy Rate | Avg Input Tokens | Strategy Overhead | Avg Total Latency | Production Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **FullContext** | 100% (10/10) | 1,768 | < 0.01 ms | 0.09 s | ⚠️ High Cost Baseline |
| **SlidingWindow** | 90% (9/10) | 1,732 | < 0.01 ms | 0.08 s | ❌ Unsafe (Loses early facts) |
| **Masking** | 100% (10/10) | 1,768 | 0.01 ms | 0.09 s | ⚠️ Privacy/PII Only |
| **RecursiveSummary** | 30% (3/10) | 1,580 | 0.01 ms | 0.08 s | ❌ Critical Fail (Loses specifics) |
| **ZonePruning** | **100% (10/10)** | **1,633 (-7.6%)** | **0.01 ms** | **0.08 s** | **✅ Production Standard** |

### The Memory and Knowledge Gap

During case intake, the agent accumulates case details, conflict-check results, policy information, and MCP tool results across multiple reasoning steps. The recurring failure demonstrated by this system is that **previously established case evidence has to be re-established when it is removed from the active conversation context by context pruning**.

This happens because the agent's active reasoning context is built from its conversation memory, while the context-management strategies may remove older messages to reduce token usage. If an important conflict result, policy condition, or case fact is removed, the agent no longer has that evidence directly available when making a later decision.

The memory and retrieval components described above exist to address this specific gap: short-term memory (`RollingBuffer` / `Scratchpad`) maintains the active intake state, routing (`MemoryRouter`) determines what evicted information is worth retaining, consolidation (`MemoryConsolidator` / `ConsolidationScheduler`) promotes durable information into semantic memory, context strategies control what remains in the active context, and the retrieval mechanisms (`NaiveRAG`, `HybridRAG`, `AgenticRAG`, `GraphRAG`) provide a way to recover relevant knowledge that is no longer directly available to the agent.

### Strategy & Failure Mode Analysis

#### 1. ZonePruning Strategy *(Selected Production Strategy)*
- **Accuracy:** 100% (10/10)
- **Mechanism:** Retains the system/first user message (`keep_first_user_msg=True`), caps intermediate tool payload outputs to 150 characters, and preserves the last *N* turns intact (`keep_recent=2`).
- **Why it wins:** Achieves an average token reduction of **7.6%** (saving over **46%** in token usage on high-volume tool call cases like `case_001`) while maintaining perfect decision accuracy.

#### 2. SlidingWindow Strategy (90% Accuracy)
- **Failure:** Failed `case_001_high_risk_waiver` (Returned `APPROVE`, expected `REJECT`).
- **Root Cause:** Drops earlier conversation turns as new messages arrive (`max_messages=4`). Early high-risk waiver rules and client flags were truncated out, causing the model to evaluate late turns without knowing the risk constraints.

#### 3. RecursiveSummary Strategy (30% Accuracy)
- **Failure:** Failed 7 out of 10 test cases (`case_001`, `case_003`, `case_004`, `case_005`, `case_006`, `case_007`, `case_009`).
- **Root Cause:** Condensed text summaries strip away exact legal micro-facts, specific party names, license numbers, and flag conditions (e.g., `"CA Bar Status: Suspended"`, `"Corporate Seal: MISSING"`, `"Conflict: Partner John Doe"`). Without explicit exact-token triggers, decision rules defaulted incorrectly to `APPROVE`.

---

## Available Tools

### Read-only Tools
- `database_health`: verifies that the SQLite database is reachable and that key tables exist.
- `get_client`: retrieves a client record by party ID.
- `get_case`: retrieves a full case record, including client and policy metadata.
- `get_conflict_checks`: returns conflict-check records for a case.
- `get_lawyer`: retrieves lawyer details by lawyer ID.

### Write Tools
- `accept_case`: updates a case to `accepted` and records the decision metadata.
- `reject_case`: updates a case to `rejected` and records the decision metadata.
- `assign_case_to_lawyer`: assigns an active lawyer to an accepted case if the lawyer is eligible and has capacity.

### Resources
- `company://intake-policy`
- `company://case-types`
- `company://required-documents`
- `company://lawyers`
- `company://statistics`
- `company://staff`
- `company://policies/conflict`

### Prompts
- `summarize_case`: a structured prompt template for generating legal intake summaries.

---

## Security Model

This project deliberately avoids granting the LLM direct access to the law firm's operational databases. Instead, the agent interacts through the MCP server using a small set of approved tools.

That design provides:
- A narrow permission boundary.
- Stronger controls around state-changing actions.
- Better auditability for case decisions.
- Reduced chance of accidental or unauthorized data exposure.

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start the Server
```bash
python -m mcp_server.server
```

The server runs over HTTP on port `8000` by default.

### Run Context Evaluation Benchmark
To test context management strategies across the transcript test suite:
```bash
python -m context_eval.run_eval
```

Results and strategy comparison matrices will be generated and saved to `context_eval/results/comparison.csv`.

### Run a Manual Memory Consolidation Pass
```bash
python -m mcp_server.memory.scheduler
```
This runs `MemoryConsolidator` once. In production, `ConsolidationScheduler` runs this automatically on a background thread at a fixed interval.

### Optional: Inspect the Server
You can inspect the MCP server with the MCP inspector:
```bash
npx @modelcontextprotocol/inspector
```

---

## Project Structure

- [`agent`](agent): Agent wrapper logic, MCP client integration, and agent loop execution.
- [`mcp_server`](mcp_server): FastMCP server implementation, tools, prompts, and resources.
  - [`mcp_server/memory`](mcp_server/memory): Short-term buffer & scratchpad (`short_term.py`), eviction routing (`router.py`), episodic→semantic consolidation (`consolidation.py`), background scheduler (`scheduler.py`), and JSON-backed stores (`episodic_store.json`, `semantic_store.json`, `history_store.json`, `logs/router_log.json`).
  - [`mcp_server/rag`](mcp_server/rag): Retrieval strategies (`NaiveRAG`, `HybridRAG` + `BM25Index`, `AgenticRAG`, `GraphRAG`) and the shared [`vector_store`](mcp_server/rag/vector_store) (`VectorStore`, HNSW-backed).
- [`db`](db): SQLite database, schema, seed data, and ERD assets.
- [`context_eval`](context_eval): Framework for benchmarking context strategies (`FullContext`, `SlidingWindow`, `Masking`, `RecursiveSummary`, `ZonePruning`), test transcript suite (`test_suite/`), and `run_eval.py`.
- [`elicitation_test.py`](elicitation_test.py): Exercises the elicitation flow.
- [`smoke_test.py`](smoke_test.py): Simple smoke test for the MCP server.

---

## Example Workflow

1. The agent reads intake information through `get_case` and `get_client`.
2. It checks conflict and policy data via resources and `get_conflict_checks`.
3. The context engine applies `ZonePruning` to compact intermediate tool responses while keeping active context safe; evicted messages pass through `MemoryRouter` and, if promoted, are consolidated into semantic memory by `MemoryConsolidator`.
4. If a needed fact is no longer present in the active context, the agent recovers it via the retrieval subsystem (`NaiveRAG`, `HybridRAG`, `AgenticRAG`, or `GraphRAG` for entity/conflict relationships).
5. It summarizes the matter using the `summarize_case` prompt.
6. A human reviewer accepts or rejects the case with `accept_case` or `reject_case`.
7. If accepted, the agent may use `assign_case_to_lawyer` to route the case to an active attorney.

---

## Notes on Behavior

- `assign_case_to_lawyer` is hidden by default and is only exposed after a case has been accepted.
- The server uses elicitation for missing fields rather than failing immediately on incomplete write requests.
- `ZonePruning` is configured as the default production context management strategy.
- `MemoryRouter` never writes to semantic memory directly — only `MemoryConsolidator`, running on its own schedule, promotes episodic facts to semantic memory.
- Superseded and expired facts are never deleted; they are marked and retained for auditability.
- The current implementation is designed for controlled, supervised use rather than fully autonomous case decisions.

---

## Summary

This repository demonstrates how an MCP server can safely connect an AI agent to a law firm's intake process. It provides secure access to sensitive legal data, supports structured review workflows, optimizes memory context windows for lower cost and high accuracy through an explicit short-term/long-term memory architecture and multi-strategy retrieval layer, and enforces a clear boundary between inspection and decision-making.