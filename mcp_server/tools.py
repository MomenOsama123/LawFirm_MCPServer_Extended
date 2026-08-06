from .server import mcp
from .database import get_connection
import uuid
import logging

from fastmcp import Context

from .elicitation import require_fields


logger = logging.getLogger(__name__)


# ---------------------------
# DATABASE HEALTH CHECK
# ---------------------------

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
# CASE RETRIEVAL
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
# ASSIGN CASE TO LAWYER
# ---------------------------    

@mcp.tool(
    description="Assign a lawyer to a case."
)
async def assign_case_to_lawyer(
    ctx: Context,
    case_id: str | None = None,
    lawyer_id: str | None = None,
    assigned_by: str | None = None,
    role_on_case: str | None = "lead",
) -> dict:

    values = await require_fields(
        ctx,
        {
            "case_id": case_id,
            "lawyer_id": lawyer_id,
            "assigned_by": assigned_by,
            "role_on_case": role_on_case,
        },
        {
            "case_id": "The case ID to assign.",
            "lawyer_id": "The lawyer that will handle the case.",
            "assigned_by": "The staff member assigning the lawyer.",
            "role_on_case": "Role of the lawyer on this case.",
        },
    )

    case_id = values["case_id"]
    lawyer_id = values["lawyer_id"]
    assigned_by = values["assigned_by"]
    role_on_case = values["role_on_case"]

    # Statuses that are allowed to move into 'assigned'.
    # Adjust this set to match your actual case-status lifecycle.
    ASSIGNABLE_STATUSES = {"accepted"}

    with get_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT status FROM "case" WHERE case_id = ?',
                (case_id,)
            )
            case = cursor.fetchone()

            if not case:
                return {"error": "Case not found."}

            case_status = case["status"]

            if case_status not in ASSIGNABLE_STATUSES:
                return {
                    "error": (
                        f"Case cannot be assigned from its current status "
                        f"('{case_status}'). Case must be in one of: "
                        f"{sorted(ASSIGNABLE_STATUSES)}."
                    )
                }

            cursor.execute("""
                SELECT current_caseload, max_caseload
                FROM lawyer
                WHERE lawyer_id = ?
                  AND status='active'
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
                role_on_case,
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

        except Exception as e:
            conn.rollback()
            logger.exception(
                "Failed to assign lawyer '%s' to case '%s': %s",
                lawyer_id, case_id, e
            )
            return {"error": f"Assignment failed and was rolled back: {e}"}

    # Hide this tool again after assignment
    logger.info("Case assigned successfully.")

    await ctx.disable_components(
        names={"assign_case_to_lawyer"},
        components={"tool"},
    )

    # Hide this tool again after assignment
    logger.info("Case assigned successfully.")

    if hasattr(ctx, "disable_components"):
        await ctx.disable_components(
            names={"assign_case_to_lawyer"},
            components={"tool"},
        )
    logger.info("assign_case_to_lawyer hidden again")

    return {
        "success": True,
        "assignment_id": assignment_id,
        "message": "Case assigned successfully."
    }

# ---------------------------
# ACCEPT CASE
# ---------------------------

@mcp.tool(
    description="Accept a case after review."
)
async def accept_case(
    ctx: Context,
    case_id: str | None = None,
    decided_by: str | None = None,
    decision_reason: str | None = None,
) -> dict:

    values = await require_fields(
        ctx,
        {
            "case_id": case_id,
            "decided_by": decided_by,
            "decision_reason": decision_reason,
        },
        {
            "case_id": "The case ID to accept.",
            "decided_by": "The staff member approving the case.",
            "decision_reason": "Reason for accepting the case.",
        },
    )

    case_id = values["case_id"]
    decided_by = values["decided_by"]
    decision_reason = values["decision_reason"]

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

    # Expose assignment tool only to THIS session (safely guarded)
    try:
        if hasattr(ctx, "enable_components"):
            await ctx.enable_components(
                names={"assign_case_to_lawyer"},
                components={"tool"},
            )
            logger.info("Unlocked assign_case_to_lawyer tool")
    except RuntimeError as e:
        logger.warning(
            "Could not enable component (no active session context): %s", e
        )
    except Exception as e:
        logger.warning("Unexpected error enabling components: %s", e)

    return {
        "success": True,
        "message": (
            "Case accepted. "
            "The Assign Case To Lawyer tool has been unlocked."
        )
    }


# ---------------------------
# REJECT CASE
# ---------------------------

@mcp.tool(
    description="Reject a case after review."
)
async def reject_case(
    ctx: Context,
    case_id: str | None = None,
    decided_by: str | None = None,
    decision_reason: str | None = None,
) -> dict:

    values = await require_fields(
        ctx,
        {
            "case_id": case_id,
            "decided_by": decided_by,
            "decision_reason": decision_reason,
        },
        {
            "case_id": "The case ID to reject.",
            "decided_by": "The staff member rejecting the case.",
            "decision_reason": "Reason for rejecting the case.",
        },
    )

    case_id = values["case_id"]
    decided_by = values["decided_by"]
    decision_reason = values["decision_reason"]

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
            case_id,
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "Case not found."}

    return {
        "success": True,
        "message": "Case rejected.",
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