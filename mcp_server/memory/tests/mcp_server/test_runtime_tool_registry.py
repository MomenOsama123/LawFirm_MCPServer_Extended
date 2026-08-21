import pytest
from fastmcp import Client, FastMCP

from mcp_server.runtime import RuntimeToolRegistry


@pytest.fixture
def mcp():
    return FastMCP(name="TestServer")


@pytest.fixture
def registry(mcp):
    return RuntimeToolRegistry(mcp)


@pytest.mark.anyio
async def test_register_tool_updates_live_mcp_server(mcp, registry):
    def hello(name: str) -> str:
        """Say hello."""
        return f"Hello {name}"

    registry.register_tool(hello)

    assert registry.is_registered("hello")

    tools = await mcp.list_tools()

    assert any(tool.name == "hello" for tool in tools)


@pytest.mark.anyio
async def test_unregister_tool_removes_tool_from_live_mcp_server(mcp, registry):
    def hello(name: str) -> str:
        """Say hello."""
        return f"Hello {name}"

    registry.register_tool(hello)

    assert any(tool.name == "hello" for tool in await mcp.list_tools())

    removed = registry.unregister_tool("hello")

    assert removed is True
    assert not registry.is_registered("hello")
    assert not any(tool.name == "hello" for tool in await mcp.list_tools())


def test_duplicate_registration_is_safe(mcp, registry):
    def hello(name: str) -> str:
        """Say hello."""
        return f"Hello {name}"

    first = registry.register_tool(hello)
    second = registry.register_tool(hello)

    assert first is second
    assert registry.list_registered_tools() == ("hello",)


def test_unregister_unknown_tool_is_safe(mcp, registry):
    removed = registry.unregister_tool("does_not_exist")

    assert removed is False