from typing import List

import numpy as np
import pytest

from accwidgets.graph import CurveData, PointData
import accwidgets.graph.datamodel.datamodelclipping as clipping


def _point(x_val, y_val) -> PointData:
    """Create a dict representing a point

    Args:
        x_val: X Value
        y_val: Y Value
    """
    return PointData(x=x_val, y=y_val)


def _curve(x_val, y_val) -> CurveData:
    """Create a dict representing a point

    Args:
        x_val: X Value
        y_val: Y Value
    """
    return CurveData(x=x_val, y=y_val, check_validity=False)


def test_binary_search_line_between_and_even_number_of_points():
    x_list = list(range(0, 101))
    line = 5.6
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 5
    assert result["after"] == 6


def test_binary_search_line_between_and_odd_number_of_points():
    x_list = list(range(1, 101))
    line = 5.6
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 4
    assert result["after"] == 5


def test_binary_search_line_between_and_line_int_value():
    x_list = list(range(0, 101))
    line = 5
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 5
    assert result["after"] == 5


def test_binary_search_line_between_and_range_small():
    x_list = list(range(0, 2))
    line = 0.5
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 0
    assert result["after"] == 1


def test_binary_search_line_on_first_value_odd_range():
    x_list = list(range(0, 2))
    line = 0
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 0
    assert result["after"] == 0


def test_binary_search_line_on_first_value_even_range():
    x_list = list(range(0, 1))
    line = 0
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 0
    assert result["after"] == 0


def test_binary_search_line_before_first_element_even_range():
    x_list = list(range(0, 101))
    line = -1
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == -1
    assert result["after"] == 0


def test_binary_search_one_element_line_on_it():
    x_list = [2.0]
    line = 2.0
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 0
    assert result["after"] == 0


def test_binary_search_one_element_line_before_it():
    x_list = [2.0]
    line = 1.0
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == -1
    assert result["after"] == 0


def test_binary_search_one_element_line_after_it():
    x_list = [2.0]
    line = 3.0
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 0
    assert result["after"] == -1


def test_binary_search_line_before_first_element_odd_range():
    x_list = list(range(0, 100))
    line = -1
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == -1
    assert result["after"] == 0


def test_binary_search_line_on_last_point_even_range():
    x_list = list(range(0, 101))
    line = 101
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 100
    assert result["after"] == -1


def test_binary_search_line_on_last_point_odd_range():
    x_list: List[int] = list(range(0, 100))
    line = 100
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 99
    assert result["after"] == -1


def test_binary_search_empty_list():
    x_list: List[float] = []
    line = 11
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == -1
    assert result["after"] == -1


def test_binary_search_line_on_first_point_odd_float_range():
    x_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    line = 0.0
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 0
    assert result["after"] == 0


def test_binary_search_line_on_second_point_odd_float_range():
    x_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    line = 0.25
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 1
    assert result["after"] == 1


def test_binary_search_line_on_middle_point_odd_float_range():
    x_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    line = 0.5
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 2
    assert result["after"] == 2


def test_binary_search_line_on_next_to_last_point_odd_float_range():
    x_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    line = 0.75
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 3
    assert result["after"] == 3


def test_binary_search_line_on_last_point_odd_float_range():
    x_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    line = 1.0
    result = clipping.bin_search_surrounding_points(x_list, line)
    assert result["before"] == 4
    assert result["after"] == 4


@pytest.mark.parametrize(
    ["point_1", "point_2", "line", "expected_x", "expected_y"],
    [
        (_point(0, 0), _point(2, 2), 1, 1, 1),
        (_point(0, 0), _point(2, 1), 1, 1, 0.5),
        (_point(100.0, 100.0), _point(200.0, 200.0), 150.0, 150.0, 150.0),
        (_point(-100.0, -100.0), _point(100.0, 100.0), 0.0, 0.0, 0.0),
        (_point(0, 0), _point(0, 0), 0.0, 0.0, 0.0),
        (_point(-200.0, -200.0), _point(-100.0, -100.0), -150.0, -150.0, -150.0),
        (_point(0, 0), _point(2, 2), -1, np.nan, np.nan),
        (_point(0, 0), _point(2, 2), 3, np.nan, np.nan),
    ],
)
def test_calc_intersection(point_1,
                           point_2,
                           line,
                           expected_x,
                           expected_y):
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == expected_x or np.isnan(result.x) and np.isnan(expected_x)
    assert result.y == expected_y or np.isnan(result.y) and np.isnan(expected_y)


