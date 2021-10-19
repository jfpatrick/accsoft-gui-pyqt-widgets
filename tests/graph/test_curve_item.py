import pytest
import numpy as np
from typing import List, Union, Optional, cast, NamedTuple, Any
from accwidgets.graph import (LivePlotCurve, ExPlotWidgetConfig, CurveData, PlotWidgetStyle, CyclicPlotCurve,
                              UpdateSource, PointData, CyclicPlotTimeSpan, InvalidDataStructureWarning)
from .mock_utils.mock_data_source import MockDataSource
from .mock_utils.mock_timing_source import MockTimingSource
from .mock_utils.widget_test_window import PlotWidgetTestWindow, MinimalTestWindow


class SampleCyclicPlotCurveData(NamedTuple):
    """
    Collection of a cyclic curve's old and new curve as
    a named tuple. Mainly used for testing purposes.
    """

    old_curve: CurveData
    new_curve: CurveData


class SampleCurveDataWithTime:

    def __init__(self,
                 x: Union[List, np.ndarray],
                 y: Union[List, np.ndarray],
                 timestamps: Union[List, np.ndarray]):
        if isinstance(x, list):
            x = np.array(x)
        if isinstance(y, list):
            y = np.array(y)
        if isinstance(timestamps, list):
            timestamps = np.array(timestamps)
        if timestamps.size != y.size:
            raise ValueError(f"The curve cannot be created with different count of y "
                             f"({y.size}) and timestamps ({timestamps.size}).")
        self.x: np.ndarray = x
        self.y: np.ndarray = y
        self.timestamps: np.ndarray = timestamps

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        try:
            return(
                np.allclose(self.timestamps, other.timestamps)
                and np.allclose(self.x, other.x)
                and np.allclose(self.y, other.y)
            )
        except ValueError:
            return False


def test_simple_linear_data_append(cyclic_plot_test_window):
    timestamps = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    datasets_delta = 0.25
    current_dataset_timestamp = 0.0
    window = cyclic_plot_test_window(5.0)
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


def test_plot_after_first_timing_update(cyclic_plot_test_window):
    window = cyclic_plot_test_window(2.0)
    plot_item = window.plot.plotItem.live_curves[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.5, 0.5)
    expected_full = SampleCurveDataWithTime(timestamps=[0.5], x=[], y=[0.5])
    expected_new = SampleCurveDataWithTime(timestamps=[0.5], x=[0.5], y=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, [], [], [], [])


