from project_root.rag.policy_retriever import retrieve_policy_docs


def test_conflict_policy_doc_is_retrieved():
    results = retrieve_policy_docs("What counts as a conflict of interest?", top_k=3)
    assert len(results) > 0
    sources = [r["metadata"].get("source", "") for r in results]
    assert any("conflict" in s.lower() for s in sources)