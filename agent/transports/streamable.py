from fastmcp.client.transports import (
    StreamableHttpTransport,
)

from .base import BaseTransport


class HTTPMCPTransport(
    BaseTransport
):
    """
    Creates a Streamable HTTP transport
    for connecting to a remote MCP server.
    """

    def __init__(
        self,
        url: str,
    ) -> None:

        self.url = url

    def create(
        self,
    ) -> StreamableHttpTransport:

        return StreamableHttpTransport(
            url=self.url
        )