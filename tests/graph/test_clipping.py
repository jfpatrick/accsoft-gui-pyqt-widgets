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
    return CurveData(x=x_val, y=y_val)


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


def test_calc_intersection_intersect_in_the_middle_with_zero():
    point_1 = _point(0, 0)
    point_2 = _point(2, 2)
    line = 1
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == 1
    assert result.y == 1


def test_calc_intersection_intersect_in_the_middle_with_zero_float_result():
    point_1 = _point(0, 0)
    point_2 = _point(2, 1)
    line = 1
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == 1
    assert result.y == 0.5


def test_calc_intersection_intersect_in_the_middle_without_zero():
    point_1 = _point(100.0, 100.0)
    point_2 = _point(200.0, 200.0)
    line = 150.0
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == 150.0
    assert result.y == 150.0


def test_calc_intersection_intersect_in_the_middle_with_negative():
    point_1 = _point(-100.0, -100.0)
    point_2 = _point(100.0, 100.0)
    line = 0
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == 0.0
    assert result.y == 0.0


def test_calc_intersection_intersect_in_the_middle_both_negative():
    point_1 = _point(-200.0, -200.0)
    point_2 = _point(-100.0, -100.0)
    line = -150.0
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == -150.0
    assert result.y == -150.0


def test_calc_intersection_same_points_and_intersection_on_them():
    point_1 = _point(0, 0)
    point_2 = _point(0, 0)
    line = 0
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == 0
    assert result.y == 0


def test_calc_intersection_in_front_of_range_negative():
    point_1 = _point(0, 0)
    point_2 = _point(2, 2)
    line = -1
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x is np.nan
    assert result.y is np.nan


def test_calc_intersection_after_range():
    point_1 = _point(0, 0)
    point_2 = _point(2, 2)
    line = 3
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x is np.nan
    assert result.y is np.nan


def test_calc_intersection_wrong_order_in_front_of_range():
    point_1 = _point(2, 2)
    point_2 = _point(0, 0)
    line = 1
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == 1
    assert result.y == 1


def test_calc_intersection_wrong_order_on_end_of_range():
    point_1 = _point(2, 2)
    point_2 = _point(0, 0)
    line = 2
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x == 2
    assert result.y == 2


def test_calc_intersection_wrong_order_after_range():
    point_1 = _point(2, 2)
    point_2 = _point(0, 0)
    line = 3
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x is np.nan
    assert result.y is np.nan


def test_calc_intersection_wrong_order_in_front_of_range_negative():
    point_1 = _point(2, 2)
    point_2 = _point(0, 0)
    line = -1
    result = clipping.calc_intersection(point_1, point_2, line)
    assert result.x is np.nan
    assert result.y is np.nan


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
