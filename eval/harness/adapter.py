"""AgreementsAgentAdapter — bridges the LAB task runner to our multi-agent system.

Mock mode: patches the database session factory and A2A client per-task,
then calls the planner graph directly in-process.

Live mode: issues real HTTP requests to the running FastAPI server at port 8000.
"""

import json
import shutil
import sys
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from langchain_core.messages import HumanMessage

from eval.tasks.base import LABTask


@dataclass
class TaskResult:
    task_id: str
    instruction: str
    actual_output: str
    intent_classified: str | None
    latency_ms: float
    error: str | None = None


class AgreementsAgentAdapter:
    """Runs LAB tasks against the agreements management system.

    Args:
        mode: "mock" runs entirely in-process; "live" requires all 4 servers running.
    """

    def __init__(self, mode: Literal["mock", "live"] = "mock"):
        self.mode = mode

    @asynccontextmanager
    async def isolated_env(self, task: LABTask):
        """Provide an isolated database for a single task, then tear it down."""
        if self.mode == "mock":
            async with self._mock_isolated_env(task) as context:
                yield context
        else:
            # Live mode: no isolation — assume the live server manages its own state
            yield {}

    @asynccontextmanager
    async def _mock_isolated_env(self, task: LABTask):
        """Create a fresh temp SQLite DB, patch module state, and seed agreements."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        import agreements.mcp_servers.database_server as db_srv
        import agreements.mcp_servers.document_server as doc_srv
        from agreements.models.agreement import Base

        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / f"eval_{task.id}.db"
        db_url = f"sqlite+aiosqlite:///{db_path}"

        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        with (
            patch.object(db_srv, "AsyncSessionFactory", session_factory),
            patch.object(db_srv, "_db_initialized", True),
            patch.object(doc_srv, "AsyncSessionFactory", session_factory),
            patch.object(doc_srv, "_db_initialized", True),
        ):
            context: dict = {}
            for i, seed in enumerate(task.environment.seed_agreements):
                created_json = await db_srv.create_agreement(
                    title=seed["title"],
                    agreement_type=seed["agreement_type"],
                    parties=seed["parties"],
                    content=seed["content"],
                    status=seed.get("status", "draft"),
                )
                created = json.loads(created_json)
                context[f"seeded_id_{i}"] = created["id"]
                if i == 0:
                    context["seeded_id"] = created["id"]

            yield context

        await engine.dispose()
        shutil.rmtree(tmp_dir, ignore_errors=True)

    async def run_task(self, task: LABTask, context: dict) -> TaskResult:
        """Execute a task and return the result with timing."""
        start = time.monotonic()
        try:
            if self.mode == "mock":
                output, intent = await self._run_mock(task)
            else:
                output, intent = await self._run_live(task)
            latency_ms = (time.monotonic() - start) * 1000
            return TaskResult(
                task_id=task.id,
                instruction=task.instruction,
                actual_output=output,
                intent_classified=intent,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return TaskResult(
                task_id=task.id,
                instruction=task.instruction,
                actual_output="",
                intent_classified=None,
                latency_ms=latency_ms,
                error=str(exc),
            )

    async def _run_mock(self, task: LABTask) -> tuple[str, str | None]:
        """Run the planner graph in-process, intercepting A2A calls with MockAgreementsBackend."""
        from eval.harness.mock_backend import MockAgreementsBackend
        from agreements.agents.planner.graph import build_planner_graph
        from agreements.config import settings

        backend = MockAgreementsBackend()

        url_to_intent = {
            settings.creator_agent_url: "create",
            settings.query_agent_url: "query",
            settings.modifier_agent_url: "modify",
        }

        async def mock_call_specialist(agent_url: str, task_description: str) -> str:
            intent = url_to_intent.get(agent_url, "query")
            return await backend.dispatch(intent, task_description)

        with patch("agreements.a2a.client.call_specialist", new=mock_call_specialist):
            graph = build_planner_graph()
            result = await graph.ainvoke({
                "messages": [HumanMessage(content=task.instruction)]
            })

        response = result.get("response") or result.get("specialist_result", "")
        intent = result.get("intent")
        return str(response), intent

    async def _run_live(self, task: LABTask) -> tuple[str, str | None]:
        """Issue a real HTTP POST to the running FastAPI server."""
        import httpx

        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
            resp = await client.post("/agreements/chat", json={"message": task.instruction})
            resp.raise_for_status()
            data = resp.json()

        return data.get("response", ""), data.get("intent")
