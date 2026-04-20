"""Planner LangGraph StateGraph — classifies intent and routes to specialist agents via A2A."""

import json
import re
from typing import Annotated, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from agreements.agents.planner.prompts import INTENT_CLASSIFICATION_PROMPT, SYNTHESIS_PROMPT
from agreements.config import settings


class PlannerState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: Optional[str]
    task_description: Optional[str]
    specialist_result: Optional[str]
    response: Optional[str]


def _build_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
    )


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    # Try raw JSON
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON found in: {text}")


async def analyze_intent(state: PlannerState) -> dict:
    """Classify the user's intent and extract task description."""
    user_request = state["messages"][-1].content
    llm = _build_llm()
    prompt = INTENT_CLASSIFICATION_PROMPT.format(user_request=user_request)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        parsed = _extract_json(response.content)
        intent = parsed.get("intent", "query")
        task_description = parsed.get("task_description", user_request)
    except (ValueError, json.JSONDecodeError):
        intent = "query"
        task_description = user_request

    return {"intent": intent, "task_description": task_description}


def route_intent(state: PlannerState) -> str:
    """Conditional edge: route to the appropriate specialist node."""
    intent = state.get("intent", "query")
    if intent == "create":
        return "call_creator"
    elif intent == "modify":
        return "call_modifier"
    return "call_query"


async def call_creator(state: PlannerState) -> dict:
    from agreements.a2a.client import call_specialist
    result = await call_specialist(settings.creator_agent_url, state["task_description"])
    return {"specialist_result": result}


async def call_query(state: PlannerState) -> dict:
    from agreements.a2a.client import call_specialist
    result = await call_specialist(settings.query_agent_url, state["task_description"])
    return {"specialist_result": result}


async def call_modifier(state: PlannerState) -> dict:
    from agreements.a2a.client import call_specialist
    result = await call_specialist(settings.modifier_agent_url, state["task_description"])
    return {"specialist_result": result}


async def synthesize_response(state: PlannerState) -> dict:
    """Format the specialist result into a user-facing response."""
    user_request = state["messages"][-1].content
    specialist_result = state.get("specialist_result", "No result received.")

    llm = _build_llm()
    prompt = SYNTHESIS_PROMPT.format(
        user_request=user_request,
        specialist_result=specialist_result,
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {
        "response": response.content,
        "messages": [AIMessage(content=response.content)],
    }


def build_planner_graph():
    """Build and compile the planner StateGraph."""
    graph = StateGraph(PlannerState)

    graph.add_node("analyze_intent", analyze_intent)
    graph.add_node("call_creator", call_creator)
    graph.add_node("call_query", call_query)
    graph.add_node("call_modifier", call_modifier)
    graph.add_node("synthesize_response", synthesize_response)

    graph.add_edge(START, "analyze_intent")
    graph.add_conditional_edges(
        "analyze_intent",
        route_intent,
        {
            "call_creator": "call_creator",
            "call_query": "call_query",
            "call_modifier": "call_modifier",
        },
    )
    graph.add_edge("call_creator", "synthesize_response")
    graph.add_edge("call_query", "synthesize_response")
    graph.add_edge("call_modifier", "synthesize_response")
    graph.add_edge("synthesize_response", END)

    return graph.compile()
