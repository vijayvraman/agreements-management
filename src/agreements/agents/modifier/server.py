"""A2A server for the Modifier specialist agent (port 8003)."""

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agreements.agents.modifier.executor import ModifierAgentExecutor

agent_card = AgentCard(
    name="Agreement Modifier Agent",
    description="Updates, deletes, and modifies existing legal agreements.",
    url="http://localhost:8003/",
    version="1.0.0",
    skills=[
        AgentSkill(
            id="modify_agreement",
            name="Modify Agreement",
            description="Update fields, change status, delete, or re-render an existing agreement.",
            tags=["modify", "update", "delete", "agreement", "legal"],
        ),
    ],
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

_handler = DefaultRequestHandler(
    agent_executor=ModifierAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=_handler,
).build()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
