import json 
from pathlib import Path
from mcp_server.memory.router import MemoryRouter
from mcp_server.memory.short_term import RollingBuffer


def test_router_logs_decision(tmp_path):
    """
    Verify that every routing decision is written
    to a JSON log file.
    """
    router = MemoryRouter()
    router.LOG_DIR = tmp_path
    router.LOG_FILE = tmp_path / "router_log.json"

    message = {
        "role": "user",
        "content": "My favorite color is blue."
    }

    decision = router.route(message)
    assert router.LOG_FILE.exists()

    with open(router.LOG_FILE, "r", encoding="utf-8") as file:
        logs = json.load(file)

    assert len(logs) == 1
    assert logs[0]["decision"] == decision.destination
    assert "reasoning" in logs[0]


def test_router_has_no_semantic_write_path():
    """
    Router must never import or write
    directly to semantic memory.
    """

    router_file = Path(__file__).parent.parent / "router.py"

    source = router_file.read_text(encoding="utf-8").lower()

    forbidden = [
        "import semantic",
        "from .semantic",
        "from semantic",
        "semanticmemory",
        "write_semantic",
        "save_semantic",
    ]

    for keyword in forbidden:
        assert keyword not in source
        
        


def test_router_fires_on_buffer_overflow(tmp_path):
    """
    Router should automatically run when
    the rolling buffer reaches capacity.
    """

    buffer = RollingBuffer(max_messages=2)

    buffer.router.LOG_DIR = tmp_path
    buffer.router.LOG_FILE = tmp_path / "router_log.json"

    buffer.add_message("user", "Hello")
    buffer.add_message("assistant", "Hi")

    # Causes overflow
    buffer.add_message("user", "My name is Ahmed")

    assert buffer.router.LOG_FILE.exists()

    with open(buffer.router.LOG_FILE, "r", encoding="utf-8") as file:
        logs = json.load(file)

    assert len(logs) == 1