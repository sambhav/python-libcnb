from pathlib import Path
from typing import Any, Dict, List, Union

import toml
from pydantic import BaseModel, Field, validator


class License(BaseModel):
    type_: str = Field(alias="type", default="")
    uri: str = ""


class BuildpackInfo(BaseModel):

    id: str
    version: str
    name: str = ""
    homepage: str = ""
    clear_env: bool = Field(alias="clear-env", default=False)
    description: str = ""
    keywords: List[str] = []
    licenses: List[License] = []


class BuildpackStack(BaseModel):
    id: str
    mixins: List[str] = []


class BuildpackGroupEntry(BaseModel):
    id: str
    version: str
    optional: bool = False


class BuildpackGroup(BaseModel):
    group: List[BuildpackGroupEntry] = []


class Buildpack(BaseModel):
    api: str
    info: BuildpackInfo = Field(alias="buildpack")
    path: Path
    stacks: List[BuildpackStack] = []
    metadata: Dict[str, Any] = {}
    order: List[BuildpackGroup] = []

    @classmethod
    def from_toml(cls, path: Union[str, Path]):
        path = Path(path)
        data = toml.loads(path.read_text())
        data["path"] = path.absolute()
        return cls.parse_obj(data)
