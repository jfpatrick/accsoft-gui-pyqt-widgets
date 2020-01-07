""" Clipping functionality for linegraph datamodel """

import logging
from typing import Dict, List, Union

import numpy as np

from accwidgets.graph.datamodel.datastructures import (
    CurveData,
    CurveDataWithTime,
    PointData,
)

LOGGER = logging.getLogger(__name__)


def intersect(
    graph_points: Union[CurveDataWithTime, CurveData],
    vertical_line_x_position: float,
) -> Dict[str, Union[PointData, int]]:
    """Intersect a plot line with a vertical line, for example a boundary
    defined by a x-value.

    The result is collected in a dictionary containing the following entries:
        - the last point's index before the intersection
        - the first point's index after the intersection
        - the intersection between the curve and the passed boundary
    If one of the indices does not exist, -1 is returned in its position.
    If the intersection does not exist, a Point (nan, nan) is returned.

    Args:
        graph_points (Dict[str, List[float]]): x and y values as list
            packaged in a dictionary
        vertical_line_x_position (float): Line on which the intersection
            should be calculated on

    Returns:
        Dictionary containing the results of the intersection
    """
    result: Dict[str, Union[int, PointData]] = {
        "last_before_index": -1,
        "first_after_index": -1,
        "intersection": PointData(np.nan, np.nan),
    }
    x_positions = graph_points.x_values
    y_positions = graph_points.y_values
    if len(x_positions) != len(y_positions):
        LOGGER.error(f"Length:({len(x_positions)}, {len(y_positions)}), Passed Points: {graph_points}")
        raise ValueError("The count of X indices and Y values is not the same.")
    surrounding_points = bin_search_surrounding_points(x_positions, vertical_line_x_position)
    result["last_before_index"] = surrounding_points["before"]
    result["first_after_index"] = surrounding_points["after"]
    # Line is actually in between two points -> Calculate intersection point
    if result["last_before_index"] != -1 and result["first_after_index"] != -1:
        last_before_obj = PointData(
            x_value=x_positions[surrounding_points["before"]],
            y_value=y_positions[surrounding_points["before"]],
        )
        first_after_obj = PointData(
            x_value=x_positions[surrounding_points["after"]],
            y_value=y_positions[surrounding_points["after"]],
        )
        # Intersection between Old Curve
        result["intersection"] = calc_intersection(last_before_obj, first_after_obj, vertical_line_x_position)
    return result


def calc_intersection(point_1: PointData, point_2: PointData, new_point_x_position: float) -> PointData:
    """Calculates the position of a point with a given X value that is
    located on the straight line between point_1 and point_2.

    Args:
        point_1 (dict): Point 1, for example in front of the boundary
        point_2 (dict): Point 2, for example after the boundary
        new_point_x_position (float): X position of the intersection

    Returns:
        Dictionary representing with the intersected point. In case no
        intersection can be calculated from the given points an empty
        dictionary will be returned
    """
    if point_2.x_value < point_1.x_value:
        LOGGER.debug("Parameters are in wrong order. This might hint, that a bug appeared in the code before. \n"
                     f"Point 1:     {point_1} \n"
                     f"Point 2:     {point_2} \n"
                     f"X Position:  {new_point_x_position}")
        point_1, point_2 = point_2, point_1
    if (
        new_point_x_position > point_2.x_value
        or new_point_x_position < point_1.x_value
    ):
        LOGGER.debug("New position not between the passed points, listing their X positions: \n"
                     f"New= {new_point_x_position}, P1= {point_1.x_value}, P2= {point_2.x_value}")
        return PointData()
    if point_2.x_value == point_1.x_value:
        return PointData(x_value=point_1.x_value, y_value=point_1.y_value)
    # Calculate intersection with boundary
    delta_p1_p2_x = point_2.x_value - point_1.x_value
    delta_p1_p2_y = point_2.y_value - point_1.y_value
    delta_p1_line_x = new_point_x_position - point_1.x_value
    temp_x = point_1.x_value + delta_p1_p2_x * (delta_p1_line_x / delta_p1_p2_x)
    temp_y = point_1.y_value + delta_p1_p2_y * (delta_p1_line_x / delta_p1_p2_x)
    return PointData(x_value=temp_x, y_value=temp_y)


def bin_search_surrounding_points(
    x_list: Union[np.ndarray, List[float], List[int]],
    clipping_line_x_position: float,
) -> Dict[str, int]:
    """Searches for the two points closest to the given position of the
    vertical line. Multiple cases can happen here:

    1: Line between two points -> return two points

    2: Line outside the point range -> return closest single point + (-1)
    on the one that does not exist

    3: Less than two points -> one point 0, no points -1 for both

    Args:
        x_list (List[float]): List of x coordinates
        clipping_line_x_position (float): X coordinate of the intersection point

    Returns:
        Dictionary with before and after indices, that references the points
        in the original passed list
    """
    # pylint: disable=too-many-branches
    surrounding_points_indices = {"before": 0, "after": len(x_list) - 1}
    if isinstance(x_list, np.ndarray):
        x_list = x_list.tolist()
    if not x_list:
        surrounding_points_indices["before"] = -1
        surrounding_points_indices["after"] = -1
    # Line in front of complete X range
    elif clipping_line_x_position < x_list[surrounding_points_indices["before"]]:
        surrounding_points_indices["before"] = -1
        surrounding_points_indices["after"] = 0
    # Line after complete X range
    elif clipping_line_x_position > x_list[surrounding_points_indices["after"]]:
        surrounding_points_indices["before"] = len(x_list) - 1
        surrounding_points_indices["after"] = -1
    # Line in X Range
    else:
        while (
            surrounding_points_indices["before"]
            <= surrounding_points_indices["after"]
        ):
            midpoint = (
                surrounding_points_indices["before"]
                + surrounding_points_indices["after"]
            ) // 2
            # Are points surrounding the line already?
            if not x_list:
                break
            elif len(x_list) == 1:
                if x_list[0] == clipping_line_x_position:
                    surrounding_points_indices["after"] = 0
                    surrounding_points_indices["before"] = 0
                break
            elif (
                len(x_list) > 1
                and x_list[surrounding_points_indices["before"]]
                <= clipping_line_x_position
                <= x_list[surrounding_points_indices["before"] + 1]
            ):
                if x_list[midpoint] == clipping_line_x_position:
                    surrounding_points_indices["after"] = midpoint
                    surrounding_points_indices["before"] = midpoint
                elif (
                    x_list[surrounding_points_indices["before"]]
                    == clipping_line_x_position
                ):
                    surrounding_points_indices[
                        "after"
                    ] = surrounding_points_indices["before"]
                elif (
                    x_list[surrounding_points_indices["before"] + 1]
                    == clipping_line_x_position
                ):
                    surrounding_points_indices["before"] = (
                        surrounding_points_indices["before"] + 1
                    )
                    surrounding_points_indices[
                        "after"
                    ] = surrounding_points_indices["before"]
                else:
                    surrounding_points_indices["after"] = (
                        surrounding_points_indices["before"] + 1
                    )
                break
            else:
                if clipping_line_x_position < x_list[midpoint]:
                    surrounding_points_indices["after"] = midpoint
                elif clipping_line_x_position > x_list[midpoint]:
                    surrounding_points_indices["before"] = midpoint
                else:
                    # Line position exactly on a point
                    surrounding_points_indices["after"] = midpoint
                    surrounding_points_indices["before"] = midpoint
                    break
    return surrounding_points_indices
