# pylint: disable=missing-docstring

from typing import List, Union, Optional, Tuple
import warnings

import pyqtgraph
import pytest
import numpy

from accsoft_gui_pyqt_widgets.graph import (LivePlotCurve,
                                            LivePlotCurveConfig,
                                            ExPlotWidgetConfig,
                                            CurveDataWithTime, PlotWidgetStyle,
                                            SlidingPointerPlotCurve,
                                            UpdateSource,
                                            PointData)

from .mock_utils.mock_data_source import MockDataSource
from .mock_utils.mock_timing_source import MockTimingSource
from .mock_utils.widget_test_window import PlotWidgetTestWindow, MinimalTestWindow


def test_simple_linear_data_append(qtbot):
    """
    Args:
        qtbot:
    """
    timestamps = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    datasets_delta = 0.25
    current_dataset_timestamp = 0.0
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5.0)
    _simple_linear_update(
        window.time_source_mock,
        window.data_source_mock,
        timestamps,
        current_dataset_timestamp,
        datasets_delta,
    )
    expected_data = numpy.arange(
        current_dataset_timestamp, timestamps[-1] + datasets_delta, datasets_delta
    )
    curves = window.plot.plotItem.get_live_data_curves()
    assert len(curves) == 1
    curve = curves[0]
    assert isinstance(curve, SlidingPointerPlotCurve)
    assert curve.get_last_time_stamp() == 10.0
    assert numpy.allclose(curve.get_full_buffer().timestamps, expected_data)
    assert numpy.allclose(curve.get_full_buffer().y_values, expected_data)


