from typing import List, Tuple, Dict, Optional, Union

import numpy as np
import pyqtgraph as pg
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent
import pytest

from accwidgets.graph import (
    PlotItemLayer,
    LayerIdentification,
    ExPlotItem,
    ExPlotWidget,
    ExViewBox,
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)

from .mock_utils.mock_data_source import MockDataSource
from .mock_utils.widget_test_window import PlotWidgetTestWindow

# Some constants for the tests related to axes

standard_axes_names = ["top", "bottom", "left", "right"]
not_existing_axes_names = ["non_existing_layer"]
additional_axes_names = ["first_layer"]
all_existing_axes_names = standard_axes_names + additional_axes_names
all_axes_names = standard_axes_names + not_existing_axes_names + additional_axes_names


@pytest.mark.parametrize("method", {
    ExViewBox.setRange,
    ExViewBox.setYRange,
})
@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_set_y_range(qtbot, method: classmethod, item_to_test):
    """
    Test addition of the layer parameter in the setRange and setYRange
    function of the ExPlotItem
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_0 = plot.layer()
    layer_1 = plot.add_layer(layer_id="layer_1")
    layer_2 = plot.add_layer(layer_id="layer_2")
    plot.setXRange(min=-10.0, max=10.0, padding=0.0)
    # default layer
    _set_range(
        method=method,
        plot_item=plot,
        view_range=(0.0, 1.0),
    )
    _set_range(
        method=method,
        plot_item=plot,
        view_range=(1.0, 2.0),
        layer="layer_1",
    )
    _set_range(
        method=method,
        plot_item=plot,
        view_range=(2.0, 3.0),
        layer="layer_2",
    )
    check_range(layer_0.view_box.targetRange(), [[-10, 10], [0.0, 1.0]])
    check_range(layer_1.view_box.targetRange(), [[-10, 10], [1.0, 2.0]])
    check_range(layer_2.view_box.targetRange(), [[-10, 10], [2.0, 3.0]])
    # reference = empty string
    _set_range(
        method=method,
        plot_item=plot,
        view_range=(-1.0, 0.0),
        layer="",
    )
    check_range(layer_0.view_box.targetRange(), [[-10, 10], [-1.0, 0.0]])
    with pytest.raises(KeyError):
        plot.setYRange(
            min=-100.0,
            max=0.0,
            padding=0.0,
            layer="non existing layer",
        )
    # No ranges should be touched
    check_range(layer_0.view_box.targetRange(), [[-10, 10], [-1.0, 0.0]])
    check_range(layer_1.view_box.targetRange(), [[-10, 10], [1.0, 2.0]])
    check_range(layer_2.view_box.targetRange(), [[-10, 10], [2.0, 3.0]])


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_invert_y(qtbot, item_to_test):
    """
    Test addition of the layer parameter in the setYRange
    function of the ExPlotItem
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_0 = plot.layer()
    layer_1 = plot.add_layer(layer_id="layer_1")
    plot.invertY(True)
    assert layer_0.view_box.yInverted()
    assert not layer_1.view_box.yInverted()
    plot.invertY(True, layer="layer_1")
    assert layer_0.view_box.yInverted()
    assert layer_1.view_box.yInverted()
    plot.invertY(False)
    assert not layer_0.view_box.yInverted()
    assert layer_1.view_box.yInverted()
    plot.invertY(False, layer=layer_1)
    assert not layer_0.view_box.yInverted()
    assert not layer_1.view_box.yInverted()


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_link_y_layers(qtbot, item_to_test):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_id

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    first_layer = plot.add_layer("first_layer")
    second_layer = plot.add_layer("second_layer")
    # Layers are not linked. They move separate.
    plot.setYRange(min=-5.0, max=5.0, padding=0.0)
    check_range(plot.getViewBox().targetRange(), [[0, 1], [-5.0, 5.0]])
    check_range(first_layer.view_box.targetRange(), [[0, 1], [0.0, 1.0]])
    check_range(second_layer.view_box.targetRange(), [[0, 1], [0.0, 1.0]])
    # Link all axes
    plot.setYLink(view=first_layer.view_box)
    plot.setYLink(view=second_layer.view_box, layer=first_layer)
    # Since all layers are linked, the movements should be transferred
    plot.setYRange(min=-15.0, max=15.0, padding=0.0)
    check_range(plot.getViewBox().targetRange(), [[0, 1], [-15.0, 15.0]])
    check_range(first_layer.view_box.targetRange(), [[0, 1], [-15.0, 15.0]])
    check_range(second_layer.view_box.targetRange(), [[0, 1], [-15.0, 15.0]])


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_get_view_box(qtbot, item_to_test):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_id

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    first_layer = plot.add_layer("first_layer")
    second_layer = plot.add_layer("second_layer")
    assert window.plot.plotItem.vb == plot.getViewBox()
    assert window.plot.plotItem.vb == plot.getViewBox("")
    assert first_layer.view_box == plot.getViewBox(first_layer)
    assert first_layer.view_box == plot.getViewBox("first_layer")
    assert second_layer.view_box == plot.getViewBox(second_layer)
    assert second_layer.view_box == plot.getViewBox("second_layer")
    with pytest.raises(KeyError):
        plot.getViewBox("non_existing_layer_id")


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_get_axis(qtbot, item_to_test):
    """
    Test get axes by their name as well as axes from additional
    layers by their layer identifier.
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    first_layer = plot.add_layer("first_layer")
    second_layer = plot.add_layer("second_layer")
    assert plot.getAxis(name="first_layer") == first_layer.axis_item
    assert plot.getAxis(name="second_layer") == second_layer.axis_item
    with pytest.raises(Exception):
        plot.getAxis(name="non_existing_layer")
    # Test that original functionality is still there
    for axis in standard_axes_names:
        assert plot.getAxis(name=axis) == super(type(window.plot.plotItem), window.plot.plotItem).getAxis(name=axis)


@pytest.mark.parametrize("name", all_axes_names)
@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_show_axis(qtbot, name, item_to_test):
    """Test show axes by their name."""
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    if name not in standard_axes_names + not_existing_axes_names:
        plot.add_layer(name)
    if name in not_existing_axes_names:
        with pytest.raises(Exception):
            plot.showAxis(axis=name, show=True)
    else:
        plot.showAxis(axis=name, show=True)
        assert plot.getAxis(name=name).isVisible()
        plot.showAxis(axis=name, show=False)
        assert not plot.getAxis(name=name).isVisible()


@pytest.mark.parametrize("name", all_axes_names)
@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_add_axes_label(qtbot, name, item_to_test):
    """Test adding labels to axes by their name."""
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    complicated_german_axis_label = "Achsenbeschreibungsbuchstabensequenz"
    if name not in standard_axes_names + not_existing_axes_names:
        plot.add_layer(name)
    if name in not_existing_axes_names:
        with pytest.raises(Exception):
            plot.setLabel(axis=name, text=complicated_german_axis_label)
    else:
        plot.setLabel(axis=name, text=complicated_german_axis_label)
        assert plot.getAxis(name=name).labelText == complicated_german_axis_label
        for non_tested_name in [a for a in standard_axes_names if a != name]:
            assert plot.getAxis(name=non_tested_name).labelText == ""


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_add_axes_labels(qtbot, item_to_test):
    """Test convenience function for adding labels to axes 'addLabels'"""
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    for identifier in additional_axes_names:
        plot.add_layer(layer_id=identifier)
    complicated_german_axis_label = "Achsenbeschreibungsbuchstabensequenz"
    kwargs = {}
    for index, axis_name in enumerate(all_existing_axes_names):
        kwargs[axis_name] = complicated_german_axis_label + f"_{index}"
    plot.setLabels(**kwargs)
    for key, value in kwargs.items():
        assert plot.getAxis(name=key).labelText == value


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_simple_adding_two_new_layers(qtbot, item_to_test):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_id

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    first_layer = plot.add_layer("first_layer")
    second_layer = plot.add_layer("second_layer")
    assert first_layer == plot.layer("first_layer")
    assert second_layer == plot.layer("second_layer")
    with pytest.raises(KeyError):
        plot.layer("third_layer")
    assert len(window.plot.plotItem.layers) == 3
    # Make shure that the position tuple is set in the plotItems axes attribute
    assert "right" in window.plot.plotItem.axes["first_layer"]["pos"]
    assert "right" in window.plot.plotItem.axes["second_layer"]["pos"]


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_adding_layer_with_view_ranges_and_invert(qtbot, item_to_test):
    """ Test the optional parameters when adding a new layer
    for setting the y range as well as inverting the axis.

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_0 = plot.add_layer(layer_id="layer_0")
    assert not layer_0.view_box.yInverted()
    check_range(layer_0.view_box.targetRange(), [[0, 1], [0, 1]])
    layer_1 = plot.add_layer(
        layer_id="layer_1",
        y_range=(-1.0, 2.0),
        y_range_padding=0.0,
    )
    assert not layer_0.view_box.yInverted()
    assert not layer_1.view_box.yInverted()
    check_range(layer_0.view_box.targetRange(), [[0, 1], [0, 1]])
    check_range(layer_1.view_box.targetRange(), [[0, 1], [-1.0, 2.0]])
    layer_2 = plot.add_layer(
        layer_id="layer_2",
        invert_y=True,
    )
    check_range(layer_0.view_box.targetRange(), [[0, 1], [0, 1]])
    check_range(layer_1.view_box.targetRange(), [[0, 1], [-1.0, 2.0]])
    assert not layer_0.view_box.yInverted()
    assert not layer_1.view_box.yInverted()
    assert layer_2.view_box.yInverted()


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_removal_of_layer(qtbot, item_to_test):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_id

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    first_layer = plot.add_layer("first_layer")
    second_layer = plot.add_layer("second_layer")
    assert first_layer == plot.layer("first_layer")
    assert second_layer == plot.layer("second_layer")
    assert len(window.plot.plotItem.layers) == 3
    plot.remove_layer("first_layer")
    with pytest.raises(KeyError):
        plot.layer("first_layer")
    assert first_layer not in window.plot.plotItem.layers
    assert len(window.plot.plotItem.layers) == 2
    # Second layer is still accessible
    assert second_layer == plot.layer("second_layer")
    with pytest.raises(KeyError):
        plot.layer("first_layer")
    with pytest.raises(KeyError):
        plot.layer("layer_that_does_not_exist")
    plot.remove_layer(second_layer)
    assert len(window.plot.plotItem.layers) == 1


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_get_all_layers_viewboxes(qtbot, item_to_test):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_id

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    plot_item_layer = plot.layer()
    first_layer = plot.add_layer("first_layer")
    second_layer = plot.add_layer("second_layer")
    assert len(window.plot.plotItem.view_boxes) == 3
    assert plot_item_layer.view_box in window.plot.plotItem.view_boxes
    assert first_layer.view_box in window.plot.plotItem.view_boxes
    assert second_layer.view_box in window.plot.plotItem.view_boxes
    plot.remove_layer(second_layer)
    assert len(window.plot.plotItem.view_boxes) == 2
    assert plot_item_layer.view_box in window.plot.plotItem.view_boxes
    assert first_layer.view_box in window.plot.plotItem.view_boxes


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_new_layer_viewbox_and_axis(qtbot, item_to_test):
    """test_new_layer_viewbox_and_axis

    - Has new layer its own viewbox and axis?
    - Is the axis label properly set?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    new_layer = plot.add_layer("layer_2_id", text="layer_2_label")
    assert new_layer.view_box and new_layer.view_box is not plot.getViewBox()
    assert new_layer.axis_item and new_layer.axis_item is not plot.getAxis("left")
    assert new_layer.axis_item.labelText == "layer_2_label"
    assert new_layer.id == "layer_2_id"
    assert len(window.plot.plotItem.layers) == 2


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_plot_item_default_layer(qtbot, item_to_test):
    """ test_plot_item_default_layer

    - Is the "default" PlotItem Layer correctly added to the Layer Collection

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    default_layer = plot.layer()
    assert default_layer.axis_item is plot.getAxis("left")
    assert default_layer.view_box is plot.getViewBox()
    assert default_layer.id == PlotItemLayer.default_layer_id
    assert default_layer is plot.layer(PlotItemLayer.default_layer_id)
    assert len(window.plot.plotItem.layers) == 1


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_draw_add_plotdataitem_to_specific_layer(qtbot, item_to_test):
    """ test_draw_add_plotdataitem_to_specific_layer

    - Is the PlotDataItem correctly added to the right layer?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    default_layer = plot.layer()
    layer_2 = plot.add_layer("layer_2")
    values_1 = _create_values()
    values_2 = _create_values()
    item_for_default_layer = pg.PlotDataItem(values_1[0], values_1[1])
    item_for_second_layer = pg.PlotDataItem(values_2[0], values_2[1])
    plot.addItem(layer="", item=item_for_default_layer)
    plot.addItem(layer="layer_2", item=item_for_second_layer)
    assert len(default_layer.view_box.addedItems) == 1
    assert len(layer_2.view_box.addedItems) == 1
    assert default_layer.view_box.addedItems[0] is item_for_default_layer
    assert layer_2.view_box.addedItems[0] is item_for_second_layer


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_layers_with_new_plotting_style(qtbot, item_to_test):
    """ test_draw_add_plotdataitem_to_specific_layer

    - Is the PlotDataItem correctly added to the right layer?
    - Are all decorators drawn in the correct layer?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_1 = plot.add_layer("layer_1")
    layer_1_items = layer_1.view_box.addedItems
    default_layer_items = plot.getViewBox().addedItems
    data_source_mock = MockDataSource()
    layer_1_curve = plot.addCurve(
        layer="layer_1",
        data_source=data_source_mock,
    )
    window.time_source_mock.create_new_value(0.0)
    # Default layer already has elements in it (line at time span start, time span end, line for current time)
    empty_default_layer_items_count = len(default_layer_items)
    for item in default_layer_items:
        assert item in (
            window.plot.plotItem._time_line,
            window.plot.plotItem._time_span_start_boundary,
            window.plot.plotItem._time_span_end_boundary,
        )
    # Create new data and timing updates
    data_source_mock.create_new_value(timestamp=0.2, value=1.0)
    data_source_mock.create_new_value(timestamp=0.5, value=1.0)
    window.time_source_mock.create_new_value(1.0)
    # Expected in Viewbox: Curve
    assert len(layer_1_items) == 1
    assert len(default_layer_items) == empty_default_layer_items_count
    assert layer_1_curve in layer_1_items
    assert layer_1_curve not in default_layer_items
    default_layer_curve = plot.addCurve(data_source=data_source_mock)
    # Create some updates for the new curve (without data no plotted curve)
    data_source_mock.create_new_value(timestamp=1.2, value=1.0)
    data_source_mock.create_new_value(timestamp=1.5, value=1.0)
    window.time_source_mock.create_new_value(2.0)
    default_layer_items = plot.getViewBox().addedItems
    # Layer 1 should not be affected by the new curve
    assert len(layer_1_items) == 1
    # The default layer should have the new items included
    assert len(default_layer_items) == empty_default_layer_items_count + 1
    assert default_layer_curve in default_layer_items
    assert default_layer_curve not in layer_1_items


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_set_axis_range(qtbot, item_to_test):
    """ test_set_axis_range

    - Are the viewboxes's axes properly connected to each other?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    plot._couple_layers_yrange(link=False)
    layer_0 = plot.layer()
    layer_1 = plot.add_layer(
        layer_id="layer_1",
        text="layer_1",
    )
    layer_2 = plot.add_layer(
        layer_id="layer_2",
        text="layer_2",
    )
    manual_range_change(layer_0, xRange=[-10, 10], yRange=[0, 10])
    manual_range_change(layer_1, yRange=[3, 8])
    manual_range_change(layer_2, yRange=[-5, -2])
    check_range(layer_0.view_box.targetRange(), [[-10, 10], [0, 10]])
    check_range(layer_1.view_box.targetRange(), [[-10, 10], [3, 8]])
    check_range(layer_2.view_box.targetRange(), [[-10, 10], [-5, -2]])
    # Check if X axis are properly linked together
    manual_range_change(layer_0, xRange=[-20, 20])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [0, 10]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [3, 8]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-5, -2]])
    # Check translation in connected axes
    plot._couple_layers_yrange(link=True)
    manual_range_change(layer_0, yRange=[10, 20])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [10, 20]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [8, 13]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-2, 1]])
    # Move axes back to their original position
    manual_range_change(layer_0, yRange=[0, 10])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [0, 10]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [3, 8]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-5, -2]])
    # Check translation in disconnected axes
    plot._couple_layers_yrange(link=False)
    manual_range_change(layer_0, yRange=[10, 20])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [10, 20]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [3, 8]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-5, -2]])
    # Move axes back to their original position
    manual_range_change(layer_0, yRange=[0, 10])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [0, 10]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [3, 8]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-5, -2]])
    # Check scaling in connected axes
    plot._couple_layers_yrange(link=True)
    manual_range_change(layer_0, yRange=[-10, 20])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [-10, 20]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [-2, 13]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-8, 1]])
    # Check scaling in disconnected axes
    plot._couple_layers_yrange(link=False)
    manual_range_change(layer_0, yRange=[0, 10])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [0, 10]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [-2, 13]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-8, 1]])


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_auto_range_all_layers_at_same_range(qtbot, item_to_test):
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_0 = plot.layer()
    layer_1 = plot.add_layer("layer_1")
    layer_2 = plot.add_layer("layer_2")
    plot.addItem(layer="", item=pg.PlotDataItem([0, 1], [0, 1]))
    plot.addItem(layer="layer_1", item=pg.PlotDataItem([0, 1], [2, -1]))
    plot.addItem(layer="layer_2", item=pg.PlotDataItem([0, 1], [5, 5]))
    layer_0.view_box.setRange(xRange=[-1.0, 2.0], yRange=[2.0, 3.0], padding=0.0)
    layer_1.view_box.setRange(xRange=[-1.0, 2.0], yRange=[2.0, 3.0], padding=0.0)
    layer_2.view_box.setRange(xRange=[-1.0, 2.0], yRange=[2.0, 3.0], padding=0.0)
    layer_0.view_box.autoRange(padding=0.0)
    check_range(layer_0.view_box.targetRange(), [[0.0, 1.0], [-1.0, 5.0]])
    check_range(layer_1.view_box.targetRange(), [[0.0, 1.0], [-1.0, 5.0]])
    check_range(layer_2.view_box.targetRange(), [[0.0, 1.0], [-1.0, 5.0]])


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_auto_range_all_layers_at_different_range(qtbot, item_to_test):
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_0 = plot.layer()
    layer_1 = plot.add_layer(layer_id="layer_1")
    layer_2 = plot.add_layer(layer_id="layer_2")
    plot.addItem(layer="", item=pg.PlotDataItem([-10, 150], [0, 1]))
    plot.addItem(layer="layer_1", item=pg.PlotDataItem([0, 1], [1.0, 3.0]))
    plot.addItem(layer="layer_2", item=pg.PlotDataItem([250, 300, 350, 400], [-150.0, 0.0, -200.0, 100.0]))
    layer_0.view_box.setRange(xRange=[-1.0, 2.0], yRange=[3.0, 5.0], padding=0.0)
    layer_1.view_box.setRange(xRange=[-1.0, 2.0], yRange=[-2.0, 2.0], padding=0.0)
    layer_2.view_box.setRange(xRange=[-1.0, 2.0], yRange=[-200.0, -100.0], padding=0.0)
    # Autorange, check if also repeatable
    for _ in range(0, 100):
        layer_0.view_box.autoRange(padding=0.0)
        check_range(layer_0.view_box.targetRange(), [[-10.0, 400.0], [0.0, 9.0]])
        check_range(layer_1.view_box.targetRange(), [[-10.0, 400.0], [-8.0, 10.0]])
        check_range(layer_2.view_box.targetRange(), [[-10.0, 400.0], [-350.0, 100.0]])


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_auto_button_visibility(qtbot, item_to_test):
    """
    Check if the small autoBtn [A] is properly visible if any
    layer is not in the auto scaling mode anymore and a mouse
    pointer is hovering over the plot.
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_0 = plot.layer()
    layer_1 = plot.add_layer(layer_id="layer_1")
    plot.addItem(layer="", item=pg.PlotDataItem([-10, 150], [0, 1]))
    plot.addItem(layer="layer_1", item=pg.PlotDataItem([0, 1], [1.0, 3.0]))
    assert not window.plot.plotItem.autoBtn.isVisible()
    _simulate_mouse_hover_for_auto_button(plot, True)
    # All axes are in auto scale mode -> button should not appear on mouse hover
    assert not window.plot.plotItem.autoBtn.isVisible()
    layer_0.view_box.setRange(xRange=[-1.0, 2.0], yRange=[3.0, 5.0], padding=0.0)
    _simulate_mouse_hover_for_auto_button(plot, False)
    # Default layer has been moved, but mouse is not hovering over plot
    assert not window.plot.plotItem.autoBtn.isVisible()
    _simulate_mouse_hover_for_auto_button(plot, True)
    assert window.plot.plotItem.autoBtn.isVisible()
    layer_1.view_box.setRange(xRange=[-1.0, 2.0], yRange=[-2.0, 2.0], padding=0.0)
    _simulate_mouse_hover_for_auto_button(plot, False)
    assert not window.plot.plotItem.autoBtn.isVisible()
    layer_0.view_box.enableAutoRange()
    assert not window.plot.plotItem.autoBtn.isVisible()
    _simulate_mouse_hover_for_auto_button(plot, True)
    assert window.plot.plotItem.autoBtn.isVisible()
    layer_1.view_box.enableAutoRange()
    assert not window.plot.plotItem.autoBtn.isVisible()


