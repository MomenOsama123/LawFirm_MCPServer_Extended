"""
Lightweight live request path that wires short-term buffer, router, a placeholder
for RAG retrieval, and a Self-RAG check. This module purposely reuses the
existing mcp_server.memory and rag.self_check modules and does not create any
new server or DB instances.

This file provides a single entrypoint `handle_live_request(case_id, user_text)`
which is suitable for demonstration and testing of the memory + retrieval
integration.
"""

from typing import List, Dict, Any
import logging

from .memory import ConversationMemory
from .agent import call_model, SYSTEM_PROMPT

from mcp_server.memory.short_term import RollingBuffer
from rag.self_check import SelfRAGVerifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def retrieve_with_rag(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Placeholder RAG retrieval hook.

    Left intentionally unimplemented as requested. Returns an empty list so the
    live request path and Self-RAG checks can be exercised end-to-end without
    wiring a full RAG system. Implementers can replace this function with a
    call into the existing RAG modules (e.g. rag.hybrid.HybridRAG) later.
    """

    logger.info("RAG retrieval placeholder called (not implemented): query='%s'", query)
    # Return the shape expected by SelfRAGVerifier: list[dict(content=str, score=float, ...)]
    return []


def handle_live_request(case_id: str, user_text: str) -> Dict[str, Any]:
    """
    Handle a single live request using the short-term rolling buffer,
    invoke the router (handled by RollingBuffer when evicting), call a RAG
    placeholder, and run a Self-RAG relevance check. The resulting context is
    sent to the existing agent call_model() function so the path is exercised
    end-to-end.

    Returns a dict containing the model response and debug/log information
    useful for a demo transcript.
    """

    logs: List[str] = []

    # 1) Create memory objects
    memory = ConversationMemory()
    rolling = RollingBuffer(max_messages=50)

    # 2) Add system prompt and user request to both rolling buffer and memory
    memory.add_message(role="system", content=SYSTEM_PROMPT)
    memory.add_message(role="user", content=(f"Evaluate legal case: {case_id}"))

    rolling.add_message(role="system", content=(f"Case system prompt (id={case_id})"))
    rolling.add_message(role="user", content=user_text)

    logs.append("Short-term rolling buffer updated with system + user messages.")
    logger.info(logs[-1])

    # 3) Run RAG retrieval (placeholder)
    retrieved_docs = retrieve_with_rag(user_text, top_k=3)
    logs.append(f"RAG retrieval returned {len(retrieved_docs)} documents (placeholder).")
    logger.info(logs[-1])

    # 4) Run Self-RAG post-retrieval relevance check
    verifier = SelfRAGVerifier()
    relevant_docs = verifier.check_retrieval_relevance(user_text, retrieved_docs)
    logs.append(f"Self-RAG relevance filter kept {len(relevant_docs)} documents.")
    logger.info(logs[-1])

    # 5) Merge relevant retrieved docs into the conversation memory
    for i, doc in enumerate(relevant_docs):
        snippet = doc.get("content", "")
        memory.add_message(role="system", content=(f"Retrieved snippet {i+1}: {snippet}"))

    if relevant_docs:
        logs.append("Relevant retrieved documents were injected into agent memory.")
        logger.info(logs[-1])
    else:
        logs.append("No relevant retrieved documents to inject into memory.")
        logger.info(logs[-1])

    # 6) Merge rolling buffer messages into the prompt messages (keeps memory's ordering)
    # Note: ConversationMemory stores messages in order; extend with rolling buffer for extra context.
    for msg in rolling.get_messages():
        memory.add_message(role=msg.get("role", "system"), content=msg.get("content", ""))

    logs.append(f"Merged {len(rolling.get_messages())} rolling-buffer messages into conversation memory.")
    logger.info(logs[-1])

    # 7) Prepare messages and call the existing agent model function
    messages = memory.get_messages()

    logs.append(f"Calling call_model() with {len(messages)} messages.")
    logger.info(logs[-1])

    try:
        gemini_response = call_model(messages)
        response_text = gemini_response.get("text", "")
        usage = gemini_response.get("usage")

        logs.append("Received response from the LLM.")
        logger.info(logs[-1])

    except Exception as e:
        logger.exception("LLM call failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "logs": logs,
        }

    # 8) Run Self-RAG post-generation grounding check
    grounding = verifier.check_generation_grounding(response_text, relevant_docs)
    logs.append(f"Self-RAG grounding verdict: {grounding}")
    logger.info(logs[-1])

    # 9) Return structured result (suitable for demo transcript)
    return {
        "success": True,
        "case_id": case_id,
        "user_text": user_text,
        "retrieved_count": len(retrieved_docs),
        "relevant_count": len(relevant_docs),
        "grounding": grounding,
        "response": response_text,
        "usage": usage,
        "logs": logs,
    }