def test_plot_after_first_timing_update(qtbot):
    """
    Args:
        qtbot:
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.5, 0.5)
    expected_full = CurveDataWithTime(timestamps=[0.5], x_values=[], y_values=[0.5])
    expected_new = CurveDataWithTime(timestamps=[0.5], x_values=[0.5], y_values=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, [], [], [], [])


def test_plot_before_first_timing_update(qtbot):
    """
    Args:
        qtbot:
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    expected_new = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    # Start actual testing
    data.create_new_value(0.5, 0.5)
    expected_full = CurveDataWithTime(timestamps=[0.5], x_values=[], y_values=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    time.create_new_value(0.0)
    expected_new = CurveDataWithTime(timestamps=[0.5], x_values=[0.5], y_values=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, [], [], [], [])


# ================================================================
# Clipping is happening in mainly 4 areas:
# 1. Clipping of points with timestamp that is bigger than the
#    current time at the vertical line representing the current time
# 2. Clipping of the old curve at the line representing the current
#    time
# 3. Clipping of the new and old curve at the cycle end
# ================================================================


def test_clipping_of_points_with_time_stamps_in_front_of_current_time_line(qtbot):
    """Test the handling of data with timestamps that are bigger than the
    currently known one. The expected behavior is that the curve is clipped at
    the current timeline and as time progresses, more of the "future" line is
    revealed.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.0, 0.0)
    data.create_new_value(1.0, 1.0)
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0], x_values=[], y_values=[0.0, 1.0]
    )
    expected_new = CurveDataWithTime(
        timestamps=[0.0, 1.0], x_values=[0.0, 1.0], y_values=[0.0, 1.0]
    )
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [0.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], []
    )
    time.create_new_value(0.5)
    expected_new_curve_x_values = [0.0, 0.5]
    expected_new_curve_y_values = [0.0, 0.5]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], []
    )
    time.create_new_value(0.75)
    expected_new_curve_x_values = [0.0, 0.75]
    expected_new_curve_y_values = [0.0, 0.75]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], []
    )
    time.create_new_value(1.0)
    expected_new_curve_x_values = [0.0, 1.0]
    expected_new_curve_y_values = [0.0, 1.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], []
    )
    time.create_new_value(1.5)
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], []
    )
    data.create_new_value(2.0, 0.0)
    expected_new_curve_x_values = [0.0, 1.0, 1.5]
    expected_new_curve_y_values = [0.0, 1.0, 0.5]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[], y_values=[0.0, 1.0, 0.0]
    )
    expected_new = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 0.0]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], []
    )
    time.create_new_value(2.0)
    expected_old_curve_x_values = [0.0, 1.0, 2.0]
    expected_old_curve_y_values = [0.0, 1.0, 0.0]
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [0.0]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[], y_values=[0.0, 1.0, 0.0]
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 0.0]
    )
    expected_new = CurveDataWithTime(timestamps=[2.0], x_values=[0.0], y_values=[0.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_clipping_points_ranging_into_next_cycle(qtbot):
    """Test connection between old and new curve

    1. Points in front and after cycle end

    2. Last point in curve is exactly on the cycle end

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(0.0)
    data.create_new_value(0.0, 0.0)
    time.create_new_value(1.0)
    data.create_new_value(0.75, 0.75)
    time.create_new_value(2.0)
    data.create_new_value(1.75, 1.75)
    time.create_new_value(3.0)
    data.create_new_value(2.75, 2.75)
    expected_old_curve_x_values = [1.0, 1.75, 2.0]
    expected_old_curve_y_values = [1.0, 1.75, 2.0]
    expected_new_curve_x_values = [2.0 - 2.0, 2.75 - 2.0]
    expected_new_curve_y_values = [2.0, 2.75]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 0.75, 1.75, 2.75],
        x_values=[],
        y_values=[0.0, 0.75, 1.75, 2.75],
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.0, 0.75, 1.75],
        x_values=[0.0, 0.75, 1.75],
        y_values=[0.0, 0.75, 1.75],
    )
    expected_new = CurveDataWithTime(
        timestamps=[2.75], x_values=[0.75], y_values=[2.75]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    time.create_new_value(4.0)
    data.create_new_value(3.75, 3.75)
    data.create_new_value(4.0, 4.0)
    time.create_new_value(5.0)
    data.create_new_value(4.75, 4.75)
    expected_old_curve_x_values = [5.0 - 4.0, 3.75 - 2.0, 4.0 - 2.0]
    expected_old_curve_y_values = [1 + 2.0, 3.75, 4.0]
    expected_new_curve_x_values = [4.0 - 4.0, 4.75 - 4.0]
    expected_new_curve_y_values = [4.0, 4.75]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 0.75, 1.75, 2.75, 3.75, 4.0, 4.75],
        x_values=[],
        y_values=[0.0, 0.75, 1.75, 2.75, 3.75, 4.0, 4.75],
    )
    expected_old = CurveDataWithTime(
        timestamps=[2.75, 3.75, 4.0],
        x_values=[2.75 - 2.0, 3.75 - 2.0, 4.0 - 2.0],
        y_values=[2.75, 3.75, 4.0],
    )
    expected_new = CurveDataWithTime(
        timestamps=[4.0, 4.75], x_values=[0.0, 0.75], y_values=[4.0, 4.75]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_clipping_old_curve_with_progressing_time(qtbot):
    # pylint: disable=too-many-statements
    """
    Args:
        qtbot:
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(0.0)
    data.create_new_value(0.0, 0.0)
    time.create_new_value(1.0)
    data.create_new_value(1.0, 1.0)
    time.create_new_value(2.0)
    data.create_new_value(2.0, 2.0)
    # Overdrawing
    expected_old_curve_x_values = [0.0, 1.0, 2.0]
    expected_old_curve_y_values = [0.0, 1.0, 2.0]
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [2.0]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[], y_values=[0.0, 1.0, 2.0]
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0]
    )
    expected_new = CurveDataWithTime(timestamps=[2.0], x_values=[0.0], y_values=[2.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    time.create_new_value(2.5)
    expected_old_curve_x_values = [0.5, 1.0, 2.0]
    expected_old_curve_y_values = [0.5, 1.0, 2.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    time.create_new_value(3.0)
    expected_old_curve_x_values = [1.0, 2.0]
    expected_old_curve_y_values = [1.0, 2.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    data.create_new_value(2.5, 2.5)
    expected_old_curve_x_values = [1.0, 2.0]
    expected_old_curve_y_values = [1.0, 2.0]
    expected_new_curve_x_values = [0.0, 0.5]
    expected_new_curve_y_values = [2.0, 2.5]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0, 2.5], x_values=[], y_values=[0.0, 1.0, 2.0, 2.5]
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0]
    )
    expected_new = CurveDataWithTime(
        timestamps=[2.0, 2.5], x_values=[0.0, 0.5], y_values=[2.0, 2.5]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    data.create_new_value(3.5, 3.5)
    expected_old_curve_x_values = [1.0, 2.0]
    expected_old_curve_y_values = [1.0, 2.0]
    expected_new_curve_x_values = [0.0, 0.5, 1.0]
    expected_new_curve_y_values = [2.0, 2.5, 3.0]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0, 2.5, 3.5],
        x_values=[],
        y_values=[0.0, 1.0, 2.0, 2.5, 3.5],
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0]
    )
    expected_new = CurveDataWithTime(
        timestamps=[2.0, 2.5, 3.5], x_values=[0.0, 0.5, 1.5], y_values=[2.0, 2.5, 3.5]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    time.create_new_value(3.0)
    expected_old_curve_x_values = [1.0, 2.0]
    expected_old_curve_y_values = [1.0, 2.0]
    expected_new_curve_x_values = [0.0, 0.5, 1.0]
    expected_new_curve_y_values = [2.0, 2.5, 3.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    time.create_new_value(3.5)
    expected_old_curve_x_values = [1.5, 2.0]
    expected_old_curve_y_values = [1.5, 2.0]
    expected_new_curve_x_values = [0.0, 0.5, 1.5]
    expected_new_curve_y_values = [2.0, 2.5, 3.5]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    data.create_new_value(4.0, 4.0)
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
        x_values=[],
        y_values=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0]
    )
    expected_new = CurveDataWithTime(
        timestamps=[2.0, 2.5, 3.5, 4.0],
        x_values=[0.0, 0.5, 1.5, 2.0],
        y_values=[2.0, 2.5, 3.5, 4.0],
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    time.create_new_value(4.0)
    expected_old_curve_x_values = [0.0, 0.5, 1.5, 2.0]
    expected_old_curve_y_values = [2.0, 2.5, 3.5, 4.0]
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [4.0]
    expected_full = CurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
        x_values=[],
        y_values=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
    )
    expected_old = CurveDataWithTime(
        timestamps=[2.0, 2.5, 3.5, 4.0],
        x_values=[0.0, 0.5, 1.5, 2.0],
        y_values=[2.0, 2.5, 3.5, 4.0],
    )
    expected_new = CurveDataWithTime(timestamps=[4.0], x_values=[0.0], y_values=[4.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_time_and_data_update_order(qtbot):
    """Compare the outcome of timing-update after data-update to the opposite
    order. Both should lead to the same result if the sent timestamps and data
    is the same.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window_1 = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    window_2 = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item_1 = window_1.plot.plotItem.get_live_data_curves()[0]
    plot_item_2 = window_2.plot.plotItem.get_live_data_curves()[0]
    time_1 = window_1.time_source_mock
    time_2 = window_2.time_source_mock
    data_1 = window_1.data_source_mock
    data_2 = window_2.data_source_mock
    time_1.create_new_value(0.0)
    data_1.create_new_value(0.0, 0.0)
    data_2.create_new_value(0.0, 0.0)
    time_2.create_new_value(0.0)
    assert plot_item_1.equals(plot_item_2)
    time_1.create_new_value(1.0)
    data_1.create_new_value(0.5, 0.5)
    data_2.create_new_value(0.5, 0.5)
    time_2.create_new_value(1.0)
    assert plot_item_1.equals(plot_item_2)
    time_1.create_new_value(2.0)
    data_1.create_new_value(1.0, 1.0)
    data_1.create_new_value(1.5, 1.5)
    data_1.create_new_value(2.0, 2.0)
    data_2.create_new_value(1.0, 1.0)
    data_2.create_new_value(1.5, 1.5)
    data_2.create_new_value(2.0, 2.0)
    time_2.create_new_value(2.0)
    assert plot_item_1.equals(plot_item_2)


def test_data_delivered_in_wrong_order(qtbot):
    """Test if a sent dataset with an timestamp older than an already added one
    will be inserted at the right index. It is expected, that they are inserted
    in the way, that the internal saved data is always ordered by the timestamps
    of the datasets.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(0.0)
    data.create_new_value(1.0, 1.0)
    time.create_new_value(0.5)
    data.create_new_value(0.5, 0.5)
    time.create_new_value(1.0)
    expected_old_curve_x_values: List[float] = []
    expected_old_curve_y_values: List[float] = []
    expected_new_curve_x_values = [0.5, 1.0]
    expected_new_curve_y_values = [0.5, 1.0]
    expected_full = CurveDataWithTime(
        timestamps=[0.5, 1.0], x_values=[], y_values=[0.5, 1.0]
    )
    expected_old = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    expected_new = CurveDataWithTime(
        timestamps=[0.5, 1.0], x_values=[0.5, 1.0], y_values=[0.5, 1.0]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    data.create_new_value(1.75, 1.75)
    data.create_new_value(1.5, 1.5)
    data.create_new_value(1.25, 1.25)
    time.create_new_value(1.9)
    expected_old_curve_x_values = []
    expected_old_curve_y_values = []
    expected_new_curve_x_values = [0.5, 1.0, 1.25, 1.5, 1.75]
    expected_new_curve_y_values = [0.5, 1.0, 1.25, 1.5, 1.75]
    expected_full = CurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75],
        x_values=[],
        y_values=[0.5, 1.0, 1.25, 1.5, 1.75],
    )
    expected_old = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    expected_new = CurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75],
        x_values=[0.5, 1.0, 1.25, 1.5, 1.75],
        y_values=[0.5, 1.0, 1.25, 1.5, 1.75],
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    data.create_new_value(2.1, 2.1)
    time.create_new_value(2.1)
    data.create_new_value(1.9, 1.9)  # Update with plot that belongs now to old curve
    expected_old_curve_x_values = [0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.0]
    expected_old_curve_y_values = [0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.0]
    expected_new_curve_x_values = [2.0 - 2.0, 2.1 - 2.0]
    expected_new_curve_y_values = [2.0, 2.1]
    expected_full = CurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.1],
        x_values=[],
        y_values=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.1],
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
        x_values=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
        y_values=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
    )
    expected_new = CurveDataWithTime(
        timestamps=[2.1], x_values=[2.1 - 2.0], y_values=[2.1]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_timestamp_delivered_in_wrong_order(qtbot):
    """Test the handling of timestamps that are older than an already received
    one. It is to expected that the timing update is ignored.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(0.0)
    data.create_new_value(0.5, 0.5)
    time.create_new_value(1.0)
    data.create_new_value(1.0, 1.0)
    expected_old_curve_x_values: List[float] = []
    expected_old_curve_y_values: List[float] = []
    expected_new_curve_x_values = [0.5, 1.0]
    expected_new_curve_y_values = [0.5, 1.0]
    expected_full = CurveDataWithTime(
        timestamps=[0.5, 1.0], x_values=[], y_values=[0.5, 1.0]
    )
    expected_old = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    expected_new = CurveDataWithTime(
        timestamps=[0.5, 1.0], x_values=[0.5, 1.0], y_values=[0.5, 1.0]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    # Timing update should not have an impact
    time.create_new_value(0.5)
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    data.create_new_value(2.1, 2.1)
    time.create_new_value(2.1)
    expected_old_curve_x_values = [0.5, 1.0, 2.0]
    expected_old_curve_y_values = [0.5, 1.0, 2.0]
    expected_new_curve_x_values = [2.0 - 2.0, 2.1 - 2.0]
    expected_new_curve_y_values = [2.0, 2.1]
    expected_full = CurveDataWithTime(
        timestamps=[0.5, 1.0, 2.1], x_values=[], y_values=[0.5, 1.0, 2.1]
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.5, 1.0], x_values=[0.5, 1.0], y_values=[0.5, 1.0]
    )
    expected_new = CurveDataWithTime(
        timestamps=[2.1], x_values=[2.1 - 2.0], y_values=[2.1]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    # Simulate going back to the old curve
    time.create_new_value(1.9)
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )
    # Delivering the same timestamp 2x should have no impact as well
    time.create_new_value(2.1)
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_no_timing_source_attached(qtbot):
    """Test the handling of timestamps that are older than an already received
    one. It is to expected that the timing update is ignored.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0, should_create_timing_source=False)
    plot_item = window.plot.plotItem.get_live_data_curves()[0]
    data = window.data_source_mock
    data.create_new_value(0.5, 0.5)
    data.create_new_value(1.0, 1.0)
    expected_old_curve_x_values: List[float] = []
    expected_old_curve_y_values: List[float] = []
    expected_new_curve_x_values = [0.5, 1.0]
    expected_new_curve_y_values = [0.5, 1.0]
    expected_full = CurveDataWithTime(
        timestamps=[0.5, 1.0], x_values=[], y_values=[0.5, 1.0]
    )
    expected_old = CurveDataWithTime(timestamps=[], x_values=[], y_values=[])
    expected_new = CurveDataWithTime(
        timestamps=[0.5, 1.0], x_values=[0.5, 1.0], y_values=[0.5, 1.0]
    )
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


@pytest.mark.parametrize("params", [
    ({"pen": "r", "symbol": "o"}),
    ({"pen": "r"}),
    ({"pen": None, "symbol": "o"}),
    ({"pen": None}),
])
def test_plotdataitem_components_visible(qtbot, params):
    """
    Test if passing nan to a curve and especially scatter plot
    raises an error.

    PyQtGraph's ScatterPlotItem generates an RuntimeWarning based on numpy less/more
    operations on arrays containing NaN's. All LivePlotCurve's should filter NaN's
    before passing their data to the ScatterPlotItem for drawing. To make sure this
    works, we look for any warnings coming from the ScatterPlotItem when passing data
    containing NaN's.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_minimal_test_window(qtbot)
    source = UpdateSource()
    # symbol -> pass data to symbol as well
    item: LivePlotCurve = window.plot.addCurve(data_source=source, **params)
    source.sig_data_update[PointData].emit(PointData(0.0, 0.0))
    source.sig_data_update[PointData].emit(PointData(1.0, 1.0))
    source.sig_data_update[PointData].emit(PointData(numpy.nan, numpy.nan))
    source.sig_data_update[PointData].emit(PointData(2.0, 2.0))
    source.sig_data_update[PointData].emit(PointData(3.0, 3.0))
    # Condition as in PlotDataItem.updateItems()
    if params.get("pen") is not None or (params.get("brush") and params.get("fillLevel") is not None):
        assert item.curve.isVisible()
    else:
        assert not item.curve.isVisible()
    if params.get("symbol") is not None:
        assert item.scatter.isVisible()
    else:
        assert not item.scatter.isVisible()


# ~~~~~~~~~~~~~~ Test numpy RuntimeWarning when passing NaN to ScatterPlotItem ~~~~~~~~~~~~~~~

def _handle_numpy_error(err, flag):
    """
    Handle numpy error that is expected from the ScatterPlotItem's paint function
    when passing data that contains NaN entries. If the exception is detected
    a flag is set that fails the test_nan_values_in_scatter_plot().
    """
    if err == "invalid value" and flag == 8:
        global test_nan_values_in_scatter_plot_exception_flag
        test_nan_values_in_scatter_plot_exception_flag = True


@pytest.mark.parametrize("data_sequence", [
    [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0)],
    [(0.0, 0.0), (1.0, 1.0), (numpy.nan, numpy.nan), (2.0, 2.0), (3.0, 3.0)],
    [(0.0, 0.0), (1.0, 1.0), (1.1, numpy.nan), (2.0, 2.0), (3.0, 3.0)],
    [(0.0, 0.0), (1.0, 1.0), (0.1, numpy.nan), (2.0, 2.0), (3.0, 3.0)],
    [(0.0, 0.0), (1.0, 1.0), (1.1, numpy.nan), (1.2, numpy.nan), (2.0, 2.0), (3.0, 3.0)],
    [(0.0, 0.0), (1.0, 1.0), (1.1, numpy.nan), (2.1, numpy.nan), (2.0, 2.0), (3.0, 3.0)],
    [(0.0, 0.0), (1.0, 1.0), (numpy.nan, 4.0), (2.0, 2.0), (3.0, 3.0)],
])
def test_nan_values_in_scatter_plot(qtbot, data_sequence: List[Tuple[float, float]]):
    """ Test if passing nan to a curve and especially scatter plot
    raises an error.

    PyQtGraph's ScatterPlotItem generates an RuntimeWarning based on numpy less/more
    operations on arrays containing NaN's. All LivePlotCurve's should filter NaN's
    before passing their data to the ScatterPlotItem for drawing. To make sure this
    works, we look for any warnings coming from the ScatterPlotItem when passing data
    containing NaN's.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    global test_nan_values_in_scatter_plot_exception_flag
    test_nan_values_in_scatter_plot_exception_flag = False
    window = _prepare_minimal_test_window(qtbot)
    source = UpdateSource()
    # symbol -> pass data to symbol as well
    window.plot.addCurve(data_source=source, symbol="o")
    numpy.seterrcall(_handle_numpy_error)
    numpy.seterr(all="call")
    for point in data_sequence:
        source.sig_data_update.emit(PointData(point[0], point[1]))
        # Wait a bit, so the ScatterPlotItems paint function get's called properly
        qtbot.wait(1)
        # See if the numpy error handler has been called with the invalid error
        assert not test_nan_values_in_scatter_plot_exception_flag


# ~~~~~~~~~~~~~~ Helper Functions ~~~~~~~~~~~~~~~


def _prepare_sliding_pointer_plot_test_window(
        qtbot,
        cycle_size: float,
        should_create_timing_source: bool = True
) -> PlotWidgetTestWindow:
    """
    Prepare a window for testing. A curve and optionally a timing source
    can be directly integrated in the window.

    Args:
        qtbot: qtbot pytest fixture
        cycle_size (int): cycle size, how much data should be shown
    """
    plot_config = ExPlotWidgetConfig(
        plotting_style=PlotWidgetStyle.SLIDING_POINTER,
        cycle_size=cycle_size,
        time_progress_line=True,
    )
    curve_config = LivePlotCurveConfig()
    window = PlotWidgetTestWindow(plot_config, [curve_config], item_to_add=LivePlotCurve, should_create_timing_source=should_create_timing_source)
    window.show()
    qtbot.addWidget(window)
    return window


def _prepare_minimal_test_window(
        qtbot,
        plotting_style: Optional[PlotWidgetStyle] = None,
        cycle_size: Optional[float] = None,
        time_progress_line: Optional[bool] = None,
) -> PlotWidgetTestWindow:
    """
    Prepare a window for testing. This window won't create any curves or timing
    sources etc. but only a window with an empty plot.

    Args:
        qtbot: qtbot pytest fixture
        cycle_size (int): cycle size, how much data should be shown
    """
    plot_config = ExPlotWidgetConfig(
        plotting_style=plotting_style or PlotWidgetStyle.SCROLLING_PLOT,
        cycle_size=cycle_size or 10,
        time_progress_line=time_progress_line or False,
    )
    window = MinimalTestWindow(plot_config)
    window.show()
    qtbot.addWidget(window)
    qtbot.waitForWindowShown(window)
    return window


def _check_curves(
    plot_item: SlidingPointerPlotCurve,
    expected_full: CurveDataWithTime,
    expected_old: CurveDataWithTime,
    expected_new: CurveDataWithTime,
):
    """
    Args:
        plot_item (SlidingPointerPlotCurve):
        expected_full (CurveDataWithTime):
        expected_old (CurveDataWithTime):
        expected_new (CurveDataWithTime):
    """
    result = (
        plot_item.get_full_buffer() == expected_full
        and plot_item.get_new_curve_buffer() == expected_new
        and plot_item.get_old_curve_buffer() == expected_old
    )
    return result


def _check_plot_data_items_data(
    curve: SlidingPointerPlotCurve,
    expected_nc_x: Union[numpy.ndarray, List[float]] = None,
    expected_nc_y: Union[numpy.ndarray, List[float]] = None,
    expected_oc_x: Union[numpy.ndarray, List[float]] = None,
    expected_oc_y: Union[numpy.ndarray, List[float]] = None,
):
    """

    Args:
        curve:
        expected_nc_x: Expected x values in the
        expected_nc_y:
        expected_oc_x:
        expected_oc_y:

    Returns:
        True if the plotdataitem has the expected data
    """
    try:
        data = curve.get_last_drawn_data()
        if isinstance(expected_nc_x, List):
            expected_nc_x = numpy.array(expected_nc_x)
        if isinstance(expected_nc_y, List):
            expected_nc_y = numpy.array(expected_nc_y)
        if isinstance(expected_oc_x, List):
            expected_oc_x = numpy.array(expected_oc_x)
        if isinstance(expected_oc_y, List):
            expected_oc_y = numpy.array(expected_oc_y)
        result = (
            numpy.allclose(data.new_curve.x_values, expected_nc_x)
            and numpy.allclose(data.new_curve.y_values, expected_nc_y)
            and numpy.allclose(data.old_curve.x_values, expected_oc_x)
            and numpy.allclose(data.old_curve.y_values, expected_oc_y)
        )
    except:
        return False
    return result


def _simple_linear_update(
    time_source: MockTimingSource,
    data_source: MockDataSource,
    timestamps: List[float],
    current_dataset_timestamp: float,
    datasets_delta: float,
):
    """Simple append data with the same distances between them :param
    time_source: Timing Source :type time_source: ManualTimingSource :param
    data_source: Data Source :type data_source: ManualDataSource :param
    timestamps: timestamps that are supposed to be emitted :param
    current_dataset_timestamp: timestamp to start from :type
    current_dataset_timestamp: float :param datasets_delta: Distance between the
    timestamps of points :type datasets_delta: float

    Args:
        time_source (ManualTimingSource):
        data_source (ManualDataSource):
        timestamps:
        current_dataset_timestamp (float):
        datasets_delta (float):
    """
    for timestamp in timestamps:
        time_source.create_new_value(timestamp)
        while current_dataset_timestamp <= timestamp:
            data_source.create_new_value(
                current_dataset_timestamp, current_dataset_timestamp
            )
            current_dataset_timestamp += datasets_delta
