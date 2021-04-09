"""Test module for libcnb."""

from libcnb import __author__, __email__, __version__


def test_project_info():
    """Test __author__ value."""
    assert __author__ == "Sambhav Kothari"
    assert __email__ == "sambhavs.email@gmail.com"
    assert __version__ == "0.0.0"
