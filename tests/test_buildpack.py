from pathlib import Path

import pytest

import libcnb


@pytest.fixture
def mock_buildpack_path():
    yield Path("tests") / "testdata" / "buildpack"


def test_buildpack_serialization(mock_buildpack_path):
    # WHEN
    buildpack = libcnb.Buildpack.from_path(mock_buildpack_path)
    # THEN
    assert buildpack == {
        "api": "0.6",
        "info": {
            "id": "test-id",
            "version": "1.1.1",
            "name": "test-name",
            "homepage": "",
            "clear_env": True,
            "description": "A test buildpack",
            "keywords": ["test", "buildpack"],
            "licenses": [
                {"type_": "Apache-2.0", "uri": "https://spdx.org/licenses/Apache-2.0.html"},
                {"type_": "Apache-1.1", "uri": "https://spdx.org/licenses/Apache-1.1.html"},
            ],
        },
        "path": Path("tests/testdata/buildpack").absolute(),
        "stacks": [{"id": "test-id", "mixins": ["test-name"]}],
        "metadata": {"test-key": "test-value"},
        "order": [{"group": [{"id": "test-id", "version": "2.2.2", "optional": True}]}],
    }
