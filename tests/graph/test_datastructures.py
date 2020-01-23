"""
Tests that tests if a data structure's validity is determined correctly,
The tests rely on warnings being emitted on creating the data structures.
"""

from typing import NamedTuple, Union, List, Sequence, Optional, cast
import itertools

import pytest
import numpy as np
from accwidgets import graph as accgraph

from .mock_utils.utils import warn_always


class PointNamedTuple(NamedTuple):

    x: Union[float, Sequence[Optional[float]], None]
    y: Union[float, Sequence[Optional[float]], None]


class BarNamedTuple(NamedTuple):

    x: Union[float, Sequence[Optional[float]], None]
    y: Union[float, Sequence[Optional[float]], None]
    h: Union[float, Sequence[Optional[float]], None]


class InjectionBarNamedTuple(NamedTuple):

    x: Union[float, Sequence[Optional[float]], None]
    y: Union[float, Sequence[Optional[float]], None]
    h: Union[float, Sequence[Optional[float]], None]
    w: Union[float, Sequence[Optional[float]], None]
    l: Union[str, Sequence[Optional[str]], None]


class TimestampMarkerNamedTuple(NamedTuple):

    x: Union[float, Sequence[Optional[float]], None]
    c: Union[str, Sequence[Optional[str]], None]
    l: Union[str, Sequence[Optional[str]], None]


# ~~~~~~~~~~ Curve Data-Structures ~~~~~~~~~~

