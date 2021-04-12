"""Classes and functions binding the various plan I/O during the detect/build phase to a Python API."""
from pathlib import Path
from typing import Any, Dict, List, Union

import toml
from pydantic import BaseModel


class BuildPlanProvide(BaseModel):
    """BuildPlanProvide represents a dependency provided by a buildpack.

    Attributes:
        name: The name of the dependency.
    """

    name: str


class BuildPlanRequire(BaseModel):
    """BuildPlanRequire represents a dependency required by a buildpack.

    Attributes:
        name: The name of the dependency.
        metadata: The optional metadata for the dependency.
    """

    name: str
    metadata: Dict[str, Any] = {}


class BuildPlan(BaseModel):
    """BuildPlan represents the provisions and requirements of a buildpack during detection.

    Attributes:
        provides: The dependencies provided by the buildpack.
        requires: The dependencies required by the buildpack.
    """

    provides: List[BuildPlanProvide] = []
    requires: List[BuildPlanRequire] = []


class BuildpackPlanEntry(BaseModel):
    """BuildpackPlanEntry represents an entry in the buildpack plan.

    Attributes:
        name: The name of the entry.
        metadata: The optional metadata of the entry.
    """

    name: str
    metadata: Dict[str, Any] = {}


class BuildpackPlan(BaseModel):
    """BuildpackPlan represents a buildpack plan input during the build process.

    Attributes:
        entries: All the buildpack plan entries.
    """

    entries: List[BuildpackPlanEntry] = []

    @classmethod
    def from_path(cls, path: Union[Path, str]) -> "BuildpackPlan":
        """Loads a buildpack plan from the path to a TOML file."""
        return cls.parse_obj(toml.loads(Path(path).read_text()))
