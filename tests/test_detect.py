import sys
from pathlib import Path

import pytest
import toml

import libcnb


def detect_pass(context):
    return libcnb.DetectResult(passed=True)


def detect_fail(context):
    return libcnb.DetectResult(passed=False)


@pytest.fixture
def mock_detect_context(
    mock_platform_path, mock_buildpack_plan_path, monkeypatch, mock_buildpack_path
):
    monkeypatch.setattr(
        "sys.argv", ["detect", str(mock_platform_path), str(mock_buildpack_plan_path)]
    )
    monkeypatch.setenv("CNB_BUILDPACK_DIR", str(mock_buildpack_path))
    monkeypatch.setenv("CNB_STACK_ID", "test")
    yield mock_platform_path, mock_buildpack_plan_path, mock_buildpack_path, "test"


@pytest.mark.parametrize(
    "detector, passed",
    [
        (detect_pass, True),
        (detect_fail, False),
    ],
)
def test_detect_exit(detector, passed, mock_detect_context):
    if not passed:
        with pytest.raises(SystemExit) as exit:
            libcnb.detect(detector)
        assert exit.value.code == 100
    else:
        libcnb.detect(detector)


def test_detect_values(mock_detect_context):
    # GIVEN
    platform_path, plan, buildpack_path, stack_id = mock_detect_context
    # WHEN
    def detector(context: libcnb.DetectContext):
        assert context.application_dir == Path(".").absolute()
        assert context.platform.path == platform_path.absolute()
        assert context.buildpack.path == buildpack_path.absolute()
        assert context.stack_id == stack_id
        return libcnb.DetectResult(
            passed=True,
            plans=[
                libcnb.BuildPlan(provides=[libcnb.BuildPlanProvide.parse_obj({"name": "test"})]),
                libcnb.BuildPlan(
                    provides=[libcnb.BuildPlanProvide.parse_obj({"name": "test-another"})],
                    requires=[
                        libcnb.BuildPlanRequire.parse_obj(
                            {"name": "require", "metadata": {"key": "value"}}
                        )
                    ],
                ),
            ],
        )

    libcnb.detect(detector)
    # THEN
    assert toml.loads(plan.read_text()) == {
        "requires": [],
        "provides": [{"name": "test"}],
        "or": [
            {
                "provides": [{"name": "test-another"}],
                "requires": [{"name": "require", "metadata": {"key": "value"}}],
            }
        ],
    }


def test_detect_errors_on_missing_stack(mock_detect_context, monkeypatch):
    # GIVEN
    detector = detect_pass
    # WHEN
    monkeypatch.delenv("CNB_STACK_ID")
    # THEN
    with pytest.raises(Exception, match="CNB_STACK_ID is not set"):
        libcnb.detect(detector)


def test_detect_errors_on_missing_buildpack_path(mock_detect_context, monkeypatch):
    # GIVEN
    detector = detect_pass
    # WHEN
    monkeypatch.delenv("CNB_BUILDPACK_DIR")
    # THEN
    with pytest.raises(Exception, match="CNB_BUILDPACK_DIR is not set"):
        libcnb.detect(detector)


def test_detect_errors_on_old_api(mock_detect_context, monkeypatch, mock_old_buildpack_path):
    # GIVEN
    detector = detect_pass
    # WHEN
    monkeypatch.setenv("CNB_BUILDPACK_DIR", str(mock_old_buildpack_path))
    print(sys.argv)
    # THEN
    with pytest.raises(
        Exception,
        match="This version of libcnb is only compatible with buildpack API .* or greater",
    ):
        libcnb.detect(detector)


def test_detect_context(mock_buildpack_path, mock_platform_path):
    # GIVEN
    context_input = {
        "application_dir": Path(".").absolute(),
        "buildpack": libcnb.Buildpack.from_path(mock_buildpack_path),
        "platform": libcnb.Platform.from_path(mock_platform_path),
        "stack_id": "test",
    }
    # WHEN
    context: libcnb.DetectContext = libcnb.DetectContext.parse_obj(context_input)
    # THEN
    assert context.application_dir == Path(".").absolute()
    assert context.buildpack.path == mock_buildpack_path.absolute()
    assert context.platform.path == mock_platform_path.absolute()
    assert context.stack_id == "test"


def test_detect_context_error(mock_buildpack_path, mock_platform_path):
    # GIVEN
    context_input = {
        "application_dir": Path(".").absolute(),
        "buildpack": 1,
        "platform": 1,
        "stack_id": "test",
    }
    # THEN
    with pytest.raises(ValueError, match="Invalid type"):
        libcnb.DetectContext.parse_obj(context_input)
