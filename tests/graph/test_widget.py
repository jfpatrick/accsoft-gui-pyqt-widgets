from datetime import datetime
from typing import Union, List, Tuple, Dict, Type, Optional, cast
import itertools

import pytest
import pyqtgraph as pg
import numpy as np

from accwidgets.graph import (
    LiveBarGraphItem,
    LiveTimestampMarker,
    LiveInjectionBarGraphItem,
    LivePlotCurve,
    StaticPlotCurve,
    StaticBarGraphItem,
    StaticInjectionBarGraphItem,
    StaticTimestampMarker,
    ExPlotItem,
    ExPlotWidget,
    ExPlotWidgetConfig,
    BarData,
    DataModelBasedItem,
    TimestampMarkerData,
    InjectionBarData,
    PlotWidgetStyle,
    PointData,
    RelativeTimeAxisItem,
    ScrollingBarGraphItem,
    ScrollingTimestampMarker,
    ScrollingInjectionBarGraphItem,
    ScrollingPlotCurve,
    CyclicPlotCurve,
    TimeAxisItem,
    UpdateSource,
    TimeSpan,
)

from .mock_utils.mock_data_source import MockDataSource
from .mock_utils.widget_test_window import PlotWidgetTestWindow, MinimalTestWindow


def check_axis_strings(plot_item: ExPlotItem, style: PlotWidgetStyle) -> bool:
    """
    Check if the axes are showing the expected text at each tick

    Args:
        plot_item: Plot item which's axes should be checked
        style: Expected style for the plot item which the axes depend on

    Returns:
        True, if the Axis item processes the values as expected
    """

    values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    if style == PlotWidgetStyle.CYCLIC_PLOT:
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


@pytest.mark.parametrize("item_to_add", [
    StaticPlotCurve,
    StaticBarGraphItem,
    StaticInjectionBarGraphItem,
    StaticTimestampMarker,
])
def test_static_plot_widget_creation(
        qtbot,
        item_to_add: Type[DataModelBasedItem],
) -> None:
    window = PlotWidgetTestWindow(
        plot_config=ExPlotWidgetConfig(
            plotting_style=PlotWidgetStyle.STATIC_PLOT,
        ),
        item_to_add=item_to_add)
    window.show()
    qtbot.addWidget(window)
    assert len(window.plot.plotItem.data_model_items) == 1
    assert isinstance(window.plot.plotItem.data_model_items[0], item_to_add)


@pytest.mark.parametrize("time_span", [2, 100])
@pytest.mark.parametrize("plotting_style", [
    PlotWidgetStyle.SCROLLING_PLOT,
    PlotWidgetStyle.CYCLIC_PLOT,
])
@pytest.mark.parametrize("time_line", [False, True])
@pytest.mark.parametrize("item_to_add", [
    (LivePlotCurve, "curve"),
    (LiveBarGraphItem, "bargraph"),
    (LiveTimestampMarker, "injectionbar"),
    (LiveInjectionBarGraphItem, ""),
])
def test_live_plot_widget_creation(
    qtbot,
    time_span: int,
    plotting_style: PlotWidgetStyle,
    time_line: bool,
    item_to_add: Tuple[Type[DataModelBasedItem], str, Dict],
):
    """Iterate through the possible combinations of parameters when creating
     a new PlotWidget and check if all elements are created as expected.

    Args:
        qtbot:
        time_span: time span size to use
        plotting_style: plotting style to use
        time_line: should a line at the current timestamp be drawn
        item_to_add: Type of data-item to add and the key for getting the fitting opts
    """
    plot_config = ExPlotWidgetConfig(
        time_span=time_span,
        plotting_style=plotting_style,
        time_progress_line=time_line,
    )
    window = PlotWidgetTestWindow(
        plot_config=plot_config,
        item_to_add=item_to_add[0],
        opts=_test_change_plot_config_on_running_plot_opts.get(item_to_add[1], {}),
    )
    if window.time_source_mock is None:
        raise ValueError("Timing Source for the test window was not created as expected.")
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


