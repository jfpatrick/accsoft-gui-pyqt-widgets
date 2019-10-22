from typing import List

import numpy as np
import pyqtgraph as pg

import accsoft_gui_pyqt_widgets.graph as accgraph

from .mock_utils.widget_test_window import PlotWidgetTestWindow


def test_scrolling_plot_fixed_scrolling_x_range(qtbot):
    """ test_simple_adding_two_new_layers(qtbot)

    - Are new layers created and accessible by their layer_identifier

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    # window = _prepare_sliding_pointer_plot_test_window(qtbot, 5)
    window = _prepare_sliding_pointer_plot_test_window(qtbot=qtbot, time_span=5.0, should_create_timing_source=True)
    plot_item: pg.PlotItem = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(30.0)
    plot_item.vb.setRange(yRange=[-1.0, 1.0], padding=0.0)
    assert check_range(plot_item.vb.targetRange(), [[25.0, 30.0], [-1.0, 1.0]])
    data.create_new_value(0.0, 0.0)
    time.create_new_value(29.0)
    assert check_range(plot_item.vb.targetRange(), [[25.0, 30.0], [-1.0, 1.0]])
    time.create_new_value(35.0)
    assert check_range(plot_item.vb.targetRange(), [[30.0, 35.0], [-1.0, 1.0]])
    # time updates always set the range no matter what it was before
    plot_item.vb.setRange(xRange=[0.0, 1.0], padding=0.0)
    time.create_new_value(40.0)
    assert check_range(plot_item.vb.targetRange(), [[35.0, 40.0], [-1.0, 1.0]])
    # data updates do not change the x range
    data.create_new_value(41.0, 0.0)
    assert check_range(plot_item.vb.targetRange(), [[35.0, 40.0], [-1.0, 1.0]])


def _prepare_sliding_pointer_plot_test_window(qtbot, time_span: float, should_create_timing_source: bool = True):
    """
    Prepare a window for testing

    Args:
        qtbot: qtbot pytest fixture
        time_span (int): time span size, how much data should be shown
    """
    plot_config = accgraph.ExPlotWidgetConfig(
        plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
        time_span=time_span,
        time_progress_line=True,
        scrolling_plot_fixed_x_range=True,
        scrolling_plot_fixed_x_range_offset=0.0
    )
    window = PlotWidgetTestWindow(
        plot_config,
        item_to_add=accgraph.LivePlotCurve,
        should_create_timing_source=should_create_timing_source
    )
    window.show()
    qtbot.addWidget(window)
    return window


def check_range(actual_range: List[List[float]], expected_range: List[List[float]]):
    """Compare a viewboxes range with an expected range"""
    result = True
    for actual, expected in list(zip(actual_range, expected_range)):
        if not np.isnan(expected[0]):
            result = result and np.isclose(actual[0], expected[0])
        if not np.isnan(expected[1]):
            result = result and np.isclose(actual[1], expected[1])
    return result
