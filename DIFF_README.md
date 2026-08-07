Note: memory + retrieval integration test

This change demonstrates wiring the agent live request path to the existing
short-term memory (mcp_server/memory/), memory router, and the project's
Self-RAG verifier. No new server or database was created for this work.

What was added:
- agent/agent_loop.py: a lightweight live request handler that:
  - Uses mcp_server.memory.RollingBuffer (short-term buffer)
  - Invokes the MemoryRouter via the RollingBuffer eviction behavior
  - Calls a RAG placeholder hook (retrieve_with_rag) — left intentionally
    unimplemented as requested
  - Runs rag.self_check.SelfRAGVerifier to filter retrievals and perform a
    post-generation grounding check
  - Calls the existing agent.call_model() function to exercise the end-to-end
    path

Why no new server or DB was created:
- The handler reuses mcp_server.memory modules for short-term memory and
  routing decisions.
- The handler does not create or modify any database connections or server
  objects under mcp_server/ or db/. Any MCP tool calls should continue to use
  the existing mcp_server/ + db/ implementations.

Where to look:
- agent/agent_loop.py — live request wiring (new)
- mcp_server/memory/short_term.py — rolling buffer used by the handler
- project_root/rag/self_check.py — Self-RAG verifier used by the handler

This note is intentionally short to make it easy to spot the architectural
decision: reuse existing server and DB modules; do not create duplicates.
