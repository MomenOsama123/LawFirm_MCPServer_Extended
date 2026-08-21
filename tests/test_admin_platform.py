import pytest
from fastapi.testclient import TestClient
from platform.admin.app import app

client = TestClient(app)

def test_admin_tool_registration():
    # 1. Register tool
    reg_response = client.post(
        "/admin/tools/register",
        json={"agent_id": "case_assignment_agent", "tool_name": "assign_case_to_lawyer"}
    )
    assert reg_response.status_code == 200
    assert "assign_case_to_lawyer" in reg_response.json()["active_tools"]

    # 2. Get tools
    get_response = client.get("/admin/tools/case_assignment_agent")
    assert get_response.status_code == 200
    assert "assign_case_to_lawyer" in get_response.json()["tools"]

    # 3. Unregister tool
    unreg_response = client.post(
        "/admin/tools/unregister",
        json={"agent_id": "case_assignment_agent", "tool_name": "assign_case_to_lawyer"}
    )
    assert unreg_response.status_code == 200
    assert "assign_case_to_lawyer" not in unreg_response.json()["active_tools"]


def test_admin_hitl_pending_tickets():
    response = client.get("/admin/hitl/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)