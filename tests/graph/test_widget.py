# pylint: disable=missing-docstring

from datetime import datetime
from typing import Union

import pytest
from pyqtgraph import InfiniteLine, PlotDataItem

from accsoft_gui_pyqt_widgets.graph import (LiveBarGraphItem,
                                            LiveTimestampMarker,
                                            LiveInjectionBarGraphItem,
                                            LivePlotCurve,
                                            LivePlotCurveConfig,
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
                                            TimeAxisItem)

from .mock_utils.widget_test_window import PlotWidgetTestWindow


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
@pytest.mark.parametrize("v_line", [False, True])
@pytest.mark.parametrize("h_line", [False, True])
@pytest.mark.parametrize("point", [False, True])
@pytest.mark.parametrize("item_to_add", [
    "ScatterPlot",
    LivePlotCurve,
    LiveBarGraphItem,
    LiveTimestampMarker,
    LiveInjectionBarGraphItem
])
def test_all_available_widget_configurations(
    qtbot,
    cycle_size: int,
    plotting_style: PlotWidgetStyle,
    time_line: bool,
    v_line: bool,
    h_line: bool,
    point: bool,
    item_to_add: Union[DataModelBasedItem, str]
):
    """Iterate through the possible combinations of parameters when creating
     a new PlotWidget and check if all elements are created as expected.

    Args:
        qtbot:
        cycle_size (float):
        plotting_style (PlotWidgetStyle):
        time_line (bool):
        v_line (bool):
        h_line (bool):
        point (bool):
        item_to_add (Union[DataModelBasedItem, str]):
    """
    # pylint: disable=too-many-locals,protected-access

    plot_config = ExPlotWidgetConfig(
        cycle_size=cycle_size,
        plotting_style=plotting_style,
        time_progress_line=time_line,
    )
    curve_config = LivePlotCurveConfig(
        draw_vertical_line=v_line, draw_horizontal_line=h_line, draw_point=point
    )
    window = PlotWidgetTestWindow(plot_config=plot_config, curve_configs=[curve_config], item_to_add=item_to_add)
    window.show()
    qtbot.addWidget(window)
    time_1, time_2 = 0.0, 1.0
    data_x, data_y = 0.75, 5.25
    window.time_source_mock.create_new_value(time_1)
    emit_fitting_value(item_to_add, window.data_source_mock, data_x, data_y)
    window.time_source_mock.create_new_value(time_2)
    assert isinstance(window.plot, ExPlotWidget)
    plot_item: ExPlotItem = window.plot.plotItem
    check_plot_curves(item_to_add, plot_item, time_2, data_x, data_y, v_line, h_line, point)
    check_bargraph(item_to_add, plot_item, time_2)
    check_injectionbar_graph(item_to_add, plot_item, time_2)
    assert check_axis_strings(plot_item, plotting_style)


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
        data_x: float,
        data_y: float,
        v_line: bool,
        h_line: bool,
        point: bool
):
    """Check if the """
    if item_to_add == LivePlotCurve or isinstance(item_to_add, str) and item_to_add == "ScatterPlot":
        assert len(plot_item.get_live_data_curves()) == 1
        assert len(plot_item.get_live_data_bar_graphs()) == 0
        assert len(plot_item.get_live_data_injection_bars()) == 0
        assert len(plot_item.get_timestamp_markers()) == 0
        plot_data_item: LivePlotCurve = plot_item.get_live_data_curves()[0]
        if plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            assert isinstance(plot_data_item, ScrollingPlotCurve)
        elif plot_item._plot_config.plotting_style == PlotWidgetStyle.SLIDING_POINTER:
            assert isinstance(plot_data_item, SlidingPointerPlotCurve)
        assert isinstance(plot_item._time_line, InfiniteLine)
        assert plot_item._time_line.value() == time_2
        if v_line:
            assert isinstance(plot_data_item._decorators.vertical_line, InfiniteLine)
            assert plot_data_item._decorators.vertical_line.value() == data_x
        else:
            assert plot_data_item._decorators.vertical_line is None
        if h_line:
            assert isinstance(plot_data_item._decorators.horizontal_line, InfiniteLine)
            assert plot_data_item._decorators.horizontal_line.value() == data_y
        else:
            assert plot_data_item._decorators.horizontal_line is None
        if point:
            assert isinstance(plot_data_item._decorators.point, PlotDataItem)
            assert list(plot_data_item._decorators.point.getData()[0]) == [data_x]
            assert list(plot_data_item._decorators.point.getData()[1]) == [data_y]
        else:
            assert plot_data_item._decorators.point is None


def check_bargraph(
        item_to_add: Union[DataModelBasedItem, str],
        plot_item: ExPlotItem,
        time_2: float
):
    """Check if the """
    if item_to_add == LiveBarGraphItem and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.get_live_data_curves()) == 0
        assert len(plot_item.get_live_data_bar_graphs()) == 1
        assert len(plot_item.get_live_data_injection_bars()) == 0
        assert len(plot_item.get_timestamp_markers()) == 0
        bargraph: LiveBarGraphItem = plot_item.get_live_data_bar_graphs()[0]
        assert isinstance(bargraph, ScrollingBarGraphItem)
        assert isinstance(plot_item._time_line, InfiniteLine)
        assert plot_item._time_line.value() == time_2
        # Check if the fixed bar width is set correctly
        assert bargraph._fixed_bar_width == 0.25


def check_injectionbar_graph(
        item_to_add: Union[DataModelBasedItem, str],
        plot_item: ExPlotItem,
        time_2: float
):
    """Check if the """
    if item_to_add == LiveInjectionBarGraphItem and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.get_live_data_curves()) == 0
        assert len(plot_item.get_live_data_bar_graphs()) == 0
        assert len(plot_item.get_live_data_injection_bars()) == 1
        assert len(plot_item.get_timestamp_markers()) == 0
        bargraph: LiveInjectionBarGraphItem = plot_item.get_live_data_injection_bars()[0]
        assert isinstance(bargraph, ScrollingInjectionBarGraphItem)
        assert isinstance(plot_item._time_line, InfiniteLine)
        assert plot_item._time_line.value() == time_2


def check_infinite_lines(
        item_to_add: Union[DataModelBasedItem, str],
        plot_item: ExPlotItem,
        time_2: float
):
    """Check if the """
    if item_to_add == LiveTimestampMarker and plot_item._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
        assert len(plot_item.get_live_data_curves()) == 0
        assert len(plot_item.get_live_data_bar_graphs()) == 0
        assert len(plot_item.get_live_data_injection_bars()) == 0
        assert len(plot_item.get_timestamp_markers()) == 1
        bargraph: LiveTimestampMarker = plot_item.get_timestamp_markers()[0]
        assert isinstance(bargraph, ScrollingTimestampMarker)
        assert isinstance(plot_item._time_line, InfiniteLine)
        assert plot_item._time_line.value() == time_2
