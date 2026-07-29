from fastmcp import FastMCP

mcp = FastMCP(
    name="Law_Firm_MCP",
    version="1.0.0"
)

from tools import *
from prompts import *

if __name__ == "__main__":
    mcp.run()