def test_plot_before_first_timing_update(cyclic_plot_test_window):
    window = cyclic_plot_test_window(2.0)
    plot_item = window.plot.plotItem.live_curves[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    # Start actual testing
    data.create_new_value(0.5, 0.5)
    expected_full = SampleCurveDataWithTime(timestamps=[0.5], x=[], y=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    time.create_new_value(0.0)
    expected_new = SampleCurveDataWithTime(timestamps=[0.5], x=[0.5], y=[0.5])
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


def test_clipping_of_points_with_time_stamps_in_front_of_current_time_line(cyclic_plot_test_window):
    """Test the handling of data with timestamps that are bigger than the
    currently known one. The expected behavior is that the curve is clipped at
    the current timeline and as time progresses, more of the "future" line is
    revealed.
    """
    window = cyclic_plot_test_window(2.0)
    plot_item = window.plot.plotItem.live_curves[0]
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.0, 0.0)
    data.create_new_value(1.0, 1.0)
    expected_full = SampleCurveDataWithTime(timestamps=[0.0, 1.0], x=[], y=[0.0, 1.0])
    expected_new = SampleCurveDataWithTime(timestamps=[0.0, 1.0], x=[0.0, 1.0], y=[0.0, 1.0])
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
    expected_full = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[], y=[0.0, 1.0, 0.0])
    expected_new = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 0.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    time.create_new_value(2.0)
    expected_old_curve_x_values = [0.0, 1.0, 2.0]
    expected_old_curve_y_values = [0.0, 1.0, 0.0]
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [0.0]
    expected_full = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[], y=[0.0, 1.0, 0.0])
    expected_old = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 0.0])
    expected_new = SampleCurveDataWithTime(timestamps=[2.0], x=[0.0], y=[0.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_clipping_points_ranging_into_next_time_span(cyclic_plot_test_window):
    """Test connection between old and new curve

    1. Points in front and after time span end

    2. Last point in curve is exactly on the time span end
    """
    window = cyclic_plot_test_window(2.0)
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
    expected_full = SampleCurveDataWithTime(
        timestamps=[0.0, 0.75, 1.75, 2.75],
        x=[],
        y=[0.0, 0.75, 1.75, 2.75],
    )
    expected_old = SampleCurveDataWithTime(
        timestamps=[0.0, 0.75, 1.75],
        x=[0.0, 0.75, 1.75],
        y=[0.0, 0.75, 1.75],
    )
    expected_new = SampleCurveDataWithTime(timestamps=[2.75], x=[0.75], y=[2.75])
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
    expected_full = SampleCurveDataWithTime(
        timestamps=[0.0, 0.75, 1.75, 2.75, 3.75, 4.0, 4.75],
        x=[],
        y=[0.0, 0.75, 1.75, 2.75, 3.75, 4.0, 4.75],
    )
    expected_old = SampleCurveDataWithTime(
        timestamps=[2.75, 3.75, 4.0],
        x=[2.75 - 2.0, 3.75 - 2.0, 4.0 - 2.0],
        y=[2.75, 3.75, 4.0],
    )
    expected_new = SampleCurveDataWithTime(timestamps=[4.0, 4.75], x=[0.0, 0.75], y=[4.0, 4.75])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_clipping_old_curve_with_progressing_time(cyclic_plot_test_window):
    window = cyclic_plot_test_window(2.0)
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
    expected_full = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[], y=[0.0, 1.0, 2.0])
    expected_old = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = SampleCurveDataWithTime(timestamps=[2.0], x=[0.0], y=[2.0])
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
    expected_full = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0, 2.5], x=[], y=[0.0, 1.0, 2.0, 2.5])
    expected_old = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = SampleCurveDataWithTime(timestamps=[2.0, 2.5], x=[0.0, 0.5], y=[2.0, 2.5])
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
    expected_full = SampleCurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0, 2.5, 3.5],
        x=[],
        y=[0.0, 1.0, 2.0, 2.5, 3.5],
    )
    expected_old = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = SampleCurveDataWithTime(timestamps=[2.0, 2.5, 3.5], x=[0.0, 0.5, 1.5], y=[2.0, 2.5, 3.5])
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
    expected_full = SampleCurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
        x=[],
        y=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
    )
    expected_old = SampleCurveDataWithTime(timestamps=[0.0, 1.0, 2.0], x=[0.0, 1.0, 2.0], y=[0.0, 1.0, 2.0])
    expected_new = SampleCurveDataWithTime(
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
    expected_full = SampleCurveDataWithTime(
        timestamps=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
        x=[],
        y=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0],
    )
    expected_old = SampleCurveDataWithTime(
        timestamps=[2.0, 2.5, 3.5, 4.0],
        x=[0.0, 0.5, 1.5, 2.0],
        y=[2.0, 2.5, 3.5, 4.0],
    )
    expected_new = SampleCurveDataWithTime(timestamps=[4.0], x=[0.0], y=[4.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_time_and_data_update_order(cyclic_plot_test_window):
    """Compare the outcome of timing-update after data-update to the opposite
    order. Both should lead to the same result if the sent timestamps and data
    is the same.
    """
    window_1 = cyclic_plot_test_window(2.0)
    window_2 = cyclic_plot_test_window(2.0)
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


def test_data_delivered_in_wrong_order(cyclic_plot_test_window):
    """Test if a sent dataset with an timestamp older than an already added one
    will be inserted at the right index. It is expected, that they are inserted
    in the way, that the internal saved data is always ordered by the timestamps
    of the datasets.
    """
    window = cyclic_plot_test_window(2.0)
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
    expected_full = SampleCurveDataWithTime(timestamps=[0.5, 1.0], x=[], y=[0.5, 1.0])
    expected_old = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = SampleCurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
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
    expected_full = SampleCurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75],
        x=[],
        y=[0.5, 1.0, 1.25, 1.5, 1.75],
    )
    expected_old = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = SampleCurveDataWithTime(
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
    expected_full = SampleCurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.1],
        x=[],
        y=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.1],
    )
    expected_old = SampleCurveDataWithTime(
        timestamps=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
        x=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
        y=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9],
    )
    expected_new = SampleCurveDataWithTime(timestamps=[2.1], x=[2.1 - 2.0], y=[2.1])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values,
    )


