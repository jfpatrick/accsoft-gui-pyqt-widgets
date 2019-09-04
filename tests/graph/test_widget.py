# pylint: disable=missing-docstring

from datetime import datetime
from typing import Union, List, Tuple, Dict
import itertools

import pytest
import pyqtgraph as pg
import numpy as np

from accsoft_gui_pyqt_widgets.graph import (LiveBarGraphItem,
                                            LiveTimestampMarker,
                                            LiveInjectionBarGraphItem,
                                            LivePlotCurve,
                                            ExPlotItem, ExPlotWidget,
                                            ExPlotWidgetConfig, BarData,
                                            DataModelBasedItem,
                                            TimestampMarkerData, InjectionBarData,
                                            PlotWidgetStyle, PointData,
                                            RelativeTimeAxisItem,
                                            ScrollingBarGraphItem,
                                            ScrollingTimestampMarker,
                                            ScrollingInjectionBarGraphItem,
                                            ScrollingPlotCurve,
                                            SlidingPointerPlotCurve,
                                            TimeAxisItem,
                                            UpdateSource)

from .mock_utils.mock_data_source import MockDataSource
from .mock_utils.widget_test_window import PlotWidgetTestWindow, MinimalTestWindow


def check_axis_strings(plot_item: ExPlotItem, style: PlotWidgetStyle) -> bool:
    """
    Check if the axes are showing the expected text at each tick

    Args:
        plot_item (ExPlotItem):
        style (PlotWidgetStyle):

    Returns:
        True, if the Axis item processes the values as expected
    """

    values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    if style == PlotWidgetStyle.SLIDING_POINTER:
        expected = ["0.0s", "+1.0s", "+2.0s", "+3.0s", "+4.0s", "+5.0s"]
        type_correct = isinstance(plot_item.getAxis("bottom"), RelativeTimeAxisItem)
        strings_correct = plot_item.getAxis("bottom").tickStrings(values, 1, 1) == expected
        return type_correct and strings_correct
    if style == PlotWidgetStyle.SCROLLING_PLOT:
        expected = [
            datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values
        ]
        type_correct = isinstance(plot_item.getAxis("bottom"), TimeAxisItem)
        strings_correct = plot_item.getAxis("bottom").tickStrings(values, 1, 1) == expected
        return type_correct and strings_correct
    return False


# pylint: disable=too-many-arguments
@pytest.mark.parametrize("cycle_size", [2, 100])
@pytest.mark.parametrize("plotting_style", [
    PlotWidgetStyle.SCROLLING_PLOT,
    PlotWidgetStyle.SLIDING_POINTER
])
@pytest.mark.parametrize("time_line", [False, True])
@pytest.mark.parametrize("item_to_add", [
    (LivePlotCurve, "curve"),
    (LiveBarGraphItem, "bargraph"),
    (LiveTimestampMarker, "injectionbar"),
    (LiveInjectionBarGraphItem, ""),
])
def test_all_available_widget_configurations(
    qtbot,
    cycle_size: int,
    plotting_style: PlotWidgetStyle,
    time_line: bool,
    item_to_add: Tuple[DataModelBasedItem, str, Dict]
):
    """Iterate through the possible combinations of parameters when creating
     a new PlotWidget and check if all elements are created as expected.

    Args:
        qtbot:
        cycle_size: cycle size to use
        plotting_style: plotting style to use
        time_line: should a line at the current timestamp be drawn
        item_to_add: Type of data-item to add and the key for getting the fitting opts
    """
    # pylint: disable=too-many-locals,protected-access

    plot_config = ExPlotWidgetConfig(
        cycle_size=cycle_size,
        plotting_style=plotting_style,
        time_progress_line=time_line,
    )
    window = PlotWidgetTestWindow(
        plot_config=plot_config,
        item_to_add=item_to_add[0],
        opts=_test_change_plot_config_on_running_plot_opts.get(item_to_add[1], {})
    )
    window.show()
    qtbot.addWidget(window)
    time_1, time_2 = 0.0, 1.0
    data_x, data_y = 0.75, 5.25
    window.time_source_mock.create_new_value(time_1)
    emit_fitting_value(item_to_add, window.data_source_mock, data_x, data_y)
    window.time_source_mock.create_new_value(time_2)
    assert isinstance(window.plot, ExPlotWidget)
    plot_item: ExPlotItem = window.plot.plotItem
    check_plot_curves(item_to_add, plot_item, time_2)
    check_bargraph(item_to_add, plot_item, time_2)
    check_injectionbar_graph(item_to_add, plot_item, time_2)
    assert check_axis_strings(plot_item, plotting_style)


