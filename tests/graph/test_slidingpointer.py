# pylint: disable=missing-docstring

from typing import List, Dict
import json
import numpy
from accsoft_gui_pyqt_widgets.graph import SlidingPointerPlotItem, PlotWidgetStyle, ExtendedPlotWidgetConfig
from .test_utils.manual_data_source import ManualDataSource
from .test_utils.manual_timing_source import ManualTimingSource
from .test_utils.widget_test_window import ExtendedPlotWidgetTestingWindow


def test_simple_linear_data_append(qtbot):
    """
    Args:
        qtbot:
    """
    timestamps = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    datasets_delta = 0.25
    current_dataset_timestamp = 0.0
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 5.0)
    _simple_linear_update(window.time_source_mock,
                          window.data_source_mock,
                          timestamps,
                          current_dataset_timestamp,
                          datasets_delta)
    expected_data = list(numpy.arange(current_dataset_timestamp, timestamps[-1] + datasets_delta, datasets_delta))
    assert window.plot.plotItem.get_last_time_stamp() == 10.0
    assert window.plot.plotItem.get_full_buffer()["timestamps"] == expected_data
    assert window.plot.plotItem.get_full_buffer()["y"] == expected_data


def test_plot_after_first_timing_update(qtbot):
    """
    Args:
        qtbot:
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = _curve_dict(timestamps=[], x_values=[], y_values=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.5, 0.5)
    expected_full = _curve_dict(timestamps=[0.5], y_values=[0.5])
    expected_new = _curve_dict(timestamps=[0.5], x_values=[0.5], y_values=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, [], [], [], [])


def test_plot_before_first_timing_update(qtbot):
    """
    Args:
        qtbot:
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = _curve_dict(timestamps=[], x_values=[], y_values=[])
    expected_new = _curve_dict(timestamps=[], x_values=[], y_values=[])
    # Start actual testing
    data.create_new_value(0.5, 0.5)
    expected_full = _curve_dict(timestamps=[0.5], y_values=[0.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    time.create_new_value(0.0)
    expected_new = _curve_dict(timestamps=[0.5], x_values=[0.5], y_values=[0.5])
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
    plot_item = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    expected_old = _curve_dict(timestamps=[], x_values=[], y_values=[])
    # Start actual testing
    time.create_new_value(0.0)
    data.create_new_value(0.0, 0.0)
    data.create_new_value(1.0, 1.0)
    expected_full = _curve_dict(timestamps=[0.0, 1.0], y_values=[0.0, 1.0])
    expected_new = _curve_dict(timestamps=[0.0, 1.0], x_values=[0.0, 1.0], y_values=[0.0, 1.0])
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
    expected_full = _curve_dict(timestamps=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 0.0])
    expected_new = _curve_dict(timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 0.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(plot_item, expected_new_curve_x_values, expected_new_curve_y_values, [], [])
    time.create_new_value(2.0)
    expected_old_curve_x_values = [0.0, 1.0, 2.0]
    expected_old_curve_y_values = [0.0, 1.0, 0.0]
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [0.0]
    expected_full = _curve_dict(timestamps=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 0.0])
    expected_old = _curve_dict(timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 0.0])
    expected_new = _curve_dict(timestamps=[2.0], x_values=[0.0], y_values=[0.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)


def test_clipping_points_ranging_into_next_cycle(qtbot):
    """Test connection between old and new curve

    1. Points in front and after cycle end

    2. Last point in curve is exactly on the cycle end

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem
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
    expected_full = _curve_dict(timestamps=[0.0, 0.75, 1.75, 2.75], y_values=[0.0, 0.75, 1.75, 2.75])
    expected_old = _curve_dict(timestamps=[0.0, 0.75, 1.75, 2.0], x_values=[0.0, 0.75, 1.75, 2.0], y_values=[0.0, 0.75, 1.75, 2.0])
    expected_new = _curve_dict(timestamps=[2.0, 2.75], x_values=[0.0, 0.75], y_values=[2.0, 2.75])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item, expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    time.create_new_value(4.0)
    data.create_new_value(3.75, 3.75)
    data.create_new_value(4.0, 4.0)
    time.create_new_value(5.0)
    data.create_new_value(4.75, 4.75)
    expected_old_curve_x_values = [5.0 - 4.0, 3.75 - 2.0, 4.0 - 2.0]
    expected_old_curve_y_values = [1 + 2.0, 3.75, 4.0]
    expected_new_curve_x_values = [4.0 - 4.0, 4.75 - 4.0]
    expected_new_curve_y_values = [4.0, 4.75]
    expected_full = _curve_dict(timestamps=[0.0, 0.75, 1.75, 2.75, 3.75, 4.0, 4.75],
                                y_values=[0.0, 0.75, 1.75, 2.75, 3.75, 4.0, 4.75])
    expected_old = _curve_dict(timestamps=[2.75, 3.75, 4.0],
                               x_values=[2.75 - 2.0, 3.75 - 2.0, 4.0 - 2.0],
                               y_values=[2.75, 3.75, 4.0])
    expected_new = _curve_dict(timestamps=[4.0, 4.75], x_values=[0.0, 0.75], y_values=[4.0, 4.75])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)


def test_clipping_old_curve_with_progressing_time(qtbot):
    # pylint: disable=too-many-statements
    """
    Args:
        qtbot:
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem
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
    expected_full = _curve_dict(timestamps=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0])
    expected_old = _curve_dict(timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0])
    expected_new = _curve_dict(timestamps=[2.0], x_values=[0.0], y_values=[2.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    time.create_new_value(2.5)
    expected_old_curve_x_values = [0.5, 1.0, 2.0]
    expected_old_curve_y_values = [0.5, 1.0, 2.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    time.create_new_value(3.0)
    expected_old_curve_x_values = [1.0, 2.0]
    expected_old_curve_y_values = [1.0, 2.0]
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    data.create_new_value(2.5, 2.5)
    expected_old_curve_x_values = [1.0, 2.0]
    expected_old_curve_y_values = [1.0, 2.0]
    expected_new_curve_x_values = [0.0, 0.5]
    expected_new_curve_y_values = [2.0, 2.5]
    expected_full = _curve_dict(timestamps=[0.0, 1.0, 2.0, 2.5], y_values=[0.0, 1.0, 2.0, 2.5])
    expected_old = _curve_dict(timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0])
    expected_new = _curve_dict(timestamps=[2.0, 2.5], x_values=[0.0, 0.5], y_values=[2.0, 2.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    data.create_new_value(3.5, 3.5)
    expected_old_curve_x_values = [1.0, 2.0]
    expected_old_curve_y_values = [1.0, 2.0]
    expected_new_curve_x_values = [0.0, 0.5, 1.0]
    expected_new_curve_y_values = [2.0, 2.5, 3.0]
    expected_full = _curve_dict(timestamps=[0.0, 1.0, 2.0, 2.5, 3.5], y_values=[0.0, 1.0, 2.0, 2.5, 3.5])
    expected_old = _curve_dict(timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0])
    expected_new = _curve_dict(timestamps=[2.0, 2.5, 3.5], x_values=[0.0, 0.5, 1.5], y_values=[2.0, 2.5, 3.5])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
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
        expected_old_curve_y_values)
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
        expected_old_curve_y_values)
    data.create_new_value(4.0, 4.0)
    expected_full = _curve_dict(timestamps=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0], y_values=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0])
    expected_old = _curve_dict(timestamps=[0.0, 1.0, 2.0], x_values=[0.0, 1.0, 2.0], y_values=[0.0, 1.0, 2.0])
    expected_new = _curve_dict(timestamps=[2.0, 2.5, 3.5, 4.0], x_values=[0.0, 0.5, 1.5, 2.0], y_values=[2.0, 2.5, 3.5, 4.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    time.create_new_value(4.0)
    expected_old_curve_x_values = [0.0, 0.5, 1.5, 2.0]
    expected_old_curve_y_values = [2.0, 2.5, 3.5, 4.0]
    expected_new_curve_x_values = [0.0]
    expected_new_curve_y_values = [4.0]
    expected_full = _curve_dict(timestamps=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0], y_values=[0.0, 1.0, 2.0, 2.5, 3.5, 4.0])
    expected_old = _curve_dict(timestamps=[2.0, 2.5, 3.5, 4.0], x_values=[0.0, 0.5, 1.5, 2.0], y_values=[2.0, 2.5, 3.5, 4.0])
    expected_new = _curve_dict(timestamps=[4.0], x_values=[0.0], y_values=[4.0])
    assert _check_curves(plot_item, expected_full, expected_old, expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)


def test_time_and_data_update_order(qtbot):
    """Compare the outcome of timing-update after data-update to the opposite
    order. Both should lead to the same result if the sent timestamps and data
    is the same.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window_1 = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    window_2 = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item_1 = window_1.plot.plotItem
    plot_item_2 = window_2.plot.plotItem
    time_1 = window_1.time_source_mock
    time_2 = window_2.time_source_mock
    data_1 = window_1.data_source_mock
    data_2 = window_2.data_source_mock
    time_1.create_new_value(0.0)
    data_1.create_new_value(0.0, 0.0)
    data_2.create_new_value(0.0, 0.0)
    time_2.create_new_value(0.0)
    d_2 = plot_item_2.get_data_items_data()
    assert _check_curves(
        plot_item_1,
        plot_item_2.get_full_buffer(),
        plot_item_2.get_old_curve_buffer(),
        plot_item_2.get_new_curve_buffer())
    assert _check_plot_data_items_data(
        plot_item_1,
        d_2["new_curve_x"],
        d_2["new_curve_y"],
        d_2["old_curve_x"],
        d_2["old_curve_x"])
    time_1.create_new_value(1.0)
    data_1.create_new_value(0.5, 0.5)
    data_2.create_new_value(0.5, 0.5)
    time_2.create_new_value(1.0)
    assert _check_curves(
        plot_item_1,
        plot_item_2.get_full_buffer(),
        plot_item_2.get_old_curve_buffer(),
        plot_item_2.get_new_curve_buffer())
    assert _check_plot_data_items_data(
        plot_item_1,
        d_2["new_curve_x"],
        d_2["new_curve_y"],
        d_2["old_curve_x"],
        d_2["old_curve_x"])
    time_1.create_new_value(2.0)
    data_1.create_new_value(1.0, 1.0)
    data_1.create_new_value(1.5, 1.5)
    data_1.create_new_value(2.0, 2.0)
    data_2.create_new_value(1.0, 1.0)
    data_2.create_new_value(1.5, 1.5)
    data_2.create_new_value(2.0, 2.0)
    time_2.create_new_value(2.0)
    assert _check_curves(
        plot_item_1,
        plot_item_2.get_full_buffer(),
        plot_item_2.get_old_curve_buffer(),
        plot_item_2.get_new_curve_buffer())
    assert _check_plot_data_items_data(
        plot_item_1,
        d_2["new_curve_x"],
        d_2["new_curve_y"],
        d_2["old_curve_x"],
        d_2["old_curve_x"])


def test_data_delivered_in_wrong_order(qtbot):
    """Test if a sent dataset with an timestamp older than an already added one
    will be inserted at the right index. It is expected, that they are inserted
    in the way, that the internal saved data is always ordered by the timestamps
    of the datasets.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(0.0)
    data.create_new_value(1.0, 1.0)
    time.create_new_value(0.5)
    data.create_new_value(0.5, 0.5)
    time.create_new_value(1.0)
    expected_old_curve_x_values = []
    expected_old_curve_y_values = []
    expected_new_curve_x_values = [0.5, 1.0]
    expected_new_curve_y_values = [0.5, 1.0]
    expected_full = _curve_dict(timestamps=[0.5, 1.0], y_values=[0.5, 1.0])
    expected_old = _curve_dict(timestamps=[], x_values=[], y_values=[])
    expected_new = _curve_dict(timestamps=[0.5, 1.0], x_values=[0.5, 1.0], y_values=[0.5, 1.0])
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    data.create_new_value(1.75, 1.75)
    data.create_new_value(1.5, 1.5)
    data.create_new_value(1.25, 1.25)
    time.create_new_value(1.9)
    expected_old_curve_x_values = []
    expected_old_curve_y_values = []
    expected_new_curve_x_values = [0.5, 1.0, 1.25, 1.5, 1.75]
    expected_new_curve_y_values = [0.5, 1.0, 1.25, 1.5, 1.75]
    expected_full = _curve_dict(timestamps=[0.5, 1.0, 1.25, 1.5, 1.75], y_values=[0.5, 1.0, 1.25, 1.5, 1.75])
    expected_old = _curve_dict(timestamps=[], x_values=[], y_values=[])
    expected_new = _curve_dict(timestamps=[0.5, 1.0, 1.25, 1.5, 1.75], x_values=[0.5, 1.0, 1.25, 1.5, 1.75],
                               y_values=[0.5, 1.0, 1.25, 1.5, 1.75])
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    data.create_new_value(2.1, 2.1)
    time.create_new_value(2.1)
    data.create_new_value(1.9, 1.9)  # Update with plot that belongs now to old curve
    expected_old_curve_x_values = [0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.0]
    expected_old_curve_y_values = [0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.0]
    expected_new_curve_x_values = [2.0 - 2.0, 2.1 - 2.0]
    expected_new_curve_y_values = [2.0, 2.1]
    expected_full = _curve_dict(timestamps=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.1],
                                y_values=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.1])
    expected_old = _curve_dict(timestamps=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.0],
                               x_values=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.0], y_values=[0.5, 1.0, 1.25, 1.5, 1.75, 1.9, 2.0])
    expected_new = _curve_dict(timestamps=[2.0, 2.1], x_values=[0.0, 2.1 - 2.0], y_values=[2.0, 2.1])
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)


