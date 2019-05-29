# pylint: disable=missing-docstring

from datetime import datetime
import pytest
from pyqtgraph import InfiniteLine, PlotDataItem
from accsoft_gui_pyqt_widgets.graph import ExtendedPlotWidget, ScrollingPlotItem, SlidingPointerPlotItem, PlotWidgetStyle,\
    ExtendedPlotWidgetConfig, ExtendedPlotItem
from .test_utils.widget_test_window import ExtendedPlotWidgetTestingWindow

def check_axis_strings(plot_item: ExtendedPlotItem, style: PlotWidgetStyle) -> bool:
    """
    Args:
        plot_item (ScrollingPlotItem):
        style (PlotWidgetStyle):

    Returns:
        True, if the Axis item processes the values as expected
    """

    values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    if style == PlotWidgetStyle.SLIDING_POINTER:
        expected = ["0.0s", "+1.0s", "+2.0s", "+3.0s", "+4.0s", "+5.0s"]
        return plot_item.getAxis("bottom").tickStrings(values, 1, 1) == expected
    if style == PlotWidgetStyle.SCROLLING_PLOT:
        expected = [datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]
        return plot_item.getAxis("bottom").tickStrings(values, 1, 1) == expected
    return False


@pytest.mark.parametrize("cycle_size", [2.0, 100.0])
@pytest.mark.parametrize("plotting_style, expected_plotting_class", [
    (PlotWidgetStyle.SCROLLING_PLOT, ScrollingPlotItem),
    (PlotWidgetStyle.SLIDING_POINTER, SlidingPointerPlotItem)
])
@pytest.mark.parametrize("time_line", [False, True])
@pytest.mark.parametrize("v_line", [False, True])
@pytest.mark.parametrize("h_line", [False, True])
@pytest.mark.parametrize("point", [False, True])
def test_all_available_widget_configurations(qtbot,
                                             cycle_size: float,
                                             plotting_style: PlotWidgetStyle,
                                             expected_plotting_class: type,
                                             time_line: bool,
                                             v_line: bool,
                                             h_line: bool,
                                             point: bool):
    """Iterate through the possible combinations of parameters when creating the
    ExtendedPlotWidget and check if all elements are created as expected.

    Args:
        qtbot:
    """
    # pylint: disable=too-many-locals,protected-access

    plot_config = ExtendedPlotWidgetConfig(
        cycle_size=cycle_size,
        plotting_style=plotting_style,
        time_progress_line=time_line,
        v_draw_line=v_line,
        h_draw_line=h_line,
        draw_point=point
    )
    window = ExtendedPlotWidgetTestingWindow(plot_config)
    window.show()
    qtbot.addWidget(window)
    # Decorators need one time update for the initial drawing of the decorators, f.e. time_line
    # can not be drawn without a first timing update, same with decorators for appended data
    time_1 = 0.0
    data_x = 0.75
    data_y = 5.25
    time_2 = 1.0
    window.time_source_mock.create_new_value(time_1)
    window.data_source_mock.create_new_value(data_x, data_y)
    window.time_source_mock.create_new_value(time_2)
    assert isinstance(window.plot, ExtendedPlotWidget)
    assert isinstance(window.plot.plotItem, expected_plotting_class)
    plot_item: ExtendedPlotItem = window.plot.plotItem
    assert isinstance(plot_item._time_line, InfiniteLine)
    assert plot_item._time_line.value() == time_2
    if v_line:
        assert isinstance(plot_item._plotting_line_v, InfiniteLine)
        assert plot_item._plotting_line_v.value() == data_x
    else:
        assert plot_item._plotting_line_v is None
    if h_line:
        assert isinstance(plot_item._plotting_line_h, InfiniteLine)
        assert plot_item._plotting_line_h.value() == data_y
    else:
        assert plot_item._plotting_line_h is None
    if point:
        assert isinstance(plot_item._plotting_line_point, PlotDataItem)
        assert list(plot_item._plotting_line_point.getData()[0]) == [data_x]
        assert list(plot_item._plotting_line_point.getData()[1]) == [data_y]
    else:
        assert plot_item._plotting_line_point is None
    assert check_axis_strings(plot_item, plotting_style)
