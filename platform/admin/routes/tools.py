import asyncio
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from pydantic import BaseModel
from mcp_server.server import mcp_server_instance

router = APIRouter(prefix="/admin/tools", tags=["Tools"])

@router.get("/{agent_id}")
async def get_tools(agent_id: str):
    return {
        "agent_id": agent_id,
        "tools": mcp_server_instance.get_agent_tools(agent_id),
    }

@router.post("/register")
async def register_tool(payload: dict):
    agent_id = payload.get("agent_id")
    tool = payload.get("tool") or payload.get("tool_name")
    
    if not agent_id or not tool:
        raise HTTPException(status_code=400, detail="agent_id and tool/tool_name are required")

    success = mcp_server_instance.register_dynamic_tool(agent_id, tool)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to register tool in MCP Runtime")

    return {
        "status": "success",
        "message": f"Tool registered for agent '{agent_id}'",
        "active_tools": mcp_server_instance.get_agent_tools(agent_id)
    }

@router.post("/unregister")
async def unregister_tool(payload: dict):
    agent_id = payload.get("agent_id")
    tool_name = payload.get("tool_name")

@router.get("/{agent_id}")
def get_agent_tools(agent_id: str):
    return {"agent_id": agent_id, "tools": mcp_server_instance.get_agent_tools(agent_id)}


class MCPToolRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


async def _call_mcp_tool(tool: str, arguments: Dict[str, Any]):
    allowed_tools = {
        "database_health",
        "get_case",
        "get_client",
        "get_conflict_checks",
        "get_lawyer",
        "accept_case",
        "reject_case",
    }
    if tool not in allowed_tools:
        raise HTTPException(status_code=400, detail="Tool is not available to the UI.")

    url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")

    def execute():
        async def request():
            async with Client(StreamableHttpTransport(url=url)) as client:
                result = await client.call_tool(tool, arguments)
                return result.data

        return asyncio.run(request())

    try:
        return await run_in_threadpool(execute)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MCP server unavailable: {exc}") from exc


@router.post("/mcp/call")
async def call_mcp_tool(payload: MCPToolRequest):
    return {"tool": payload.tool, "data": await _call_mcp_tool(payload.tool, payload.arguments)}
