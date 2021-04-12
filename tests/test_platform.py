from pathlib import Path

import pytest

import libcnb


@pytest.fixture
def mock_platform_path():
    yield Path("tests") / "testdata" / "platform"


def test_platform_serialization(mock_platform_path):
    # WHEN
    platform = libcnb.Platform.from_path(mock_platform_path)
    # THEN
    assert platform.env == {"TEST": "value", "T2": "another value\n\nin\n\nmultiple\n\nlines"}


def test_empty_platform():
    # WHEN
    platform = libcnb.Platform(path="")
    # THEN
    assert platform.env == {}
