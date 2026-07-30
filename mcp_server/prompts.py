from .server import mcp

@mcp.prompt(
    description="Generates a structured legal summary framework for a client's case file or notes."
)
def summarize_case(case_details: str = "") -> str:
    """Prompt template for analyzing and summarizing legal cases."""
    
    context = f"\n\nCase Context / Notes:\n{case_details}" if case_details else ""

    return f"""You are a legal assistant analyzing a law firm case.
Please review the case details provided and generate a concise summary.{context}

Format your response with the following sections:
1. **Executive Summary**: Core legal issue and client background.
2. **Key Facts & Timeline**: Critical facts, dates, and evidence.
3. **Legal & Financial Risks**: Key vulnerabilities, potential liability, or statute limitations.
4. **Recommended Strategy & Attorney Profile**: Next steps and the ideal legal specialization required for assignment.
"""