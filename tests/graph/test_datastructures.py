"""
Tests that tests if a data structure's validity is determined correctly,
The tests rely on warnings being emitted on creating the data structures.
"""

from typing import NamedTuple, Union, List
import itertools

import pytest
import numpy as np
from accwidgets import graph as accgraph


class PointNamedTuple(NamedTuple):

    x: Union[float, List[float], None]
    y: Union[float, List[float], None]


class BarNamedTuple(NamedTuple):

    x: Union[float, List[float], None]
    y: Union[float, List[float], None]
    h: Union[float, List[float], None]


class InjectionBarNamedTuple(NamedTuple):

    x: Union[float, List[float], None]
    y: Union[float, List[float], None]
    h: Union[float, List[float], None]
    w: Union[float, List[float], None]
    l: Union[str, List[str], None]


class TimestampMarkerNamedTuple(NamedTuple):

    x: Union[float, List[float], None]
    c: Union[str, List[str], None]
    l: Union[str, List[str], None]

# ~~~~~~~~~~ Curve Data-Structures ~~~~~~~~~~

@pytest.mark.parametrize("combinations", [
    PointNamedTuple(0.0, 1.0),
    PointNamedTuple(np.nan, np.nan),
    PointNamedTuple(None, None),
    PointNamedTuple(0.0, np.nan),
    PointNamedTuple(0.0, None),
])
def test_valid_point_data(recwarn, warn_always, combinations: PointNamedTuple):
    _ = accgraph.PointData(
        x_value=combinations.x,
        y_value=combinations.y,
    )
    assert len(recwarn) == 0


@pytest.mark.parametrize("combinations", [
    PointNamedTuple(np.nan, 0.0),
    PointNamedTuple(None, 0.0),
])
def test_invalid_point_data(warn_always, combinations):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.PointData(
            x_value=combinations.x,
            y_value=combinations.y,
        )


@pytest.mark.parametrize("combinations", [
    PointNamedTuple([0.0, np.nan, 1.0, 2.0, 3.0], [0.0, np.nan, 1.0, np.nan, 2.0]),
    PointNamedTuple([0.0, None, 1.0, 2.0, 3.0], [0.0, None, 1.0, None, 2.0]),
])
def test_valid_curve_data(recwarn, warn_always, combinations: PointNamedTuple):
    curve = accgraph.CurveData(
        x_values=combinations.x,
        y_values=combinations.y,
    )
    assert len(recwarn) == 0
    assert np.allclose(curve.is_valid(), np.array([True, True, True, True, True]))


@pytest.mark.parametrize("combinations", [
    PointNamedTuple([0.0, np.nan, np.nan, 3.0], [0.0, 1.0, np.nan, np.nan]),
    PointNamedTuple([0.0, None, None, 3.0], [0.0, 1.0, None, None]),
])
def test_invalid_curve_data(recwarn, warn_always, combinations: PointNamedTuple):
    curve = accgraph.CurveData(
        x_values=combinations.x,
        y_values=combinations.y,
    )
    assert len(recwarn) == 1
    assert recwarn.pop(accgraph.InvalidDataStructureWarning)
    assert np.allclose(curve.is_valid(), np.array([True, False, True, True]))