@pytest.mark.parametrize(
    ["point_1", "point_2", "line", "expected_x", "expected_y"],
    [
        (_point(2, 2), _point(0, 0), 1, 1, 1),
        (_point(2, 2), _point(0, 0), 2, 2, 2),
        (_point(2, 2), _point(0, 0), 3, np.nan, np.nan),
        (_point(2, 2), _point(0, 0), -1, np.nan, np.nan),
    ],
)
def test_calc_intersection_wrong_order(point_1,
                                       point_2,
                                       line,
                                       expected_x,
                                       expected_y):
    with pytest.warns(UserWarning,
                      match=r"Parameters are in wrong order"):
        result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == expected_x or np.isnan(result.x) and np.isnan(expected_x)
    assert result.y == expected_y or np.isnan(result.y) and np.isnan(expected_y)


def test_intersect_in_range():
    x_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    y_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    curve = _curve(x_values, y_values)
    line = 1.5
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == 1
    assert result["first_after_index"] == 2
    intersection = result["intersection"]
    if isinstance(intersection, PointData):
        assert intersection.x == 1.5
        assert intersection.y == 1.5
    else:
        raise ValueError("Intersection is not an instance of PointData")


def test_intersect_on_first_element():
    x_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    y_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    curve = _curve(x_values, y_values)
    line = 0.0
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == 0
    assert result["first_after_index"] == 0
    intersection = result["intersection"]
    if isinstance(intersection, PointData):
        assert intersection.x == 0
        assert intersection.y == 0
    else:
        raise ValueError("Intersection is not an instance of PointData")


def test_intersect_before_first_element():
    x_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    y_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    curve = _curve(x_values, y_values)
    line = -1.0
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == -1
    assert result["first_after_index"] == 0
    assert result["intersection"].is_nan


def test_intersect_on_last_element():
    x_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    y_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    curve = _curve(x_values, y_values)
    line = 4.0
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == 4
    assert result["first_after_index"] == 4
    intersection = result["intersection"]
    if isinstance(intersection, PointData):
        assert intersection.x == 4.0
        assert intersection.y == 4.0
    else:
        raise ValueError("Intersection is not an instance of PointData")


def test_intersect_after_last_element():
    x_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    y_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    curve = _curve(x_values, y_values)
    line = 5.0
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == 4
    assert result["first_after_index"] == -1
    assert result["intersection"].is_nan


def test_intersect_one_point_line_after():
    x_values = [0]
    y_values = [0]
    curve = _curve(x_values, y_values)
    line = 1
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == 0
    assert result["first_after_index"] == -1
    assert result["intersection"].is_nan


def test_intersect_one_point_line_before():
    x_values = [0]
    y_values = [0]
    curve = _curve(x_values, y_values)
    line = -1
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == -1
    assert result["first_after_index"] == 0
    assert result["intersection"].is_nan


def test_intersect_empty_list():
    x_values: List[float] = []
    y_values: List[float] = []
    curve = _curve(x_values, y_values)
    line = 0
    result = clipping.intersect(curve, line)
    assert result["last_before_index"] == -1
    assert result["first_after_index"] == -1
    assert result["intersection"].is_nan


def test_intersect_different_length_arrays():
    x_values: List[float] = [1, 2, 3, 4, 5]
    y_values: List[float] = [1, 2, 3, 4]
    with pytest.raises(ValueError):
        curve = _curve(x_values, y_values)
        line = 0
        clipping.intersect(curve, line)
