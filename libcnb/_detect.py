"""Classes and functions related to the detect phase."""
import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Union

import toml
from packaging.version import parse
from pydantic import BaseModel, Field, validator
from pydantic.fields import ModelField

from libcnb._buildpack import Buildpack
from libcnb._plan import BuildPlan, BuildPlanProvide, BuildPlanRequire
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
            path = Path(value).absolute()
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


class _BuildPlans(BaseModel):
    provides: List[BuildPlanProvide]
    requires: List[BuildPlanRequire]
    or_: List[BuildPlan] = Field(alias="or", default=[])

    class Config:  # noqa: D101, D106
        allow_population_by_field_name = True


def _export_build_plans(plans: List[BuildPlan], path: Path) -> None:
    path.write_text(
        toml.dumps(
            _BuildPlans(provides=plans[0].provides, requires=plans[0].requires, or_=plans[1:]).dict(
                by_alias=True
            )
        )
    )


def detect(detector: Detector) -> None:
    """An implementation of the detect phase according to the Cloud Native Buildpacks specification.

    Args:
        detector: The definition of a callback that can be invoked when the
            detect function is executed. Buildpack authors should implement a detector
            that performs the specific detect phase operations for a buildpack. It should be
            a callable that takes in a DetectContext and returns a DetectResult.
    """
    args = _get_detect_args()
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
            f"This version of libcnb is only compatible with buildpack API {MIN_BUILDPACK_API} or greater"
        )
    result = detector(context)
    if not result.passed:
        sys.exit(100)
    if result.plans:
        _export_build_plans(result.plans, args.plan)
    return
