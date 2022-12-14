"""
Tests for widget properties used by the designer plugin.
"""
# pylint: disable=protected-access

import pytest
import json
import numpy as np
from accwidgets.graph import (
    XAxisSideOptions,
    DefaultYAxisSideOptions,
    GridOrientationOptions,
    StaticPlotWidget,
    ScrollingPlotWidget,
    CyclicPlotWidget,
)
from .mock_utils.widget_test_window import MinimalTestWindow


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_title_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot._set_plot_title(new_val="My title")
    assert window.plot.plotItem.titleLabel.text == "My title"
    assert window.plot._get_plot_title() == "My title"


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_grid_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    # Show grid in x direction
    window.plot.gridOrientation = GridOrientationOptions.X
    assert window.plot.plotItem.ctrl.xGridCheck.isChecked()
    assert not window.plot.plotItem.ctrl.yGridCheck.isChecked()
    assert window.plot.gridOrientation == GridOrientationOptions.X
    # Show no Grid
    window.plot.gridOrientation = GridOrientationOptions.Hidden
    assert not window.plot.plotItem.ctrl.yGridCheck.isChecked()
    assert not window.plot.plotItem.ctrl.xGridCheck.isChecked()
    assert window.plot.gridOrientation == GridOrientationOptions.Hidden
    # Grid in Y direction
    window.plot.gridOrientation = GridOrientationOptions.Y
    assert not window.plot.plotItem.ctrl.xGridCheck.isChecked()
    assert window.plot.plotItem.ctrl.yGridCheck.isChecked()
    assert window.plot.gridOrientation == GridOrientationOptions.Y
    # Grid in X and Y direction
    window.plot.gridOrientation = GridOrientationOptions.Both
    assert window.plot.plotItem.ctrl.xGridCheck.isChecked()
    assert window.plot.plotItem.ctrl.yGridCheck.isChecked()
    assert window.plot.gridOrientation == GridOrientationOptions.Both


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
])
def test_time_line_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot._set_show_time_line(new_val=True)
    assert window.plot._get_show_time_line()
    assert window.plot.plotItem._time_line
    window.plot._set_show_time_line(new_val=False)
    assert not window.plot._get_show_time_line()
    assert not window.plot.plotItem._time_line


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
])
def test_time_span_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot._set_left_time_span_boundary(new_val=3.1415)
    assert window.plot._get_left_time_span_boundary() == 3.1415
    assert window.plot.plotItem.plot_config.time_span.left_boundary_offset == 3.1415
    window.plot._set_left_time_span_boundary(new_val=10.0)
    assert window.plot._get_left_time_span_boundary() == 10.0
    assert window.plot.plotItem.plot_config.time_span.left_boundary_offset == 10.0


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_x_axis_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot.showXAxis = XAxisSideOptions.Hidden
    assert window.plot.showXAxis == XAxisSideOptions.Hidden
    window.plot.showXAxis = XAxisSideOptions.Bottom
    assert window.plot.showXAxis == XAxisSideOptions.Bottom
    window.plot.showXAxis = XAxisSideOptions.Top
    assert window.plot.showXAxis == XAxisSideOptions.Top
    window.plot.showXAxis = XAxisSideOptions.Both
    assert window.plot.showXAxis == XAxisSideOptions.Both
    window.plot.showXAxis = XAxisSideOptions.Hidden
    assert window.plot.showXAxis == XAxisSideOptions.Hidden


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_y_axis_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot.showYAxis = DefaultYAxisSideOptions.Hidden
    assert window.plot.showYAxis == DefaultYAxisSideOptions.Hidden
    window.plot.showYAxis = DefaultYAxisSideOptions.Left
    assert window.plot.showYAxis == DefaultYAxisSideOptions.Left
    window.plot.showYAxis = DefaultYAxisSideOptions.Right
    assert window.plot.showYAxis == DefaultYAxisSideOptions.Right
    window.plot.showYAxis = DefaultYAxisSideOptions.Both
    assert window.plot.showYAxis == DefaultYAxisSideOptions.Both
    window.plot.showYAxis = DefaultYAxisSideOptions.Hidden
    assert window.plot.showYAxis == DefaultYAxisSideOptions.Hidden


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_axis_labels_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot._set_layer_ids(layers=["0"])
    window.plot.showXAxis = XAxisSideOptions.Bottom
    window.plot.showYAxis = DefaultYAxisSideOptions.Left
    window.plot._set_layer_ids(layers=["0"])
    labels = {
        "top": "x",
        "bottom": "x",
        "left": "y",
        "right": "y",
        "0": "0",
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    assert window.plot.plotItem.getAxis("top").labelText == "x"
    assert window.plot.plotItem.getAxis("bottom").labelText == "x"
    assert window.plot.plotItem.getAxis("left").labelText == "y"
    assert window.plot.plotItem.getAxis("right").labelText == "y"
    assert window.plot.plotItem.getAxis("0").labelText == "0"
    window.plot.showYAxis = DefaultYAxisSideOptions.Both
    window.plot.showXAxis = XAxisSideOptions.Both
    assert window.plot.plotItem.getAxis("top").labelText == "x"
    assert window.plot.plotItem.getAxis("bottom").labelText == "x"
    assert window.plot.plotItem.getAxis("left").labelText == "y"
    assert window.plot.plotItem.getAxis("right").labelText == "y"
    assert window.plot.plotItem.getAxis("0").labelText == "0"


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_axis_ranges_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot.showXAxis = XAxisSideOptions.Bottom
    window.plot.showYAxis = DefaultYAxisSideOptions.Left
    window.plot._set_layer_ids(layers=["0"])
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
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_layer_ids_property(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot._set_layer_ids(layers=["custom_layer_0"])
    assert len(window.plot.layerIDs) == 1
    assert window.plot._get_layer_ids() == ["custom_layer_0"]
    window.plot._set_layer_ids(layers=["custom_layer_0", "custom_layer_1"])
    assert len(window.plot.layerIDs) == 2
    assert window.plot._get_layer_ids() == [
        "custom_layer_0",
        "custom_layer_1",
    ]
    window.plot._set_layer_ids(layers=[])
    assert len(window.plot.layerIDs) == 0
    assert window.plot._get_layer_ids() == []


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_layer_rename(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot._set_layer_ids(layers=["0", "1"])
    labels = {
        "bottom": "x",
        "0": "y",
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "0": [-10.0, 10.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    assert len(window.plot.layerIDs) == 2
    # rename layer '0' to 'renamed'
    window.plot._set_layer_ids(layers=["renamed", "1"])
    expected_labels = {
        "right": "",
        "left": "",
        "top": "",
        "bottom": "x",
        "renamed": "y",
        "1": "",
    }
    assert json.loads(window.plot._get_axis_labels()) == expected_labels
    expected_ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "renamed": [-10.0, 10.0],
        "1": [0, 1],
    }
    assert json.loads(window.plot._get_axis_ranges()) == expected_ranges


@pytest.mark.parametrize("widget", [
    ScrollingPlotWidget,
    CyclicPlotWidget,
    StaticPlotWidget,
])
def test_layer_removal(qtbot, widget):
    window = MinimalTestWindow(plot_widget=widget())
    window.plot._set_layer_ids(layers=["0", "1"])
    labels = {
        "bottom": "x",
        "0": "y",
    }
    window.plot._set_axis_labels(new_val=json.dumps(labels))
    ranges = {
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
        "0": [-10.0, 10.0],
    }
    window.plot._set_axis_ranges(new_val=json.dumps(ranges))
    assert len(window.plot.layerIDs) == 2
    # remove layer '0'
    window.plot._set_layer_ids(layers=["1"])
    expected_labels = {
        "right": "",
        "top": "",
        "bottom": "x",
        "left": "",
        "1": "",
    }
    assert json.loads(window.plot._get_axis_labels()) == expected_labels
    expected_ranges = {
        "1": [0, 1],
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
    }
    assert json.loads(window.plot._get_axis_ranges()) == expected_ranges
    # add layer with same name
    window.plot._set_layer_ids(layers=["0", "1"])
    expected_ranges = {
        "0": [0, 1],
        "1": [0, 1],
        "x": [-5.0, 5.0],
        "y": [0.0, 10.0],
    }
    assert json.loads(window.plot._get_axis_ranges()) == expected_ranges
    expected_labels = {
        "right": "",
        "top": "",
        "bottom": "x",
        "left": "",
        "1": "",
        "0": "",
    }
    assert json.loads(window.plot._get_axis_labels()) == expected_labels
    assert len(window.plot.layerIDs) == 2
