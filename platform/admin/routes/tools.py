from fastapi import APIRouter, HTTPException
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

    if not agent_id or not tool_name:
        raise HTTPException(status_code=400, detail="agent_id and tool_name are required")

    success = mcp_server_instance.unregister_dynamic_tool(agent_id, tool_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unregister tool from MCP Runtime")

    return {
        "status": "success",
        "message": f"Tool '{tool_name}' removed for agent '{agent_id}'",
        "active_tools": mcp_server_instance.get_agent_tools(agent_id)
    }