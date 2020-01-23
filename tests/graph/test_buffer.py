"""Tests for the Sorting functionality of the buffers as well as CurveDataBuffer."""
# pylint: disable=protected-access

from typing import List, Tuple

import numpy as np
import pytest

from accwidgets import graph as accgraph
from .mock_utils.widget_test_window import MinimalTestWindow


# ~~~ Sorting Tests ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def test_check_sorting_of_many_points():
    """Check sorting of one million shuffled points"""
    expected_x = np.arange(0.0, 100000.0)
    expected_y = np.arange(0.0, 100000.0)
    actual_x = np.copy(expected_x)
    np.random.shuffle(actual_x)
    actual_y = np.copy(actual_x)
    actual_x, actual_y = accgraph.BaseSortedDataBuffer.sorted_data_arrays(
        primary_values=actual_x, secondary_values_list=[actual_y],
    )
    assert np.array_equal(expected_x, actual_x)
    assert np.array_equal(expected_y, actual_y[0])


def test_sorting_lists_with_different_lengths():
    """Check sorting of one million shuffled points"""
    expected_x = np.arange(0.0, 7.0)
    expected_y = np.arange(0.0, 6.0)
    actual_x = np.copy(expected_x)
    actual_y = np.copy(expected_y)
    np.random.shuffle(actual_x)
    np.random.shuffle(actual_y)
    with pytest.raises(ValueError):
        accgraph.BaseSortedDataBuffer.sorted_data_arrays(
            primary_values=actual_x, secondary_values_list=[actual_y],
        )


def test_sorting_lists_with_different_dimensions():
    """Check sorting of one million shuffled points"""
    expected_x = np.array([[0.0], [1.0]])
    expected_y = np.array([0.0, 1.0])
    actual_x = np.copy(expected_x)
    actual_y = np.copy(expected_y)
    np.random.shuffle(actual_x)
    np.random.shuffle(actual_y)
    with pytest.raises(ValueError):
        accgraph.BaseSortedDataBuffer.sorted_data_arrays(
            primary_values=actual_x, secondary_values_list=[actual_y],
        )


def test_sorting_of_empty_lists():
    """Check sorting of one million shuffled points"""
    expected_x = np.array([])
    expected_y = np.array([])
    actual_x = np.copy(expected_x)
    actual_y = np.copy(expected_y)
    np.random.shuffle(actual_x)
    np.random.shuffle(actual_y)
    accgraph.BaseSortedDataBuffer.sorted_data_arrays(
        primary_values=actual_x, secondary_values_list=[actual_y],
    )
    assert np.array_equal(expected_x, actual_x)
    assert np.array_equal(expected_y, actual_y)

