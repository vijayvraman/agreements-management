"""Creator specialist LangGraph agent — creates new agreements using MCP tools."""

from typing import Annotated, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from agreements.config import settings

# MCP tool subsets for the creator specialist
_CREATOR_TOOLS = ["database_create_agreement", "template_list_templates",
                  "template_get_template", "template_render_template",
                  "document_export_to_pdf"]


class CreatorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    agreement_result: Optional[dict]


def _should_continue(state: CreatorState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


async def build_graph(mcp_tools: list):
    """Build the creator specialist graph with the provided MCP tools."""
    llm = ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
    ).bind_tools(mcp_tools)

    async def agent_node(state: CreatorState) -> dict:
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(mcp_tools)

    graph = StateGraph(CreatorState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
