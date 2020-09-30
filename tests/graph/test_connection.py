import pytest
import numpy as np
from freezegun import freeze_time
from datetime import datetime
from dateutil.tz import tzoffset
from accwidgets.graph import (PlottingItemDataFactory, InvalidDataStructureWarning, PointData, BarData,
                              InjectionBarData, TimestampMarkerData, CurveData, BarCollectionData,
                              InjectionBarCollectionData, TimestampMarkerCollectionData)

# We have to make the freeze time utc, otherwise freeze-gun seems to
# take the current timezone which lets tests fail
TZ = tzoffset("UTC+0", 0)
STATIC_TIME = datetime(year=2020, day=1, month=1, tzinfo=TZ)
HEADER_TIME = datetime(year=2019, day=1, month=1, tzinfo=TZ)
ACQ_TS_FIELD = PlottingItemDataFactory.TIMESTAMP_HEADER_FIELD
HEADER_INFO = {ACQ_TS_FIELD: HEADER_TIME}


# For matching warning messages we capture
_INVALID_DATA_STRUCTURE_WARNING_MSG = r"is not valid and can't be drawn for " \
                                      r"the following reasons:"


# ~~~~~~~~~~~~~~~~~~~~~ Signal Bound Update Source Tests ~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize(
    "input_val,"
    "expected_x,"
    "expected_y", [
        ([1.0], STATIC_TIME.timestamp(), 1.0),
        ([1.0, 0.0], 0.0, 1.0),
        # With Header INfo
        ([1.0, HEADER_INFO], HEADER_TIME.timestamp(), 1.0),
        ([1.0, 0.0, HEADER_INFO], 0.0, 1.0),
    ])
@freeze_time(STATIC_TIME)
def test_point_data_from_value(input_val,
                               expected_x,
                               expected_y):
    actual = PlottingItemDataFactory._to_point(*input_val)
    assert actual.x == expected_x
    assert actual.y == expected_y


@pytest.mark.parametrize(
    "input_val,"
    "expected_height,"
    "expected_x,"
    "expected_y", [
        ([1.0], 1.0, STATIC_TIME.timestamp(), 0.0),
        ([1.0, 0.0], 1.0, STATIC_TIME.timestamp(), 0.0),
        ([1.0, 0.0, 2.0], 1.0, 2.0, 0.0),
        # With Header Info
        ([1.0, HEADER_INFO], 1.0, HEADER_TIME.timestamp(), 0.0),
        ([1.0, 0.0, HEADER_INFO], 1.0, HEADER_TIME.timestamp(), 0.0),
        ([1.0, 0.0, 2.0, HEADER_INFO], 1.0, 2.0, 0.0),
    ])
@freeze_time(STATIC_TIME)
def test_bar_data_from_value(input_val,
                             expected_height,
                             expected_x,
                             expected_y):
    actual = PlottingItemDataFactory._to_bar(*input_val)
    assert actual.height == expected_height
    assert actual.x == expected_x
    assert actual.y == expected_y