_test_change_plot_config_on_running_plot_time_span_change = list(itertools.product([10.0, 30.0], [10.0, 30.0]))
_test_change_plot_config_on_running_plot_x_offset_change = list(itertools.product([-5.0, 0.0, 5.0], [-5.0, 0.0, 5.0]))
_test_change_plot_config_on_running_plot_plotting_style_change = list(itertools.product(
    [PlotWidgetStyle.SCROLLING_PLOT, PlotWidgetStyle.CYCLIC_PLOT],
    [PlotWidgetStyle.SCROLLING_PLOT, PlotWidgetStyle.CYCLIC_PLOT],
))
_test_change_plot_config_on_running_plot_time_line_change = list(itertools.product([True, False], [True, False]))
_test_change_plot_config_on_running_plot_opts: Dict[str, Dict[str, Union[str, float]]] = {
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
    },
}


@pytest.mark.parametrize("time_span_change", _test_change_plot_config_on_running_plot_time_span_change)
@pytest.mark.parametrize("x_offset_change", _test_change_plot_config_on_running_plot_x_offset_change)
@pytest.mark.parametrize("plotting_style_change", _test_change_plot_config_on_running_plot_plotting_style_change)
@pytest.mark.parametrize("time_line_change", _test_change_plot_config_on_running_plot_time_line_change)
def test_change_plot_config_on_running_plot(
    qtbot,
    time_span_change: List[float],
    x_offset_change: List[float],
    plotting_style_change: List[PlotWidgetStyle],
    time_line_change: List[bool],
):
    """Test if changes in the configuration are applied correctly in an already running plot"""
    left = time_span_change[0] - x_offset_change[0]
    right = -x_offset_change[0]
    plot_config_before_change = ExPlotWidgetConfig(
        time_span=TimeSpan(
            left=left,
            right=right,
        ),
        plotting_style=plotting_style_change[0],
        time_progress_line=time_line_change[0],
    )
    window = MinimalTestWindow(
        plot=plot_config_before_change,
    )
    qtbot.waitForWindowShown(window)
    plotwidget: ExPlotWidget = window.plot
    ds_curve = MockDataSource()
    ds_bar = MockDataSource()
    ds_injection = MockDataSource()
    ds_line = MockDataSource()
    plotwidget.addCurve(
        data_source=ds_curve,
        **_test_change_plot_config_on_running_plot_opts["curve"],  # type: ignore
    )
    emit_fitting_value(LivePlotCurve, ds_curve, 10.0, 0.0)
    emit_fitting_value(LivePlotCurve, ds_curve, 20.0, 0.0)
    emit_fitting_value(LivePlotCurve, ds_curve, 30.0, 0.0)
    if PlotWidgetStyle.CYCLIC_PLOT not in plotting_style_change:
        # Bar graph in its own layer
        plotwidget.add_layer(layer_id="layer_1")
        plotwidget.addBarGraph(  # type: ignore
            data_source=ds_bar,
            layer="layer_1",
            **_test_change_plot_config_on_running_plot_opts["bargraph"],  # type: ignore
        )
        emit_fitting_value(LiveBarGraphItem, ds_bar, 10.0, 0.0)
        emit_fitting_value(LiveBarGraphItem, ds_bar, 20.0, 0.0)
        emit_fitting_value(LiveBarGraphItem, ds_bar, 30.0, 0.0)
        # Injection bar Graph in its own layer
        plotwidget.add_layer(layer_id="layer_2")
        plotwidget.addInjectionBar(  # type: ignore
            data_source=ds_injection,
            layer="layer_2",
            **_test_change_plot_config_on_running_plot_opts["injectionbar"],  # type: ignore
        )
        emit_fitting_value(LiveInjectionBarGraphItem, ds_injection, 10.0, 0.0)
        emit_fitting_value(LiveInjectionBarGraphItem, ds_injection, 20.0, 0.0)
        emit_fitting_value(LiveInjectionBarGraphItem, ds_injection, 30.0, 0.0)
        # Infinite Lines in its own layer
        plotwidget.addTimestampMarker(data_source=ds_line)
        emit_fitting_value(LiveTimestampMarker, ds_line, 10.0, 0.0)
        emit_fitting_value(LiveTimestampMarker, ds_line, 20.0, 0.0)
        emit_fitting_value(LiveTimestampMarker, ds_line, 30.0, 0.0)
    check_scrolling_plot_with_fixed_xrange(
        time_span_change=time_span_change[0],
        x_offset_change=x_offset_change[0] if plotting_style_change[0] == PlotWidgetStyle.SCROLLING_PLOT else 0,
        plotting_style_change=plotting_style_change[0],
        plotwidget=plotwidget,
    )
    check_decorators(plot_item=plotwidget.plotItem)
    items = [
        plotwidget.plotItem._time_line,
        plotwidget.plotItem._time_span_start_boundary,
        plotwidget.plotItem._time_span_end_boundary,
    ]
    left = time_span_change[1] - x_offset_change[1]
    right = -x_offset_change[1]
    plot_config_after_change = ExPlotWidgetConfig(
        time_span=TimeSpan(
            left=left,
            right=right,
        ),
        plotting_style=plotting_style_change[1],
        time_progress_line=time_line_change[1],
    )
    plotwidget.update_config(plot_config_after_change)
    check_scrolling_plot_with_fixed_xrange(
        time_span_change=time_span_change[1],
        x_offset_change=x_offset_change[1],
        plotting_style_change=plotting_style_change[1],
        plotwidget=plotwidget,
    )
    check_decorators(plot_item=plotwidget.plotItem, prior_items=items)