@pytest.mark.parametrize("combinations", [
    PointNamedTuple(0.0, 1.0),
    PointNamedTuple(np.nan, np.nan),
    PointNamedTuple(None, None),
    PointNamedTuple(0.0, np.nan),
    PointNamedTuple(0.0, None),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_point_data(recwarn, combinations: PointNamedTuple):
    _ = accgraph.PointData(
        x=cast(float, combinations.x),
        y=cast(float, combinations.y),
    )
    assert len(recwarn) == 0


@pytest.mark.parametrize("combinations", [
    PointNamedTuple(np.nan, 0.0),
    PointNamedTuple(None, 0.0),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_point_data(combinations):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.PointData(
            x=cast(float, combinations.x),
            y=cast(float, combinations.y),
        )


@pytest.mark.parametrize("combinations", [
    PointNamedTuple([0.0, np.nan, 1.0, 2.0, 3.0], [0.0, np.nan, 1.0, np.nan, 2.0]),
    PointNamedTuple([0.0, None, 1.0, 2.0, 3.0], [0.0, None, 1.0, None, 2.0]),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_curve_data(recwarn, combinations: PointNamedTuple):
    curve = accgraph.CurveData(
        x=cast(List[float], combinations.x),
        y=cast(List[float], combinations.y),
    )
    assert len(recwarn) == 0
    assert np.allclose(curve.is_valid(), np.array([True, True, True, True, True]))


@pytest.mark.parametrize("combinations", [
    PointNamedTuple([0.0, np.nan, np.nan, 3.0], [0.0, 1.0, np.nan, np.nan]),
    PointNamedTuple([0.0, None, None, 3.0], [0.0, 1.0, None, None]),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_curve_data(recwarn, combinations: PointNamedTuple):
    curve = accgraph.CurveData(
        x=cast(List[float], combinations.x),
        y=cast(List[float], combinations.y),
    )
    assert len(recwarn) == 1
    assert recwarn.pop(accgraph.InvalidDataStructureWarning)
    assert np.allclose(curve.is_valid(), np.array([True, False, True, True]))


@pytest.mark.parametrize("combinations", [
    PointNamedTuple(p[0], p[1]) for p in itertools.permutations([[0.0], [0.0, 1.0]], 2)
])
def test_curve_data_one_different_length(combinations: PointNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.CurveData(x=cast(List[float], combinations.x), y=cast(List[float], combinations.y))


# ~~~~~~~~~~ Bargraph Data-Structures ~~~~~~~~~~


@pytest.mark.parametrize("combinations", [
    BarNamedTuple(0.0, 1.0, 2.0),
    BarNamedTuple(0.0, np.nan, 2.0),
    BarNamedTuple(0.0, None, 2.0),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_bar_data(recwarn, combinations: BarNamedTuple):
    _ = accgraph.BarData(
        x=cast(float, combinations.x),
        y=cast(float, combinations.y),
        height=cast(float, combinations.h),
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
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_bar_data(combinations: BarNamedTuple):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.BarData(
            x=cast(float, combinations.x),
            y=cast(float, combinations.y),
            height=cast(float, combinations.h),
        )


@pytest.mark.parametrize("combinations", [
    BarNamedTuple([0.0, 0.0], [1.0, np.nan], [2.0, 2.0]),
    BarNamedTuple([0.0, 0.0], [1.0, None], [2.0, 2.0]),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_bar_collection_data(recwarn, combinations: BarNamedTuple):
    bar_collection = accgraph.BarCollectionData(
        x=cast(List[float], combinations.x),
        y=cast(List[float], combinations.y),
        heights=cast(List[float], combinations.h),
    )
    assert len(recwarn) == 0
    assert np.allclose(bar_collection.is_valid(), np.array([True, True]))


@pytest.mark.parametrize("combinations", [
    BarNamedTuple(
        [np.nan, 0.0, np.nan, 0.0, 0.0, np.nan, 0.0, np.nan],
        [1.0, 1.0, 1.0, 1.0, np.nan, np.nan, np.nan, np.nan],
        [2.0, 2.0, np.nan, np.nan, np.nan, 2.0, 2.0, np.nan],
    ),
    BarNamedTuple(
        [None, 0.0, None, 0.0, 0.0, None, 0.0, None],
        [1.0, 1.0, 1.0, 1.0, None, None, None, None],
        [2.0, 2.0, None, None, None, 2.0, 2.0, None],
    ),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_bar_collection_data(recwarn, combinations: BarNamedTuple):
    bar_collection = accgraph.BarCollectionData(
        x=cast(List[float], combinations.x),
        y=cast(List[float], combinations.y),
        heights=cast(List[float], combinations.h),
    )
    assert len(recwarn) == 1
    assert recwarn.pop(accgraph.InvalidDataStructureWarning)
    assert np.allclose(bar_collection.is_valid(), np.array([False, True, False, False, False, False, True, False]))


@pytest.mark.parametrize("combinations", [
    BarNamedTuple(cast(List[float], p[0]),
                  cast(List[float], p[1]),
                  cast(List[float], p[2]))
    for p in itertools.permutations([[], [0.0], [0.0, 1.0]], 3)
])
def test_bar_collection_data_multiple_different_length(combinations):
    with pytest.raises(ValueError):
        _ = accgraph.BarCollectionData(
            x=cast(List[float], combinations.x),
            y=cast(List[float], combinations.y),
            heights=cast(List[float], combinations.h),
        )


@pytest.mark.parametrize("combinations", [
    BarNamedTuple(p[0], p[1], p[2]) for p in itertools.permutations([[0.0], [0.0], [0.0, 1.0]], 3)
])
def test_bar_collection_data_one_different_length(combinations):
    with pytest.raises(ValueError):
        _ = accgraph.BarCollectionData(
            x=cast(List[float], combinations.x),
            y=cast(List[float], combinations.y),
            heights=cast(List[float], combinations.h),
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
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_injection_bar_data(recwarn, combinations: InjectionBarNamedTuple):
    _ = accgraph.InjectionBarData(
        x=cast(float, combinations.x),
        y=cast(float, combinations.y),
        height=cast(float, combinations.h),
        width=cast(float, combinations.w),
        label=cast(str, combinations.l),
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
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_injection_bar_data(combinations: InjectionBarNamedTuple):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.InjectionBarData(
            x=cast(float, combinations.x),
            y=cast(float, combinations.y),
            height=cast(float, combinations.h),
            width=cast(float, combinations.w),
            label=cast(str, combinations.l),
        )


@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        [2.0, np.nan, 2.0, np.nan],
        [3.0, 3.0, np.nan, np.nan],
        ["", "", "", ""],
    ),
    InjectionBarNamedTuple(
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        [2.0, None, 2.0, None],
        [3.0, 3.0, None, None],
        ["", "", "", ""],
    ),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_injection_bar_collection_data(recwarn, combinations: InjectionBarNamedTuple):
    bar_collection = accgraph.InjectionBarCollectionData(
        x=cast(List[float], combinations.x),
        y=cast(List[float], combinations.y),
        heights=cast(List[float], combinations.h),
        widths=cast(List[float], combinations.w),
        labels=cast(List[str], combinations.l),
    )
    assert len(recwarn) == 0
    assert np.allclose(bar_collection.is_valid(), np.array([True, True, True, True]))


@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(
        [np.nan, 0.0, np.nan, np.nan, np.nan, 0.0, 0.0, 0.0, 0.0, np.nan, np.nan, np.nan, 0.0, np.nan],
        [1.0, 0.0, 1.0, 1.0, 1.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 0.0, np.nan],
        [2.0, 0.0, np.nan, 2.0, np.nan, 2.0, np.nan, 2.0, np.nan, 2.0, np.nan, 2.0, np.nan, np.nan],
        [3.0, 0.0, 3.0, np.nan, np.nan, 3.0, 3.0, np.nan, np.nan, 3.0, 3.0, np.nan, np.nan, np.nan],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ),
    InjectionBarNamedTuple(
        [None, 0.0, None, None, None, 0.0, 0.0, 0.0, 0.0, None, None, None, 0.0, None],
        [1.0, 0.0, 1.0, 1.0, 1.0, None, None, None, None, None, None, None, 0.0, None],
        [2.0, 0.0, None, 2.0, None, 2.0, None, 2.0, None, 2.0, None, 2.0, None, None],
        [3.0, 0.0, 3.0, None, None, 3.0, 3.0, None, None, 3.0, 3.0, None, None, None],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_injection_bar_collection_data(recwarn, combinations: InjectionBarNamedTuple):
    bar_collection = accgraph.InjectionBarCollectionData(
        x=cast(List[float], combinations.x),
        y=cast(List[float], combinations.y),
        heights=cast(List[float], combinations.h),
        widths=cast(List[float], combinations.w),
        labels=cast(List[str], combinations.l),
    )
    assert len(recwarn) == 1
    assert recwarn.pop(accgraph.InvalidDataStructureWarning)
    assert np.allclose(
        bar_collection.is_valid(),
        np.array([False, True, False, False, False, False, False, False, False, False, False, False, True, False]),
    )


@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(cast(List[float], p[0]),
                           cast(List[float], p[1]),
                           cast(List[float], p[2]),
                           cast(List[float], p[3]),
                           [""])
    for p in itertools.permutations([[], [0.0], [0.0, 1.0], [0.0, 1.0]], 4)
])
def test_injection_bar_collection_data_multiple_different_length(combinations: InjectionBarNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.InjectionBarCollectionData(
            x=cast(List[float], combinations.x),
            y=cast(List[float], combinations.y),
            heights=cast(List[float], combinations.h),
            widths=cast(List[float], combinations.w),
            labels=cast(List[str], combinations.l),
        )


@pytest.mark.parametrize("combinations", [
    InjectionBarNamedTuple(p[0], p[1], p[2], p[3], [""]) for p in itertools.permutations([[0.0], [0.0], [0.0], [0.0, 1.0]], 4)
])
def test_injection_bar_collection_data_one_different_length(combinations: InjectionBarNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.InjectionBarCollectionData(
            x=cast(List[float], combinations.x),
            y=cast(List[float], combinations.y),
            heights=cast(List[float], combinations.h),
            widths=cast(List[float], combinations.w),
            labels=cast(List[str], combinations.l),
        )


# ~~~~~~~~~~ Timestamp Marker Data-Structures ~~~~~~~~~~

@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(0.0, "r", ""),
    TimestampMarkerNamedTuple(0.0, None, ""),
    TimestampMarkerNamedTuple(0.0, None, ""),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_timestamp_marker_data(recwarn, combinations: TimestampMarkerNamedTuple):
    _ = accgraph.TimestampMarkerData(
        x=cast(float, combinations.x),
        color=cast(str, combinations.c),
        label=cast(str, combinations.l),
    )
    assert len(recwarn) == 0


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(0.0, "", "label"),
    TimestampMarkerNamedTuple(0.0, "#XYZ", "label"),
    TimestampMarkerNamedTuple(0.0, None, "label"),
    TimestampMarkerNamedTuple(0.0, "red, comrade, use red", "label"),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_timestamp_marker_color(recwarn, combinations: TimestampMarkerNamedTuple):
    data = accgraph.TimestampMarkerData(
        x=cast(float, combinations.x),
        color=cast(str, combinations.c),
        label=cast(str, combinations.l),
    )
    assert len(recwarn) == 0
    assert data.color == accgraph.DEFAULT_COLOR


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(
        [0.0, 1.0, 2.0, 3.0],
        ["", "#XYZ", None, "red, comrade, use red"],
        ["label 0", "label 1", "label 2", "label 3"],
    ),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_timestamp_marker_collection_color(recwarn, combinations: TimestampMarkerNamedTuple):
    data = accgraph.TimestampMarkerCollectionData(
        x=cast(List[float], combinations.x),
        colors=cast(List[str], combinations.c),
        labels=cast(List[str], combinations.l),
    )
    assert len(recwarn) == 0
    assert np.array_equal(data.colors, [accgraph.DEFAULT_COLOR, accgraph.DEFAULT_COLOR, accgraph.DEFAULT_COLOR, accgraph.DEFAULT_COLOR])


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple(np.nan, "r", ""),
    TimestampMarkerNamedTuple(None, "r", ""),
])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_timestamp_marker_data(combinations: TimestampMarkerNamedTuple):
    with pytest.warns(accgraph.InvalidDataStructureWarning):
        _ = accgraph.TimestampMarkerData(
            x=cast(float, combinations.x),
            color=cast(str, combinations.c),
            label=cast(str, combinations.l),
        )


@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_timestamp_marker_collection_data(recwarn):
    bar_collection = accgraph.TimestampMarkerCollectionData(
        x=[0.0],
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
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_timestamp_marker_collection_data(recwarn, combinations: TimestampMarkerNamedTuple):
    bar_collection = accgraph.TimestampMarkerCollectionData(
        x=cast(List[float], combinations.x),
        colors=cast(List[str], combinations.c),
        labels=cast(List[str], combinations.l),
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
            x=cast(List[float], combinations.x),
            colors=cast(List[str], combinations.c),
            labels=cast(List[str], combinations.l),
        )


@pytest.mark.parametrize("combinations", [
    TimestampMarkerNamedTuple([np.nan], ["r"], ["label_1", "label_2"]),
    TimestampMarkerNamedTuple([], [], ["label_1"]),
])
def test_timestamp_marker_collection_data_one_different_length(combinations: TimestampMarkerNamedTuple):
    with pytest.raises(ValueError):
        _ = accgraph.TimestampMarkerCollectionData(
            x=cast(List[float], combinations.x),
            colors=cast(List[str], combinations.c),
            labels=cast(List[str], combinations.l),
        )
