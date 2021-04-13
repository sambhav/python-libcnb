from unittest.mock import Mock

import pytest

import libcnb


@pytest.fixture
def mock_phases(monkeypatch):
    detect_mock = Mock()
    build_mock = Mock()
    monkeypatch.setattr("libcnb._run.detect", detect_mock)
    monkeypatch.setattr("libcnb._run.build", build_mock)
    yield detect_mock, build_mock


def test_run_build(monkeypatch, mock_phases):
    # GIVEN
    monkeypatch.setattr("sys.argv", ["bin/build"])
    detect_mock, build_mock = mock_phases
    # WHEN
    libcnb.run(detector=None, builder=None)
    # THEN
    assert build_mock.called
    assert not detect_mock.called


def test_run_detect(monkeypatch, mock_phases):
    # GIVEN
    monkeypatch.setattr("sys.argv", ["bin/detect"])
    detect_mock, build_mock = mock_phases
    # WHEN
    libcnb.run(detector=None, builder=None)
    # THEN
    assert detect_mock.called
    assert not build_mock.called


def test_run_unknown(monkeypatch, mock_phases):
    # GIVEN
    monkeypatch.setattr("sys.argv", ["bin/unknown"])
    # THEN
    with pytest.raises(Exception, match="unknown is not a supported executable type."):
        libcnb.run(detector=None, builder=None)
