"""Modifier specialist LangGraph agent — updates and deletes agreements using MCP tools."""

from typing import Annotated, Optional

from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from agreements.config import settings


class ModifierState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    agreement_result: Optional[dict]


def _should_continue(state: ModifierState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


async def build_graph(mcp_tools: list):
    """Build the modifier specialist graph with the provided MCP tools."""
    llm = ChatGroq(
        model=settings.specialist_llm_model,
        api_key=settings.groq_api_key,
    ).bind_tools(mcp_tools)

    async def agent_node(state: ModifierState) -> dict:
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(mcp_tools)

    graph = StateGraph(ModifierState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
