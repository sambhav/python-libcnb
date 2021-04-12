"""Classes and functions binding the various buildpack outputs during the build phase to a Python API."""
from pathlib import Path
from typing import Any, Dict, List, Union

import toml
from pydantic import BaseModel, Field


class Process(BaseModel):
    """Process represents metadata about a type of command that can be run.

    Attributes:
        type_: The type of the process.
        command: The command of the process.
        args: The arguments to the command.
        direct: If set to True the command is exec'd directly by the os (no profile.d scripts run).
        default: If set to True the process type being defined should be the default process type for the app image.
    """

    type_: str = Field(alias="type")
    command: str
    args: List[str] = []
    direct: bool = False
    default: bool = False

    class Config:  # noqa: D101, D106
        allow_population_by_field_name = True


class Label(BaseModel):
    """Label represents an image label.

    Attributes:
        key: The key of the label.
        value: The value of the label.
    """

    key: str
    value: str


class Slice(BaseModel):
    """Slice represents metadata about a slice.

    Attributes:
        paths: The contents of the slice.
    """

    paths: List[str] = []


class BOMEntry(BaseModel):
    """BOMEntry contains a bill of materials entry.

    Attributes:
        name: The name of the entry.
        metadata: The optional metadata of the entry.
    """

    name: str
    metadata: Dict[str, Any] = {}


class UnmetPlanEntry(BaseModel):
    """UnmetPlanEntry denotes an unmet buildpack plan entry.

    When a buildpack returns an UnmetPlanEntry in the BuildResult, any BuildpackPlanEntry
    with a matching name will be provided to subsequent providers.

    Attributes:
        name: The name of the entry.
    """

    name: str


class LaunchMetadata(BaseModel):
    """LaunchMetadata represents the contents of launch.toml.

    Attributes:
        labels: The collection of image labels contributed by the buildpack.
        processes: The collection of process types contributed by the buildpack.
        slices: The collection of process types contributed by the buildpack.
        bom: The collection of entries for the bill of materials.
    """

    labels: List[Label] = []
    processes: List[Process] = []
    slices: List[Slice] = []
    bom: List[BOMEntry] = []

    def to_path(self, path: Union[str, Path]) -> None:
        """Export LaunchMetadata to the TOML file at the given path."""
        Path(path).write_text(toml.dumps(self.dict(by_alias=True)))

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "LaunchMetadata":
        """Creates a LaunchMetadata from the TOML file at the given path."""
        return cls.parse_obj(toml.loads(Path(path).read_text()))

    def __bool__(self) -> bool:
        """Returns true if there is any content to be written to the output toml file."""
        return bool(self.labels or self.processes or self.slices or self.bom)


class BuildMetadata(BaseModel):
    """BuildMetadata represents the contents of build.toml.

    Attributes:
        bom: The collection of entries for the bill of materials.
        unmet: The collection of buildpack plan entries that should be passed through to subsequent providers.
    """

    bom: List[BOMEntry] = []
    unmet: List[UnmetPlanEntry] = []

    def to_path(self, path: Union[str, Path]) -> None:
        """Export LaunchMetadata to the TOML file at the given path."""
        Path(path).write_text(toml.dumps(self.dict(by_alias=True)))

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "BuildMetadata":
        """Creates a BuildMetadata from the TOML file at the given path."""
        return cls.parse_obj(toml.loads(Path(path).read_text()))

    def __bool__(self) -> bool:
        """Returns true if there is any content to be written to the output toml file."""
        return bool(self.bom or self.unmet)


class Store(BaseModel):
    """Store represents the contents of store.toml.

    Attributes:
        metadata: Represents the persistent metadata.
    """

    metadata: Dict[str, Any] = {}

    def to_path(self, path: Union[str, Path]) -> None:
        """Export Store to the TOML file at the given path."""
        Path(path).write_text(toml.dumps(self.dict(by_alias=True)))

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "Store":
        """Creates a Store from the TOML file at the given path."""
        return cls.parse_obj(toml.loads(Path(path).read_text()))

    def __bool__(self) -> bool:
        """Returns true if there is any content to be written to the output toml file."""
        return bool(self.metadata)