@pytest.mark.parametrize("combinations", list(
    PointNamedTuple(p[0], p[1]) for p in itertools.permutations([[0.0], [0.0, 1.0]], 2)
))
def test_curve_data_one_different_length(combinations: PointNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.CurveData(
            x_values=combinations.x,
            y_values=combinations.y,
        )


# ~~~~~~~~~~ Bargraph Data-Structures ~~~~~~~~~~


@pytest.mark.parametrize("combinations", [
    BarNamedTuple(0.0, 1.0, 2.0),
    BarNamedTuple(0.0, np.nan, 2.0),
    BarNamedTuple(0.0, None, 2.0),
])
def test_valid_bar_data(recwarn, warn_always, combinations: BarNamedTuple):
    _ = accgraph.BarData(
        x_value=combinations.x,
        y_value=combinations.y,
        height=combinations.h,
    )
    assert len(recwarn) == 0


@pytest.mark.parametrize("combinations", [
    BarNamedTuple(np.nan, 1.0, 2.0),
    BarNamedTuple(None, 1.0, 2.0),
    BarNamedTuple(np.nan, 1.0, np.nan),
    BarNamedTuple(None, 1.0, None),
    BarNamedTuple(0.0, 1.0, np.nan),
    BarNamedTuple(0.0, 1.0, None),
    BarNamedTuple(0.0, np.nan, np.nan),
    BarNamedTuple(0.0, None, None),
    BarNamedTuple(np.nan, np.nan, 2.0),
    BarNamedTuple(None, None, 2.0),
    BarNamedTuple(np.nan, np.nan, np.nan),
    BarNamedTuple(None, None, None),
])
def test_invalid_bar_data(warn_always, combinations: BarNamedTuple):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.BarData(
            x_value=combinations.x,
            y_value=combinations.y,
            height=combinations.h,
        )


@pytest.mark.parametrize("combinations", [
    BarNamedTuple([0.0, 0.0], [1.0, np.nan], [2.0, 2.0]),
    BarNamedTuple([0.0, 0.0], [1.0, None], [2.0, 2.0]),
])
def test_valid_bar_collection_data(recwarn, warn_always, combinations: BarNamedTuple):
    bar_collection = accgraph.BarCollectionData(
        x_values=combinations.x,
        y_values=combinations.y,
        heights=combinations.h,
    )
    assert len(recwarn) == 0
    assert np.allclose(bar_collection.is_valid(), np.array([True, True]))


@pytest.mark.parametrize("combinations", [
    BarNamedTuple(
        [np.nan, 0.0, np.nan, 0.0, 0.0, np.nan, 0.0, np.nan],
        [1.0, 1.0, 1.0, 1.0, np.nan, np.nan, np.nan, np.nan],
        [2.0, 2.0, np.nan, np.nan, np.nan, 2.0, 2.0, np.nan]
    ),
    BarNamedTuple(
        [None, 0.0, None, 0.0, 0.0, None, 0.0, None],
        [1.0, 1.0, 1.0, 1.0, None, None, None, None],
        [2.0, 2.0, None, None, None, 2.0, 2.0, None]
    ),
])
def test_invalid_bar_collection_data(recwarn, warn_always, combinations: BarNamedTuple):
    bar_collection = accgraph.BarCollectionData(
        x_values=combinations.x,
        y_values=combinations.y,
        heights=combinations.h,
    )
    assert len(recwarn) == 1
    assert recwarn.pop(accgraph.InvalidDataStructureWarning)
    assert np.allclose(bar_collection.is_valid(), np.array([False, True, False, False, False, False, True, False]))


@pytest.mark.parametrize("combinations", list(
    BarNamedTuple(p[0], p[1], p[2]) for p in itertools.permutations([[], [0.0], [0.0, 1.0]], 3)
))
def test_bar_collection_data_multiple_different_length(combinations):
    with pytest.raises(ValueError):
        _ = accgraph.BarCollectionData(
            x_values=combinations.x,
            y_values=combinations.y,
            heights=combinations.h,
        )


@pytest.mark.parametrize("combinations", list(
    BarNamedTuple(p[0], p[1], p[2]) for p in itertools.permutations([[0.0], [0.0], [0.0, 1.0]], 3)
))
def test_bar_collection_data_one_different_length(combinations):
    with pytest.raises(ValueError):
        _ = accgraph.BarCollectionData(
            x_values=combinations.x,
            y_values=combinations.y,
            heights=combinations.h,
        )


# ~~~~~~~~~~ Injection Bar Data-Structures ~~~~~~~~~~

@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(0.0, 1.0, 2.0, 3.0, ""),
    InjectionBarNamedTuple(0.0, 1.0, np.nan, 3.0, ""),
    InjectionBarNamedTuple(0.0, 1.0, None, 3.0, ""),
    InjectionBarNamedTuple(0.0, 1.0, 2.0, np.nan, ""),
    InjectionBarNamedTuple(0.0, 1.0, 2.0, None, ""),
    InjectionBarNamedTuple(0.0, 1.0, np.nan, np.nan, ""),
    InjectionBarNamedTuple(0.0, 1.0, None, None, ""),
])
def test_valid_injection_bar_data(recwarn, warn_always, combinations: InjectionBarNamedTuple):
    _ = accgraph.InjectionBarData(
        x_value=combinations.x,
        y_value=combinations.y,
        height=combinations.h,
        width=combinations.w,
        label=combinations.l,
    )
    assert len(recwarn) == 0


