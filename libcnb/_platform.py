"""Classes and functions binding the Platform metadata."""
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Mapping, Union

from pydantic import BaseModel, Field

_EMPTY_MAP: Mapping[str, str] = MappingProxyType({})


class Platform(BaseModel):
    """Platform is the contents of the platform directory.

    Attributes:
        path: The path to the platform directory.
        env: The environment exposed by the platform.
    """

    path: Path
    env: Mapping[str, str] = Field(default_factory=lambda: _EMPTY_MAP)

    class Config:  # noqa: D101, D106
        arbitrary_types_allowed = True

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "Platform":
        """Construct a Platform object from a given path."""
        path = Path(path).absolute()
        env: Dict[str, str] = {}
        for env_path in (path / "env").glob("*"):
            if env_path.is_file():
                env[env_path.name] = env_path.read_text()
        return cls(path=path, env=MappingProxyType(env))
