"""Async A2A client wrapper for calling specialist agents."""

import httpx
from a2a.client import A2ACardResolver, A2AClient, create_text_message_object
from a2a.types import MessageSendParams, SendMessageRequest


async def call_specialist(agent_url: str, task_input: str) -> str:
    """Send a task to a specialist A2A agent and return its text response.

    Args:
        agent_url: Base URL of the specialist agent (e.g. http://localhost:8001).
        task_input: Natural-language task description for the specialist.

    Returns:
        Text response from the specialist agent.
    """
    async with httpx.AsyncClient(timeout=120.0) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=agent_url)
        agent_card = await resolver.get_agent_card()

        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        message = create_text_message_object(content=task_input)
        request = SendMessageRequest(
            id=_new_id(),
            params=MessageSendParams(message=message),
        )

        response = await client.send_message(request=request)

    result = response.root.result  # Task | Message
    return _extract_text(result)


def _new_id() -> str:
    import uuid
    return str(uuid.uuid4())


def _extract_text(result) -> str:
    """Extract plain text from a Task or Message result."""
    from a2a.types import Message, Task

    if isinstance(result, Message):
        return _text_from_message(result)

    if isinstance(result, Task):
        # Task.result is an optional Artifact; fall back to status message
        if result.status and result.status.message:
            return _text_from_message(result.status.message)
        return f"Task {result.id} completed with status {result.status.state if result.status else 'unknown'}"

    return str(result)


def _text_from_message(message) -> str:
    texts = []
    for part in (message.parts or []):
        root = getattr(part, "root", part)
        if hasattr(root, "text"):
            texts.append(root.text)
    return "\n".join(texts) if texts else ""
