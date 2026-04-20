"""Main FastAPI application — exposes POST /agreements/chat and invokes the planner agent."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from agreements.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Agreements Management API",
    description="Multi-agent legal agreements management system",
    version="1.0.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: str | None = None


@app.post("/agreements/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a natural-language request about legal agreements.

    The planner agent classifies the intent (create / query / modify) and
    delegates to the appropriate specialist agent via the A2A protocol.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    from agreements.agents.planner.graph import build_planner_graph

    planner = build_planner_graph()
    result = await planner.ainvoke({"messages": [HumanMessage(content=request.message)]})

    return ChatResponse(
        response=result.get("response", "No response generated."),
        intent=result.get("intent"),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