def test_timestamp_delivered_in_wrong_order(cyclic_plot_test_window):
    """Test the handling of timestamps that are older than an already received
    one. It is to expected that the timing update is ignored.
    """
    window = cyclic_plot_test_window(2.0)
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
    expected_full = SampleCurveDataWithTime(timestamps=[0.5, 1.0], x=[], y=[0.5, 1.0])
    expected_old = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = SampleCurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
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
    expected_full = SampleCurveDataWithTime(timestamps=[0.5, 1.0, 2.1], x=[], y=[0.5, 1.0, 2.1])
    expected_old = SampleCurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
    expected_new = SampleCurveDataWithTime(timestamps=[2.1], x=[2.1 - 2.0], y=[2.1])
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


def test_no_timing_source_attached(cyclic_plot_test_window):
    """Test the handling of timestamps that are older than an already received
    one. It is to expected that the timing update is ignored.
    """
    window = cyclic_plot_test_window(2.0, should_create_timing_source=False)
    plot_item = window.plot.plotItem.live_curves[0]
    data = window.data_source_mock
    data.create_new_value(0.5, 0.5)
    data.create_new_value(1.0, 1.0)
    expected_old_curve_x_values: List[float] = []
    expected_old_curve_y_values: List[float] = []
    expected_new_curve_x_values = [0.5, 1.0]
    expected_new_curve_y_values = [0.5, 1.0]
    expected_full = SampleCurveDataWithTime(timestamps=[0.5, 1.0], x=[], y=[0.5, 1.0])
    expected_old = SampleCurveDataWithTime(timestamps=[], x=[], y=[])
    expected_new = SampleCurveDataWithTime(timestamps=[0.5, 1.0], x=[0.5, 1.0], y=[0.5, 1.0])
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
def test_plotdataitem_components_visible(minimal_test_window, params):
    """
    Test if passing nan to a curve and especially scatter plot
    raises an error.

    PyQtGraph's ScatterPlotItem generates an RuntimeWarning based on numpy less/more
    operations on arrays containing NaN's. All LivePlotCurve's should filter NaN's
    before passing their data to the ScatterPlotItem for drawing. To make sure this
    works, we look for any warnings coming from the ScatterPlotItem when passing data
    containing NaN's.
    """
    window = minimal_test_window()
    source = UpdateSource()
    # symbol -> pass data to symbol as well
    item: LivePlotCurve = window.plot.addCurve(data_source=source, **params)
    source.send_data(PointData(0.0, 0.0))
    source.send_data(PointData(1.0, 1.0))
    source.send_data(PointData(np.nan, np.nan))
    source.send_data(PointData(2.0, 2.0))
    source.send_data(PointData(3.0, 3.0))
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


