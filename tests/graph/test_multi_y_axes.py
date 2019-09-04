from typing import List

import numpy
import pyqtgraph as pg
import pytest

from accsoft_gui_pyqt_widgets.graph import (
    PlotItemLayer,
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)

from .mock_utils.mock_data_source import MockDataSource
from .mock_utils.widget_test_window import PlotWidgetTestWindow


def test_simple_adding_two_new_layers(qtbot):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_identifier

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    first_layer = plot_item.add_layer("first_layer")
    second_layer = plot_item.add_layer("second_layer")
    assert first_layer == plot_item.get_layer_by_identifier("first_layer")
    assert second_layer == plot_item.get_layer_by_identifier("second_layer")
    with pytest.raises(KeyError):
        plot_item.get_layer_by_identifier("third_layer")
    assert len(plot_item._layers) == 3


def test_removal_of_layer(qtbot):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_identifier

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    first_layer = plot_item.add_layer("first_layer")
    second_layer = plot_item.add_layer("second_layer")
    assert first_layer == plot_item.get_layer_by_identifier("first_layer")
    assert second_layer == plot_item.get_layer_by_identifier("second_layer")
    assert len(plot_item.get_all_layers()) == 3
    plot_item.remove_layer("first_layer")
    with pytest.raises(KeyError):
        plot_item.get_layer_by_identifier("first_layer")
    assert first_layer not in plot_item.get_all_layers()
    assert len(plot_item.get_all_layers()) == 2
    # Second layer is still accessible
    assert second_layer == plot_item.get_layer_by_identifier("second_layer")
    with pytest.raises(KeyError):
        plot_item.get_layer_by_identifier("first_layer")
    with pytest.raises(KeyError):
        plot_item.get_layer_by_identifier("layer_that_does_not_exist")
    plot_item.remove_layer(second_layer)
    assert len(plot_item.get_all_layers()) == 1


def test_get_all_layers_viewboxes(qtbot):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_identifier

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    plot_item_layer = plot_item.get_layer_by_identifier(layer_identifier="")
    first_layer = plot_item.add_layer("first_layer")
    second_layer = plot_item.add_layer("second_layer")
    assert len(plot_item._layers.get_view_boxes()) == 3
    assert plot_item_layer.view_box in plot_item._layers.get_view_boxes()
    assert first_layer.view_box in plot_item._layers.get_view_boxes()
    assert second_layer.view_box in plot_item._layers.get_view_boxes()
    plot_item.remove_layer(second_layer)
    assert len(plot_item._layers.get_view_boxes()) == 2
    assert plot_item_layer.view_box in plot_item._layers.get_view_boxes()
    assert first_layer.view_box in plot_item._layers.get_view_boxes()


def test_new_layer_viewbox_and_axis(qtbot):
    """test_new_layer_viewbox_and_axis

    - Has new layer its own viewbox and axis?
    - Is the axis label properly set?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    new_layer = plot_item.add_layer(
        "layer_2_id", axis_label_kwargs={"text": "layer_2_label"}
    )
    assert new_layer.view_box and new_layer.view_box is not plot_item.vb
    assert new_layer.axis_item and new_layer.axis_item is not plot_item.getAxis("left")
    assert new_layer.axis_item.labelText == "layer_2_label"
    assert new_layer.identifier == "layer_2_id"
    assert len(plot_item._layers) == 2


def test_plot_item_default_layer(qtbot):
    """ test_plot_item_default_layer

    - Is the "default" PlotItem Layer correctly added to the Layer Collection

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    default_layer = plot_item.get_layer_by_identifier("")
    assert default_layer.axis_item is plot_item.getAxis("left")
    assert default_layer.view_box is plot_item.vb
    assert (
            default_layer.identifier == PlotItemLayer.default_layer_identifier
    )
    assert default_layer is plot_item.get_layer_by_identifier(
        PlotItemLayer.default_layer_identifier
    )
    assert len(plot_item._layers) == 1


