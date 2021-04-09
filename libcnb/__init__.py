"""Python libcnb namespace."""

from importlib_metadata import PackageNotFoundError, version

__author__ = "Sambhav Kothari"
__email__ = "sambhavs.email@gmail.com"

# Used to automatically set version number from github actions
# as well as not break when being tested locally
try:
    __version__ = version(__package__)  # type: ignore
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
