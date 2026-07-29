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