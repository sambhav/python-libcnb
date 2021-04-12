"""Classes and functions related to the buildpack specific information and metadata."""
from pathlib import Path
from typing import Any, Dict, List, Union

import toml
from pydantic import BaseModel, Field


class License(BaseModel):
    """License contains information about a Software License governing the use or redistribution of a buildpack.

    Attributes:
        type_: The identifier for the license.
            It may use the SPDX 2.1 license expression, but is not limited
            to identifiers in the SPDX Licenses List.
        uri: A string that may be specified in lieu of or in addition to type to point to the license
            if this buildpack is using a nonstandard license.
    """

    type_: str = Field(alias="type", default="")
    uri: str = ""

    class Config:  # noqa: D101, D106
        allow_population_by_field_name = True


class BuildpackInfo(BaseModel):
    """BuildpackInfo is information about the buildpack.

    Attributes:
        id: The id of the buildpack.
        version: The version of the buildpack.
        name: The name of the buildpack.
        homepage: The homepage of the buildpack.
        clear_env: Clears user-defined environment variables when true
            on executions of bin/detect and bin/build.
        description: The string describing the buildpack.
        keywords: A list of words that are associated with the buildpack.
        licenses: A list of buildpack licenses.
    """

    id: str
    version: str
    name: str = ""
    homepage: str = ""
    clear_env: bool = Field(alias="clear-env", default=False)
    description: str = ""
    keywords: List[str] = []
    licenses: List[License] = []


class BuildpackStack(BaseModel):
    """BuildpackStack is a stack supported by the buildpack.

    Attributes:
        id: The id of the stack.
        mixins: The collection of mixins associated with the stack.
    """

    id: str
    mixins: List[str] = []


class BuildpackGroupEntry(BaseModel):
    """BuildpackGroupEntry is a buildpack within in a buildpack order group.

    Attributes:
        id: The id of the buildpack.
        version: The version of the buildpack.
        optional: Whether the buildpack is optional within the buildpack group.
    """

    id: str
    version: str
    optional: bool = False


class BuildpackOrder(BaseModel):
    """BuildpackOrder is an order definition in the buildpack.

    Attributes:
        group: The collection of groups within the order.
    """

    group: List[BuildpackGroupEntry] = []


class Buildpack(BaseModel):
    """Buildpack is the contents of the buildpack.toml file.

    Attributes:
        api: The api version expected by the buildpack.
        info: Information about the buildpack.
        path: The absolute path to the buildpack.
        stacks: The collection of stacks supported by the buildpack.
        metadata: Arbitrary metadata attached to the buildpack.
        order: Collection of buildpack order definitions in the buildpack.
    """

    api: str
    info: BuildpackInfo = Field(alias="buildpack")
    path: Path
    stacks: List[BuildpackStack] = []
    metadata: Dict[str, Any] = {}
    order: List[BuildpackOrder] = []

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "Buildpack":
        """Loads the buildpack information given a path on disk."""
        path = Path(path)
        data = toml.loads((path / "buildpack.toml").read_text())
        data["path"] = path.absolute()
        return cls.parse_obj(data)