def test_timestamp_delivered_in_wrong_order(qtbot):
    """Test the handling of timestamps that are older than an already received
    one. It is to expected that the timing update is ignored.

    Args:
        qtbot: pytest-qt fixture for interaction with qt-application
    """
    window = _prepare_sliding_pointer_plot_test_window(qtbot, 2.0)
    plot_item = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(0.0)
    data.create_new_value(0.5, 0.5)
    time.create_new_value(1.0)
    data.create_new_value(1.0, 1.0)
    expected_old_curve_x_values = []
    expected_old_curve_y_values = []
    expected_new_curve_x_values = [0.5, 1.0]
    expected_new_curve_y_values = [0.5, 1.0]
    expected_full = _curve_dict(timestamps=[0.5, 1.0], y_values=[0.5, 1.0])
    expected_old = _curve_dict(timestamps=[], x_values=[], y_values=[])
    expected_new = _curve_dict(timestamps=[0.5, 1.0], x_values=[0.5, 1.0], y_values=[0.5, 1.0])
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    # Timing update should not have an impact
    time.create_new_value(0.5)
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    data.create_new_value(2.1, 2.1)
    time.create_new_value(2.1)
    expected_old_curve_x_values = [0.5, 1.0, 2.0]
    expected_old_curve_y_values = [0.5, 1.0, 2.0]
    expected_new_curve_x_values = [2.0 - 2.0, 2.1 - 2.0]
    expected_new_curve_y_values = [2.0, 2.1]
    expected_full = _curve_dict(timestamps=[0.5, 1.0, 2.1], y_values=[0.5, 1.0, 2.1])
    expected_old = _curve_dict(timestamps=[0.5, 1.0, 2.0], x_values=[0.5, 1.0, 2.0], y_values=[0.5, 1.0, 2.0])
    expected_new = _curve_dict(timestamps=[2.0, 2.1], x_values=[2.0 - 2.0, 2.1 - 2.0], y_values=[2.0, 2.1])
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    # Simulate going back to the old curve
    time.create_new_value(1.9)
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)
    # Delivering the same timestamp 2x should have no impact as well
    time.create_new_value(2.1)
    assert _check_curves(
        plot_item,
        expected_full,
        expected_old,
        expected_new)
    assert _check_plot_data_items_data(
        plot_item,
        expected_new_curve_x_values,
        expected_new_curve_y_values,
        expected_old_curve_x_values,
        expected_old_curve_y_values)


