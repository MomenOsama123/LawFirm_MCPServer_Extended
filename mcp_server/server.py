import logging
from fastmcp import FastMCP


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="Law_Firm_MCP")

from .tools import *
from .prompts import *
from .resources import *

# Hide assignment tools by default
mcp.disable(names={"assign_case_to_lawyer"})


if __name__ == "__main__":
    logger.info("Starting Law Firm MCP server...")
    mcp.run( # converting the stdio to http server
    transport="http",
    host="0.0.0.0",
    port=8000,
)

# python -m mcp_server.server
# npx @modelcontextprotocol/inspector