from project_root.rag.vector_store.store import VectorStore
from project_root.rag.naive import NaiveRAG
from project_root.rag.policy_loader import load_policy_documents

_policy_rag = None 


def get_policy_rag() -> NaiveRAG:
    """
    Shared NaiveRAG instance over the firm's policy documents.
    Import and reuse this everywhere policy retrieval is needed —
    do not build a second VectorStore for policy docs.
    """
    global _policy_rag
    if _policy_rag is None:
        store = VectorStore(dim=384)
        store.add_documents(load_policy_documents())
        _policy_rag = NaiveRAG(store)
    return _policy_rag


def retrieve_policy_docs(query: str, top_k: int = 3):
    return get_policy_rag().retrieve(query, top_k=top_k)