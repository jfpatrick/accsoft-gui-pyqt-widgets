# pylint: disable=missing-docstring

from typing import List, Union, Optional, Tuple, Type, cast

import pytest
import numpy as np

from accwidgets.graph import (
    LivePlotCurve,
    ExPlotWidgetConfig,
    CurveDataWithTime,
    CyclicPlotCurveData,
    PlotWidgetStyle,
    CyclicPlotCurve,
    UpdateSource,
    PointData,
    CyclicPlotTimeSpan,
    InvalidDataStructureWarning,
)

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
    window = _prepare_cyclic_plot_test_window(qtbot, 5.0)
    _simple_linear_update(
        window.time_source_mock,
        window.data_source_mock,
        timestamps,
        current_dataset_timestamp,
        datasets_delta,
    )
    expected_data = np.arange(current_dataset_timestamp, timestamps[-1] + datasets_delta, datasets_delta)
    curves = window.plot.plotItem.live_curves
    assert len(curves) == 1
    curve = curves[0]
    assert isinstance(curve, CyclicPlotCurve)
    assert curve.last_timestamp == 10.0
    buffer = _make_curve_from_buffer(curve)
    assert np.allclose(buffer.timestamps, expected_data)
    assert np.allclose(buffer.y, expected_data)


def test_plot_after_first_timing_update(qtbot):
    """
    Args:
        qtbot:
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.live_curves[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = CurveDataWithTime(timestamps=[], x=[], y=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.5, 0.5)
    expected_full = CurveDataWithTime(timestamps=[0.5], x=[], y=[0.5])
    expected_new = CurveDataWithTime(timestamps=[0.5], x=[0.5], y=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, [], [], [], [])


def test_plot_before_first_timing_update(qtbot):
    """
    Args:
        qtbot:
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.live_curves[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = CurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = CurveDataWithTime(timestamps=[], x=[], y=[])
    # Start actual testing
    data.create_new_value(0.5, 0.5)
    expected_full = CurveDataWithTime(timestamps=[0.5], x=[], y=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    time.create_new_value(0.0)
    expected_new = CurveDataWithTime(timestamps=[0.5], x=[0.5], y=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, [], [], [], [])


# ================================================================
# Clipping is happening in mainly 4 areas:
# 1. Clipping of points with timestamp that is bigger than the
#    current time at the vertical line representing the current time
# 2. Clipping of the old curve at the line representing the current
#    time
# 3. Clipping of the new and old curve at the time span end
# ================================================================


def test_clipping_of_points_with_time_stamps_in_front_of_current_time_line(qtbot):
    """Test the handling of data with timestamps that are bigger than the
    currently known one. The expected behavior is that the curve is clipped at
    the current timeline and as time progresses, more of the "future" line is
    revealed.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.live_curves[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = CurveDataWithTime(timestamps=[], x=[], y=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.0, 0.0)
    data.create_new_value(1.0, 1.0)
    expected_full = CurveDataWithTime(timestamps=[0.0, 1.0], x=[], y=[0.0, 1.0])
    expected_new = CurveDataWithTime(timestamps=[0.0, 1.0], x=[0.0, 1.0], y=[0.0, 1.0])
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [0.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    time.create_new_value(0.5)
    expected_new_curve_x_values = [0.0, 0.5]
    expected_new_curve_y_values = [0.0, 0.5]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    time.create_new_value(0.75)
    expected_new_curve_x_values = [0.0, 0.75]
    expected_new_curve_y_values = [0.0, 0.75]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    time.create_new_value(1.0)
    expected_new_curve_x_values = [0.0, 1.0]
    expected_new_curve_y_values = [0.0, 1.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    time.create_new_value(1.5)
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    data.create_new_value(2.0, 0.0)
    expected_new_curve_x_values = [0.0, 1.0, 1.5]
    expected_new_curve_y_values = [0.0, 1.0, 0.5]
    expected_full = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[], y=[0.0, 1.0, 0.0])
    expected_new = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 0.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    time.create_new_value(2.0)
    expected_old_curve_x_values = [0.0, 1.0, 2.0]
    expected_old_curve_y_values = [0.0, 1.0, 0.0]
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [0.0]
    expected_full = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[], y=[0.0, 1.0, 0.0])
    expected_old = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 0.0])
    expected_new = CurveDataWithTime(timestamps=[2.0], x=[0.0], y=[0.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_clipping_points_ranging_into_next_time_span(qtbot):
    """Test connection between old and new curve

    1. Points in front and after time span end

    2. Last point in curve is exactly on the time span end

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.live_curves[0]
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
        x=[],
        y=[0.0, 0.75, 1.75, 2.75],
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.0, 0.75, 1.75],
        x=[0.0, 0.75, 1.75],
        y=[0.0, 0.75, 1.75],
    )
    expected_new = CurveDataWithTime(timestamps=[2.75], x=[0.75], y=[2.75])
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
        x=[],
        y=[0.0, 0.75, 1.75, 2.75, 3.75, 4.0, 4.75],
    )
    expected_old = CurveDataWithTime(
        timestamps=[2.75, 3.75, 4.0],
        x=[2.75 - 2.0, 3.75 - 2.0, 4.0 - 2.0],
        y=[2.75, 3.75, 4.0],
    )
    expected_new = CurveDataWithTime(timestamps=[4.0, 4.75], x=[0.0, 0.75], y=[4.0, 4.75])
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
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.live_curves[0]
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
    expected_full = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[], y=[0.0, 1.0, 2.0])
    expected_old = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = CurveDataWithTime(timestamps=[2.0], x=[0.0], y=[2.0])
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
    expected_full = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0, 2.5], x=[], y=[0.0, 1.0, 2.0, 2.5])
    expected_old = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = CurveDataWithTime(timestamps=[2.0, 2.5], x=[0.0, 0.5], y=[2.0, 2.5])
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
        x=[],
        y=[0.0, 1.0, 2.0, 2.5, 3.5],
    )
    expected_old = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = CurveDataWithTime(timestamps=[2.0, 2.5, 3.5], x=[0.0, 0.5, 1.5], y=[2.0, 2.5, 3.5])
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
        x=[],
        y=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
    )
    expected_old = CurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = CurveDataWithTime(
        timestamps=[2.0, 2.5, 3.5, 4.0],
        x=[0.0, 0.5, 1.5, 2.0],
        y=[2.0, 2.5, 3.5, 4.0],
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
        x=[],
        y=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
    )
    expected_old = CurveDataWithTime(
        timestamps=[2.0, 2.5, 3.5, 4.0],
        x=[0.0, 0.5, 1.5, 2.0],
        y=[2.0, 2.5, 3.5, 4.0],
    )
    expected_new = CurveDataWithTime(timestamps=[4.0], x=[0.0], y=[4.0])
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
    window_1 = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    window_2 = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item_1 = window_1.plot.plotItem.live_curves[0]
    plot_item_2 = window_2.plot.plotItem.live_curves[0]
    time_1 = window_1.time_source_mock
    time_2 = window_2.time_source_mock
    data_1 = window_1.data_source_mock
    data_2 = window_2.data_source_mock
    time_1.create_new_value(0.0)
    data_1.create_new_value(0.0, 0.0)
    data_2.create_new_value(0.0, 0.0)
    time_2.create_new_value(0.0)
    assert equals(plot_item_1, plot_item_2)
    time_1.create_new_value(1.0)
    data_1.create_new_value(0.5, 0.5)
    data_2.create_new_value(0.5, 0.5)
    time_2.create_new_value(1.0)
    assert equals(plot_item_1, plot_item_2)
    time_1.create_new_value(2.0)
    data_1.create_new_value(1.0, 1.0)
    data_1.create_new_value(1.5, 1.5)
    data_1.create_new_value(2.0, 2.0)
    data_2.create_new_value(1.0, 1.0)
    data_2.create_new_value(1.5, 1.5)
    data_2.create_new_value(2.0, 2.0)
    time_2.create_new_value(2.0)
    assert equals(plot_item_1, plot_item_2)


