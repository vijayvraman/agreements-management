"""Prompt templates for the LLM judge (Harvey LAB-style batched rubric evaluation)."""

RUBRIC_EVALUATION_PROMPT = """\
You are an impartial evaluator assessing an AI agent's response to a legal agreements \
management task. Evaluate each rubric criterion as PASS or FAIL.

TASK INSTRUCTION:
{instruction}

EXPECTED BEHAVIOR:
{expected_description}

ACTUAL AGENT OUTPUT:
{actual_output}

RUBRIC CRITERIA:
{rubrics}

For each criterion, determine PASS or FAIL with a one-sentence justification.
Respond ONLY with a valid JSON array — no extra text, no markdown fencing:
[
  {{"id": "r1", "passed": true, "reasoning": "The response explicitly names Acme Corp."}},
  {{"id": "r2", "passed": false, "reasoning": "Beta Ltd is not mentioned anywhere."}}
]
"""