_test_change_plot_config_on_running_plot_cycle_size_change = list(itertools.product([10.0, 30.0], [10.0, 30.0]))
_test_change_plot_config_on_running_plot_x_offset_change = list(itertools.product([-5.0, 0.0, 5.0], [-5.0, 0.0, 5.0]))
_test_change_plot_config_on_running_plot_plotting_style_change = list(itertools.product(
    [PlotWidgetStyle.SCROLLING_PLOT, PlotWidgetStyle.SLIDING_POINTER],
    [PlotWidgetStyle.SCROLLING_PLOT, PlotWidgetStyle.SLIDING_POINTER]
))
_test_change_plot_config_on_running_plot_time_line_change = list(itertools.product([True, False], [True, False]))
_test_change_plot_config_on_running_plot_opts = {
    "curve": {
        "symbol": "o",
        "pen": "g",
        "symbolPen": "w",
    },
    "bargraph": {
        "pen": "r",
        "brush": "b",
        "width": 0.3,
    },
    "injectionbar": {
        "pen": "r",
    }
}


@pytest.mark.parametrize("cycle_size_change", _test_change_plot_config_on_running_plot_cycle_size_change)
@pytest.mark.parametrize("x_offset_change", _test_change_plot_config_on_running_plot_x_offset_change)
@pytest.mark.parametrize("plotting_style_change", _test_change_plot_config_on_running_plot_plotting_style_change)
@pytest.mark.parametrize("time_line_change", _test_change_plot_config_on_running_plot_time_line_change)
def test_change_plot_config_on_running_plot(
    qtbot,
    cycle_size_change: List[float],
    x_offset_change: List[float],
    plotting_style_change: List[PlotWidgetStyle],
    time_line_change: List[bool]
):
    """Test if changes in the configuration are applied correctly in an already running plot"""
    plot_config_before_change = ExPlotWidgetConfig(
        cycle_size=cycle_size_change[0],
        plotting_style=plotting_style_change[0],
        time_progress_line=time_line_change[0],
        x_range_offset=x_offset_change[0]
    )
    plot_config_after_change = ExPlotWidgetConfig(
        cycle_size=cycle_size_change[1],
        plotting_style=plotting_style_change[1],
        time_progress_line=time_line_change[1],
        x_range_offset=x_offset_change[1]
    )
    window = MinimalTestWindow(
        plot_config=plot_config_before_change,
    )
    qtbot.waitForWindowShown(window)
    plotwidget: ExPlotWidget = window.plot
    ds_curve = MockDataSource()
    ds_bar = MockDataSource()
    ds_injection = MockDataSource()
    ds_line = MockDataSource()
    plotwidget.addCurve(
        data_source=ds_curve,
        **_test_change_plot_config_on_running_plot_opts["curve"]
    )
    emit_fitting_value(LivePlotCurve, ds_curve, 10.0, 0.0)
    emit_fitting_value(LivePlotCurve, ds_curve, 20.0, 0.0)
    emit_fitting_value(LivePlotCurve, ds_curve, 30.0, 0.0)
    if PlotWidgetStyle.SLIDING_POINTER not in plotting_style_change:
        # Bar graph in its own layer
        plotwidget.add_layer(identifier="layer_1")
        plotwidget.addBarGraph(
            data_source=ds_bar,
            layer_identifier="layer_1",
            **_test_change_plot_config_on_running_plot_opts["bargraph"]
        )
        emit_fitting_value(LiveBarGraphItem, ds_bar, 10.0, 0.0)
        emit_fitting_value(LiveBarGraphItem, ds_bar, 20.0, 0.0)
        emit_fitting_value(LiveBarGraphItem, ds_bar, 30.0, 0.0)
        # Injection bar Graph in its own layer
        plotwidget.add_layer(identifier="layer_2")
        plotwidget.addInjectionBar(
            data_source=ds_injection,
            layer_identifier="layer_2",
            **_test_change_plot_config_on_running_plot_opts["injectionbar"]
        )
        emit_fitting_value(LiveInjectionBarGraphItem, ds_injection, 10.0, 0.0)
        emit_fitting_value(LiveInjectionBarGraphItem, ds_injection, 20.0, 0.0)
        emit_fitting_value(LiveInjectionBarGraphItem, ds_injection, 30.0, 0.0)
        # Infinite Lines in its own layer
        plotwidget.addTimestampMarker(data_source=ds_line)
        emit_fitting_value(LiveTimestampMarker, ds_line, 10.0, 0.0)
        emit_fitting_value(LiveTimestampMarker, ds_line, 20.0, 0.0)
        emit_fitting_value(LiveTimestampMarker, ds_line, 30.0, 0.0)
    check_scrolling_plot_with_fixed_x_range(
        cycle_size_change=cycle_size_change[0],
        x_offset_change=x_offset_change[0],
        plotting_style_change=plotting_style_change[0],
        plotwidget=plotwidget,
    )
    plotwidget.update_configuration(plot_config_after_change)
    check_scrolling_plot_with_fixed_x_range(
        cycle_size_change=cycle_size_change[1],
        x_offset_change=x_offset_change[1],
        plotting_style_change=plotting_style_change[1],
        plotwidget=plotwidget,
    )


