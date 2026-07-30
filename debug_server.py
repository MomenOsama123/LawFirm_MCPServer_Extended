import asyncio
from mcp_server.server import mcp

async def main():
    print("=" * 50)
    print("RESOURCES")
    print("=" * 50)

    resources = await mcp.list_resources()

    print(f"Found {len(resources)} resources\n")

    for resource in resources:
        print(resource)

asyncio.run(main())