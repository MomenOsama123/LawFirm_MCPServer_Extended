import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from .mcp_instance import mcp

from .runtime import RuntimeToolRegistry
from .tools import *
from .prompts import *
from .resources import *

runtime_registry = RuntimeToolRegistry(mcp)

runtime_registry.register_tool(assign_case_to_lawyer)
if __name__ == "__main__":
    logger.info("Starting Law Firm MCP server...")

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
    )


# python -m mcp_server.server
# npx @modelcontextprotocol/inspector