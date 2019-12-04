"""
Tests for widget properties used by the designer plugin.
"""
# pylint: disable=protected-access

import pytest
import json
import numpy as np
from accwidgets.graph import (
    StaticPlotWidget,
    ScrollingPlotWidget,
    SlidingPlotWidget,
)
from .mock_utils.widget_test_window import MinimalTestWindow


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget
])
def test_title_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_plot_title(new_val="My title")
    assert window.plot.plotItem.titleLabel.text == "My title"
    assert window.plot._get_plot_title() == "My title"


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget
])
def test_grid_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    # Grid in X direction
    window.plot._set_show_x_grid(new_val=True)
    assert window.plot.plotItem.ctrl.xGridCheck.isChecked()
    assert window.plot._get_show_x_grid()
    window.plot._set_show_x_grid(new_val=False)
    assert not window.plot.plotItem.ctrl.xGridCheck.isChecked()
    assert not window.plot._get_show_x_grid()
    # Grid in Y direction
    window.plot._set_show_y_grid(new_val=True)
    assert window.plot.plotItem.ctrl.yGridCheck.isChecked()
    assert window.plot._get_show_y_grid()
    window.plot._set_show_y_grid(new_val=False)
    assert not window.plot.plotItem.ctrl.yGridCheck.isChecked()
    assert not window.plot._get_show_y_grid()


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
])
def test_time_line_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_show_time_line(new_val=True)
    assert window.plot._get_show_time_line()
    assert window.plot.plotItem._time_line
    window.plot._set_show_time_line(new_val=False)
    assert not window.plot._get_show_time_line()
    assert not window.plot.plotItem._time_line


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
])
def test_time_span_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_time_span(new_val=3.1415)
    assert window.plot._get_time_span() == 3.1415
    assert window.plot.plotItem.plot_config.time_span == 3.1415
    window.plot._set_time_span(new_val=10.0)
    assert window.plot._get_time_span() == 10.0
    assert window.plot.plotItem.plot_config.time_span == 10.0


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_bottom_axis_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_show_bottom_axis(new_val=False)
    assert not window.plot._get_show_bottom_axis()
    window.plot._set_show_bottom_axis(new_val=True)
    assert window.plot._get_show_bottom_axis()


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_top_axis_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_show_top_axis(new_val=True)
    assert window.plot._get_show_top_axis()
    window.plot._set_show_top_axis(new_val=False)
    assert not window.plot._get_show_top_axis()


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_right_axis_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_show_right_axis(new_val=True)
    assert window.plot._get_show_right_axis()
    window.plot._set_show_right_axis(new_val=False)
    assert not window.plot._get_show_right_axis()


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_left_axis_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_show_left_axis(new_val=False)
    assert not window.plot._get_show_left_axis()
    window.plot._set_show_left_axis(new_val=True)
    assert window.plot._get_show_left_axis()


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_axis_labels_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_layer_ids(new_val=["0"])
    window.plot._set_show_top_axis(new_val=False)
    window.plot._set_show_bottom_axis(new_val=True)
    window.plot._set_show_right_axis(new_val=False)
    window.plot._set_show_left_axis(new_val=True)
    window.plot._set_layer_ids(new_val=["0"])
    labels = {
        "top": "top",
        "bottom": "bottom",
        "left": "left",
        "right": "right",
        "0": "0"
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    assert window.plot.plotItem.getAxis("top").labelText == ""
    assert window.plot.plotItem.getAxis("bottom").labelText == "bottom"
    assert window.plot.plotItem.getAxis("left").labelText == "left"
    assert window.plot.plotItem.getAxis("right").labelText == ""
    assert window.plot.plotItem.getAxis("0").labelText == "0"
    window.plot._set_show_top_axis(new_val=True)
    window.plot._set_show_bottom_axis(new_val=True)
    window.plot._set_show_right_axis(new_val=True)
    window.plot._set_show_left_axis(new_val=True)
    assert window.plot.plotItem.getAxis("top").labelText == "top"
    assert window.plot.plotItem.getAxis("bottom").labelText == "bottom"
    assert window.plot.plotItem.getAxis("left").labelText == "left"
    assert window.plot.plotItem.getAxis("right").labelText == "right"
    assert window.plot.plotItem.getAxis("0").labelText == "0"


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_axis_ranges_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_layer_ids(new_val=["0"])
    window.plot._set_show_top_axis(new_val=False)
    window.plot._set_show_bottom_axis(new_val=True)
    window.plot._set_show_right_axis(new_val=False)
    window.plot._set_show_left_axis(new_val=True)
    window.plot._set_layer_ids(new_val=["0"])
    # Set range for x, y and y of new layer
    ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "0": [-10.0, 10.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    actual = window.plot.plotItem.vb.targetRange()
    assert np.allclose(np.array(actual[0]), np.array([-5.0, 5.0]), atol=0.5)
    assert np.allclose(np.array(actual[1]), np.array([0.0, 10.0]), atol=0.5)
    actual = window.plot.plotItem.getViewBox(layer="0").targetRange()
    assert np.allclose(np.array(actual[1]), np.array([-10.0, 10.0]), atol=1.0)
    assert window.plot._get_axis_ranges() == json.dumps(ranges)
    # Change ranges again
    ranges = {
        "x": [-1.0, 1.0],
        "y": [-10.0, 10.0],
        "0": [-100.0, 100.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    actual = window.plot.plotItem.vb.targetRange()
    assert np.allclose(np.array(actual[0]), np.array([-1.0, 1.0]), atol=0.1)
    assert np.allclose(np.array(actual[1]), np.array([-10.0, 10.0]), atol=1.0)
    actual = window.plot.plotItem.getViewBox(layer="0").targetRange()
    assert np.allclose(np.array(actual[1]), np.array([-100.0, 100.0]), atol=10.0)
    # Add key that is non existing layer key
    ranges = {
        "x": [-1.0, 1.0],
        "y": [-10.0, 10.0],
        "0": [-100.0, 100.0],
        "layer that does not exist": [-1000.0, 1000.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    actual = window.plot.plotItem.vb.targetRange()
    assert np.allclose(np.array(actual[0]), np.array([-1.0, 1.0]), atol=0.1)
    assert np.allclose(np.array(actual[1]), np.array([-10.0, 10.0]), atol=1.0)
    actual = window.plot.plotItem.getViewBox(layer="0").targetRange()
    assert np.allclose(np.array(actual[1]), np.array([-100.0, 100.0]), atol=10.0)

# ~~~~~~~~~~~~~~ Tests for layer property synchronization ~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_additional_layer_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_additional_layers_count(new_val=1)
    assert window.plot._get_additional_layers_count() == 1
    assert window.plot._get_layer_ids() == [
        "layer_0"
    ]
    window.plot._set_additional_layers_count(new_val=2)
    assert window.plot._get_additional_layers_count() == 2
    assert window.plot._get_layer_ids() == [
        "layer_0",
        "layer_1",
    ]
    window.plot._set_additional_layers_count(new_val=1)
    assert window.plot._get_additional_layers_count() == 1
    assert window.plot._get_layer_ids() == [
        "layer_0",
    ]
    window.plot._set_additional_layers_count(new_val=0)
    assert window.plot._get_additional_layers_count() == 0
    assert window.plot._get_layer_ids() == []


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_layer_ids_property(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_layer_ids(new_val=["custom_layer_0"])
    assert window.plot._get_additional_layers_count() == 1
    assert window.plot._get_layer_ids() == [
        "custom_layer_0"
    ]
    window.plot._set_layer_ids(
        new_val=["custom_layer_0", "custom_layer_1"]
    )
    assert window.plot._get_additional_layers_count() == 2
    assert window.plot._get_layer_ids() == [
        "custom_layer_0",
        "custom_layer_1",
    ]
    window.plot._set_layer_ids(new_val=[])
    assert window.plot._get_additional_layers_count() == 0
    assert window.plot._get_layer_ids() == []


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_layer_rename(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_layer_ids(
        new_val=["0", "1"]
    )
    labels = {
        "bottom": "x",
        "0": "y"
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "0": [-10.0, 10.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    assert window.plot._get_additional_layers_count() == 2
    # rename layer '0' to 'renamed'
    window.plot._set_layer_ids(
        new_val=["renamed", "1"]
    )
    expected_labels = {
        "bottom": "x",
        "renamed": "y"
    }
    assert window.plot._get_axis_labels() == json.dumps(expected_labels)
    expected_ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "renamed": [-10.0, 10.0],
    }
    assert window.plot._get_axis_ranges() == json.dumps(expected_ranges)
    # rename layer not in ranges / labels
    window.plot._set_layer_ids(
        new_val=["renamed", "no effect"]
    )
    assert window.plot._get_axis_ranges() == json.dumps(expected_ranges)
    assert window.plot._get_axis_labels() == json.dumps(expected_labels)


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_layer_removal(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_layer_ids(
        new_val=["0", "1"]
    )
    labels = {
        "bottom": "x",
        "0": "y"
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "0": [-10.0, 10.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    assert window.plot._get_additional_layers_count() == 2
    # remove layer '0'
    window.plot._set_layer_ids(
        new_val=["1"]
    )
    expected_labels = {
        "bottom": "x",
    }
    assert window.plot._get_axis_labels() == json.dumps(expected_labels)
    expected_ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
    }
    assert window.plot._get_axis_ranges() == json.dumps(expected_ranges)
    # add layer with same name
    window.plot._set_layer_ids(
        new_val=["0", "1"]
    )
    assert window.plot._get_axis_ranges() == json.dumps(expected_ranges)
    assert window.plot._get_axis_labels() == json.dumps(expected_labels)
    assert window.plot._get_additional_layers_count() == 2


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_layer_removal_and_rename(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_layer_ids(
        new_val=["0", "1"]
    )
    labels = {
        "bottom": "x",
        "0": "y"
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "0": [-10.0, 10.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    assert window.plot._get_additional_layers_count() == 2
    # remove layer "0" and rename layer "1"
    window.plot._set_layer_ids(
        new_val=["was 1"]
    )
    expected_labels = {
        "bottom": "x",
    }
    assert window.plot._get_axis_labels() == json.dumps(expected_labels)
    expected_ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
    }
    assert window.plot._get_axis_ranges() == json.dumps(expected_ranges)
    assert window.plot._get_additional_layers_count() == 1


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    SlidingPlotWidget,
    StaticPlotWidget,
])
def test_shuffle_layers(qtbot, widget):
    window = MinimalTestWindow(
        plot_widget=widget()
    )
    window.plot._set_layer_ids(
        new_val=["0", "1"]
    )
    labels = {
        "bottom": "x",
        "0": "y"
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "0": [-10.0, 10.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    assert window.plot._get_additional_layers_count() == 2
    # shuffle layer "0" and "1"
    window.plot._set_layer_ids(
        new_val=["1", "0"]
    )
    expected_labels = {
        "bottom": "x",
        "1": "y"
    }
    assert window.plot._get_axis_labels() == json.dumps(expected_labels)
    expected_ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "1": [-10.0, 10.0],
    }
    assert window.plot._get_axis_ranges() == json.dumps(expected_ranges)
