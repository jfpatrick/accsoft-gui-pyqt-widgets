import numpy as np
from typing import List, Iterable, Union, Tuple


def assert_view_box_range_similar(actual_range: Iterable[Union[Tuple[float, float], List[float]]],
                                  expected_range: Iterable[Union[Tuple[float, float], List[float]]],
                                  tolerance_factor: float = 0.05):
    """
    Compare a viewboxes range with an expected range

    Args:
        actual_range: Actual range that is supposed to be checked
        expected_range: Range that we expect
        tolerance_factor: Sometimes the range of  the plot is a bit hard to predict
                          because of padding on ranges. This tolerance factor influences
                          the range in which the actual range is seen as right.
    """
    def assert_within_tolerance(a, b, atol):
        assert abs(b - a) <= atol

    for actual, expected in list(zip(actual_range, expected_range)):
        abs_tolerance = (expected[1] - expected[0]) * tolerance_factor
        if not np.isnan(expected[0]):
            assert_within_tolerance(actual[0], expected[0], abs_tolerance)
        if not np.isnan(expected[1]):
            assert_within_tolerance(actual[1], expected[1], abs_tolerance)
