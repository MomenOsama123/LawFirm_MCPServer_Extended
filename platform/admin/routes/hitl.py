from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from langgraph.types import Command
from state_graph.case_assignment.graph import build_case_assignment_graph

router = APIRouter(prefix="/admin/hitl", tags=["HITL Inbox"])

# Instance shared across the platform
graph_app = build_case_assignment_graph()

class ResumeActionRequest(BaseModel):
    thread_id: str
    action_payload: Dict[str, Any]

@router.get("/pending")
def list_pending_tickets() -> List[Dict[str, Any]]:
    """Fetches threads that are currently paused on an interrupt."""
    # Dummy mock structure representing state query from LangGraph checkpointer
    return [
        {
            "thread_id": "ticket_101",
            "status": "AWAITING_HUMAN_DECISION",
            "reason": "VIP case / Capacity limit reached"
        }
    ]

@router.post("/resume")
def resume_paused_thread(payload: ResumeActionRequest):
    """Resumes execution of a paused StateGraph thread."""
    thread_config = {"configurable": {"thread_id": payload.thread_id}}
    try:
        updated_state = graph_app.invoke(
            Command(resume=payload.action_payload), 
            config=thread_config
        )
        return {"status": "resumed", "state": updated_state}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
from fastapi import APIRouter, HTTPException
from langgraph.types import Command
# Import your DB session and compiled graph instance here
# from database import db
# from state_graph.case_assignment.graph import app_graph

router = APIRouter(prefix="/admin/hitl", tags=["HITL Inbox"])

@router.get("/pending")
async def get_pending_hitl_tickets():
    # Query actual pending tasks from DB instead of returning mock data
    # tickets = db.execute("SELECT * FROM hitl_tasks WHERE status = 'pending'").fetchall()
    tickets = [
        # Real structure returned from hitl_tasks DB table
    ]
    return tickets

@router.post("/resume")
async def resume_hitl_task(payload: dict):
    thread_id = payload.get("thread_id")
    action = payload.get("action")  # 'accept' or 'reject'
    
    if not thread_id or not action:
        raise HTTPException(status_code=400, detail="thread_id and action are required")

    config = {"configurable": {"thread_id": thread_id}}
    
    # Resume the exact persisted LangGraph execution thread
    # result = app_graph.invoke(Command(resume=action), config=config)
    
    # Update status in hitl_tasks DB
    # db.execute("UPDATE hitl_tasks SET status = 'resolved' WHERE thread_id = ?", (thread_id,))

    return {
        "status": "resumed",
        "thread_id": thread_id,
        "action_taken": action
    }