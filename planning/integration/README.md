# Static vs Dynamic Decomposition Comparison

## Overview

This experiment compares two task-decomposition strategies for the law-firm case intake workflow:

1. **Static Decomposition** — the LLM generates the complete task DAG before execution.
2. **Dynamic Decomposition** — the LLM selects one task at a time, executes it through the real MCP server, observes the result, and then decides what to do next.

Both approaches use the **same Gemini model**, the **same MCP server**, the **same MCP tools**, and the **same case-review goal**.

The purpose of the experiment is to evaluate the architectural difference between planning the entire workflow upfront and adapting the workflow based on real tool observations.

---

## Experiment Configuration

### Model

Both approaches use the same model:

```text
Gemini 3.5 Flash
temperature = 0.1
```

No separate model or provider is used for either approach.

### MCP Server

Both approaches connect to the same running MCP server:

```text
http://127.0.0.1:8000/mcp
```

Available tools include:

```text
database_health
get_client
get_case
accept_case
reject_case
get_conflict_checks
get_lawyer
```

### Test Case

```text
Case ID:       case-003
Client ID:     party-004
Decision staff: staff-003
```

### Goal

The agent must:

* retrieve the client's information;
* retrieve the case information;
* retrieve conflict checks;
* determine whether the case should be rejected;
* reject the case when the rejection conditions are satisfied;
* provide a decision reason.

The case contains an unresolved conflict check:

```text
Conflict Check: check-001
Matched Party:  party-003
Match Type:     fuzzy_name_match
Confidence:     0.87
Resolution:     unresolved
```

This conflict is sufficient to justify rejection.

---

# Static Decomposition

The static approach generates the complete DAG before executing anything.

The generated plan contained five tasks:

```text
t1 → get_client
t2 → get_case
t3 → get_conflict_checks

t1 ─┐
t2 ─┼→ t4 → reject_case → t5 → synthesis
t3 ─┘
```

### Execution

The independent retrieval tasks were executed in parallel:

```text
t1: get_client
t2: get_case
t3: get_conflict_checks
```

After all three completed:

```text
t4: reject_case
```

was executed.

Finally:

```text
t5: LLM synthesis
```

produced the final response.

### Static Result

The case was successfully rejected by `staff-003`.

The static approach retrieved:

```text
Client information      ✓
Case details             ✓
Conflict checks          ✓
Rejection                ✓
Final synthesis          ✓
```

---

# Dynamic Decomposition

The dynamic approach does not generate the complete plan upfront.

Instead, the planner repeatedly follows this loop:

```text
LLM decides next task
        ↓
MCP tool executes task
        ↓
Real result returned
        ↓
Result becomes an observation
        ↓
LLM decides next task
        ↓
...
```

The dynamic execution required only four planner steps.

### Step 1 — Retrieve Client

```text
Task:
Retrieve client information for party-004

Tool:
get_client
```

The MCP server returned the real client information.

### Step 2 — Retrieve Conflict Checks

```text
Task:
Retrieve conflict checks for case-003

Tool:
get_conflict_checks
```

The MCP server returned:

```text
check-001
matched_party_id = party-003
match_type = fuzzy_name_match
confidence_score = 0.87
resolution = unresolved
```

### Step 3 — Reject Case

After observing the unresolved conflict, the planner determined that the case should be rejected.

```text
Tool:
reject_case
```

The decision reason was based directly on the observed conflict:

```text
Unresolved conflict check check-001 with party-003
(fuzzy name match, confidence score 0.87).
```

The MCP server confirmed:

```text
success: true
message: Case rejected.
```

### Step 4 — Finish

The planner recognized that the goal had been satisfied and stopped.

No unnecessary case retrieval or additional reasoning step was performed.

---

# Comparison

| Aspect                | Static Decomposition           | Dynamic Decomposition       |
| --------------------- | ------------------------------ | --------------------------- |
| Planning              | Complete DAG generated upfront | One task selected at a time |
| Model                 | Gemini 3.5 Flash               | Gemini 3.5 Flash            |
| MCP server            | Same                           | Same                        |
| Client retrieval      | Yes                            | Yes                         |
| Case retrieval        | Yes                            | No                          |
| Conflict retrieval    | Yes                            | Yes                         |
| Rejection             | Yes                            | Yes                         |
| Final decision        | REJECT                         | REJECT                      |
| Planner steps         | 5 DAG nodes                    | 4 execution steps           |
| Adaptation to results | Limited after plan generation  | Core behavior               |
| Early stopping        | No                             | Yes                         |
| Real MCP execution    | Yes                            | Yes                         |

