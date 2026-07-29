from server import mcp
# from database import get_connection

@mcp.tool(
    description="Retrieve a client's basic information by their unique ID."
)
def get_client(client_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()

    if row is None:
        return {"error": f"Client with ID {client_id} not found."}

    return dict(row)


@mcp.tool(
    description="Retrieve case details including status and assigned lawyer by case ID."
)
def get_case(case_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        row = cursor.fetchone()

    if row is None:
        return {"error": f"Case with ID {case_id} not found."}

    return dict(row)


@mcp.tool(
    description="Assign a specific case to a lawyer by providing case_id and lawyer_id."
)
def assign_case_to_lawyer(case_id: int, lawyer_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE cases SET lawyer_id = ? WHERE id = ?",
            (lawyer_id, case_id),
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return {"error": f"Case with ID {case_id} does not exist."}

    return {"success": True, "message": f"Case {case_id} assigned to lawyer {lawyer_id}."}


@mcp.tool(
    description="Mark a case as settled and set the settlement dollar amount."
)
def settle_case(case_id: int, amount: float) -> dict:
    if amount < 0:
        return {"error": "Settlement amount cannot be negative."}

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE cases SET status = 'settled', settlement_amount = ? WHERE id = ?",
            (amount, case_id),
        )
        conn.commit()

        if cursor.rowcount == 0:
            return {"error": f"Case with ID {case_id} does not exist."}

    return {"success": True, "message": f"Case {case_id} successfully settled for ${amount:,.2f}."}