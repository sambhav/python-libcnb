import shutil
from collections import UserDict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Union

import toml
from pydantic import BaseModel


class Profile(UserDict):
    def add(self, name: str, value: str) -> None:
        self.data[name] = value

    @classmethod
    def from_path(cls, profile_path: Union[Path, str]) -> "Profile":
        profile_path = Path(profile_path)
        profile = cls()
        for path in profile_path.glob("*"):
            if path.is_file():
                profile.add(path.name, path.read_text())
        return profile

    def to_path(self, path: Union[Path, str]) -> None:
        path = Path(path)
        for key, value in self.items():
            (path / key).write_text(value)


class Environment(UserDict):
    def append(self, name: str, value: str, delim: str) -> None:
        self.data[f"{name}.append"] = value
        self.data[f"{name}.delim"] = delim

    def prepend(self, name: str, value: str, delim: str) -> None:
        self.data[f"{name}.prepend"] = value
        self.data[f"{name}.delim"] = delim

    def default(self, name: str, value: str) -> None:
        self.data[f"{name}.default"] = value

    def override(self, name: str, value: str) -> None:
        self.data[f"{name}.override"] = value

    @classmethod
    def from_path(cls, env_path: Union[Path, str]) -> "Environment":
        env_path = Path(env_path)
        env = cls()
        for path in env_path.glob("*"):
            if path.is_file() and path.suffix in {
                "append",
                "prepend",
                "default",
                "delim",
                "override",
            }:
                env[path.name] = path.read_text()
        return env

    def to_path(self, path: Union[Path, str]) -> None:
        path = Path(path)
        for key, value in self.items():
            (path / key).write_text(value)


LAYER_TYPES = {"launch", "cache", "build"}


class ExecD:
    def __init__(self, path: Path):
        self.path = path

    def file_path(self, name: str) -> Path:
        return self.path / name

    def process_file_path(self, process: str, name: str) -> Path:
        return self.path / process / name


class Layer(BaseModel):

    path: Path
    build: bool = False
    launch: bool = False
    cache: bool = False
    shared_env: Environment = Environment()
    launch_env: Environment = Environment()
    build_env: Environment = Environment()
    process_launch_envs: Dict[str, Environment] = {}
    metadata: Dict[str, Any] = {}
    profile: Profile = Profile()
    process_profiles: Dict[str, Profile] = {}

    class Config:
        arbitrary_types_allowed = True

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def metadata_file(self) -> Path:
        return Path(f"{self.path}.toml")

    def load(self) -> "Layer":
        try:
            metadata = toml.loads(self.metadata_file.read_text())
        except FileNotFoundError:
            metadata = {}
        layer_types = metadata.get("types", {})
        for layer_type in LAYER_TYPES:
            setattr(self, layer_type, layer_types.get(layer_type, False))
        self.metadata = metadata.get("metadata", {})
        self.shared_env = Environment.from_path(self.path / "env")
        self.build_env = Environment.from_path(self.path / "env.build")
        launch_env_path = self.path / "env.launch"
        self.launch_env = Environment.from_path(launch_env_path)
        self.process_launch_envs = {}
        for path in launch_env_path.glob("*"):
            if path.is_dir():
                self.process_launch_envs[path.name] = Environment.from_path(path)
        self.profile = Profile.from_path(self.path / "profile.d")
        self.process_profiles = {}
        for path in (self.path / "profile.d").glob("*"):
            if path.is_dir():
                self.process_profiles[path.name] = Profile.from_path(path)
        return self

    def dump(self) -> None:
        metadata = {
            "types": {key: getattr(self, key) for key in LAYER_TYPES},
            "metadata": self.metadata,
        }
        self.metadata_file.write_text(toml.dumps(metadata))
        self.shared_env.to_path(self.path / "env")
        self.build_env.to_path(self.path / "env.build")
        self.launch_env.to_path(self.path / "env.launch")
        for process, process_env in self.process_launch_envs.items():
            process_env.to_path(self.path / "env.launch" / process)
        self.profile.to_path(self.path / "profile.d")
        for process, process_profile in self.process_profiles.items():
            process_profile.to_path(self.path / "profile.d" / process)

    @property
    def exec_d(self) -> ExecD:
        return ExecD(self.path / "exec.d")

    def reset(self) -> "Layer":
        self.metadata_file.unlink()
        shutil.rmtree(self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        return self.load()

    def compare_metadata(self, expected_metadata: Dict[str, Any], exact: bool = False) -> bool:
        layer = self.load()
        if exact:
            if layer.metadata != expected_metadata:
                return False
            return True
        for key, value in expected_metadata.items():
            if layer.metadata.get(key) != value:
                return False
        return True


class Layers(BaseModel):

    path: Path

    def get(self, name: str) -> Layer:
        return Layer(path=(self.path / name)).load()
