"""A2A AgentExecutor for the Modifier specialist."""

from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from agreements.agents.modifier.graph import build_graph

_MCP_CONFIG = {
    "database": {
        "transport": "stdio",
        "command": "python",
        "args": ["src/agreements/mcp_servers/database_server.py"],
    },
    "templates": {
        "transport": "stdio",
        "command": "python",
        "args": ["src/agreements/mcp_servers/template_server.py"],
    },
    "documents": {
        "transport": "stdio",
        "command": "python",
        "args": ["src/agreements/mcp_servers/document_server.py"],
    },
}

_ALLOWED_TOOL_PREFIXES = (
    "get_agreement",
    "update_agreement",
    "delete_agreement",
    "render_template",
    "export_to_pdf",
    "import_document",
)


class ModifierAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()

        try:
            async with MultiServerMCPClient(_MCP_CONFIG) as mcp_client:
                all_tools = mcp_client.get_tools()
                tools = [t for t in all_tools if any(t.name.endswith(p) for p in _ALLOWED_TOOL_PREFIXES)]
                graph = await build_graph(tools)

            result = await graph.ainvoke({"messages": [HumanMessage(content=user_input)]})
            last_message = result["messages"][-1]
            reply_text = last_message.content if hasattr(last_message, "content") else str(last_message)
        except Exception as e:
            reply_text = f"Modifier agent error: {e}"

        await event_queue.enqueue_event(new_agent_text_message(reply_text))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
