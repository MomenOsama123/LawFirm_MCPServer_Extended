from server import mcp


@mcp.prompt()
def summarize_case():

    return """
Summarize the client's legal issue.

Highlight:

- important facts

- possible risks

- recommended attorney
"""