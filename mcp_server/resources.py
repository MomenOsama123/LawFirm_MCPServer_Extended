from .mcp_instance import mcp


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


@mcp.resource("company://case-types")
def case_types():

    return """
Supported case types

- Criminal
- Civil
- Family
- Employment
- Corporate
- Intellectual Property
"""


@mcp.resource("company://required-documents")
def required_documents():

    return """
Criminal
- Police report
- National ID

Family
- Marriage certificate
- National ID

Corporate
- Commercial registration
- Company tax card
"""


from .database import get_connection

@mcp.resource("company://lawyers")
def lawyers():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                lawyer_id,
                full_name,
                specialization,
                current_caseload,
                max_caseload
            FROM lawyer
            WHERE status='active'
        """)

        rows = cursor.fetchall()

    return [dict(r) for r in rows]


@mcp.resource("company://statistics")
def statistics():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM "case"')
        cases = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM lawyer")
        lawyers = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM lawyer
            WHERE status='active'
        """)
        active = cursor.fetchone()[0]

    return {
        "cases": cases,
        "lawyers": lawyers,
        "active_lawyers": active
    }



@mcp.resource("company://staff")
def staff():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                staff_id,
                full_name,
                role
            FROM staff
        """)

        rows = cursor.fetchall()

    return [dict(r) for r in rows]



@mcp.resource("company://policies/conflict")
def conflict_policy():

    return """
A case must be rejected if:

- The firm currently represents the opposing party.
- A lawyer has a personal relationship with the opposing party.
- Confidential information from another client could influence the case.
"""