from server import mcp
# from database import get_connection # 


@mcp.tool(
    description="Retrieve a client's information."
)
def get_client(client_id: int):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM clients WHERE id=?",
        (client_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return {"error": "Client not found"}

    return dict(row)


@mcp.tool(
    description="Retrieve a case's information."
)
def get_case(case_id: int):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cases WHERE id=?",
        (case_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return {"error": "Case not found"}

    return dict(row)


@mcp.tool(
    description="Assign a case to a lawyer."
)
def assign_case_to_lawyer(case_id: int, lawyer_id: int):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "UPDATE cases SET lawyer_id=? WHERE id=?",
        (lawyer_id, case_id),
    )

    conn.commit()
    conn.close()

    return {"success": True}


@mcp.tool(
    description="Settle a case"
)
def settle_case(case_id: int, amount: float):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "UPDATE cases SET status='settled', settlement_amount=? WHERE id=?",
        (amount, case_id),
    )

    conn.commit()
    conn.close()

    return {"success": True}