@pytest.mark.parametrize(
    "input_values, "
    "expected_x, "
    "expected_y, "
    "expected_height, "
    "expected_width, "
    "expected_label, "
    "raises_warning", [
        ([1.0], STATIC_TIME.timestamp(), np.nan, 1.0, np.nan, "", True),
        ([1.0, 2.0], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, "", False),
        ([1.0, 2.0, "test_label"], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label", False),
        ([1.0, "test_label", 2.0], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label", False),
        (["test_label", 1.0, 2.0], STATIC_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label", False),
        ([1.0, 2.0, 3.0, "test_label", 4.0], 4.0, 2.0, 1.0, 3.0, "test_label", False),
        # With Header Info
        ([1.0, HEADER_INFO], HEADER_TIME.timestamp(), np.nan, 1.0, np.nan, "", True),
        ([1.0, 2.0, HEADER_INFO], HEADER_TIME.timestamp(), 2.0, 1.0, np.nan, "", False),
        ([1.0, 2.0, "test_label", HEADER_INFO], HEADER_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label", False),
        ([1.0, "test_label", 2.0, HEADER_INFO], HEADER_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label", False),
        (["test_label", 1.0, 2.0, HEADER_INFO], HEADER_TIME.timestamp(), 2.0, 1.0, np.nan, "test_label", False),
        ([1.0, 2.0, 3.0, "test_label", 4.0, HEADER_INFO], 4.0, 2.0, 1.0, 3.0, "test_label", False),
    ])
@freeze_time(STATIC_TIME)
def test_injection_bar_data_from_value(input_values,
                                       expected_x,
                                       expected_y,
                                       expected_height,
                                       expected_width,
                                       expected_label,
                                       raises_warning):
    if raises_warning:
        with pytest.warns(InvalidDataStructureWarning,
                          match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
            actual = PlottingItemDataFactory._to_injection_bar(*input_values)
    else:
        actual = PlottingItemDataFactory._to_injection_bar(*input_values)
    assert actual.x == expected_x
    assert actual.y == expected_y or all(np.isnan([actual.y, expected_y]))
    assert actual.height == expected_height
    assert actual.width == expected_width or all(np.isnan([actual.width, expected_width]))
    assert actual.label == expected_label


@pytest.mark.parametrize(
    "input_value,"
    "expected_x,"
    "expected_color,"
    "expected_label", [
        ([], STATIC_TIME.timestamp(), "w", ""),
        ([0.0], 0.0, "w", ""),
        ([0.0, "test_label"], 0.0, "w", "test_label"),
        ([0.0, "test_label", "r"], 0.0, "r", "test_label"),
        # With Header info
        ([HEADER_INFO], HEADER_TIME.timestamp(), "w", ""),
        ([0.0, HEADER_INFO], 0.0, "w", ""),
        ([0.0, "test_label", HEADER_INFO], 0.0, "w", "test_label"),
        ([0.0, "test_label", "r", HEADER_INFO], 0.0, "r", "test_label"),
    ])
@freeze_time(STATIC_TIME)
def test_timestampmarker_data_from_value(input_value,
                                         expected_label,
                                         expected_color,
                                         expected_x):
    actual = PlottingItemDataFactory._to_ts_marker(*input_value)
    assert actual.x == expected_x
    assert actual.color == expected_color
    assert actual.label == expected_label


# Collection data structures
# --------------------------
# Headers will be thrown away, since they can not be interpreted
# unambiguously


@pytest.mark.parametrize(
    "input_values,"
    "expected_x,"
    "expected_y", [
        ([[1.0]], [0.0], [1.0]),
        ([[1.0], [2.0]], [2.0], [1.0]),
        # With header information
        ([[1.0], HEADER_INFO], [0.0], [1.0]),
        ([[1.0], [2.0], HEADER_INFO], [2.0], [1.0]),
    ])
def test_curve_data_from_value(input_values,
                               expected_x,
                               expected_y):
    actual = PlottingItemDataFactory._to_curve(*input_values)
    assert np.array_equal(actual.x, expected_x)
    assert np.array_equal(actual.y, expected_y)


@pytest.mark.parametrize(
    "input_values,"
    "expected_x,"
    "expected_y,"
    "expected_height", [
        ([[2.0]], [0.0], [0.0], [2.0]),
        ([[2.0], [1.0]], [0.0], [1.0], [2.0]),
        ([[2.0], [1.0], [3.0]], [3.0], [1.0], [2.0]),
        # With Header Info
        ([[2.0], HEADER_INFO], [0.0], [0.0], [2.0]),
        ([[2.0], [1.0], HEADER_INFO], [0.0], [1.0], [2.0]),
        ([[2.0], [1.0], [3.0], HEADER_INFO], [3.0], [1.0], [2.0]),
    ])
def test_bar_collection_data_from_value(input_values,
                                        expected_height,
                                        expected_x,
                                        expected_y):
    # Wrap values into array since we it is a collection
    actual = PlottingItemDataFactory._to_bar_collection(*input_values)
    assert np.array_equal(actual.x, expected_x)
    assert np.array_equal(actual.y, expected_y)
    assert np.array_equal(actual.heights, expected_height)


@pytest.mark.parametrize(
    "input_values,"
    "expected_x,"
    "expected_y,"
    "expected_height,"
    "expected_width,"
    "expected_label, "
    "raises_warning", [
        ([[1.0]], [0.0], [np.nan], [1.0], [0.0], [""], True),
        ([[1.0], [2.0]], [0.0], [2.0], [1.0], [0.0], [""], False),
        ([[1.0], [2.0], ["test_label"]], [0.0], [2.0], [1.0], [0.0], ["test_label"], False),
        ([[1.0], ["test_label"], [2.0]], [0.0], [2.0], [1.0], [0.0], ["test_label"], False),
        ([["test_label"], [1.0], [2.0]], [0.0], [2.0], [1.0], [0.0], ["test_label"], False),
        ([[1.0], [2.0], [3.0], ["test_label"]], [0.0], [2.0], [1.0], [3.0], ["test_label"], False),
        ([[1.0], [2.0], [3.0], ["test_label"], [4.0]], [4.0], [2.0], [1.0], [3.0], ["test_label"], False),
        # With Header Information
        ([[1.0], HEADER_INFO], [0.0], [np.nan], [1.0], [0.0], [""], True),
        ([[1.0], [2.0], HEADER_INFO], [0.0], [2.0], [1.0], [0.0], [""], False),
        ([[1.0], [2.0], ["test_label"], HEADER_INFO], [0.0], [2.0], [1.0], [0.0], ["test_label"], False),
        ([[1.0], ["test_label"], [2.0], HEADER_INFO], [0.0], [2.0], [1.0], [0.0], ["test_label"], False),
        ([["test_label"], [1.0], [2.0], HEADER_INFO], [0.0], [2.0], [1.0], [0.0], ["test_label"], False),
        ([[1.0], [2.0], [3.0], ["test_label"], HEADER_INFO], [0.0], [2.0], [1.0], [3.0], ["test_label"], False),
        ([[1.0], [2.0], [3.0], ["test_label"], [4.0], HEADER_INFO], [4.0], [2.0], [1.0], [3.0], ["test_label"], False),
    ])
def test_injection_bar_collection_data_from_value(input_values,
                                                  expected_x,
                                                  expected_y,
                                                  expected_height,
                                                  expected_width,
                                                  expected_label,
                                                  raises_warning):
    # Wrap values into array since we it is a collection
    if raises_warning:
        with pytest.warns(InvalidDataStructureWarning,
                          match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
            actual = PlottingItemDataFactory._to_injection_bar_collection(*input_values)
    else:
        actual = PlottingItemDataFactory._to_injection_bar_collection(*input_values)
    assert np.array_equal(actual.x, expected_x)
    assert (
        np.array_equal(actual.y, expected_y)
        or all(np.isnan(actual.y))
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
        # With header Info
        ([[0.0], HEADER_INFO], [0.0], ["w"], [""]),
        ([[0.0], HEADER_INFO], [0.0], ["w"], [""]),
        ([[0.0], ["test_label"], HEADER_INFO], [0.0], ["w"], ["test_label"]),
        ([[0.0], ["test_label"], ["r"], HEADER_INFO], [0.0], ["r"], ["test_label"]),
    ])
def test_timestampmarker_collection_data_from_value(input_values,
                                                    expected_x,
                                                    expected_color,
                                                    expected_labels):
    actual = PlottingItemDataFactory._to_ts_marker_collection(*input_values)
    assert np.array_equal(actual.x, expected_x)
    assert np.array_equal(actual.colors, expected_color)
    assert np.array_equal(actual.labels, expected_labels)


@pytest.mark.parametrize("expected, args", [
    (PointData, [0.0]),
    (BarData, [0.0]),
    (InjectionBarData, [0.0, 1.0, 2.0, 3.0]),
    (TimestampMarkerData, [0.0]),
    (CurveData, [[0.0]]),
    (BarCollectionData, [[0.0]]),
    (InjectionBarCollectionData, [[0.0], [1.0], [2.0], [3.0]]),
    (TimestampMarkerCollectionData, [[0.0]]),
])
def test_default_transform_function_lookup(expected, args):
    actual = PlottingItemDataFactory.get_transformation(data_type=expected)(*args)
    assert isinstance(actual, expected)


@pytest.mark.parametrize("dtype, data, should_unwrap", [
    (PointData, 0, False),
    (BarData, 0, False),
    (InjectionBarData, 0, False),
    (TimestampMarkerData, 0, False),
    (PointData, [0], True),
    (BarData, [0], True),
    (InjectionBarData, [0], True),
    (TimestampMarkerData, [0], True),
    # Collections
    (CurveData, [0], False),
    (BarCollectionData, [0], False),
    (InjectionBarCollectionData, [0], False),
    (TimestampMarkerCollectionData, [0], False),
    (CurveData, [[0], [0]], True),
    (BarCollectionData, [[0], [0]], True),
    (InjectionBarCollectionData, [[0], [0]], True),
    (TimestampMarkerCollectionData, [[0], [0]], True),
])
def test_should_unwrap(dtype, data, should_unwrap):
    actual = PlottingItemDataFactory.should_unwrap(data, dtype=dtype)
    assert actual == should_unwrap


@pytest.mark.parametrize("input, args, header", [
    ([0.0, 1.0, 2.0, {"acqTimestamp": 0.0}], [0.0, 1.0, 2.0], {"acqTimestamp": 0.0}),
    ([0.0, 1.0, 2.0], [0.0, 1.0, 2.0], None),
    ([{"acqTimestamp": 0.0}], [], {"acqTimestamp": 0.0}),
    ([], [], None),
])
def test_header_extraction(input, args, header):
    a_args, a_header = PlottingItemDataFactory._extract_header(input)
    assert a_args == args
    assert a_header == header
