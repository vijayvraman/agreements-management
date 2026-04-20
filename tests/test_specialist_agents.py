"""Tests for specialist agent LangGraph graphs (MCP tools mocked)."""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _make_mock_tool(name: str, return_value: str):
    """Create a lightweight LangChain tool for testing."""

    @tool(name)
    def mock_tool(input: str = "") -> str:
        """Mock tool for testing."""
        return return_value

    return mock_tool


@pytest.mark.asyncio
async def test_creator_graph_no_tools_needed():
    """Creator graph should return a response even when no tool calls are made."""
    from agreements.agents.creator.graph import build_graph

    mock_tools = []

    # Patch ChatAnthropic to return a direct message (no tool calls)
    with patch("agreements.agents.creator.graph.ChatAnthropic") as MockLLM:
        instance = MockLLM.return_value
        instance.bind_tools.return_value = instance
        instance.ainvoke = AsyncMock(return_value=AIMessage(content="I will create an NDA for you."))

        graph = await build_graph(mock_tools)
        result = await graph.ainvoke({"messages": [HumanMessage(content="Create an NDA")]})

    assert result["messages"][-1].content == "I will create an NDA for you."


@pytest.mark.asyncio
async def test_query_graph_no_tools_needed():
    """Query graph should return a response even when no tool calls are made."""
    from agreements.agents.query.graph import build_graph

    with patch("agreements.agents.query.graph.ChatAnthropic") as MockLLM:
        instance = MockLLM.return_value
        instance.bind_tools.return_value = instance
        instance.ainvoke = AsyncMock(return_value=AIMessage(content="No agreements found."))

        graph = await build_graph([])
        result = await graph.ainvoke({"messages": [HumanMessage(content="List all agreements")]})

    assert "No agreements found" in result["messages"][-1].content


@pytest.mark.asyncio
async def test_modifier_graph_no_tools_needed():
    """Modifier graph should return a response even when no tool calls are made."""
    from agreements.agents.modifier.graph import build_graph

    with patch("agreements.agents.modifier.graph.ChatAnthropic") as MockLLM:
        instance = MockLLM.return_value
        instance.bind_tools.return_value = instance
        instance.ainvoke = AsyncMock(return_value=AIMessage(content="Agreement updated."))

        graph = await build_graph([])
        result = await graph.ainvoke({"messages": [HumanMessage(content="Update agreement abc-123")]})

    assert "updated" in result["messages"][-1].content


@pytest.mark.asyncio
async def test_creator_graph_with_tool_call():
    """Creator graph should call a tool when the LLM requests it."""
    from langchain_core.messages import AIMessage

    from agreements.agents.creator.graph import build_graph

    agreement_data = json.dumps({
        "id": "abc-123", "title": "Test NDA", "status": "draft",
        "agreement_type": "NDA", "parties": [], "content": "", "version": 1,
        "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00",
        "metadata": {},
    })

    create_tool = _make_mock_tool("create_agreement", agreement_data)

    # First call: returns tool_call; second call: returns final response
    first_response = AIMessage(
        content="",
        tool_calls=[{
            "name": "create_agreement",
            "args": {"title": "Test NDA", "agreement_type": "NDA", "parties": "[]", "content": ""},
            "id": "call_1",
        }],
    )
    second_response = AIMessage(content="Created NDA: Test NDA (id: abc-123)")

    call_count = 0

    async def side_effect(messages):
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    with patch("agreements.agents.creator.graph.ChatAnthropic") as MockLLM:
        instance = MockLLM.return_value
        instance.bind_tools.return_value = instance
        instance.ainvoke = side_effect

        graph = await build_graph([create_tool])
        result = await graph.ainvoke({"messages": [HumanMessage(content="Create a Test NDA")]})

    assert "abc-123" in result["messages"][-1].content or call_count >= 2