# ~~~~~~~~~~~~~~ Helper Functions ~~~~~~~~~~~~~~+


def _prepare_sliding_pointer_plot_test_window(qtbot, cycle_size: float):
    """
    Args:
        qtbot:
        cycle_size:
    """
    plot_config = ExtendedPlotWidgetConfig(
        cycle_size=cycle_size,
        plotting_style=PlotWidgetStyle.SLIDING_POINTER,
        time_progress_line=True,
        v_draw_line=False,
        h_draw_line=False,
        draw_point=True
    )
    window = ExtendedPlotWidgetTestingWindow(plot_config)
    window.show()
    qtbot.addWidget(window)
    return window


def _check_curves(plot_item: SlidingPointerPlotItem,
                  expected_full: Dict[str, List[float]],
                  expected_old: Dict[str, List[float]],
                  expected_new: Dict[str, List[float]]):
    """
    Args:
        plot_item (SlidingPointerPlotItem):
        expected_full:
        expected_old:
        expected_new:
    """
    result = (json.dumps(plot_item.get_full_buffer()) == json.dumps(expected_full)) \
        and (json.dumps(plot_item.get_new_curve_buffer()) == json.dumps(expected_new)) \
        and (json.dumps(plot_item.get_old_curve_buffer()) == json.dumps(expected_old))
    return result


