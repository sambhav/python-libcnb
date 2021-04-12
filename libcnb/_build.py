"""Classes and functions related to the build phase."""
import argparse
import os
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Union

from packaging.version import parse
from pydantic import BaseModel, validator
from pydantic.fields import ModelField

from libcnb._buildpack import Buildpack
from libcnb._layers import Layer, Layers
from libcnb._output import BuildMetadata, LaunchMetadata, Store
from libcnb._plan import BuildpackPlan
from libcnb._platform import Platform

MIN_BUILDPACK_API = parse("0.6")


def _get_build_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the build phase of the buildpack.")
    parser.add_argument("layers", type=Path, help="path to the layers directory")
    parser.add_argument("platform", type=Path, help="path to the platform directory")
    parser.add_argument("plan", type=Path, help="path to the output build plan TOML file.")
    return parser.parse_args(args=args)


class BuildContext(BaseModel):
    """BuildContext contains the inputs to build.

    Attributes:
        application_dir: The location of the application source code as provided by the lifecycle.
        buildpack: Metadata about the buildpack, from buildpack.toml.
        layers: The layers available to the buildpack. Also exposes a
            convinience function `get` to create or load a layer in the
            appropriate layers directory.
        store: The metadata that is persisted even across cache cleaning.
        plan: The buildpack plan provided to the buildpack.
        platform: The contents of the platform.
        stack_id: The ID of the stack.
    """

    application_dir: Path
    buildpack: Buildpack
    layers: Layers
    store: Store
    plan: BuildpackPlan
    platform: Platform
    stack_id: str

    @validator("buildpack", "platform", "store", "plan", pre=True)
    def _validate_buildpack(cls, value: Union[Any, Path, str], field: ModelField) -> Any:
        if isinstance(value, field.type_):
            return value
        if isinstance(value, (str, Path)):
            path = Path(value)
            return field.type_.from_path(path)
        raise ValueError(f"Invalid type {type(value)} for {field.name}")


class BuildResult(BaseModel):
    """BuildResult contains the results of build phase.

    Attributes:
        layers: The collection of LayerCreators contributed by the buildpack.
        store: The metadata that is persisted even across cache cleaning.
        launch_metadata: The metadata that will be exported to launch.toml.
            Allows configuring labels, processes, slices and BOM for the app image.
        build_metadata: The metadata that will be exported to build.toml.
            Allows exporting the build BOM and unmet dependencies.
    """

    layers: List[Layer] = []
    store: Store = Store()
    launch_metadata: LaunchMetadata = LaunchMetadata()
    build_metadata: BuildMetadata = BuildMetadata()

    def to_path(self, path: Union[str, Path]) -> None:
        """Exports the build result to the filesystem.

        Arguments:
            path: Path to the layers directory.
        """
        path = Path(path)
        for layer in self.layers:
            layer.dump()
        preserved_tomls = {layer.name for layer in self.layers}
        preserved_tomls.add("store")
        for toml_file in path.glob("*.toml"):
            if toml_file.stem not in preserved_tomls:
                toml_file.unlink()
        if self.store:
            self.store.to_path(path / "store.toml")
        if self.launch_metadata:
            self.launch_metadata.to_path(path / "launch.toml")
        if self.build_metadata:
            self.build_metadata.to_path(path / "build.toml")


Builder = Callable[[BuildContext], BuildResult]


def build(builder: Builder) -> None:
    """An implementation of the build phase according to the Cloud Native Buildpacks specification.

    Args:
        builder: The definition of a callback that can be invoked when the
            build function is executed. Buildpack authors should implement a builder
            that performs the specific detect phase operations for a buildpack. It should be
            a callable that takes in a BuildContext and returns a BuildResult.
    """
    args = _get_build_args()
    try:
        stack_id = os.environ["CNB_STACK_ID"]
    except KeyError:
        raise Exception("CNB_STACK_ID is not set")

    try:
        buildpack_dir = os.environ["CNB_BUILDPACK_DIR"]
    except KeyError:
        raise Exception("CNB_BUILDPACK_DIR is not set")

    context = BuildContext(
        application_dir=Path(".").absolute(),
        buildpack=buildpack_dir,  # type: ignore
        platform=args.platform,
        layers=args.layers,
        plan=args.plan,
        store=(args.layers / "store.toml"),
        stack_id=stack_id,
    )
    if parse(context.buildpack.api) < MIN_BUILDPACK_API:
        raise Exception(
            "This version of libcnb is only compatible with buildpack API 0.6 or greater"
        )
    result = builder(context)
    result.to_path(args.layers)
    return
