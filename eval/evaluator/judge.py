"""LLM judge using Harvey LAB's batched rubric evaluation approach.

All rubric criteria for a task are evaluated in a single Claude Sonnet 4.6 call,
returning structured JSON with pass/fail verdicts and reasoning per criterion.
Uses the anthropic SDK directly to keep judge calls out of LangSmith traces.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import anthropic

from eval.evaluator.prompts import RUBRIC_EVALUATION_PROMPT
from eval.harness.adapter import TaskResult
from eval.tasks.base import LABTask


@dataclass
class RubricResult:
    rubric_id: str
    passed: bool
    reasoning: str


@dataclass
class TaskEvaluation:
    task_id: str
    rubric_results: list[RubricResult]
    all_pass: bool    # True iff every required rubric passed
    partial_pass: bool  # True iff at least one rubric passed


class LLMJudge:
    """Evaluates task outputs against rubric criteria using Claude Sonnet 4.6."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self._client = anthropic.AsyncAnthropic()
        self._model = model

    async def evaluate(self, task: LABTask, result: TaskResult) -> TaskEvaluation:
        """Evaluate all rubrics for a task in a single batched LLM call."""
        if result.error:
            rubric_results = [
                RubricResult(r.id, False, f"Task errored: {result.error}")
                for r in task.rubrics
            ]
            return TaskEvaluation(
                task_id=task.id,
                rubric_results=rubric_results,
                all_pass=False,
                partial_pass=False,
            )

        rubrics_text = "\n".join(
            f"  - id={r.id} (required={r.required}): {r.criterion}"
            for r in task.rubrics
        )

        prompt = RUBRIC_EVALUATION_PROMPT.format(
            instruction=task.instruction,
            expected_description=task.expected_output_description,
            actual_output=result.actual_output,
            rubrics=rubrics_text,
        )

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=(
                "You are a precise legal AI evaluator. "
                "Return only the JSON array requested — no extra text."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        rubric_results = self._parse_response(task, raw_text)
        return self._build_evaluation(task, rubric_results)

    def _parse_response(self, task: LABTask, raw_text: str) -> list[RubricResult]:
        """Parse LLM JSON response into RubricResult list, falling back gracefully."""
        try:
            parsed = json.loads(raw_text.strip())
            results = []
            for item in parsed:
                results.append(RubricResult(
                    rubric_id=item["id"],
                    passed=bool(item["passed"]),
                    reasoning=item.get("reasoning", ""),
                ))
            return results
        except (json.JSONDecodeError, KeyError, TypeError):
            # If parsing fails, mark all rubrics as failed with the raw response
            return [
                RubricResult(r.id, False, f"Judge parse error. Raw: {raw_text[:200]}")
                for r in task.rubrics
            ]

    def _build_evaluation(
        self, task: LABTask, rubric_results: list[RubricResult]
    ) -> TaskEvaluation:
        results_by_id = {r.rubric_id: r for r in rubric_results}

        all_pass = all(
            results_by_id.get(r.id, RubricResult(r.id, False, "missing")).passed
            for r in task.rubrics
            if r.required
        )
        partial_pass = any(r.passed for r in rubric_results)

        return TaskEvaluation(
            task_id=task.id,
            rubric_results=rubric_results,
            all_pass=all_pass,
            partial_pass=partial_pass,
        )
