"""A2A server for the Query specialist agent (port 8002)."""

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agreements.agents.query.executor import QueryAgentExecutor

agent_card = AgentCard(
    name="Agreement Query Agent",
    description="Searches, lists, and retrieves legal agreements from the database.",
    url="http://localhost:8002/",
    version="1.0.0",
    skills=[
        AgentSkill(
            id="query_agreements",
            name="Query Agreements",
            description="Search for, list, or retrieve agreements by status, type, party name, or full-text search.",
            tags=["query", "search", "list", "agreement", "legal"],
        ),
    ],
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

_handler = DefaultRequestHandler(
    agent_executor=QueryAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=_handler,
).build()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
