"""A2A server for the Creator specialist agent (port 8001)."""

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agreements.agents.creator.executor import CreatorAgentExecutor

agent_card = AgentCard(
    name="Agreement Creator Agent",
    description="Creates new legal agreements (NDA, Service Agreement, Employment, Other) using templates and stores them in the database.",
    url="http://localhost:8001/",
    version="1.0.0",
    skills=[
        AgentSkill(
            id="create_agreement",
            name="Create Agreement",
            description="Draft and persist a new legal agreement from a natural language request.",
            tags=["create", "agreement", "legal", "nda", "contract"],
        ),
    ],
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

_handler = DefaultRequestHandler(
    agent_executor=CreatorAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=_handler,
).build()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