def test_draw_add_plotdataitem_to_specific_layer(qtbot):
    """ test_draw_add_plotdataitem_to_specific_layer

    - Is the PlotDataItem correctly added to the right layer?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    default_layer = plot_item.get_layer_by_identifier("")
    layer_2 = plot_item.add_layer("layer_2")
    values_1 = _create_values()
    values_2 = _create_values()
    item_for_default_layer = pg.PlotDataItem(values_1[0], values_1[1])
    item_for_second_layer = pg.PlotDataItem(values_2[0], values_2[1])
    plot_item.addItem(layer="", item=item_for_default_layer)
    plot_item.addItem(layer="layer_2", item=item_for_second_layer)
    assert len(default_layer.view_box.addedItems) == 1
    assert len(layer_2.view_box.addedItems) == 1
    assert default_layer.view_box.addedItems[0] is item_for_default_layer
    assert layer_2.view_box.addedItems[0] is item_for_second_layer


def test_layers_with_new_plotting_style(qtbot):
    """ test_draw_add_plotdataitem_to_specific_layer

    - Is the PlotDataItem correctly added to the right layer?
    - Are all decorators drawn in the correct layer?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    layer_1 = plot_item.add_layer("layer_1")
    layer_1_items = layer_1.view_box.addedItems
    default_layer_items = plot_item.get_layer_by_identifier("").view_box.addedItems
    data_source_mock = MockDataSource()
    layer_1_curve = plot_item.addCurve(
        layer_identifier="layer_1",
        data_source=data_source_mock,
    )
    window.time_source_mock.create_new_value(0.0)
    # Default layer already has elements in it (line at cycle start, cycle end, line for current time)
    empty_default_layer_items_count = len(default_layer_items)
    for item in default_layer_items:
        assert item in (
            plot_item._time_line,
            plot_item._cycle_start_line,
            plot_item._cycle_end_line,
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
    default_layer_curve = plot_item.addCurve(
        data_source=data_source_mock
    )
    # Create some updates for the new curve (without data no plotted curve)
    data_source_mock.create_new_value(timestamp=1.2, value=1.0)
    data_source_mock.create_new_value(timestamp=1.5, value=1.0)
    window.time_source_mock.create_new_value(2.0)
    default_layer_items = plot_item.get_layer_by_identifier("").view_box.addedItems
    # Layer 1 should not be affected by the new curve
    assert len(layer_1_items) == 1
    # The default layer should have the new items included
    assert (
        len(default_layer_items)
        == empty_default_layer_items_count + 1
    )
    assert default_layer_curve in default_layer_items
    assert default_layer_curve not in layer_1_items


def test_set_axis_range(qtbot):
    """ test_set_axis_range

    - Are the viewboxes's axes properly connected to each other?

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    plot_item.link_y_range_of_all_layers(link=False)
    layer_0 = plot_item.get_layer_by_identifier(layer_identifier="")
    layer_1 = plot_item.add_layer(
        identifier="layer_1",
        axis_label_kwargs={"text": "layer_1"},
    )
    layer_2 = plot_item.add_layer(
        identifier="layer_2",
        axis_label_kwargs={"text": "layer_2"},
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
    plot_item.link_y_range_of_all_layers(link=True)
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
    plot_item.link_y_range_of_all_layers(link=False)
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
    plot_item.link_y_range_of_all_layers(link=True)
    manual_range_change(layer_0, yRange=[-10, 20])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [-10, 20]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [-2, 13]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-8, 1]])
    # Check scaling in disconnected axes
    plot_item.link_y_range_of_all_layers(link=False)
    manual_range_change(layer_0, yRange=[0, 10])
    check_range(layer_0.view_box.targetRange(), [[-20, 20], [0, 10]])
    check_range(layer_1.view_box.targetRange(), [[-20, 20], [-2, 13]])
    check_range(layer_2.view_box.targetRange(), [[-20, 20], [-8, 1]])


def test_auto_range_all_layers_at_same_range(qtbot):
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    layer_0 = plot_item.get_layer_by_identifier("")
    layer_1 = plot_item.add_layer("layer_1")
    layer_2 = plot_item.add_layer("layer_2")
    plot_item.addItem(layer="", item=pg.PlotDataItem([0, 1], [0, 1]))
    plot_item.addItem(layer="layer_1", item=pg.PlotDataItem([0, 1], [2, -1]))
    plot_item.addItem(layer="layer_2", item=pg.PlotDataItem([0, 1], [5, 5]))
    layer_0.view_box.setRange(xRange=[-1.0, 2.0], yRange=[2.0, 3.0], padding=0.0)
    layer_1.view_box.setRange(xRange=[-1.0, 2.0], yRange=[2.0, 3.0], padding=0.0)
    layer_2.view_box.setRange(xRange=[-1.0, 2.0], yRange=[2.0, 3.0], padding=0.0)
    layer_0.view_box.autoRange(padding=0.0)
    check_range(layer_0.view_box.targetRange(), [[0.0, 1.0], [-1.0, 5.0]])
    check_range(layer_1.view_box.targetRange(), [[0.0, 1.0], [-1.0, 5.0]])
    check_range(layer_2.view_box.targetRange(), [[0.0, 1.0], [-1.0, 5.0]])


def test_auto_range_all_layers_at_different_range(qtbot):
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    plot_item = window.plot.plotItem
    layer_0 = plot_item.get_layer_by_identifier("")
    layer_1 = plot_item.add_layer(identifier="layer_1")
    layer_2 = plot_item.add_layer(identifier="layer_2")
    plot_item.addItem(layer="", item=pg.PlotDataItem([-10, 150], [0, 1]))
    plot_item.addItem(layer="layer_1", item=pg.PlotDataItem([0, 1], [1.0, 3.0]))
    plot_item.addItem(layer="layer_2", item=pg.PlotDataItem([250, 300, 350, 400], [-150.0, 0.0, -200.0, 100.0]))
    layer_0.view_box.setRange(xRange=[-1.0, 2.0], yRange=[3.0, 5.0], padding=0.0)
    layer_1.view_box.setRange(xRange=[-1.0, 2.0], yRange=[-2.0, 2.0], padding=0.0)
    layer_2.view_box.setRange(xRange=[-1.0, 2.0], yRange=[-200.0, -100.0], padding=0.0)
    # Autorange, check if also repeatable
    for i in range(0, 100):
        layer_0.view_box.autoRange(padding=0.0)
        check_range(layer_0.view_box.targetRange(), [[-10.0, 400.0], [0.0, 9.0]])
        check_range(layer_1.view_box.targetRange(), [[-10.0, 400.0], [-8.0, 10.0]])
        check_range(layer_2.view_box.targetRange(), [[-10.0, 400.0], [-350.0, 100.0]])


def check_range(actual_range: List[List[float]], expected_range: List[List[float]]):
    """Compare a viewboxes range with an expected range"""
    for actual, expected in list(zip(actual_range, expected_range)):
        # a bit of tolerance
        absolute_tolerance = 0.0025 * (expected[1] - expected[0])
        assert numpy.isclose(actual[0], expected[0], atol=absolute_tolerance)
        assert numpy.isclose(actual[1], expected[1], atol=absolute_tolerance)


def manual_range_change(layer: PlotItemLayer, **kwargs):
    """Simulate a manual range change in a viewbox by emitting the manual change signal before setting the range"""
    if not kwargs.get("padding"):
        kwargs["padding"] = 0.0
    layer.view_box.sigRangeChangedManually.emit(
        layer.view_box.state["mouseEnabled"]
    )  # Simulate Manual update by mouse
    layer.view_box.setRange(**kwargs)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                           Helper Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _prepare_sliding_pointer_plot_test_window(qtbot, cycle_size: int):
    """ Create a simple test window
    Args:
        qtbot: pytest-qt fixture to control pyqt applications
        cycle_size (int): Cycle size for the PlotItem
    """
    plot_config = ExPlotWidgetConfig(
        plotting_style=PlotWidgetStyle.SLIDING_POINTER,
        cycle_size=cycle_size,
        time_progress_line=True,
    )
    window = PlotWidgetTestWindow(plot_config, [])
    window.show()
    qtbot.addWidget(window)
    return window


def _create_values(amount: int = 20):
    x_values = numpy.random.randint(-amount, amount, amount)
    y_values = numpy.arange(0, amount)
    return x_values, y_values