@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(np.nan, 1.0, 2.0, 3.0, ""),
    InjectionBarNamedTuple(None, 1.0, 2.0, 3.0, ""),
    InjectionBarNamedTuple(np.nan, 1.0, np.nan, 3.0, ""),
    InjectionBarNamedTuple(None, 1.0, None, 3.0, ""),
    InjectionBarNamedTuple(np.nan, 1.0, 2.0, np.nan, ""),
    InjectionBarNamedTuple(None, 1.0, 2.0, None, ""),
    InjectionBarNamedTuple(np.nan, 1.0, np.nan, np.nan, ""),
    InjectionBarNamedTuple(None, 1.0, None, None, ""),
    InjectionBarNamedTuple(0.0, np.nan, 2.0, 3.0, ""),
    InjectionBarNamedTuple(0.0, None, 2.0, 3.0, ""),
    InjectionBarNamedTuple(0.0, np.nan, np.nan, 3.0, ""),
    InjectionBarNamedTuple(0.0, None, None, 3.0, ""),
    InjectionBarNamedTuple(0.0, np.nan, 2.0, np.nan, ""),
    InjectionBarNamedTuple(0.0, None, 2.0, None, ""),
    InjectionBarNamedTuple(0.0, np.nan, np.nan, np.nan, ""),
    InjectionBarNamedTuple(0.0, None, None, None, ""),
    InjectionBarNamedTuple(np.nan, np.nan, 2.0, 3.0, ""),
    InjectionBarNamedTuple(None, None, 2.0, 3.0, ""),
    InjectionBarNamedTuple(np.nan, np.nan, np.nan, 3.0, ""),
    InjectionBarNamedTuple(None, None, None, 3.0, ""),
    InjectionBarNamedTuple(np.nan, np.nan, 2.0, np.nan, ""),
    InjectionBarNamedTuple(None, None, 2.0, None, ""),
    InjectionBarNamedTuple(np.nan, np.nan, np.nan, np.nan, ""),
    InjectionBarNamedTuple(None, None, None, None, ""),
])
def test_invalid_injection_bar_data(warn_always, combinations: InjectionBarNamedTuple):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.InjectionBarData(
            x_value=combinations.x,
            y_value=combinations.y,
            height=combinations.h,
            width=combinations.w,
            label=combinations.l,
        )


@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        [2.0, np.nan, 2.0, np.nan],
        [3.0, 3.0, np.nan, np.nan],
        ["", "", "", ""]
    ),
    InjectionBarNamedTuple(
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        [2.0, None, 2.0, None],
        [3.0, 3.0, None, None],
        ["", "", "", ""]
    ),
])
def test_valid_injection_bar_collection_data(recwarn, warn_always, combinations: InjectionBarNamedTuple):
    bar_collection = accgraph.InjectionBarCollectionData(
        x_values=combinations.x,
        y_values=combinations.y,
        heights=combinations.h,
        widths=combinations.w,
        labels=combinations.l,
    )
    assert len(recwarn) == 0
    assert np.allclose(bar_collection.is_valid(), np.array([True, True, True, True]))


@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(
        [np.nan, 0.0, np.nan, np.nan, np.nan, 0.0, 0.0, 0.0, 0.0, np.nan, np.nan, np.nan, 0.0, np.nan],
        [1.0, 0.0, 1.0, 1.0, 1.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 0.0, np.nan],
        [2.0, 0.0, np.nan, 2.0, np.nan, 2.0, np.nan, 2.0, np.nan, 2.0, np.nan, 2.0, np.nan, np.nan],
        [3.0, 0.0, 3.0, np.nan, np.nan, 3.0, 3.0, np.nan, np.nan, 3.0, 3.0, np.nan, np.nan, np.nan],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    ),
    InjectionBarNamedTuple(
        [None, 0.0, None, None, None, 0.0, 0.0, 0.0, 0.0, None, None, None, 0.0, None],
        [1.0, 0.0, 1.0, 1.0, 1.0, None, None, None, None, None, None, None, 0.0, None],
        [2.0, 0.0, None, 2.0, None, 2.0, None, 2.0, None, 2.0, None, 2.0, None, None],
        [3.0, 0.0, 3.0, None, None, 3.0, 3.0, None, None, 3.0, 3.0, None, None, None],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    ),
])
def test_invalid_injection_bar_collection_data(recwarn, warn_always, combinations: InjectionBarNamedTuple):
    bar_collection = accgraph.InjectionBarCollectionData(
        x_values=combinations.x,
        y_values=combinations.y,
        heights=combinations.h,
        widths=combinations.w,
        labels=combinations.l,
    )
    assert len(recwarn) == 1
    assert recwarn.pop(accgraph.InvalidDataStructureWarning)
    assert np.allclose(bar_collection.is_valid(), np.array(
        [False, True, False, False, False, False, False, False, False, False, False, False, True, False]))