@pytest.mark.parametrize("plotting_style", [
    PlotWidgetStyle.SCROLLING_PLOT,
    PlotWidgetStyle.SLIDING_POINTER
])
def test_set_view_range(qtbot, plotting_style):
    """
    Test if the ViewRange can be set as expected from the PlotWidget
    as well as from the PlotItem
    """
    config = ExPlotWidgetConfig(
        plotting_style=plotting_style
    )
    window = MinimalTestWindow(plot_config=config)
    window.show()
    qtbot.waitForWindowShown(window)
    plot_widget = window.plot
    plot_item = plot_widget.plotItem
    source = UpdateSource()
    curve: LivePlotCurve = plot_item.addCurve(data_source=source)
    source.sig_data_update[PointData].emit(PointData(0.0, 0.0))
    # Set Range on PlotWidget
    expected = [[-2.5, 2.5], [-1.5, 1.5]]
    plot_widget.setXRange(expected[0][0], expected[0][1], padding=0.0)
    plot_widget.setYRange(expected[1][0], expected[1][1], padding=0.0)
    source.sig_data_update[PointData].emit(PointData(0.0, 0.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Set Range on PlotItem
    expected = [[-4.5, 4.5], [-3.5, 3.5]]
    plot_item.setXRange(expected[0][0], expected[0][1], padding=0.0)
    plot_item.setYRange(expected[1][0], expected[1][1], padding=0.0)
    source.sig_data_update[PointData].emit(PointData(1.0, 1.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Set Range on PlotItem
    expected = [[-2.5, 2.5], [-1.5, 1.5]]
    plot_item.setRange(xRange=expected[0], yRange=expected[1], padding=0.0)
    source.sig_data_update[PointData].emit(PointData(2.0, 2.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Set Range on PlotWidget
    expected = [[-4.5, 4.5], [-3.5, 3.5]]
    plot_item.setRange(xRange=expected[0], yRange=expected[1], padding=0.0)
    source.sig_data_update[PointData].emit(PointData(3.0, 3.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Auto Range (to see if still possible after setting range by hand)
    plot_widget.autoRange(padding=0.0)
    if plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        expected = [[0.0, 3.0], [0.0, 3.0]]
    elif plotting_style == PlotWidgetStyle.SLIDING_POINTER:
        expected = [
            [plot_item._cycle_start_line.pos()[0], plot_item._cycle_end_line.pos()[0]],
            [0.0, 3.0]
        ]
    source.sig_data_update[PointData].emit(PointData(4.0, 4.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected), atol=0.1)


def check_scrolling_plot_with_fixed_x_range(
    cycle_size_change: float,
    x_offset_change: float,
    plotting_style_change: PlotWidgetStyle,
    plotwidget: ExPlotWidget,
):
    """Check (if the config fits) if the fixed x range on the scrolling plot is set right."""
    if plotting_style_change == PlotWidgetStyle.SCROLLING_PLOT:
        for vb in plotwidget.plotItem.get_all_viewboxes():
            check_range(actual_range=vb.targetRange(), expected_range=[
                [(30.0 + x_offset_change)-cycle_size_change, 30.0 + x_offset_change],
                [np.nan, np.nan]
            ])


def check_range(actual_range: List[List[float]], expected_range: List[List[float]]):
    """Compare a view boxes range with an expected range"""
    for actual, expected in list(zip(actual_range, expected_range)):
        # a bit of tolerance
        absolute_tolerance = 0.0025 * (expected[1] - expected[0])
        if not np.isnan(expected[0]):
            assert np.isclose(actual[0], expected[0], atol=absolute_tolerance)
        if not np.isnan(expected[1]):
            assert np.isclose(actual[1], expected[1], atol=absolute_tolerance)


def emit_fitting_value(item_to_add, data_source, data_x: float, data_y: float):
    """Emit a the fitting data for the type of the added item"""
    if item_to_add == LivePlotCurve or isinstance(item_to_add, str) and item_to_add == "ScatterPlot":
        point = PointData(
            x_value=data_x,
            y_value=data_y
        )
        data_source.emit_new_object(point)
    elif item_to_add == LiveBarGraphItem:
        bar = BarData(
            x_value=data_x,
            y_value=data_y,
            height=data_y
        )
        data_source.emit_new_object(bar)
    elif item_to_add == LiveInjectionBarGraphItem:
        i_bar = InjectionBarData(
            x_value=data_x,
            y_value=data_y,
            height=data_y,
            width=1,
            label=str(data_x)
        )
        data_source.emit_new_object(i_bar)
    elif item_to_add == LiveTimestampMarker:
        line = TimestampMarkerData(
            x_value=data_x,
            color="r",
            label=str(data_x)
        )
        data_source.emit_new_object(line)


def check_plot_curves(
        item_to_add: Union[DataModelBasedItem, str],
        plot_item: ExPlotItem,
        time_2: float,
):
    """Check if the curve is created correctly"""
    if item_to_add == LivePlotCurve or isinstance(item_to_add, str) and item_to_add == "ScatterPlot":
        assert len(plot_item.get_live_data_bar_graphs()) == 0
        assert len(plot_item.get_live_data_injection_bars()) == 0
        assert len(plot_item.get_timestamp_markers()) == 0
        assert len(plot_item.get_live_data_curves()) == 1
        curve: LivePlotCurve = plot_item.get_live_data_curves()[0]
        # Check if all opts are set properly and also kept after change
        # These carry information like color over to the changed item
        for opt in _test_change_plot_config_on_running_plot_opts["curve"]:
            expected = _test_change_plot_config_on_running_plot_opts["curve"][opt]
            assert curve.opts.get(opt, None) == expected
        if plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            assert isinstance(curve, ScrollingPlotCurve)
        elif plot_item._plot_config.plotting_style == PlotWidgetStyle.SLIDING_POINTER:
            assert isinstance(curve, SlidingPointerPlotCurve)
        assert isinstance(plot_item._time_line, pg.InfiniteLine)
        assert plot_item._time_line.value() == time_2


def check_bargraph(
        item_to_add: Union[DataModelBasedItem, str],
        plot_item: ExPlotItem,
        time_2: float
):
    """Check if the bargraph is created correctly"""
    if item_to_add == LiveBarGraphItem and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.get_live_data_curves()) == 0
        assert len(plot_item.get_live_data_bar_graphs()) == 1
        assert len(plot_item.get_live_data_injection_bars()) == 0
        assert len(plot_item.get_timestamp_markers()) == 0
        bargraph: LiveBarGraphItem = plot_item.get_live_data_bar_graphs()[0]
        assert isinstance(bargraph, ScrollingBarGraphItem)
        assert isinstance(plot_item._time_line, pg.InfiniteLine)
        assert plot_item._time_line.value() == time_2
        # Check if the fixed bar width is set correctly
        assert bargraph._fixed_bar_width == 0.25
        # Check if all opts are set properly and also kept after change
        # These carry information like color over to the changed item
        for opt in _test_change_plot_config_on_running_plot_opts["bargraph"]:
            expected = _test_change_plot_config_on_running_plot_opts["bargraph"][opt]
            assert bargraph.opts.get(opt, None) == expected


def check_injectionbar_graph(
        item_to_add: Union[DataModelBasedItem, str],
        plot_item: ExPlotItem,
        time_2: float
):
    """Check if the injection are created correctly"""
    if item_to_add == LiveInjectionBarGraphItem and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.get_live_data_curves()) == 0
        assert len(plot_item.get_live_data_bar_graphs()) == 0
        assert len(plot_item.get_live_data_injection_bars()) == 1
        assert len(plot_item.get_timestamp_markers()) == 0
        injection_bargraph: LiveInjectionBarGraphItem = plot_item.get_live_data_injection_bars()[0]
        assert isinstance(injection_bargraph, ScrollingInjectionBarGraphItem)
        assert isinstance(plot_item._time_line, pg.InfiniteLine)
        assert plot_item._time_line.value() == time_2
        # Check if all opts are set properly and also kept after change
        # These carry information like color over to the changed item
        for opt in _test_change_plot_config_on_running_plot_opts["injectionbar"]:
            expected = _test_change_plot_config_on_running_plot_opts["injectionbar"][opt]
            assert injection_bargraph.opts.get(opt, None) == expected


def check_timestamp_markers(
        item_to_add: Union[DataModelBasedItem, str],
        plot_item: ExPlotItem,
        time_2: float
):
    """Check if the timestamp markers are created correctly"""
    if item_to_add == LiveTimestampMarker and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.get_live_data_curves()) == 0
        assert len(plot_item.get_live_data_bar_graphs()) == 0
        assert len(plot_item.get_live_data_injection_bars()) == 0
        assert len(plot_item.get_timestamp_markers()) == 1
        infinite_lines: LiveTimestampMarker = plot_item.get_timestamp_markers()[0]
        assert isinstance(infinite_lines, ScrollingTimestampMarker)
        assert isinstance(plot_item._time_line, pg.InfiniteLine)
        assert plot_item._time_line.value() == time_2
