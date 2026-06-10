#!/usr/bin/env python3
"""Harvey LAB-style evaluation CLI for the agreements management multi-agent system.

Usage:
    python eval/run_eval.py
    python eval/run_eval.py --mode mock --intent create
    python eval/run_eval.py --mode live --output results.json
    python eval/run_eval.py --intent query --fail-fast
    python eval/run_eval.py --verifier-model claude-opus-4-8
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main(args: argparse.Namespace) -> int:
    from eval.evaluator.judge import LLMJudge
    from eval.harness.adapter import AgreementsAgentAdapter
    from eval.harness.runner import TaskRunner
    from eval.metrics.reporter import MetricsReporter
    from eval.tasks.create_tasks import CREATE_TASKS
    from eval.tasks.modify_tasks import MODIFY_TASKS
    from eval.tasks.query_tasks import QUERY_TASKS

    # Select task subset
    all_tasks = []
    if args.intent in ("create", "all"):
        all_tasks.extend(CREATE_TASKS)
    if args.intent in ("query", "all"):
        all_tasks.extend(QUERY_TASKS)
    if args.intent in ("modify", "all"):
        all_tasks.extend(MODIFY_TASKS)

    if not all_tasks:
        print(f"No tasks for intent '{args.intent}'")
        return 1

    tasks_by_id = {t.id: t for t in all_tasks}

    print(f"\nEvaluating {len(all_tasks)} tasks (mode={args.mode}, intent={args.intent})")
    print("-" * 60)

    adapter = AgreementsAgentAdapter(mode=args.mode)
    runner = TaskRunner(adapter, all_tasks)

    print("\nRunning tasks...")
    results = await runner.run_all()

    print("\nScoring with LLM judge...")
    judge = LLMJudge(model=args.verifier_model)
    evaluations = []
    for task, result in zip(all_tasks, results):
        print(f"  Scoring {task.id}...")
        evaluation = await judge.evaluate(task, result)
        evaluations.append(evaluation)

        if args.fail_fast and not evaluation.all_pass:
            print(f"  [FAIL-FAST] {task.id} did not all-pass — stopping.")
            break

    reporter = MetricsReporter()
    summary = reporter.compute(evaluations, results, tasks_by_id)

    reporter.print_task_detail(evaluations, results)
    reporter.print_report(summary)

    if args.output:
        reporter.save_json(summary, evaluations, results, Path(args.output))

    # Exit code: 0 if all tasks all-passed, 1 otherwise
    return 0 if summary.all_pass_count == len(evaluations) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Harvey LAB-style evaluation for the agreements management agents."
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "live"],
        default="mock",
        help="Execution mode: 'mock' runs in-process (default), 'live' requires running servers.",
    )
    parser.add_argument(
        "--intent",
        choices=["create", "query", "modify", "all"],
        default="all",
        help="Task subset to evaluate (default: all).",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        default=None,
        help="Write full JSON report to this file.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first task that does not all-pass.",
    )
    parser.add_argument(
        "--verifier-model",
        default="claude-sonnet-4-6",
        help="Claude model used by the LLM judge (default: claude-sonnet-4-6).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)