def test_data_delivered_in_wrong_order(qtbot):
    """Test if a sent dataset with an timestamp older than an already added one
    will be inserted at the right index. It is expected, that they are inserted
    in the way, that the internal saved data is always ordered by the timestamps
    of the datasets.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.live_curves[0]
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
    expected_full = CurveDataWithTime(timestamps=[0.5, 1.0], x=[], y=[0.5, 1.0])
    expected_old = CurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = CurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
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
        x=[],
        y=[0.5, 1.0, 1.25, 1.5, 1.75],
    )
    expected_old = CurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = CurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75],
        x=[0.5, 1.0, 1.25, 1.5, 1.75],
        y=[0.5, 1.0, 1.25, 1.5, 1.75],
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
        x=[],
        y=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.1],
    )
    expected_old = CurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
        x=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
        y=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
    )
    expected_new = CurveDataWithTime(timestamps=[2.1], x=[2.1 - 2.0], y=[2.1])
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
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem.live_curves[0]
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
    expected_full = CurveDataWithTime(timestamps=[0.5, 1.0], x=[], y=[0.5, 1.0])
    expected_old = CurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = CurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
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
    expected_full = CurveDataWithTime(timestamps=[0.5, 1.0, 2.1], x=[], y=[0.5, 1.0, 2.1])
    expected_old = CurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
    expected_new = CurveDataWithTime(timestamps=[2.1], x=[2.1 - 2.0], y=[2.1])
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
    window = _prepare_cyclic_plot_test_window(qtbot, 2.0, should_create_timing_source=False)
    plot_item = window.plot.plotItem.live_curves[0]
    data = window.data_source_mock
    data.create_new_value(0.5, 0.5)
    data.create_new_value(1.0, 1.0)
    expected_old_curve_x_values: List[float] = []
    expected_old_curve_y_values: List[float] = []
    expected_new_curve_x_values = [0.5, 1.0]
    expected_new_curve_y_values = [0.5, 1.0]
    expected_full = CurveDataWithTime(timestamps=[0.5, 1.0], x=[], y=[0.5, 1.0])
    expected_old = CurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = CurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
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
    source.sig_new_data[PointData].emit(PointData(0.0, 0.0))
    source.sig_new_data[PointData].emit(PointData(1.0, 1.0))
    source.sig_new_data[PointData].emit(PointData(np.nan, np.nan))
    source.sig_new_data[PointData].emit(PointData(2.0, 2.0))
    source.sig_new_data[PointData].emit(PointData(3.0, 3.0))
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


@pytest.mark.parametrize("data_and_exp_warnings", [
    ([(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (np.nan, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (1.1, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (0.1, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (1.1, np.nan), (1.2, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (1.1, np.nan), (2.1, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (np.nan, 4.0), (2.0, 2.0), (3.0, 3.0)], [InvalidDataStructureWarning]),
])
def test_nan_values_in_scatter_plot(
        qtbot,
        recwarn,
        data_and_exp_warnings: Tuple[List[Tuple[float, float]], List[Type]],
):
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
    data_sequence: List[Tuple[float, float]] = data_and_exp_warnings[0]
    expected_warnings: List[Type] = data_and_exp_warnings[1]
    window = _prepare_minimal_test_window(qtbot)
    source = UpdateSource()
    # symbol -> pass data to symbol as well
    window.plot.addCurve(data_source=source, symbol="o")
    for point in data_sequence:
        source.sig_new_data.emit(PointData(point[0], point[1]))
        # Wait a bit, so the ScatterPlotItems paint function get's called properly
        qtbot.wait(1)
    for expected in expected_warnings:
        warning = recwarn.pop(expected)
        assert issubclass(warning.category, expected)
    assert len(recwarn) == len(expected_warnings)


# ~~~~~~~~~~~~~~ Helper Functions ~~~~~~~~~~~~~~~


def _prepare_cyclic_plot_test_window(
        qtbot,
        time_span: float,
        should_create_timing_source: bool = True,
) -> PlotWidgetTestWindow:
    """
    Prepare a window for testing. A curve and optionally a timing source
    can be directly integrated in the window.

    Args:
        qtbot: qtbot pytest fixture
        time_span (int): time span size, how much data should be shown
    """
    plot_config = ExPlotWidgetConfig(
        plotting_style=PlotWidgetStyle.CYCLIC_PLOT,
        time_span=time_span,
        time_progress_line=True,
    )
    window = PlotWidgetTestWindow(plot_config, item_to_add=LivePlotCurve, should_create_timing_source=should_create_timing_source)
    window.show()
    qtbot.addWidget(window)
    return window


def _prepare_minimal_test_window(
        qtbot,
        plotting_style: PlotWidgetStyle = PlotWidgetStyle.SCROLLING_PLOT,
        time_span: Optional[float] = None,
        time_progress_line: Optional[bool] = None,
) -> PlotWidgetTestWindow:
    """
    Prepare a window for testing. This window won't create any curves or timing
    sources etc. but only a window with an empty plot.

    Args:
        qtbot: qtbot pytest fixture
        time_span (int): time span size, how much data should be shown
    """
    plot_config = ExPlotWidgetConfig(
        plotting_style=plotting_style,
        time_span=time_span or 10,
        time_progress_line=time_progress_line or False,
    )
    window = MinimalTestWindow(plot_config)
    window.show()
    qtbot.addWidget(window)
    qtbot.waitForWindowShown(window)
    return window


def _check_curves(
    curve: CyclicPlotCurve,
    expected_full: CurveDataWithTime,
    expected_old: CurveDataWithTime,
    expected_new: CurveDataWithTime,
):
    """
    Args:
        curve: Curve that should be checked
        expected_full: What should be in the buffer?
        expected_old: What should be part of the old part of the curve
        expected_new: What should be part of the new part of the curve
    """

    result = (_make_curve_from_buffer(curve) == expected_full
              and _make_curve_from_buffers_new_part(curve) == expected_new
              and _make_curve_from_buffers_old_part(curve) == expected_old)
    return result


def _make_curve_from_buffer(curve: CyclicPlotCurve):
    """For easier comparison of the buffers content, we wrap it in a curve object"""
    x_values, y_values = curve._data_model.full_data_buffer
    return CurveDataWithTime(timestamps=x_values, x=np.array([]), y=y_values)


def _make_curve_from_buffers_new_part(curve: CyclicPlotCurve) -> CurveDataWithTime:
    """
    A list of points (without interpolating the ends)
    from the data model that are part of the new curve.
    """
    time_span = cast(CyclicPlotTimeSpan, curve._parent_plot_item.time_span)
    x_values, y_values = curve._data_model.subset_for_xrange(
        start=time_span.start,
        end=time_span.end,
    )
    return CurveDataWithTime(
        timestamps=x_values,
        x=x_values - time_span.curr_offset,
        y=y_values,
    )


def _make_curve_from_buffers_old_part(curve: CyclicPlotCurve) -> CurveDataWithTime:
    """
    A list of points (without interpolating the ends)
    from the data model that are part of the old curve.
    """
    time_span = cast(CyclicPlotTimeSpan, curve._parent_plot_item.time_span)
    x_values, y_values = curve._data_model.subset_for_xrange(
        start=time_span.prev_start,
        end=time_span.prev_end,
    )
    return CurveDataWithTime(
        timestamps=x_values,
        x=x_values - time_span.prev_offset,
        y=y_values,
    )


def _check_plot_data_items_data(
    curve: CyclicPlotCurve,
    expected_nc_x: Union[np.ndarray, List[float], None] = None,
    expected_nc_y: Union[np.ndarray, List[float], None] = None,
    expected_oc_x: Union[np.ndarray, List[float], None] = None,
    expected_oc_y: Union[np.ndarray, List[float], None] = None,
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
        data = CyclicPlotCurveData(
            old_curve=curve._clipped_curve_old,
            new_curve=curve._clipped_curve_new,
        )
        if isinstance(expected_nc_x, List):
            expected_nc_x = np.array(expected_nc_x)
        if isinstance(expected_nc_y, List):
            expected_nc_y = np.array(expected_nc_y)
        if isinstance(expected_oc_x, List):
            expected_oc_x = np.array(expected_oc_x)
        if isinstance(expected_oc_y, List):
            expected_oc_y = np.array(expected_oc_y)
        result = (
            np.allclose(data.new_curve.x, expected_nc_x)
            and np.allclose(data.new_curve.y, expected_nc_y)
            and np.allclose(data.old_curve.x, expected_oc_x)
            and np.allclose(data.old_curve.y, expected_oc_y)
        )
    except:   # noqa: bare-except
        return False
    return result


def equals(one: CyclicPlotCurve, two: CyclicPlotCurve) -> bool:
    """Compare two Cyclic Curves's content

    Explanation why not __eq__():

    Class needs to be hashable since it is used as a key in PyQtGraph
    If we would override the __eq__ function based on the values of
    the object we would either make the class not hashable or hashable
    based on the values of the object, since A == B -> hash(A) == hash(B),
    which would not be the case if we hash by identity. Such an
    implementation would lead to a modifiable object hash, which is definitely
    not what we want.
    """
    if (
            one.__class__ != two.__class__
            and _make_curve_from_buffer(one) == _make_curve_from_buffer(two)
            and _make_curve_from_buffers_new_part(one) == _make_curve_from_buffers_new_part(two)
            and _make_curve_from_buffers_old_part(one) == _make_curve_from_buffers_old_part(two)
    ):
        return False
    try:
        return (np.allclose(two._clipped_curve_old.y, one._clipped_curve_old.y)
                and np.allclose(two._clipped_curve_old.x, one._clipped_curve_old.x)
                and np.allclose(two._clipped_curve_new.x, one._clipped_curve_new.x)
                and np.allclose(two._clipped_curve_new.y, one._clipped_curve_new.y))
    except ValueError:
        return False


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
            data_source.create_new_value(current_dataset_timestamp, current_dataset_timestamp)
            current_dataset_timestamp += datasets_delta