@pytest.mark.parametrize("combinations", list(
    InjectionBarNamedTuple(p[0], p[1], p[2], p[3], [""]) for p in itertools.permutations([[], [0.0], [0.0, 1.0], [0.0, 1.0]], 4)
))
def test_injection_bar_collection_data_multiple_different_length(combinations: InjectionBarNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.InjectionBarCollectionData(
            x_values=combinations.x,
            y_values=combinations.y,
            heights=combinations.h,
            widths=combinations.w,
            labels=combinations.l,
        )


@pytest.mark.parametrize("combinations", list(
    InjectionBarNamedTuple(p[0], p[1], p[2], p[3], [""]) for p in itertools.permutations([[0.0], [0.0], [0.0], [0.0, 1.0]], 4)
))
def test_injection_bar_collection_data_one_different_length(combinations: InjectionBarNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.InjectionBarCollectionData(
            x_values=combinations.x,
            y_values=combinations.y,
            heights=combinations.h,
            widths=combinations.w,
            labels=combinations.l,
        )


# ~~~~~~~~~~ Timestamp Marker Data-Structures ~~~~~~~~~~

@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(0.0, "r", ""),
    TimestampMarkerNamedTuple(0.0, None, ""),
    TimestampMarkerNamedTuple(0.0, None, ""),
])
def test_valid_timestamp_marker_data(recwarn, warn_always, combinations: TimestampMarkerNamedTuple):
    _ = accgraph.TimestampMarkerData(
        x_value=combinations.x,
        color=combinations.c,
        label=combinations.l,
    )
    assert len(recwarn) == 0


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(0.0, "", "label"),
    TimestampMarkerNamedTuple(0.0, "#XYZ", "label"),
    TimestampMarkerNamedTuple(0.0, None, "label"),
    TimestampMarkerNamedTuple(0.0, "red, comrade, use red", "label"),
])
def test_invalid_timestamp_marker_color(recwarn, warn_always, combinations: TimestampMarkerNamedTuple):
    data = accgraph.TimestampMarkerData(
        x_value=combinations.x,
        color=combinations.c,
        label=combinations.l,
    )
    assert len(recwarn) == 0
    assert data.color == accgraph.DEFAULT_COLOR


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(
        [0.0, 1.0, 2.0, 3.0],
        ["", "#XYZ", None, "red, comrade, use red"],
        ["label 0", "label 1", "label 2", "label 3"],
    )
])
def test_invalid_timestamp_marker_collection_color(recwarn, warn_always, combinations: TimestampMarkerNamedTuple):
    data = accgraph.TimestampMarkerCollectionData(
        x_values=combinations.x,
        colors=combinations.c,
        labels=combinations.l,
    )
    assert len(recwarn) == 0
    assert np.array_equal(data.colors, [accgraph.DEFAULT_COLOR, accgraph.DEFAULT_COLOR, accgraph.DEFAULT_COLOR, accgraph.DEFAULT_COLOR])


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(np.nan, "r", ""),
    TimestampMarkerNamedTuple(None, "r", ""),
])
def test_invalid_timestamp_marker_data(warn_always, combinations: TimestampMarkerNamedTuple):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.TimestampMarkerData(
            x_value=combinations.x,
            color=combinations.c,
            label=combinations.l,
        )


def test_valid_timestamp_marker_collection_data(recwarn, warn_always):
    bar_collection = accgraph.TimestampMarkerCollectionData(
        x_values=[0.0],
        colors=["r"],
        labels=[""],
    )
    assert len(recwarn) == 0
    assert np.allclose(bar_collection.is_valid(), np.array([True, True, True, True]))


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(
        [0.0, np.nan, 0.0],
        ["r", "r", "r"],
        ["", "", ""],
    ),
    TimestampMarkerNamedTuple(
        [0.0, None, 0.0],
        ["r", "r", "r"],
        ["", "", ""],
    ),
])
def test_invalid_timestamp_marker_collection_data(recwarn, warn_always, combinations: TimestampMarkerNamedTuple):
    bar_collection = accgraph.TimestampMarkerCollectionData(
        x_values=combinations.x,
        colors=combinations.c,
        labels=combinations.l,
    )
    assert len(recwarn) == 1
    assert recwarn.pop(accgraph.InvalidDataStructureWarning)
    assert np.allclose(bar_collection.is_valid(), np.array([True, False, True]))


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple([np.nan], [], ["label_1", "label_2"]),
    TimestampMarkerNamedTuple([], ["r"], ["label_1", "label_2"]),
])
def test_timestamp_marker_collection_data_multiple_different_length(combinations: TimestampMarkerNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.TimestampMarkerCollectionData(
            x_values=combinations.x,
            colors=combinations.c,
            labels=combinations.l,
        )


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple([np.nan], ["r"], ["label_1", "label_2"]),
    TimestampMarkerNamedTuple([], [], ["label_1"]),
])
def test_timestamp_marker_collection_data_one_different_length(combinations: TimestampMarkerNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.TimestampMarkerCollectionData(
            x_values=combinations.x,
            colors=combinations.c,
            labels=combinations.l,
        )
