from mcp_server.database import get_connection

conn = get_connection()

print("\n=== CASES ===")
for row in conn.execute(
    'SELECT case_id, status FROM "case"'
).fetchall():
    print(dict(row))

print("\n=== LAWYERS ===")
for row in conn.execute(
    """
    SELECT lawyer_id, status, current_caseload, max_caseload
    FROM lawyer
    """
).fetchall():
    print(dict(row))

conn.close()