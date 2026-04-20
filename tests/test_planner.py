"""Tests for the planner LangGraph agent."""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _make_llm_mock(responses: list):
    """Return an async side_effect cycling through a list of AIMessage responses."""
    it = iter(responses)

    async def side_effect(messages):
        return next(it)

    return side_effect


@pytest.mark.asyncio
async def test_planner_routes_create_intent():
    """Planner should set intent='create' for a creation request."""
    from agreements.agents.planner.graph import build_planner_graph

    responses = [
        AIMessage(content=json.dumps({
            "intent": "create",
            "task_description": "Create an NDA between Acme Corp and Beta Ltd",
        })),
        AIMessage(content="Successfully created your NDA."),
    ]

    with patch("agreements.agents.planner.graph.ChatAnthropic") as MockLLM, \
         patch("agreements.a2a.client.call_specialist", new_callable=AsyncMock) as mock_sp:
        instance = MockLLM.return_value
        instance.ainvoke = _make_llm_mock(responses)
        mock_sp.return_value = "NDA created with id abc-123"

        graph = build_planner_graph()
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="Create an NDA between Acme Corp and Beta Ltd")]
        })

    assert result.get("intent") == "create"
    assert result.get("specialist_result") == "NDA created with id abc-123"


@pytest.mark.asyncio
async def test_planner_routes_query_intent():
    """Planner should set intent='query' for a list/search request."""
    from agreements.agents.planner.graph import build_planner_graph

    responses = [
        AIMessage(content=json.dumps({
            "intent": "query",
            "task_description": "List all active agreements",
        })),
        AIMessage(content="Here are all active agreements."),
    ]

    with patch("agreements.agents.planner.graph.ChatAnthropic") as MockLLM, \
         patch("agreements.a2a.client.call_specialist", new_callable=AsyncMock) as mock_sp:
        instance = MockLLM.return_value
        instance.ainvoke = _make_llm_mock(responses)
        mock_sp.return_value = "Found 3 active agreements."

        graph = build_planner_graph()
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="Show me all active agreements")]
        })

    assert result.get("intent") == "query"


@pytest.mark.asyncio
async def test_planner_routes_modify_intent():
    """Planner should set intent='modify' for an update request."""
    from agreements.agents.planner.graph import build_planner_graph

    responses = [
        AIMessage(content=json.dumps({
            "intent": "modify",
            "task_description": "Update agreement abc-123: change status to expired",
        })),
        AIMessage(content="Agreement abc-123 status updated to expired."),
    ]

    with patch("agreements.agents.planner.graph.ChatAnthropic") as MockLLM, \
         patch("agreements.a2a.client.call_specialist", new_callable=AsyncMock) as mock_sp:
        instance = MockLLM.return_value
        instance.ainvoke = _make_llm_mock(responses)
        mock_sp.return_value = "Agreement updated successfully."

        graph = build_planner_graph()
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="Update agreement abc-123: change status to expired")]
        })

    assert result.get("intent") == "modify"


@pytest.mark.asyncio
async def test_planner_handles_malformed_llm_response():
    """Planner should default to 'query' when LLM returns non-JSON for intent."""
    from agreements.agents.planner.graph import build_planner_graph

    responses = [
        AIMessage(content="I'm not sure what to do here, let me think..."),
        AIMessage(content="Here are the results."),
    ]

    with patch("agreements.agents.planner.graph.ChatAnthropic") as MockLLM, \
         patch("agreements.a2a.client.call_specialist", new_callable=AsyncMock) as mock_sp:
        instance = MockLLM.return_value
        instance.ainvoke = _make_llm_mock(responses)
        mock_sp.return_value = "No results."

        graph = build_planner_graph()
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="Something vague")]
        })

    assert result.get("intent") == "query"
