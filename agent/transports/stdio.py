import sys
from pathlib import Path
from fastmcp.client.transports import StdioTransport
from .base import BaseTransport


class StdioMCPTransport(BaseTransport):
    """
    Creates a local STDIO transport.

    Used during development.

    The MCP server runs as a local subprocess.
    """

    def __init__(self) -> None:

        self.project_root = (
            Path(__file__)
            .resolve()
            .parent
            .parent
            .parent
        )

    def create(self) -> StdioTransport:

        return StdioTransport(
            command=sys.executable,
            args=[
                "-m",
                "mcp_server.server",
            ],
            cwd=str(self.project_root),
        )