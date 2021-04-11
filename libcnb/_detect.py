import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Union

import toml
from packaging.version import parse
from pydantic import BaseModel, validator
from pydantic.fields import ModelField

from libcnb._buildpack import Buildpack
from libcnb._plan import BuildPlan
from libcnb._platform import Platform

MIN_BUILDPACK_API = parse("0.6")


def _get_detect_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect if the buildpack should be run.")
    parser.add_argument("platform", type=Path, help="path to the platform directory")
    parser.add_argument("plan", type=Path, help="path to the output build plan TOML file.")
    return parser.parse_args(args=args)


class DetectContext(BaseModel):
    """DetectContext contains the inputs to detection.

    Attributes:
        application_dir: The location of the application source code as provided by the lifecycle.
        buildpack: Metadata about the buildpack, from buildpack.toml.
        platform: The contents of the platform.
        stack_id: The ID of the stack.
    """

    application_dir: Path
    buildpack: Buildpack
    platform: Platform
    stack_id: str

    @validator("buildpack", "platform", pre=True)
    def _validate_buildpack(cls, value: Union[Any, Path, str], field: ModelField) -> Any:
        if isinstance(value, field.type_):
            return value
        if isinstance(value, (str, Path)):
            path = Path(value)
            return field.type_.from_path(path)
        raise ValueError(f"Invalid type {type(value)} for {field.name}")


class DetectResult(BaseModel):
    """DetectResult contains the results of detection.

    Attributes:
        passed: Indicates whether detection has passed.
        plans: The build plans contributed by the buildpack.
    """

    passed: bool = False
    plans: List[BuildPlan] = []


Detector = Callable[[DetectContext], DetectResult]


def _export_plans(plans: List[BuildPlan], path: Path) -> None:
    path.write_text(
        toml.dumps(
            {
                "provides": plans[0].provides,
                "requires": plans[0].requires,
                "or": plans[1:],
            }
        )
    )


def detect(detector: Detector, _input_args: Optional[Sequence[str]] = None) -> None:
    """An implementation of the detect phase according to the Cloud Native Buildpacks specification.

    Args:
        detector: The definition of a callback that can be invoked when the
            detect function is executed. Buildpack authors should implement a detector
            that performs the specific detect phase operations for a buildpack. It should be
            a callable that takes in a DetectContext and returns a DetectResult.
    """
    args = _get_detect_args(_input_args or None)
    try:
        stack_id = os.environ["CNB_STACK_ID"]
    except KeyError:
        raise Exception("CNB_STACK_ID is not set")

    try:
        buildpack_dir = os.environ["CNB_BUILDPACK_DIR"]
    except KeyError:
        raise Exception("CNB_BUILDPACK_DIR is not set")

    context = DetectContext(
        application_dir=Path(".").absolute(),
        buildpack=buildpack_dir,  # type: ignore
        platform=args.platform,
        stack_id=stack_id,
    )
    if parse(context.buildpack.api) < MIN_BUILDPACK_API:
        raise Exception(
            "This version of libcnb is only compatible with buildpack API 0.6 or greater"
        )
    result = detector(context)
    if not result.passed:
        sys.exit(100)
    if result.plans:
        _export_plans(result.plans, args.plan)
    return
