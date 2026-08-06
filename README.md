# [Ashfords Law Firm] — Intelligent Case Intake & Assignment System

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

The implementation is built around FastMCP, a SQLite database stored in [db](db), and an evaluation harness in [context_eval](context_eval).

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

---

### Strategy & Failure Mode Analysis

#### 1. ZonePruning Strategy *(Selected Production Strategy)*
* **Accuracy:** 100% (10/10)
* **Mechanism:** Retains the system/first user message (`keep_first_user_msg=True`), caps intermediate tool payload outputs to 150 characters, and preserves the last $N$ turns intact (`keep_recent=2`).
* **Why it wins:** Achieves an average token reduction of **7.6%** (saving over **46%** in token usage on high-volume tool call cases like `case_001`) while maintaining perfect decision accuracy.

#### 2. SlidingWindow Strategy (90% Accuracy)
* **Failure:** Failed `case_001_high_risk_waiver` (Returned `APPROVE`, expected `REJECT`).
* **Root Cause:** Drops earlier conversation turns as new messages arrive (`max_messages=4`). Early high-risk waiver rules and client flags were truncated out, causing the model to evaluate late turns without knowing the risk constraints.

#### 3. RecursiveSummary Strategy (30% Accuracy)
* **Failure:** Failed 7 out of 10 test cases (`case_001`, `case_003`, `case_004`, `case_005`, `case_006`, `case_007`, `case_009`).
* **Root Cause:** Condensed text summaries strip away exact legal micro-facts, specific party names, license numbers, and flag conditions (e.g., `"CA Bar Status: Suspended"`, `"Corporate Seal: MISSING"`, `"Conflict: Partner John Doe"`). Without explicit exact-token triggers, decision rules defaulted incorrectly to `APPROVE`.

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

This project deliberately avoids granting the LLM direct access to the law firm’s operational databases. Instead, the agent interacts through the MCP server using a small set of approved tools.

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

### Start the Server
```bash
python -m mcp_server.server
```

The server runs over HTTP on port `8000` by default.

### Optional: Inspect the Server
You can inspect the MCP server with the MCP inspector:
```bash
npx @modelcontextprotocol/inspector
```

---

## Project Structure

- [agent](agent) contains the client/agent wrapper logic.
- [mcp_server](mcp_server) contains the FastMCP server implementation, tools, prompts, and resources.
- [db](db) contains the SQLite database, schema, seed data, and ERD assets.
- [context_eval]: Framework for benchmarking context strategies (FullContext, SlidingWindow,        Masking, RecursiveSummary, ZonePruning), test transcripts suite (test_suite/), and run_eval.py.
- [elicitation_test.py](elicitation_test.py) exercises the elicitation flow.
- [smoke_test.py](smoke_test.py) provides a simple smoke test for the server.

---

## Example Workflow

1. The agent reads intake information through `get_case` and `get_client`.
2. It checks conflict and policy data via resources and `get_conflict_checks`.
3. The context engine applies ZonePruning to compact intermediate tool responses while keeping      active context safe.
3. It summarizes the matter using the `summarize_case` prompt.
4. A human reviewer accepts or rejects the case with `accept_case` or `reject_case`.
5. If accepted, the agent may use `assign_case_to_lawyer` to route the case to an active attorney.

---

## Notes on Behavior

- `assign_case_to_lawyer` is hidden by default and is only exposed after a case has been accepted.
- The server uses elicitation for missing fields rather than failing immediately on incomplete write requests.
- ZonePruning is configured as the default production context management strategy.
- The current implementation is designed for controlled, supervised use rather than fully autonomous case decisions.

---

## Summary

This repository demonstrates how an MCP server can safely connect an AI agent to a law firm’s intake process. It provides secure access to sensitive legal data, supports structured review workflows, optimizes memory context windows for lower cost and high accuracy, and enforces a clear boundary between inspection and decision-making.