"""Classes and functions related to layer metadata manipulation."""
import shutil
from collections import UserDict
from pathlib import Path
from typing import Any, Dict, Union

import toml
from pydantic import BaseModel

LAYER_TYPES = {"launch", "cache", "build"}


class Profile(UserDict):  # type: ignore
    """Profile is the collection of values to be written into profile.d."""

    def add(self, name: str, value: str) -> None:
        """Adds a profile.d script with a given name and script content.

        Arguments:
            name: Name of the profile.d script.
            value: The script content.
        """
        self.data[name] = value

    @classmethod
    def from_path(cls, profile_path: Union[Path, str]) -> "Profile":
        """Loads a collection of profile.d scripts from disk."""
        profile_path = Path(profile_path)
        profile = cls()
        for path in profile_path.glob("*"):
            if path.is_file():
                profile.add(path.name, path.read_text())
        return profile

    def to_path(self, path: Union[Path, str]) -> None:
        """Exports the current collection of profile.d scripts to disk."""
        path = Path(path)
        path.mkdir(mode=0o755, parents=True, exist_ok=True)
        for key, value in self.items():
            (path / key).write_text(str(value))


class Environment(UserDict):  # type: ignore
    """Environment provides a key-value store for declaring environment variables."""

    def append(self, name: str, value: str, delim: str) -> None:
        """Adds a key-value pair to the environment as an appended value.

        Arguments:
            name: Name of the environment variable.
            value: Value of the environment variable to append.
            delim: The delimiter to use when appending the value.
        """
        self.data[f"{name}.append"] = value
        self.data[f"{name}.delim"] = delim

    def prepend(self, name: str, value: str, delim: str) -> None:
        """Adds a key-value pair to the environment as a prepended value.

        Arguments:
            name: Name of the environment variable.
            value: Value of the environment variable to prepend.
            delim: The delimiter to use when preprending the value.
        """
        self.data[f"{name}.prepend"] = value
        self.data[f"{name}.delim"] = delim

    def default(self, name: str, value: str) -> None:
        """Adds a key-value pair to the environment as a default value.

        Arguments:
            name: Name of the environment variable.
            value: The default value of the environment variable.
        """
        self.data[f"{name}.default"] = value

    def override(self, name: str, value: str) -> None:
        """Adds a key-value pair to the environment as an overridden value.

        Arguments:
            name: Name of the environment variable.
            value: The overridden value of the environment variable.
        """
        self.data[f"{name}.override"] = value

    @classmethod
    def from_path(cls, env_path: Union[Path, str]) -> "Environment":
        """Loads the environment from the given path on disk."""
        env_path = Path(env_path)
        env = cls()
        for path in env_path.glob("*"):
            if path.is_file() and path.suffix in {
                ".append",
                ".prepend",
                ".default",
                ".delim",
                ".override",
            }:
                env[path.name] = path.read_text()
        return env

    def to_path(self, path: Union[Path, str]) -> None:
        """Exports the environment to the given path on disk."""
        path = Path(path)
        path.mkdir(mode=0o755, parents=True, exist_ok=True)
        for key, value in self.items():
            (path / key).write_text(str(value))


class ExecD:
    """Exec represents the exec.d layer location.

    Attributes:
        path (Path): The path to the exec.d directory.
    """

    def __init__(self, path: Union[str, Path]):
        """Initializer for exec.d."""
        self.path = Path(path)

    def file_path(self, name: str) -> Path:
        """Returns the fully qualified file path for a given name."""
        return (self.path / name).absolute()

    def process_file_path(self, process: str, name: str) -> Path:
        """Returns the fully qualified file path for a given process type and name."""
        return self.path / process / name


