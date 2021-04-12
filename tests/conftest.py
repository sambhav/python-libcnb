from pathlib import Path

import pytest

import libcnb


@pytest.fixture
def mock_layers(tmp_path):
    yield libcnb.Layers(path=tmp_path)


@pytest.fixture
def mock_layer(mock_layers):
    layer: libcnb.Layer = mock_layers.get("test")
    layer.launch = True
    layer.cache = True
    layer.metadata["test"] = 1
    layer.profile["test"] = "test"
    layer.shared_env.append("VAR", "test", ":")
    layer.shared_env.prepend("VAR1", "test", ":")
    layer.shared_env.default("VAR2", "test")
    layer.shared_env.override("VAR3", "test")
    layer.launch_env.default("TT", "1")
    layer.process_launch_envs["process"] = libcnb.Environment({"TEST.default": "1"})
    layer.process_profiles["process"] = libcnb.Profile({"test": "test"})
    layer.dump()
    yield layer, layer.name, mock_layers


@pytest.fixture
def mock_platform_path():
    yield Path("tests") / "testdata" / "platform"


@pytest.fixture
def mock_buildpack_path():
    yield Path("tests") / "testdata" / "buildpack"


@pytest.fixture
def mock_buildpack_plan(tmp_path):
    yield tmp_path / "plan.toml"
