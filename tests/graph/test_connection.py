from freezegun import freeze_time
from datetime import datetime

import pytest
import numpy as np

import accwidgets.graph as accgraph


STATIC_TIME = datetime(year=2020, day=1, month=1)

# ~~~~~~~~~~~~~~~~~~~~~ Signal Bound Update Source Tests ~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize(
    "input_val,"
    "expected_x,"
    "expected_y", [
        ([1.0], STATIC_TIME.timestamp(), 1.0),
        ([1.0, 0.0], 0.0, 1.0),
    ])
@pytest.mark.parametrize("pass_as_sequence", [True, False])
@freeze_time(STATIC_TIME)
def test_point_data_from_value(input_val,
                               expected_x,
                               expected_y,
                               pass_as_sequence):
    args = [input_val] if pass_as_sequence else input_val
    actual = accgraph.PlottingItemDataFactory._to_point(*args)
    assert actual.x_value == expected_x
    assert actual.y_value == expected_y


@pytest.mark.parametrize(
    "input_val,"
    "expected_height,"
    "expected_x,"
    "expected_y", [
        ([1.0], 1.0, STATIC_TIME.timestamp(), 0.0),
        ([1.0, 0.0], 1.0, STATIC_TIME.timestamp(), 0.0),
        ([1.0, 0.0, 2.0], 1.0, 2.0, 0.0),
    ])
@pytest.mark.parametrize("pass_as_sequence", [True, False])
@freeze_time(STATIC_TIME)
def test_bar_data_from_value(input_val,
                             expected_height,
                             expected_x,
                             expected_y,
                             pass_as_sequence):
    args = [input_val] if pass_as_sequence else input_val
    actual = accgraph.PlottingItemDataFactory._to_bar(*args)
    assert actual.height == expected_height
    assert actual.x_value == expected_x
    assert actual.y_value == expected_y


@pytest.mark.parametrize(
    "input_value,"
    "expected_x,"
    "expected_color,"
    "expected_label", [
        ([], STATIC_TIME.timestamp(), "w", ""),
        ([0.0], 0.0, "w", ""),
        ([0.0, "test_label"], 0.0, "w", "test_label"),
        ([0.0, "test_label", "r"], 0.0, "r", "test_label"),
    ])
@pytest.mark.parametrize("pass_as_sequence", [False, True])
@freeze_time(STATIC_TIME)
def test_timestampmarker_data_from_value(input_value,
                                         expected_label,
                                         expected_color,
                                         expected_x,
                                         pass_as_sequence):
    input_args = [input_value] if pass_as_sequence else input_value
    actual = accgraph.PlottingItemDataFactory._to_ts_marker(*input_args)
    assert actual.x_value == expected_x
    assert actual.color == expected_color
    assert actual.label == expected_label


