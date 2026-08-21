from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from mcp_server.server import mcp_server_instance

router = APIRouter(prefix="/admin/tools", tags=["Tool Control"])

class ToolManageRequest(BaseModel):
    agent_id: str
    tool_name: str

@router.post("/register")
def register_tool(payload: ToolManageRequest):
    return mcp_server_instance.register_tool(payload.agent_id, payload.tool_name)

@router.post("/unregister")
def unregister_tool(payload: ToolManageRequest):
    return mcp_server_instance.unregister_tool(payload.agent_id, payload.tool_name)

@router.get("/{agent_id}")
def get_agent_tools(agent_id: str):
    return {"agent_id": agent_id, "tools": mcp_server_instance.get_agent_tools(agent_id)}