@pytest.mark.parametrize("data_sequence,expected_warnings", [
    ([(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (np.nan, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (1.1, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (0.1, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (1.1, np.nan), (1.2, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (1.1, np.nan), (2.1, np.nan), (2.0, 2.0), (3.0, 3.0)], []),
    ([(0.0, 0.0), (1.0, 1.0), (np.nan, 4.0), (2.0, 2.0), (3.0, 3.0)], [
        (InvalidDataStructureWarning, f"{PointData(x=np.nan, y=4.0)} is not valid and can't be drawn for"
                                      " the following reasons: A point with NaN as the x value and a value "
                                      "other than NaN as a y-value is not valid."),
    ]),
])
def test_nan_values_in_scatter_plot(minimal_test_window, qtbot, recwarn, data_sequence, expected_warnings):
    """ Test if passing nan to a curve and especially scatter plot
    raises an error.

    PyQtGraph's ScatterPlotItem generates an RuntimeWarning based on numpy less/more
    operations on arrays containing NaN's. All LivePlotCurve's should filter NaN's
    before passing their data to the ScatterPlotItem for drawing. To make sure this
    works, we look for any warnings coming from the ScatterPlotItem when passing data
    containing NaN's.
    """
    window = minimal_test_window()
    source = UpdateSource()
    # symbol -> pass data to symbol as well
    window.plot.addCurve(data_source=source, symbol="o")
    for point in data_sequence:
        source.send_data(PointData(point[0], point[1]))
        # Wait a bit, so the ScatterPlotItems paint function get's called properly
        qtbot.wait(1)

    for expected_type, expected_message in expected_warnings:
        warns = [w for w in recwarn if w.message.args[0] == expected_message and w.category is expected_type]
        assert len(warns) == 1, f"Expected single warning of type {expected_type.__name__} and message " \
                                f"'{expected_message}'. Got {len(warns)}. All " \
                                f"warnings: {[w.category for w in recwarn]}"


# ~~~~~~~~~~~~~~ Helper Functions ~~~~~~~~~~~~~~~


@pytest.fixture
def cyclic_plot_test_window(qtbot):

    def _wrapper(time_span: float, should_create_timing_source: bool = True):
        plot_config = ExPlotWidgetConfig(
            plotting_style=PlotWidgetStyle.CYCLIC_PLOT,
            time_span=time_span,
            time_progress_line=True,
        )
        window = PlotWidgetTestWindow(plot_config,
                                      item_to_add=LivePlotCurve,
                                      should_create_timing_source=should_create_timing_source)
        qtbot.add_widget(window)
        with qtbot.wait_exposed(window):
            window.show()
        return window

    return _wrapper


@pytest.fixture
def minimal_test_window(qtbot):

    def _wrapper(plotting_style: PlotWidgetStyle = PlotWidgetStyle.SCROLLING_PLOT,
                 time_span: Optional[float] = None,
                 time_progress_line: Optional[bool] = None):
        plot_config = ExPlotWidgetConfig(plotting_style=plotting_style,
                                         time_span=time_span or 10,
                                         time_progress_line=time_progress_line or False)
        window = MinimalTestWindow(plot_config)
        qtbot.add_widget(window)
        with qtbot.wait_exposed(window):
            window.show()
        return window

    return _wrapper


def _check_curves(
    curve: CyclicPlotCurve,
    expected_full: SampleCurveDataWithTime,
    expected_old: SampleCurveDataWithTime,
    expected_new: SampleCurveDataWithTime,
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
    return SampleCurveDataWithTime(timestamps=x_values, x=np.array([]), y=y_values)


def _make_curve_from_buffers_new_part(curve: CyclicPlotCurve) -> SampleCurveDataWithTime:
    """
    A list of points (without interpolating the ends)
    from the data model that are part of the new curve.
    """
    time_span = cast(CyclicPlotTimeSpan, curve._parent_plot_item.time_span)
    x_values, y_values = curve._data_model.subset_for_xrange(
        start=time_span.start,
        end=time_span.end,
    )
    return SampleCurveDataWithTime(
        timestamps=x_values,
        x=x_values - time_span.curr_offset,
        y=y_values,
    )


def _make_curve_from_buffers_old_part(curve: CyclicPlotCurve) -> SampleCurveDataWithTime:
    """
    A list of points (without interpolating the ends)
    from the data model that are part of the old curve.
    """
    time_span = cast(CyclicPlotTimeSpan, curve._parent_plot_item.time_span)
    x_values, y_values = curve._data_model.subset_for_xrange(
        start=time_span.prev_start,
        end=time_span.prev_end,
    )
    return SampleCurveDataWithTime(
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
        data = SampleCyclicPlotCurveData(
            old_curve=curve._clipped_curve_old,
            new_curve=curve._clipped_curve_new,
        )
        if isinstance(expected_nc_x, list):
            expected_nc_x = np.array(expected_nc_x)
        if isinstance(expected_nc_y, list):
            expected_nc_y = np.array(expected_nc_y)
        if isinstance(expected_oc_x, list):
            expected_oc_x = np.array(expected_oc_x)
        if isinstance(expected_oc_y, list):
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
