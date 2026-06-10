"""pytest fixtures for running individual eval tasks in isolation.

Usage: pytest eval/ -k "create_nda_complete_001" -v
Note: running `pytest tests/` still only runs the original 19 tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from eval.harness.adapter import AgreementsAgentAdapter
from eval.harness.runner import TaskRunner


@pytest.fixture
def mock_adapter() -> AgreementsAgentAdapter:
    return AgreementsAgentAdapter(mode="mock")


@pytest.fixture
def live_adapter() -> AgreementsAgentAdapter:
    return AgreementsAgentAdapter(mode="live")


@pytest.fixture
def task_runner(mock_adapter: AgreementsAgentAdapter) -> TaskRunner:
    return TaskRunner(mock_adapter, tasks=[])
