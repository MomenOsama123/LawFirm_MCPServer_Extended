import logging
from fastmcp import FastMCP


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp = FastMCP(name="Law_Firm_MCP")


from tools import *
from prompts import *

if __name__ == "__main__":
    logger.info("Starting Law Firm MCP server...")
    mcp.run()  # Defaults to stdio transport