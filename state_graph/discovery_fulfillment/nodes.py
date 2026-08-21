from typing import Dict, Any
from state_graph.discovery_fulfillment.state import DiscoveryState
from project_root.rag.retriever import RAGManager

def task_decomposition_node(state: DiscoveryState) -> Dict[str, Any]:
    """Decomposes the document request into a structured fulfillment checklist."""
    instruction = state.get("instruction", "")
    
    checklist = [
        f"Identify relevant corporate records for: {instruction}",
        "Filter communication logs and email threads",
        "Extract requested financial statements and contracts"
    ]
    
    return {
        "checklist": checklist,
        "status": "awaiting_documents"
    }

def privilege_review_node(state: DiscoveryState) -> Dict[str, Any]:
    """Uses RAG retrieval to evaluate incoming documents for attorney-client privilege."""
    rag = RAGManager()
    policies = rag.retrieve_privilege_policy("attorney client privilege withholding standards")
    
    flagged_docs = []
    documents = state.get("documents", [])
    
    for doc in documents:
        content = doc.get("content", "").lower()
        doc_id = doc.get("id", "unknown")
        
        if "confidential" in content or "attorney-client" in content:
            flagged_docs.append(doc_id)
            
    return {
        "flagged_docs": flagged_docs,
        "status": "privilege_review"
    }