---

# Key Findings

## 1. Both architectures reached the correct decision

The most important result is that both approaches correctly rejected `case-003`.

The underlying reason was the unresolved conflict:

```text
check-001
party-003
confidence = 0.87
resolution = unresolved
```

Therefore, both architectures successfully completed the required business workflow.

---

## 2. Dynamic decomposition avoided unnecessary work

The static planner generated a dependency structure requiring:

```text
get_client
get_case
get_conflict_checks
```

before the rejection decision.

The dynamic planner did not retrieve the case details.

Instead, after receiving the unresolved conflict check, it determined that the available evidence was sufficient to reject the case.

This demonstrates one of the main advantages of dynamic decomposition:

> The workflow can adapt to information discovered during execution instead of blindly following a pre-generated plan.

In this particular case, the dynamic approach avoided one MCP retrieval operation.

---

## 3. Dynamic decomposition used real observations to determine the next action

The dynamic planner did not assume that the case should be rejected before retrieving evidence.

It first retrieved:

```text
client information
```

then:

```text
conflict checks
```

and only after observing:

```text
resolution = unresolved
confidence_score = 0.87
```

did it select:

```text
reject_case
```

This demonstrates observation-driven planning.

---

## 4. Static decomposition provides stronger upfront structure

The static approach generated an explicit DAG:

```text
get_client ──────┐
get_case ────────┼──→ reject_case → synthesis
get_conflicts ───┘
```

This makes dependencies explicit and allows independent tasks to execute concurrently.

For workflows where all required information is known in advance, this can provide:

* predictable execution;
* explicit dependencies;
* parallelism;
* easier inspection;
* easier reproducibility.

---

## 5. Dynamic decomposition provides better adaptability

The dynamic architecture is better suited to workflows where the next action depends heavily on the result of the previous action.

For example:

```text
get_conflict_checks
        ↓
conflict unresolved?
        ↓
YES → reject_case

NO → continue investigation
```

The next action does not need to be predetermined.

This is particularly useful when tool results can invalidate assumptions made during planning.

---

## 6. The experiment demonstrates different architectural strengths

The experiment should not be interpreted as proving that one architecture is universally better.

Instead, it demonstrates two different strengths:

### Static

Best suited for:

```text
Known workflow
Predictable dependencies
Parallelizable tasks
Need for explicit DAG structure
```

### Dynamic

Best suited for:

```text
Uncertain workflows
Result-dependent decisions
Early stopping
Adaptive investigation
Multi-step reasoning where observations determine the next action
```

---

# Important Limitation

This experiment demonstrates functional correctness and behavioral differences, but it is **not yet a statistically significant performance benchmark**.

The current run contains one case:

```text
case-003
```

Therefore, the experiment does not establish that dynamic decomposition is always faster or uses fewer tokens.

A larger evaluation set would be required to measure:

* average number of tool calls;
* LLM calls;
* total tokens;
* latency;
* decision accuracy;
* unnecessary tool calls;
* failure rate;
* planning overhead.

The current result should therefore be described as an **integration and architectural comparison**, rather than a definitive performance benchmark.

---

# Trace Artifacts

The experiment generates two trace files:

```text
artifacts/static_trace.json
artifacts/dynamic_trace.json
```

These traces contain:

* experiment goal;
* case/client identifiers;
* generated plan;
* dynamic execution steps;
* MCP tool arguments;
* MCP tool results;
* final decision.

They provide reproducible evidence of how each architecture reached the final decision.

---

# Conclusion

The integration test successfully demonstrates that both static and dynamic decomposition can execute the law-firm case-review workflow using the real MCP server.

Static decomposition generated a complete DAG and executed all planned retrieval steps before rejection.

Dynamic decomposition instead adapted to real MCP observations and stopped after obtaining sufficient evidence for rejection, avoiding the unnecessary case-retrieval step.

The experiment therefore demonstrates the core architectural distinction:

```text
Static:
Plan first → Execute plan

Dynamic:
Observe → Decide → Execute → Observe → Decide
```

Both approaches achieved the correct final decision, while dynamic decomposition demonstrated adaptive early stopping based on actual tool results.
