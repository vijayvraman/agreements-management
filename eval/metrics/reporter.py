"""MetricsReporter — aggregates evaluation results into Harvey LAB-style metrics.

Primary metric: all-pass rate (tasks where every required rubric passed).
Secondary: partial-pass rate, latency, per-intent breakdown, error count.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from eval.evaluator.judge import TaskEvaluation
from eval.harness.adapter import TaskResult


@dataclass
class IntentSummary:
    intent: str
    total: int = 0
    all_pass: int = 0
    partial_pass: int = 0
    errors: int = 0
    all_pass_rate: float = 0.0
    partial_pass_rate: float = 0.0


@dataclass
class EvalSummary:
    total_tasks: int
    all_pass_count: int
    partial_pass_count: int
    zero_pass_count: int
    error_count: int
    all_pass_rate: float
    partial_pass_rate: float
    mean_latency_ms: float
    p95_latency_ms: float
    by_intent: dict[str, IntentSummary] = field(default_factory=dict)


class MetricsReporter:
    def compute(
        self,
        evaluations: list[TaskEvaluation],
        results: list[TaskResult],
        tasks_by_id: dict,
    ) -> EvalSummary:
        result_map = {r.task_id: r for r in results}
        latencies = [r.latency_ms for r in results if not r.error]

        all_pass_count = sum(1 for e in evaluations if e.all_pass)
        partial_pass_count = sum(1 for e in evaluations if e.partial_pass and not e.all_pass)
        zero_pass_count = sum(1 for e in evaluations if not e.partial_pass and not e.all_pass)
        error_count = sum(1 for r in results if r.error)
        total = len(evaluations)

        mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_latency = _percentile(sorted(latencies), 0.95) if latencies else 0.0

        by_intent: dict[str, IntentSummary] = {}
        for eval_ in evaluations:
            task = tasks_by_id.get(eval_.task_id)
            intent = task.intent if task else "unknown"
            if intent not in by_intent:
                by_intent[intent] = IntentSummary(intent=intent)
            s = by_intent[intent]
            s.total += 1
            if eval_.all_pass:
                s.all_pass += 1
            if eval_.partial_pass:
                s.partial_pass += 1
            result = result_map.get(eval_.task_id)
            if result and result.error:
                s.errors += 1

        for s in by_intent.values():
            if s.total > 0:
                s.all_pass_rate = round(s.all_pass / s.total, 4)
                s.partial_pass_rate = round(s.partial_pass / s.total, 4)

        return EvalSummary(
            total_tasks=total,
            all_pass_count=all_pass_count,
            partial_pass_count=partial_pass_count,
            zero_pass_count=zero_pass_count,
            error_count=error_count,
            all_pass_rate=round(all_pass_count / total, 4) if total else 0.0,
            partial_pass_rate=round(partial_pass_count / total, 4) if total else 0.0,
            mean_latency_ms=round(mean_latency, 1),
            p95_latency_ms=round(p95_latency, 1),
            by_intent=by_intent,
        )

    def print_report(self, summary: EvalSummary) -> None:
        print("\n" + "=" * 60)
        print("  AGREEMENTS AGENT EVALUATION — Harvey LAB-style Report")
        print("=" * 60)
        print(f"  Total tasks:       {summary.total_tasks}")
        print(f"  All-pass (primary): {summary.all_pass_count}/{summary.total_tasks}  "
              f"({summary.all_pass_rate:.1%})")
        print(f"  Partial-pass:      {summary.partial_pass_count}/{summary.total_tasks}  "
              f"({summary.partial_pass_rate:.1%})")
        print(f"  Zero-pass:         {summary.zero_pass_count}")
        print(f"  Errors:            {summary.error_count}")
        print(f"  Mean latency:      {summary.mean_latency_ms:.0f}ms")
        print(f"  P95 latency:       {summary.p95_latency_ms:.0f}ms")
        if summary.by_intent:
            print("\n  By intent:")
            for intent, s in sorted(summary.by_intent.items()):
                print(f"    {intent:10s}  all-pass={s.all_pass_rate:.1%}  "
                      f"({s.all_pass}/{s.total})  errors={s.errors}")
        print("=" * 60 + "\n")

    def print_task_detail(
        self,
        evaluations: list[TaskEvaluation],
        results: list[TaskResult],
    ) -> None:
        result_map = {r.task_id: r for r in results}
        for eval_ in evaluations:
            result = result_map.get(eval_.task_id)
            status = "ALL-PASS" if eval_.all_pass else ("PARTIAL" if eval_.partial_pass else "FAIL")
            print(f"\n  [{status}] {eval_.task_id}")
            if result and result.error:
                print(f"    ERROR: {result.error}")
            else:
                for rr in eval_.rubric_results:
                    mark = "✓" if rr.passed else "✗"
                    print(f"    {mark} {rr.rubric_id}: {rr.reasoning}")

    def save_json(
        self,
        summary: EvalSummary,
        evaluations: list[TaskEvaluation],
        results: list[TaskResult],
        path: Path,
    ) -> None:
        result_map = {r.task_id: r for r in results}

        task_details = []
        for eval_ in evaluations:
            result = result_map.get(eval_.task_id)
            task_details.append({
                "task_id": eval_.task_id,
                "all_pass": eval_.all_pass,
                "partial_pass": eval_.partial_pass,
                "latency_ms": result.latency_ms if result else None,
                "error": result.error if result else None,
                "instruction": result.instruction if result else None,
                "actual_output": result.actual_output if result else None,
                "rubric_results": [
                    {"id": rr.rubric_id, "passed": rr.passed, "reasoning": rr.reasoning}
                    for rr in eval_.rubric_results
                ],
            })

        output = {
            "summary": {
                "total_tasks": summary.total_tasks,
                "all_pass_count": summary.all_pass_count,
                "all_pass_rate": summary.all_pass_rate,
                "partial_pass_rate": summary.partial_pass_rate,
                "mean_latency_ms": summary.mean_latency_ms,
                "p95_latency_ms": summary.p95_latency_ms,
                "error_count": summary.error_count,
                "by_intent": {
                    intent: {
                        "all_pass_rate": s.all_pass_rate,
                        "all_pass": s.all_pass,
                        "total": s.total,
                        "errors": s.errors,
                    }
                    for intent, s in summary.by_intent.items()
                },
            },
            "tasks": task_details,
        }

        Path(path).write_text(json.dumps(output, indent=2))
        print(f"  Results saved to {path}")


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = int(p * len(sorted_values))
    idx = min(idx, len(sorted_values) - 1)
    return sorted_values[idx]
