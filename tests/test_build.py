import sys
from pathlib import Path

import pytest
import toml

import libcnb


@pytest.fixture
def mock_layers(tmp_path):
    return tmp_path / "layers"


@pytest.fixture
def mock_build_context(
    mock_platform_path, mock_layers, mock_plan, monkeypatch, mock_buildpack_path
):
    monkeypatch.setattr(
        "sys.argv", ["build", str(mock_layers), str(mock_platform_path), str(mock_plan)]
    )
    monkeypatch.setenv("CNB_BUILDPACK_DIR", str(mock_buildpack_path))
    monkeypatch.setenv("CNB_STACK_ID", "test")
    yield mock_layers, mock_platform_path, mock_plan, mock_buildpack_path, "test"


def test_build_values(mock_build_context):
    # GIVEN
    layers_path, platform_path, plan, buildpack_path, stack_id = mock_build_context

    def builder(context: libcnb.BuildContext):
        assert context.application_dir == Path(".").absolute()
        assert context.layers.path == layers_path
        assert context.platform.path == platform_path.absolute()
        assert context.buildpack.path == buildpack_path.absolute()
        assert context.stack_id == stack_id
        layer = context.layers.get("test")
        another_layer = context.layers.get("test-another")
        another_layer.dump()
        assert another_layer.metadata_file.exists()
        layer.metadata["test"] = "1"
        layer.launch = True
        layer.build = True
        layer.launch_env.append("test", "test", ":")
        return libcnb.BuildResult(
            layers=[layer],
            store=libcnb.Store(metadata={"test_store": 1}),
            launch_metadata=libcnb.LaunchMetadata(
                labels=[libcnb.Label(key="test_label", value="test")],
                processes=[libcnb.Process(type_="test", command="test")],
                slices=[libcnb.Slice(paths=[Path("."), Path("*")])],
                bom=[libcnb.BOMEntry(name="test", metadata={"test": 1})],
            ),
            build_metadata=libcnb.BuildMetadata(
                bom=[libcnb.BOMEntry(name="test", metadata={"test": 1})],
                unmet=[libcnb.UnmetPlanEntry(name="unmet")],
            ),
        )

    # WHEN
    libcnb.build(builder)
    # THEN
    assert (layers_path / "test").exists()
    assert not (layers_path / "test-another.toml").exists()
    assert toml.loads((layers_path / "test.toml").read_text()) == {
        "types": {"build": True, "cache": False, "launch": True},
        "metadata": {"test": "1"},
    }
    assert toml.loads((layers_path / "launch.toml").read_text()) == {
        "labels": [{"key": "test_label", "value": "test"}],
        "processes": [
            {"type": "test", "command": "test", "args": [], "direct": False, "default": False}
        ],
        "slices": [{"paths": [".", "*"]}],
        "bom": [{"name": "test", "metadata": {"test": 1}}],
    }
    assert toml.loads((layers_path / "build.toml").read_text()) == {
        "bom": [{"name": "test", "metadata": {"test": 1}}],
        "unmet": [{"name": "unmet"}],
    }
    assert toml.loads((layers_path / "store.toml").read_text()) == {"metadata": {"test_store": 1}}


def test_detect_errors_on_missing_stack(mock_build_context, monkeypatch):
    # GIVEN
    builder = None
    # WHEN
    monkeypatch.delenv("CNB_STACK_ID")
    # THEN
    with pytest.raises(Exception, match="CNB_STACK_ID is not set"):
        libcnb.build(builder)


def test_build_errors_on_missing_buildpack_path(mock_build_context, monkeypatch):
    # GIVEN
    builder = None
    # WHEN
    monkeypatch.delenv("CNB_BUILDPACK_DIR")
    # THEN
    with pytest.raises(Exception, match="CNB_BUILDPACK_DIR is not set"):
        libcnb.build(builder)


def test_build_errors_on_old_api(mock_build_context, monkeypatch, mock_old_buildpack_path):
    # GIVEN
    builder = None
    # WHEN
    monkeypatch.setenv("CNB_BUILDPACK_DIR", str(mock_old_buildpack_path))
    print(sys.argv)
    # THEN
    with pytest.raises(
        Exception,
        match="This version of libcnb is only compatible with buildpack API .* or greater",
    ):
        libcnb.build(builder)


def test_build_context(mock_buildpack_path, mock_platform_path, tmp_path):
    # GIVEN
    context_input = {
        "application_dir": Path(".").absolute(),
        "layers": libcnb.Layers(path=(tmp_path / "layers")),
        "store": libcnb.Store(),
        "plan": libcnb.BuildpackPlan(),
        "buildpack": libcnb.Buildpack.from_path(mock_buildpack_path),
        "platform": libcnb.Platform.from_path(mock_platform_path),
        "stack_id": "test",
    }
    # WHEN
    context: libcnb.BuildContext = libcnb.BuildContext.parse_obj(context_input)
    # THEN
    assert context.application_dir == Path(".").absolute()
    assert context.buildpack.path == mock_buildpack_path.absolute()
    assert context.platform.path == mock_platform_path.absolute()
    assert context.stack_id == "test"


def test_build_context_error(mock_buildpack_path, mock_platform_path, tmp_path):
    # GIVEN
    context_input = {
        "application_dir": Path("."),
        "layers": libcnb.Layers(path=(tmp_path / "layers")),
        "store": libcnb.Store(),
        "plan": libcnb.BuildpackPlan(),
        "buildpack": 1,
        "platform": libcnb.Platform.from_path(mock_platform_path),
        "stack_id": "test",
    }
    # THEN
    with pytest.raises(ValueError, match="Invalid type"):
        libcnb.BuildContext.parse_obj(context_input)