@pytest.mark.parametrize("item_to_test", {
    ExPlotItem,
    ExPlotWidget,
})
def test_auto_button_functionality(qtbot, item_to_test):
    """
    Check if the small autoBtn [A] is properly visible if any
    layer is not in the auto scaling mode anymore and a mouse
    pointer is hovering over the plot.
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 5)
    plot: Union[ExPlotWidget, ExPlotItem] = window.plot.plotItem
    if item_to_test == ExPlotWidget:
        plot = window.plot
    layer_0 = plot.layer()
    layer_1 = plot.add_layer(layer_id="layer_1")
    plot.addItem(layer="", item=pg.PlotDataItem([-10, 150], [0, 1]))
    plot.addItem(layer="layer_1", item=pg.PlotDataItem([0, 1], [1.0, 3.0]))
    # Set the range automatically to something different
    layer_0.view_box.setRange(xRange=[0.0, 20.0], yRange=[-2.0, 2.0], padding=0.0)
    check_range(layer_0.view_box.targetRange(), [[0.0, 20.0], [-2.0, 2.0]])
    layer_1.view_box.setRange(xRange=[0.0, 200.0], yRange=[-20.0, 20.0], padding=0.0)
    check_range(layer_1.view_box.targetRange(), [[0.0, 200.0], [-20.0, 20.0]])
    # Press the small [A] button in the plot
    plot.autoBtnClicked()
    qtbot.wait_for_window_shown(window)
    check_range(layer_0.view_box.targetRange(), [[-10, 150], [0, 1]], tolerance_factor=0.05)
    check_range(layer_1.view_box.targetRange(), [[-10, 150], [1.0, 3.0]], tolerance_factor=0.05)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                           Helper Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _simulate_mouse_hover_for_auto_button(plot: Union[pg.PlotItem, pg.PlotWidget], is_hovering: bool):
    """
    qtbot.mouseMove does not really work reliably since it really moves the mouses
    position. In cases other windows lay between the mouse pointer and the window
    or in case the mouse is moved by something else, the events attached to it
    are not properly executed.
    For this we simulate the conditions in the PlotItem that would be there if the
    mouse event was properly interpreted.
    """
    if isinstance(plot, pg.PlotWidget):
        plot = plot.plotItem
    if is_hovering:
        event = HoverEvent(None, True)
        event.enter = True
        event.exit = False
    else:
        event = HoverEvent(None, False)
        event.enter = False
        event.exit = True
    plot.hoverEvent(event)


def check_range(
        actual_range: List[List[float]],
        expected_range: List[List[float]],
        tolerance_factor: float = 0.0025,
):
    """
    Compare a viewboxes range with an expected range

    Args:
        actual_range: Actual range that is supposed to be checked
        expected_range: Range that we expect
        tolerance_factor: Sometimes the range of  the plot is a bit hard to predict
                          because of padding on ranges. This tolerance factor influences
                          the range in which the actual range is seen as right.
    """
    for actual, expected in list(zip(actual_range, expected_range)):
        # a bit of tolerance
        absolute_tolerance = tolerance_factor * (expected[1] - expected[0])
        assert np.isclose(actual[0], expected[0], atol=absolute_tolerance)
        assert np.isclose(actual[1], expected[1], atol=absolute_tolerance)


def manual_range_change(layer: PlotItemLayer, **kwargs):
    """Simulate a manual range change in a viewbox by emitting the manual change signal before setting the range"""
    if not kwargs.get("padding"):
        kwargs["padding"] = 0.0
    layer.view_box.sigRangeChangedManually.emit(layer.view_box.state["mouseEnabled"])  # Simulate Manual update by mouse
    layer.view_box.setRange(**kwargs)


def _prepare_cyclic_plot_test_window(qtbot, time_span: int):
    """ Create a simple test window
    Args:
        qtbot: pytest-qt fixture to control pyqt applications
        time_span (int): time span size for the PlotItem
    """
    plot_config = ExPlotWidgetConfig(
        plotting_style=PlotWidgetStyle.CYCLIC_PLOT,
        time_span=time_span,
        time_progress_line=True,
    )
    window = PlotWidgetTestWindow(plot_config)
    window.show()
    qtbot.add_widget(window)
    return window


def _create_values(amount: int = 20):
    x_values = np.random.randint(-amount, amount, amount)
    y_values = np.arange(0, amount)
    return x_values, y_values


def _set_range(
    method: classmethod,
    plot_item: ExPlotItem,
    view_range: Tuple[float, float],
    layer: Optional[LayerIdentification] = None,
):
    kwargs: Dict = {}
    if method == ExViewBox.setYRange:
        if layer is not None:
            kwargs["layer"] = layer
        plot_item.setYRange(min=view_range[0], max=view_range[1], padding=0.0, **kwargs)
    elif method == ExViewBox.setRange:
        if layer is not None:
            kwargs[layer] = view_range
        else:
            kwargs["yRange"] = view_range
        plot_item.setRange(padding=0.0, **kwargs)
    else:
        raise ValueError(f"Unknown method {method} for setting range.")
