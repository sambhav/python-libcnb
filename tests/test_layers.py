from typing import Any

import pytest

import libcnb
from tests.conftest import mock_layers


def test_get(mock_layers):
    # WHEN
    layer: libcnb.Layer = mock_layers.get("DNE")
    # THEN
    assert layer.name == "DNE"
    assert layer.metadata_file.stem == "DNE"
    assert layer.metadata == {}
    assert layer.exec_d.path == layer.path / "exec.d"
    assert not layer.metadata_file.exists()
    assert layer.exec_d.file_path("test") == layer.exec_d.path / "test"
    assert layer.exec_d.process_file_path("test", "test") == layer.exec_d.path / "test" / "test"


def test_load(mock_layer):
    # GIVEN
    layer, layer_name, mock_layers = mock_layer
    # WHEN
    loaded_layer: libcnb.Layer = mock_layers.get(layer_name, load_all=True)
    # THEN
    assert loaded_layer == layer


def test_reset(mock_layer):
    # GIVEN
    layer, layer_name, mock_layers = mock_layer
    # WHEN
    layer.reset()
    # THEN
    # Since this is an empty layer, we are just checking to make sure that all the various
    # ways to loading it point to an empty layer
    assert mock_layers.get(layer_name, load_all=True) == mock_layers.get(layer_name, load_all=False)
    assert mock_layers.get(layer_name, load_all=True) == layer
    assert layer == libcnb.Layer(path=mock_layers.path / layer_name)


@pytest.mark.parametrize(
    "expected_metadata, exact, expected_value",
    [
        ({"test": "1"}, False, True),
        ({"test": "1"}, True, False),
        ({"test": "2"}, False, False),
        ({"test1": "1"}, False, False),
        ({"test": "1", "test2": "2"}, False, True),
        ({"test": "1", "test2": "2"}, True, True),
    ],
)
def test_compare_metadata(expected_metadata, exact, expected_value):
    # GIVEN
    layer = libcnb.Layer(path="")
    layer.metadata = {"test": "1", "test2": "2"}
    # WHEN
    output = layer.compare_metadata(expected_metadata, exact=exact)
    # THEN
    assert output == expected_value
