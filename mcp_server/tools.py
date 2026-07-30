from .server import mcp
from .database import get_connection
from datetime import datetime
import uuid
import logging


logger = logging.getLogger(__name__)


@mcp.tool(
    description="Check whether the database connection is working."
)
def database_health() -> dict:

    logger.info("Running database_health()")

    with get_connection() as conn:
        cursor = conn.cursor()

        tables = [
            "party",
            "staff",
            "lawyer",
            "case",
            "document",
            "conflict_check"
        ]

        counts = {}

        for table in tables:
            sql_table = '"case"' if table == "case" else table

            cursor.execute(f"SELECT COUNT(*) FROM {sql_table}")
            counts[table] = cursor.fetchone()[0]

    logger.info("Database health check passed.")

    return {
        "status": "connected",
        "database": str(get_connection.__globals__["DB_PATH"]),
        "tables": counts
    }

# ---------------------------
# PARTY / CLIENT
# ---------------------------

@mcp.tool(
    description="Retrieve client information using the client's party ID."
)
def get_client(client_party_id: str) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM party
            WHERE party_id = ?
              AND party_type = 'client'
        """, (client_party_id,))

        row = cursor.fetchone()

    if row is None:
        return {"error": f"Client '{client_party_id}' not found."}

    return dict(row)


# ---------------------------
# CASE
# ---------------------------

@mcp.tool(
    description="Retrieve complete case information by case ID."
)
def get_case(case_id: str) ->dict:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                c.*,
                p.full_name AS client_name,
                cp.case_type
            FROM "case" c
            JOIN party p
                ON c.client_party_id = p.party_id
            JOIN case_type_policy cp
                ON c.policy_id = cp.policy_id
            WHERE c.case_id = ?
        """, (case_id,))

        row = cursor.fetchone()

    if row is None:
        return {"error": f"Case '{case_id}' not found."}

    return dict(row)


# ---------------------------
# ASSIGN LAWYER
# ---------------------------

@mcp.tool(
    description="Assign a lawyer to a case."
)
def assign_case_to_lawyer(
    case_id: str,
    lawyer_id: str,
    assigned_by: str,
    role_on_case: str = "lead"
) -> dict:

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify case exists
        cursor.execute(
            'SELECT status FROM "case" WHERE case_id = ?',
            (case_id,)
        )
        case = cursor.fetchone()

        if not case:
            return {"error": "Case not found."}

        # Verify lawyer exists
        cursor.execute("""
            SELECT current_caseload, max_caseload
            FROM lawyer
            WHERE lawyer_id = ?
              AND status = 'active'
        """, (lawyer_id,))

        lawyer = cursor.fetchone()

        if not lawyer:
            return {"error": "Lawyer not found or inactive."}

        if lawyer["current_caseload"] >= lawyer["max_caseload"]:
            return {"error": "Lawyer is already at maximum caseload."}

        assignment_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO case_assignment(
                assignment_id,
                case_id,
                lawyer_id,
                assigned_by,
                role_on_case
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            assignment_id,
            case_id,
            lawyer_id,
            assigned_by,
            role_on_case
        ))

        cursor.execute("""
            UPDATE lawyer
            SET current_caseload = current_caseload + 1
            WHERE lawyer_id = ?
        """, (lawyer_id,))

        cursor.execute("""
            UPDATE "case"
            SET status='assigned',
                updated_at=datetime('now')
            WHERE case_id=?
        """, (case_id,))

        conn.commit()

    return {
        "success": True,
        "assignment_id": assignment_id
    }


# ---------------------------
# ACCEPT CASE
# ---------------------------

@mcp.tool(
    description="Accept a case after review."
)
def accept_case(
    case_id: str,
    decided_by: str,
    decision_reason: str
) -> dict:

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE "case"
            SET
                status='accepted',
                decision_reason=?,
                decided_by=?,
                decision_at=datetime('now'),
                updated_at=datetime('now')
            WHERE case_id=?
        """, (
            decision_reason,
            decided_by,
            case_id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "Case not found."}

    return {
        "success": True,
        "message": "Case accepted."
    }


# ---------------------------
# REJECT CASE
# ---------------------------

@mcp.tool(
    description="Reject a case after review."
)
def reject_case(
    case_id: str,
    decided_by: str,
    decision_reason: str
) -> dict:

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE "case"
            SET
                status='rejected',
                decision_reason=?,
                decided_by=?,
                decision_at=datetime('now'),
                updated_at=datetime('now')
            WHERE case_id=?
        """, (
            decision_reason,
            decided_by,
            case_id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "Case not found."}

    return {
        "success": True,
        "message": "Case rejected."
    }


# ---------------------------
# CONFLICT CHECK
# ---------------------------

@mcp.tool(
    description="Retrieve all conflict check records for a case."
)
def get_conflict_checks(case_id: str) -> list:

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM conflict_check
            WHERE case_id = ?
        """, (case_id,))

        rows = cursor.fetchall()

    return [dict(r) for r in rows]


# ---------------------------
# LAWYER DETAILS
# ---------------------------

@mcp.tool(
    description="Retrieve lawyer details."
)
def get_lawyer(lawyer_id: str) -> dict:

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM lawyer
            WHERE lawyer_id = ?
        """, (lawyer_id,))

        row = cursor.fetchone()

    if row is None:
        return {"error": "Lawyer not found."}

    return dict(row)