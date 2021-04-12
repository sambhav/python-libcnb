"""The primary entrypoint for the build and detect phases."""
import sys
from pathlib import Path

from libcnb._build import Builder, build
from libcnb._detect import Detector, detect


def _get_executable_type() -> str:
    return Path(sys.argv[0]).name


def run(detector: Detector, builder: Builder) -> None:
    """Combines the invocation of both build and detect into a single entry point.

    Calling run from an executable with a name matching "detect" or
    "builder" will result in the matching detector or builder being called respectively.

    Args:
        detector: The definition of a callback that can be invoked when the
            detect function is executed. Buildpack authors should implement a detector
            that performs the specific detect phase operations for a buildpack. It should be
            a callable that takes in a DetectContext and returns a DetectResult.
        builder: The definition of a callback that can be invoked when the
            build function is executed. Buildpack authors should implement a builder
            that performs the specific detect phase operations for a buildpack. It should be
            a callable that takes in a BuildContext and returns a BuildResult.
    """
    executable_type = _get_executable_type()
    if executable_type == "build":
        return build(builder)
    elif executable_type == "detect":
        return detect(detector)
    raise Exception(f"{executable_type} is not a supported executable type.")
