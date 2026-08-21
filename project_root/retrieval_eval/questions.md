# Retrieval Evaluation Question Suite

Target categories and intended winners:
- **Naive RAG**: General domain/background knowledge
- **Hybrid RAG**: Exact identifiers, legal codes, citation numbers, structured filters
- **Agentic RAG**: Complex multi-hop reasoning, document decomposition, cross-file synthesis
- **Graph RAG**: High-level entity relationships, community summaries, multi-entity mapping

---

### 1. Naive RAG Targets (General Knowledge)
1. **[Target: Naive]** What is the standard legal definition of "fiduciary duty" in corporate governance?
2. **[Target: Naive]** Describe the general principles of attorney-client privilege during civil litigation.
3. **[Target: Naive]** What are the basic requirements for establishing breach of contract in commercial disputes?

### 2. Hybrid RAG Targets (Exact Identifiers & Citations)
4. **[Target: Hybrid]** What were the specific holding details in case docket ID `CV-2024-88492`?
5. **[Target: Hybrid]** Find all contract clauses referencing statutory compliance under `15 U.S.C. § 78u-4(b)`.
6. **[Target: Hybrid]** What is the exact billing hourly rate listed for Senior Partner `EMP-9023` in 2025?

### 3. Agentic RAG Targets (Decomposition & Multi-Hop)
7. **[Target: Agentic]** Compare the liability exposure of Defendant A in Case C101 with Defendant B in Case C104 across all shared motions.
8. **[Target: Agentic]** Did the plaintiff in case C102 fulfill all prerequisite notice conditions outlined in clause 4.2 of document DOC-33?
9. **[Target: Agentic]** Identify all conflicting deposition statements made by witness Smith regarding the timeline on October 12th.

### 4. Graph RAG Targets (Entity Relationships & Global Summaries)
10. **[Target: Graph]** Map all parent-subsidiary relationships and joint ventures involving Acme Corp mentioned across all active cases.
11. **[Target: Graph]** Which external law firms appeared as co-counsel alongside Partner Davis across all 2024-2025 litigation?
12. **[Target: Graph]** Provide a global summary of the primary regulatory risk themes affecting financial technology clients in our repository.