@pytest.mark.parametrize(
    "input_values, "
    "expected_x, "
    "expected_y, "
    "expected_height, "
    "expected_width, "
    "expected_label", [
        ([1.0], STATIC_TIME.timestamp(), np.nan, 1.0, np.nan, ""),
        ([1.0, 2.0], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, ""),
        ([1.0, 2.0, "test_label"], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label"),
        ([1.0, "test_label", 2.0], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label"),
        (["test_label", 1.0, 2.0], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label"),
        ([1.0, 2.0, 3.0, "test_label"], STATIC_TIME.timestamp(), 2.0, 1.0, 3.0, "test_label"),
        ([1.0, 2.0, 3.0, "test_label", 4.0], 4.0, 2.0, 1.0, 3.0, "test_label"),
    ])
@pytest.mark.parametrize("pass_as_sequence", [True, False])
@freeze_time(STATIC_TIME)
def test_injection_bar_data_from_value(input_values,
                                       expected_x,
                                       expected_y,
                                       expected_height,
                                       expected_width,
                                       expected_label,
                                       pass_as_sequence):
    args = [input_values] if pass_as_sequence else input_values
    actual = accgraph.PlottingItemDataFactory._to_injection_bar(*args)
    assert actual.x_value == expected_x
    assert actual.y_value == expected_y or all(np.isnan([actual.y_value, expected_y]))
    assert actual.height == expected_height
    assert actual.width == expected_width or all(np.isnan([actual.width, expected_width]))
    assert actual.label == expected_label


# Collection data structures


@pytest.mark.parametrize(
    "input_values,"
    "expected_x,"
    "expected_y", [
        (([1.0], ), [0.0], [1.0]),
        (([1.0], [2.0]), [2.0], [1.0]),
    ])
@pytest.mark.parametrize("pass_as_sequence", [True, False])
def test_curve_data_from_value(input_values,
                               expected_x,
                               expected_y,
                               pass_as_sequence):
    args = [input_values] if pass_as_sequence else input_values
    actual = accgraph.PlottingItemDataFactory._to_curve(*args)
    assert np.array_equal(actual.x_values, expected_x)
    assert np.array_equal(actual.y_values, expected_y)


@pytest.mark.parametrize(
    "input_values,"
    "expected_x,"
    "expected_y,"
    "expected_height", [
        (([2.0], ), [0.0], [0.0], [2.0]),
        (([2.0], [1.0]), [0.0], [1.0], [2.0]),
        (([2.0], [1.0], [3.0]), [3.0], [1.0], [2.0]),
    ])
@pytest.mark.parametrize("pass_as_sequence", [True, False])
def test_bar_collection_data_from_value(input_values,
                                        expected_height,
                                        expected_x,
                                        expected_y,
                                        pass_as_sequence):
    # Wrap values into array since we it is a collection
    args = [input_values] if pass_as_sequence else input_values
    actual = accgraph.PlottingItemDataFactory._to_bar_collection(*args)
    assert np.array_equal(actual.x_values, expected_x)
    assert np.array_equal(actual.y_values, expected_y)
    assert np.array_equal(actual.heights, expected_height)


@pytest.mark.parametrize(
    "input_values,"
    "expected_x,"
    "expected_y,"
    "expected_height,"
    "expected_width,"
    "expected_label", [
        ([[1.0]], [0.0], [np.nan], [1.0], [0.0], [""]),
        ([[1.0], [2.0]], [0.0], [2.0], [1.0], [0.0], [""]),
        ([[1.0], [2.0], ["test_label"]], [0.0], [2.0], [1.0], [0.0], ["test_label"]),
        ([[1.0], ["test_label"], [2.0]], [0.0], [2.0], [1.0], [0.0], ["test_label"]),
        ([["test_label"], [1.0], [2.0]], [0.0], [2.0], [1.0], [0.0], ["test_label"]),
        ([[1.0], [2.0], [3.0], ["test_label"]], [0.0], [2.0], [1.0], [3.0], ["test_label"]),
        ([[1.0], [2.0], [3.0], ["test_label"], [4.0]], [4.0], [2.0], [1.0], [3.0], ["test_label"]),
    ])
@pytest.mark.parametrize("pass_as_sequence", [True, False])
def test_injection_bar_collection_data_from_value(input_values,
                                                  expected_x,
                                                  expected_y,
                                                  expected_height,
                                                  expected_width,
                                                  expected_label,
                                                  pass_as_sequence):
    args = [input_values] if pass_as_sequence else input_values
    actual = accgraph.PlottingItemDataFactory._to_injection_bar_collection(*args)
    assert np.array_equal(actual.x_values, expected_x)
    assert (
        np.array_equal(actual.y_values, expected_y)
        or all(np.isnan(actual.y_values))
        and all(np.isnan(expected_y))
    )
    assert np.array_equal(actual.heights, expected_height)
    assert (
        np.array_equal(actual.widths, expected_width)
        or all(np.isnan(actual.widths))
        and all(np.isnan(expected_width))
    )
    assert np.array_equal(actual.labels, expected_label)


@pytest.mark.parametrize(
    "input_values,"
    "expected_x,"
    "expected_color,"
    "expected_labels", [
        ([[0.0]], [0.0], ["w"], [""]),
        ([[0.0]], [0.0], ["w"], [""]),
        ([[0.0], ["test_label"]], [0.0], ["w"], ["test_label"]),
        ([[0.0], ["test_label"], ["r"]], [0.0], ["r"], ["test_label"]),
    ])
@pytest.mark.parametrize("pass_as_sequence", [True, False])
def test_timestampmarker_collection_data_from_value(input_values,
                                                    expected_x,
                                                    expected_color,
                                                    expected_labels,
                                                    pass_as_sequence):
    args = [input_values] if pass_as_sequence else input_values
    actual = accgraph.PlottingItemDataFactory._to_ts_marker_collection(*args)
    assert np.array_equal(actual.x_values, expected_x)
    assert np.array_equal(actual.colors, expected_color)
    assert np.array_equal(actual.labels, expected_labels)


@pytest.mark.parametrize("expected", [
    accgraph.PointData,
    accgraph.BarData,
    accgraph.InjectionBarData,
    accgraph.TimestampMarkerData,
    accgraph.CurveData,
    accgraph.BarCollectionData,
    accgraph.InjectionBarCollectionData,
    accgraph.TimestampMarkerCollectionData,
])
def test_default_transform_function_lookup(expected):
    actual = accgraph.PlottingItemDataFactory.get_transformation(data_type=expected)([0.0])
    assert isinstance(actual, expected)
