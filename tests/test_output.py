from pathlib import Path

import pytest
import toml

import libcnb


@pytest.fixture
def mock_store_path():
    yield Path("tests") / "testdata" / "store.toml"


@pytest.fixture
def mock_launch_path():
    yield Path("tests") / "testdata" / "launch.toml"


@pytest.fixture
def mock_build_path():
    yield Path("tests") / "testdata" / "build.toml"


def test_store_serialization(mock_store_path, tmp_path):
    # GIVEN
    store = libcnb.Store.from_path(mock_store_path)
    # WHEN
    store.to_path(tmp_path / "store.toml")
    # THEN
    assert toml.loads(mock_store_path.read_text()) == toml.loads(
        (tmp_path / "store.toml").read_text()
    )


@pytest.mark.parametrize("cls", [libcnb.Store, libcnb.LaunchMetadata, libcnb.BuildMetadata])
def test_serialization_empty(cls, tmp_path):
    # GIVEN
    store = cls()
    output_path = tmp_path / "output.toml"
    # WHEN
    store.to_path(output_path)
    # THEN
    assert not output_path.exists()


def test_launch_metadata_serialization(mock_launch_path, tmp_path):
    # GIVEN
    launch_metadata = libcnb.LaunchMetadata.from_path(mock_launch_path)
    # WHEN
    launch_metadata.to_path(tmp_path / "launch.toml")
    # THEN
    assert toml.loads(mock_launch_path.read_text()) == toml.loads(
        (tmp_path / "launch.toml").read_text()
    )


def test_build_metadata_serialization(mock_build_path, tmp_path):
    # GIVEN
    build_metadata = libcnb.BuildMetadata.from_path(mock_build_path)
    # WHEN
    build_metadata.to_path(tmp_path / "build.toml")
    # THEN
    assert toml.loads(mock_build_path.read_text()) == toml.loads(
        (tmp_path / "build.toml").read_text()
    )
