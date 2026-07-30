from .server import mcp


@mcp.resource(
    "company://intake-policy"
)
def intake_policy():

    return """
Every new case must:

1. Pass conflict check.

2. Include required documents.

3. Be assigned to a qualified attorney.

4. Be reviewed before approval.
"""