class Layer(BaseModel):
    """Layer provides a representation of a layer managed by a buildpack.

    This representation is based on the specification described in
    https://github.com/buildpacks/spec/blob/main/buildpack.md#layers.

    Attributes:
        path: The absolute location of the layer on disk.
        name (str): The descriptive name of the layer.
        metadata_file (Path): The aboluste location of the layer content metadata file.
        build: Indicates whether the layer is available to subsequent buildpacks
                during their build phase according to the specification:
                https://github.com/buildpacks/spec/blob/main/buildpack.md#build-layers.
        launch: Indicates whether the layer is exported into the application image
                and made available during the launch phase according to the specification:
                https://github.com/buildpacks/spec/blob/main/buildpack.md#launch-layers.
        cache: Cache indicates whether the layer is persisted and made available to
                subsequent builds of the same application according to the specification:
                https://github.com/buildpacks/spec/blob/main/buildpack.md#launch-layers
                and https://github.com/buildpacks/spec/blob/main/buildpack.md#build-layers.
        shared_env: The set of environment variables attached to the layer and
                made available during both the build and launch phases according to the
                specification:
                https://github.com/buildpacks/spec/blob/main/buildpack.md#provided-by-the-buildpacks.
        build_env: The set of environment variables attached to the layer and
                made available during the build phase according to the specification:
                https://github.com/buildpacks/spec/blob/main/buildpack.md#provided-by-the-buildpacks.
        launch_env: The set of environment variables attached to the layer and
                made available during the launch phase according to the specification:
                https://github.com/buildpacks/spec/blob/main/buildpack.md#provided-by-the-buildpacks.
        process_launch_envs: A dict of environment variables attached to the layer and
                made available to specified proccesses in the launch phase accoring to the
                specification: https://github.com/buildpacks/spec/blob/main/buildpack.md#provided-by-the-buildpacks.
        metadata: An unspecified field allowing buildpacks to communicate extra
                details about the layer. Examples of this type of metadata might include
                details about what versions of software are included in the layer such
                that subsequent builds can inspect that metadata and choose to reuse the
                layer if suitable. The Metadata field ultimately fills the metadata field
                of the Layer Content Metadata TOML file according to the specification:
                https://github.com/buildpacks/spec/blob/main/buildpack.md#layer-content-metadata-toml.
        profile: The collection of values to be written into profile.d.
        process_profiles:  A dict of process types to the collection of values to be written
            into profile.d for specific process types.
        exec_d (ExecD): The exec.d executables set in the layer.
    """

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

    class Config:  # noqa: D101, D106
        arbitrary_types_allowed = True

    @property
    def name(self) -> str:  # noqa: D102
        return self.path.name

    @property
    def metadata_file(self) -> Path:  # noqa: D102
        return Path(f"{self.path}.toml").absolute()

    @property
    def exec_d(self) -> ExecD:  # noqa: D102
        return ExecD(self.path / "exec.d")

    def load(self, load_all: bool = False) -> "Layer":
        """Loads the layer metadata from disk if it exists."""
        try:
            metadata = toml.loads(self.metadata_file.read_text())
        except FileNotFoundError:
            metadata = {}
        layer_types = metadata.get("types", {})
        for layer_type in LAYER_TYPES:
            setattr(self, layer_type, layer_types.get(layer_type, False))
        self.metadata = metadata.get("metadata", {})
        if not load_all:
            return self
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
        """Exports the layer metadata to disk."""
        self.path.mkdir(parents=True, exist_ok=True)
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

    def reset(self) -> "Layer":
        """Resets the layer metadata, cleans up the existing layer directory and creates an empty layer."""
        self.metadata_file.unlink()
        shutil.rmtree(self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        return self.load(load_all=True)

    def compare_metadata(self, expected_metadata: Dict[str, Any], exact: bool = False) -> bool:
        """Utility method to compare the layer metadata on disk with the expected metadata.

        Arguments:
            expected_metadata: A dict containing the expected metadata.
            exact: If set to true, the actual metadata must exactly match the expected metadata.
                If set to false, only the keys in expected metadata and their values are checked
                against the actual metadata. Any extra keys in actual metadata are ignored.
        """
        if exact:
            if self.metadata != expected_metadata:
                return False
            return True
        for key, value in expected_metadata.items():
            if key not in self.metadata:
                return False
            if self.metadata[key] != value:
                return False
        return True


class Layers(BaseModel):
    """Layers represents the set of layers managed by a buildpack.

    Attributes:
        path: The absolute location of the set of layers managed by a buildpack on disk.
    """

    path: Path

    def get(self, name: str, load_all: bool = False) -> Layer:
        """Create or load a layer with the given name along with its metadata.

        Arguments:
            name: Name of the layer to create or load.
            load_all: If set to True, also loads the environment and profile.d values
                associated with the layer.
        """
        return Layer(path=(self.path / name).absolute()).load(load_all=load_all)
