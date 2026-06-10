"""Harvey LAB-style task schema for the agreements management evaluation suite."""

from dataclasses import dataclass, field


@dataclass
class LABRubric:
    """A single binary pass/fail evaluation criterion."""
    id: str
    criterion: str
    required: bool = True  # if True, failure here fails the task's all-pass rate


@dataclass
class LABEnvironment:
    """Pre-existing state injected into the database before a task runs."""
    seed_agreements: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class LABTask:
    """A single evaluation task mirroring the Harvey Legal Agent Benchmark format."""
    id: str
    intent: str                           # "create" | "query" | "modify"
    instruction: str                      # sent verbatim as ChatRequest.message
    environment: LABEnvironment
    expected_output_description: str      # narrative description for the LLM judge
    rubrics: list[LABRubric]