# ~~~ Tests for CurveData Buffer ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("length_for_buffer", [10, 14])
def test_subset_creation_with_clipping_of_data_model_without_nan_values(
        length_for_buffer,
):
    """Subset Creation with """
    buffer = accgraph.SortedCurveDataBuffer(size=length_for_buffer)
    buffer.add_list_of_entries(
        x=np.arange(start=0.0, stop=10.0),
        y=np.arange(start=0.0, stop=10.0),
    )

    # Start in front of first value, End in between values
    subset = buffer.subset_for_primary_val_range(start=-4.4, end=7.9, interpolated=True)
    expected = create_expected_tuple_from_list(
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.9],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.9],
    )
    assert np.allclose(subset, expected, equal_nan=True)
    # Start in front of first value, End exactly on value
    subset = buffer.subset_for_primary_val_range(start=-2.6, end=8.0, interpolated=True)
    expected = create_expected_tuple_from_list(
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    )
    assert np.allclose(subset, expected, equal_nan=True)
    # Start in front of first value, End after last values
    subset = buffer.subset_for_primary_val_range(start=-0.1, end=11.6)
    expected = create_expected_tuple_from_list(
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
    )
    assert np.allclose(subset, expected, equal_nan=True)

    # Start on value, End in between values
    subset = buffer.subset_for_primary_val_range(start=2.0, end=7.9, interpolated=True)
    expected = create_expected_tuple_from_list(
        [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.9], [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.9],
    )
    assert np.allclose(subset, expected, equal_nan=True)
    # Start on value, End on value
    subset = buffer.subset_for_primary_val_range(start=2.0, end=8.0, interpolated=True)
    expected = create_expected_tuple_from_list(
        [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    )
    assert np.allclose(subset, expected, equal_nan=True)
    # Start on value, End after last value
    subset = buffer.subset_for_primary_val_range(start=2.0, end=12.3, interpolated=True)
    expected = create_expected_tuple_from_list(
        [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
    )
    assert np.allclose(subset, expected, equal_nan=True)

    # Start between values, End after last value
    subset = buffer.subset_for_primary_val_range(start=2.3, end=11.2, interpolated=True)
    expected = create_expected_tuple_from_list(
        [2.3, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        [2.3, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
    )
    assert np.allclose(subset, expected, equal_nan=True)
    # Start between values, End on value
    subset = buffer.subset_for_primary_val_range(start=2.3, end=8.0, interpolated=True)
    expected = create_expected_tuple_from_list(
        [2.3, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], [2.3, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    )
    assert np.allclose(subset, expected, equal_nan=True)
    # Start between values, End between values
    subset = buffer.subset_for_primary_val_range(start=2.3, end=8.9, interpolated=True)
    expected = create_expected_tuple_from_list(
        [2.3, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.9],
        [2.3, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.9],
    )
    assert np.allclose(subset, expected)

    # Start in front of first value and End in front of first value
    subset = buffer.subset_for_primary_val_range(start=-15.3, end=-0.6, interpolated=True)
    expected = create_expected_tuple(start=0.0, stop=0.0)
    assert np.allclose(subset, expected, equal_nan=True)
    # Start after last value and End after last value
    subset = buffer.subset_for_primary_val_range(start=15.3, end=24.6, interpolated=True)
    expected = create_expected_tuple(start=0.0, stop=0.0)
    assert np.allclose(subset, expected, equal_nan=True)
    # Exactly one value
    subset = buffer.subset_for_primary_val_range(start=5.0, end=5.0)
    expected = create_expected_tuple_from_list([5.0], [5.0])
    assert np.allclose(subset, expected, equal_nan=True)


@pytest.mark.parametrize("length_for_buffer", [10, 14])
def test_subset_creation_with_clipping_of_data_model_with_multiple_nan_values(
        length_for_buffer,
):
    """Check same subsets as with buffer without nans with an full buffer and an buffer with empty places left"""
    buffer = accgraph.SortedCurveDataBuffer(size=length_for_buffer)
    buffer.add_entry(x=np.nan, y=np.nan)
    buffer.add_list_of_entries(
        x=np.array([0.0, 1.0]), y=np.array([0.0, 1.0]),
    )
    buffer.add_entry(x=np.nan, y=np.nan)
    buffer.add_list_of_entries(
        x=np.array([2.0, 3.0]), y=np.array([2.0, 3.0]),
    )
    buffer.add_entry(x=np.nan, y=np.nan)
    buffer.add_list_of_entries(
        x=np.array([4.0, 5.0]), y=np.array([4.0, 5.0]),
    )
    buffer.add_entry(x=np.nan, y=np.nan)

    # Span the whole array
    subset = buffer.subset_for_primary_val_range(start=-1.0, end=7.0, interpolated=True)
    expected = create_expected_tuple_from_list(
        [0.0, 1.0, np.nan, 2.0, 3.0, np.nan, 4.0, 5.0],
        [0.0, 1.0, np.nan, 2.0, 3.0, np.nan, 4.0, 5.0],
    )
    assert np.allclose(subset, expected, equal_nan=True)
    # No value, range before first value
    subset = buffer.subset_for_primary_val_range(start=-4.0, end=-1.23, interpolated=True)
    expected = create_expected_tuple_from_list([], [])
    assert np.allclose(subset, expected, equal_nan=True)
    # No value, range after last value
    subset = buffer.subset_for_primary_val_range(start=14.32, end=43.21, interpolated=True)
    expected = create_expected_tuple_from_list([], [])
    assert np.allclose(subset, expected, equal_nan=True)
    # Only first number
    subset = buffer.subset_for_primary_val_range(start=-4.32, end=0.0, interpolated=True)
    expected = create_expected_tuple_from_list([0.0], [0.0])
    assert np.allclose(subset, expected, equal_nan=True)
    # Only first number with clipping
    subset = buffer.subset_for_primary_val_range(start=-4.32, end=0.5, interpolated=True)
    expected = create_expected_tuple_from_list([0.0, 0.5], [0.0, 0.5])
    assert np.allclose(subset, expected, equal_nan=True)
    # Only first number with clipping
    subset = buffer.subset_for_primary_val_range(start=-4.32, end=1.5, interpolated=True)
    expected = create_expected_tuple_from_list([0.0, 1.0], [0.0, 1.0])
    assert np.allclose(subset, expected, equal_nan=True)
    # Only first number with clipping
    subset = buffer.subset_for_primary_val_range(start=3.9, end=5.1, interpolated=True)
    expected = create_expected_tuple_from_list([4.0, 5.0], [4.0, 5.0])
    assert np.allclose(subset, expected, equal_nan=True)


def test_add_empty_list():
    """Check if an empty list of entries is handled correctly when appended"""
    buffer = accgraph.SortedCurveDataBuffer(size=10)
    buffer.add_list_of_entries(
        x=np.array([]), y=np.array([]),
    )
    assert buffer.is_empty


@pytest.mark.parametrize("item_to_add", [
    (accgraph.LivePlotCurve, "addCurve"),
    (accgraph.LiveBarGraphItem, "addBarGraph"),
    (accgraph.LiveInjectionBarGraphItem, "addInjectionBar"),
    (accgraph.LiveTimestampMarker, "addTimestampMarker"),
])
@pytest.mark.parametrize("use_convenience_functions", [True, False])
def test_buffer_size_configurability(
        qtbot,
        item_to_add: Tuple[accgraph.DataModelBasedItem, str],
        use_convenience_functions: bool,
):
    """Test if the datamodels buffer size is properly configurable."""
    window = MinimalTestWindow()
    window.show()
    qtbot.addWidget(window)
    plot_item = window.plot.plotItem
    data_source = accgraph.UpdateSource()
    if use_convenience_functions:
        # create item with the addXyz() functions
        convenience_function = getattr(plot_item, item_to_add[1])
        item = convenience_function(
            data_source=data_source,
            buffer_size=10,
        )
    else:
        # create items by hand and
        item = item_to_add[0].from_plot_item(  # type: ignore
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=10,
        )
        plot_item.addItem(item=item)
    # Check if the datamodel has created a buffer in the right size
    assert item._data_model._full_data_buffer._primary_values.size == 10


# ~~~ Util functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def create_expected_tuple(start: float, stop: float):
    """Create tuple with x and y value list with y[i] = x[i] + 1"""
    return np.arange(start=start, stop=stop), np.arange(start=start + 1, stop=stop + 1)


def create_expected_tuple_from_list(list_1: List[float], list_2: List[float]):
    """Convert Tuple with lists to Tuple with np.ndarray"""
    return np.array(list_1), np.array(list_2)
