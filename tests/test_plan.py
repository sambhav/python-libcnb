from pathlib import Path

import pytest

import libcnb


@pytest.fixture
def mock_plan_path():
    yield Path("tests") / "testdata" / "plan.toml"


def test_plan_serialization(mock_plan_path):
    # WHEN
    build_plan = libcnb.BuildpackPlan.from_path(mock_plan_path)
    # THEN
    assert build_plan == {
        "entries": [
            {
                "name": "test-name",
                "metadata": {"test-key": "test-value"},
            },
            {
                "name": "test-name",
                "metadata": {"test-key": "test-value2", "test-key2": "test-value2"},
            },
        ]
    }