@pytest.mark.parametrize("plotting_style", [
    PlotWidgetStyle.CYCLIC_PLOT,
])
def test_set_view_range(qtbot, plotting_style: PlotWidgetStyle):
    """
    Test if the ViewRange can be set as expected from the PlotWidget
    as well as from the PlotItem
    """
    config = ExPlotWidgetConfig(
        time_span=TimeSpan(60),
        plotting_style=plotting_style,
    )
    window = MinimalTestWindow(plot=config)
    window.show()
    qtbot.waitForWindowShown(window)
    plot_widget = window.plot
    plot_item = plot_widget.plotItem
    source = UpdateSource()
    plot_item.addCurve(data_source=source)
    source.send_data(PointData(0.0, 0.0))
    # Set Range on PlotWidget
    expected = ((-2.5, 2.5), (-1.5, 1.5))
    plot_widget.setXRange(expected[0][0], expected[0][1], padding=0.0)
    plot_widget.setYRange(expected[1][0], expected[1][1], padding=0.0)
    source.send_data(PointData(0.0, 0.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Set Range on PlotItem
    expected = ((-4.5, 4.5), (-3.5, 3.5))
    plot_item.setXRange(expected[0][0], expected[0][1], padding=0.0)
    plot_item.setYRange(expected[1][0], expected[1][1], padding=0.0)
    source.send_data(PointData(1.0, 1.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Set Range on PlotItem
    expected = ((-2.5, 2.5), (-1.5, 1.5))
    plot_item.setRange(xRange=expected[0], yRange=expected[1], padding=0.0)
    source.send_data(PointData(2.0, 2.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Set Range on PlotWidget
    expected = ((-4.5, 4.5), (-3.5, 3.5))
    plot_item.setRange(xRange=expected[0], yRange=expected[1], padding=0.0)
    source.send_data(PointData(3.0, 3.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected))
    # Auto Range (to see if still possible after setting range by hand)
    plot_widget.autoRange(padding=0.0)
    if plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        expected = ((0.0, 3.0), (0.0, 3.0))
    elif plotting_style == PlotWidgetStyle.CYCLIC_PLOT:
        start_boundary = cast(pg.InfiniteLine, plot_item._time_span_start_boundary)
        end_boundary = cast(pg.InfiniteLine, plot_item._time_span_end_boundary)
        expected = (
            (start_boundary.pos()[0], end_boundary.pos()[0]),
            (0.0, 3.0),
        )
    source.send_data(PointData(4.0, 4.0))
    actual = plot_item.vb.targetRange()
    assert np.allclose(np.array(actual), np.array(expected), atol=0.1)


@pytest.mark.parametrize("config_style_change", [
    (PlotWidgetStyle.SCROLLING_PLOT, PlotWidgetStyle.CYCLIC_PLOT),
    (PlotWidgetStyle.SCROLLING_PLOT, PlotWidgetStyle.SCROLLING_PLOT),
])
def test_static_items_config_change(qtbot, config_style_change):
    """
    Test if live data items as well as pure pyqtgraph items are still
    present after switching the plot-items configuration
    """
    config = ExPlotWidgetConfig(
        plotting_style=config_style_change[0],
    )
    window = MinimalTestWindow(plot=config)
    window.show()
    qtbot.waitForWindowShown(window)
    plot_widget = window.plot
    plot_item = plot_widget.plotItem
    source = UpdateSource()
    items = [
        plot_item.addCurve(data_source=source),
        pg.PlotDataItem([0.0, 1.0, 2.0]),
        pg.InfiniteLine(pos=0.0, angle=0),
    ]
    for item in items:
        plot_item.addItem(item)
    source.send_data(PointData(0.0, 0.0))
    for item in items:
        assert item in plot_item.vb.addedItems
    config = ExPlotWidgetConfig(
        plotting_style=config_style_change[1],
    )
    plot_item.update_config(config=config)
    for item in items:
        assert item in plot_item.vb.addedItems


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                           Checker Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def check_scrolling_plot_with_fixed_xrange(
    time_span_change: float,
    x_offset_change: float,
    plotting_style_change: PlotWidgetStyle,
    plotwidget: ExPlotWidget,
):
    """Check (if the config fits) if the fixed x range on the scrolling plot is set right."""
    if plotting_style_change == PlotWidgetStyle.SCROLLING_PLOT:
        for view_box in plotwidget.plotItem.view_boxes:
            check_range(actual_range=view_box.targetRange(), expected_range=[
                [(30.0 + x_offset_change) - time_span_change, 30.0 + x_offset_change],
                [np.nan, np.nan],
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


def check_decorators(
        plot_item: ExPlotItem,
        prior_items: Optional[List] = None,
):
    """Check if all possible decorators are drawn correctly"""
    if prior_items is None:
        prior_items = [None, None, None]
    check_bottom_axis(plot_item=plot_item)
    check_time_line(plot_item=plot_item, prior_item=prior_items[0])
    check_cyclic_time_span_boundaries(plot_item=plot_item, prior_items=prior_items[1:])


def check_bottom_axis(plot_item: ExPlotItem):
    """Check if the bottom axis is the right one"""
    expected = type(plot_item._create_fitting_axis_item(config_style=plot_item.plot_config.plotting_style))
    assert isinstance(plot_item.getAxis("bottom"), expected)


def check_time_line(
        plot_item: ExPlotItem,
        prior_item: Optional[pg.InfiniteLine] = None,
):
    """Check if the timeline is created according to the ExPlotItems config"""
    time_line_drawn = plot_item.plot_config.time_progress_line
    if time_line_drawn:
        assert plot_item._time_line is not None
        assert plot_item._time_line in plot_item.items
        assert plot_item._time_line in plot_item.vb.addedItems
    else:
        assert plot_item._time_line is None
        # Check if removal was done properly
        if prior_item is not None:
            assert prior_item not in plot_item.items
            assert prior_item not in plot_item.vb.addedItems


def check_cyclic_time_span_boundaries(
        plot_item: ExPlotItem,
        prior_items: Optional[List] = None,
):
    """Check if the time span boundaries on a sliding pointer plot are set correctly"""
    if prior_items is None:
        prior_items = []
    boundaries_drawn = plot_item.plot_config.plotting_style == PlotWidgetStyle.CYCLIC_PLOT
    if boundaries_drawn:
        assert (plot_item._time_span_start_boundary is not None and plot_item._time_span_end_boundary is not None)
        assert plot_item._time_span_start_boundary in plot_item.items
        assert plot_item._time_span_start_boundary in plot_item.vb.addedItems
        assert plot_item._time_span_end_boundary in plot_item.items
        assert plot_item._time_span_end_boundary in plot_item.vb.addedItems
    else:
        assert (plot_item._time_span_start_boundary is None and plot_item._time_span_end_boundary is None)
        if prior_items:
            assert (prior_items[0] is None and prior_items[0] is None) or (prior_items[0] is not None and prior_items[0] is not None)
            for prior_item in prior_items:
                if prior_item:
                    assert prior_item not in plot_item.items
                    assert prior_item not in plot_item.vb.addedItems


def emit_fitting_value(item_to_add, data_source, data_x: float, data_y: float):
    """Emit a the fitting data for the type of the added item"""
    if item_to_add == LivePlotCurve or isinstance(item_to_add, str) and item_to_add == "ScatterPlot":
        point = PointData(
            x=data_x,
            y=data_y,
        )
        data_source.emit_new_object(point)
    elif item_to_add == LiveBarGraphItem:
        bar = BarData(
            x=data_x,
            y=data_y,
            height=data_y,
        )
        data_source.emit_new_object(bar)
    elif item_to_add == LiveInjectionBarGraphItem:
        i_bar = InjectionBarData(
            x=data_x,
            y=data_y,
            height=data_y,
            width=1,
            label=str(data_x),
        )
        data_source.emit_new_object(i_bar)
    elif item_to_add == LiveTimestampMarker:
        line = TimestampMarkerData(
            x=data_x,
            color="r",
            label=str(data_x),
        )
        data_source.emit_new_object(line)


def check_plot_curves(
        item_to_add: Tuple[Type[DataModelBasedItem], str, Dict],
        plot_item: ExPlotItem,
        time_2: float,
):
    """Check if the curve is created correctly"""
    if item_to_add == LivePlotCurve or isinstance(item_to_add, str) and item_to_add == "ScatterPlot":
        assert len(plot_item.live_bar_graphs) == 0
        assert len(plot_item.live_injection_bars) == 0
        assert len(plot_item.live_timestamp_markers) == 0
        assert len(plot_item.live_curves) == 1
        curve: LivePlotCurve = plot_item.live_curves[0]
        # Check if all opts are set properly and also kept after change
        # These carry information like color over to the changed item
        for opt in _test_change_plot_config_on_running_plot_opts["curve"]:
            expected = _test_change_plot_config_on_running_plot_opts["curve"][opt]
            assert curve.opts.get(opt, None) == expected
        if plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            assert isinstance(curve, ScrollingPlotCurve)
        elif plot_item._plot_config.plotting_style == PlotWidgetStyle.CYCLIC_PLOT:
            assert isinstance(curve, CyclicPlotCurve)
        assert isinstance(plot_item._time_line, pg.InfiniteLine)
        assert plot_item._time_line.value() == time_2


def check_bargraph(
        item_to_add: Tuple[Type[DataModelBasedItem], str, Dict],
        plot_item: ExPlotItem,
        time_2: float,
):
    """Check if the bargraph is created correctly"""
    if item_to_add == LiveBarGraphItem and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.live_curves) == 0
        assert len(plot_item.live_bar_graphs) == 1
        assert len(plot_item.live_injection_bars) == 0
        assert len(plot_item.live_timestamp_markers) == 0
        bargraph: LiveBarGraphItem = plot_item.live_bar_graphs[0]
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
        item_to_add: Tuple[Type[DataModelBasedItem], str, Dict],
        plot_item: ExPlotItem,
        time_2: float,
):
    """Check if the injection are created correctly"""
    if item_to_add == LiveInjectionBarGraphItem and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.live_curves) == 0
        assert len(plot_item.live_bar_graphs) == 0
        assert len(plot_item.live_injection_bars) == 1
        assert len(plot_item.live_timestamp_markers) == 0
        injection_bargraph: LiveInjectionBarGraphItem = plot_item.live_injection_bars[0]
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
        time_2: float,
):
    """Check if the timestamp markers are created correctly"""
    if item_to_add == LiveTimestampMarker and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.live_curves) == 0
        assert len(plot_item.live_bar_graphs) == 0
        assert len(plot_item.live_injection_bars) == 0
        assert len(plot_item.live_timestamp_markers) == 1
        infinite_lines: LiveTimestampMarker = plot_item.live_timestamp_markers[0]
        assert isinstance(infinite_lines, ScrollingTimestampMarker)
        assert isinstance(plot_item._time_line, pg.InfiniteLine)
        assert plot_item._time_line.value() == time_2