def _check_plot_data_items_data(plot_item: SlidingPointerPlotItem,
                                expected_nc_x: List[float] = None,
                                expected_nc_y: List[float] = None,
                                expected_oc_x: List[float] = None,
                                expected_oc_y: List[float] = None):
    """
    Args:
        plot_item (SlidingPointerPlotItem):
        expected_nc_x:
        expected_nc_y:
        expected_oc_x:
        expected_oc_y:
    """
    data = plot_item.get_data_items_data()
    result = (data["new_curve_x"] == expected_nc_x) \
        and (data["new_curve_y"] == expected_nc_y) \
        and (data["old_curve_x"] == expected_oc_x) \
        and (data["old_curve_y"] == expected_oc_y)
    return result


def _curve_dict(timestamps: List[float] = None, x_values: List[float] = None, y_values: List[float] = None):
    """ Create dict out of parameters that represent a point
    Args:
        timestamps: timstamps
        x_values: x value of timestamp
        y_values: y value of point
    """
    result = {}
    if timestamps is not None:
        result["timestamps"] = timestamps
    if x_values is not None:
        result["x"] = x_values
    if y_values is not None:
        result["y"] = y_values
    return result


def _simple_linear_update(time_source: ManualTimingSource,
                          data_source: ManualDataSource,
                          timestamps: List[float],
                          current_dataset_timestamp: float,
                          datasets_delta: float):
    """ Simple append data with the same distances between them
    Args:
        time_source (ManualTimingSource): Timing Source
        data_source (ManualDataSource): Data Source
        timestamps: timestamps that are supposed to be emitted
        current_dataset_timestamp (float): timestamp to start from
        datasets_delta (float): Distance between the timestamps of points
    """
    for index, timestamp in enumerate(iterable=timestamps):
        time_source.create_new_value(timestamp)
        while current_dataset_timestamp <= timestamp:
            data_source.create_new_value(current_dataset_timestamp, current_dataset_timestamp)
            current_dataset_timestamp += datasets_delta
