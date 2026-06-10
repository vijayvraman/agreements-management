"""TaskRunner — sequentially executes a list of LAB tasks with per-task DB isolation."""

from eval.harness.adapter import AgreementsAgentAdapter, TaskResult
from eval.tasks.base import LABTask


class TaskRunner:
    """Runs tasks one at a time to preserve module-level patch isolation in mock mode."""

    def __init__(self, adapter: AgreementsAgentAdapter, tasks: list[LABTask]):
        self.adapter = adapter
        self.tasks = tasks

    async def run_all(self) -> list[TaskResult]:
        results: list[TaskResult] = []
        for task in self.tasks:
            async with self.adapter.isolated_env(task) as context:
                result = await self.adapter.run_task(task, context)
                results.append(result)
                status = "ERROR" if result.error else "OK"
                print(f"  [{status}] {task.id} ({result.latency_ms:.0f}ms)")
        return results
