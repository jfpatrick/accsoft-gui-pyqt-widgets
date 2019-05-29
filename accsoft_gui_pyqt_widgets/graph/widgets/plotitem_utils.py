""" Utilities for PlotItems """

from enum import Enum
from typing import List, Dict, NamedTuple
import logging

logging.basicConfig(level=logging.ERROR)
LOGGER = logging.getLogger(__name__)


class PlotWidgetStyle(Enum):
    """Enumeration for the different available styles for the widgets

    SCROLLING_PLOT: New data gets appended and old one clipped before a
    specific time point. This creates a scrolling movement of the graph in
    positive x direction

    SLIDING_POINTER: A moving line redraws periodically an non moving line
    graph. The old version gets overdrawn as soon as a new point exists that is
    plotted to the same position in x range
    """

    SCROLLING_PLOT = 1
    SLIDING_POINTER = 2


class ExtendedPlotWidgetConfig(NamedTuple):
    """ Configuration for the ExtendedPlotWidget and other classes

    NamedTuple for wrapping the configuration of the ExtendedPlotWidget All
    configuration options provide a default value and can be let empty.
    """

    cycle_size: float = 100.0
    plotting_style: PlotWidgetStyle = PlotWidgetStyle.SLIDING_POINTER
    time_progress_line: bool = True
    v_draw_line: bool = False
    h_draw_line: bool = False
    draw_point: bool = False


class PlotItemUtils:
    """Collection of static Utility Functions to decrease complexity in
    ExtendedPlotItem Classes
    """

    @staticmethod
    def intersect(graph_points: Dict[str, List[float]], vertical_line_x_position: float):
        """Intersect a plot line with a vertical line, for example a boundary
        defined by a x-value.

        Args:
            graph_points (Dict[str, List[float]]): x and y values as list
                packaged in a dictionary
            vertical_line_x_position (float): Line on which the intersection
                should be calculated on
        """
        result = {
            "last_before_index": -1,
            "first_after_index": -1,
            "intersection": {},
        }
        x_positions = graph_points["x"]
        y_positions = graph_points["y"]
        if len(x_positions) != len(y_positions):
            LOGGER.warning(
                f"Length:({len(x_positions)}, {len(y_positions)}), Passed Points: {graph_points}")
            raise ValueError("The count of X indices and Y values is not the same.")
        surrounding_points = PlotItemUtils.bin_search_surrounding_points(x_positions, vertical_line_x_position)
        result["last_before_index"] = surrounding_points["before"]
        result["first_after_index"] = surrounding_points["after"]
        # Line is actually in between two points -> Calculate intersection point
        if result["last_before_index"] != -1 and result["first_after_index"] != -1:
            last_before_obj = {
                "x": x_positions[
                    surrounding_points["before"]
                ],
                "y": y_positions[
                    surrounding_points["before"]
                ],
            }
            first_after_obj = {
                "x": x_positions[
                    surrounding_points["after"]
                ],
                "y": y_positions[
                    surrounding_points["after"]
                ],
            }
            # Intersection between Old Curve
            result["intersection"] = PlotItemUtils.calc_intersection(
                last_before_obj,
                first_after_obj,
                vertical_line_x_position
            )
        return result

    @staticmethod
    def calc_intersection(point_1: Dict[str, float], point_2: Dict[str, float], new_point_x_position: float) -> Dict[str, float]:
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
        keys_1 = point_1.keys()
        keys_2 = point_2.keys()
        # Handle Data in the wrong format
        if not("x" in keys_1 & keys_2 and "y" in keys_1 & keys_2):
            LOGGER.warning("Parameters are in wrong format. \n"
                           f"Point 1:     {point_1} \n"
                           f"Point 2:     {point_2} \n"
                           f"X Position:  {new_point_x_position}")
            raise TypeError("The passed points do not have the right form.")
        # Handle special cases of intersections
        if point_2["x"] < point_1["x"]:
            LOGGER.warning("Parameters are in wrong order. This might hint, that a bug appeared in the code before. \n"
                           f"Point 1:     {point_1} \n"
                           f"Point 2:     {point_2} \n"
                           f"X Position:  {new_point_x_position}")
            # Change order of points
            point_1, point_2 = point_2, point_1
        if new_point_x_position > point_2["x"] or new_point_x_position < point_1["x"]:
            LOGGER.warning("New position not between the passed points, listing their X positions: \n"
                           f"New= {new_point_x_position}, P1= {point_1['x']}, P2= {point_2['x']}")
            return {}
        if point_2["x"] == point_1["x"]:
            return {"x": point_1["x"], "y": point_1["y"]}
        # Calculate intersection with boundary
        delta_p1_p2_x = point_2["x"] - point_1["x"]
        delta_p1_p2_y = point_2["y"] - point_1["y"]
        delta_p1_line_x = new_point_x_position - point_1["x"]
        temp_x = point_1["x"] + delta_p1_p2_x * (delta_p1_line_x / delta_p1_p2_x)
        temp_y = point_1["y"] + delta_p1_p2_y * (delta_p1_line_x / delta_p1_p2_x)
        return {"x": temp_x, "y": temp_y}

    @staticmethod
    def bin_search_surrounding_points(x_list: List[float], clipping_line_x_position: float) -> Dict[str, int]:
        """Searches for the two points closest to the given position of the
        vertical line. Multiple cases can happen here:

        1: Line between two points -> return two points

        2: Line outside the point range -> return closest single point + (-1)
        on the one that does not exist

        3: Less then two points -> one point 0, no points -1 for both

        Args:
            x_list (List[float]): List of x coordinates
            clipping_line_x_position (float): X coordinate of the intersection point

        Returns:
            Dictionary with before and after indices, that references the points
            in the original passed list
        """
        # pylint: disable=too-many-branches
        surrounding_points = {
            "before": 0,
            "after": len(x_list) - 1,
        }
        if not x_list:
            surrounding_points["before"] = -1
            surrounding_points["after"] = -1
        # Line in front of complete X range
        elif clipping_line_x_position < x_list[surrounding_points["before"]]:
            surrounding_points["before"] = -1
            surrounding_points["after"] = 0
        # Line after complete X range
        elif clipping_line_x_position > x_list[surrounding_points["after"]]:
            surrounding_points["before"] = len(x_list) - 1
            surrounding_points["after"] = -1
        # Line in X Range
        else:
            while surrounding_points["before"] <= surrounding_points["after"]:
                midpoint = (surrounding_points["before"] + surrounding_points["after"]) // 2
                # Are points surrounding the line already?
                if not x_list:
                    break
                elif len(x_list) == 1:
                    if x_list[0] == clipping_line_x_position:
                        surrounding_points["after"] = 0
                        surrounding_points["before"] = 0
                    break
                elif len(x_list) > 1 and x_list[surrounding_points["before"]] <= clipping_line_x_position <= x_list[surrounding_points["before"] + 1]:
                    if x_list[midpoint] == clipping_line_x_position:
                        surrounding_points["after"] = midpoint
                        surrounding_points["before"] = midpoint
                    elif x_list[surrounding_points["before"]] == clipping_line_x_position:
                        surrounding_points["after"] = surrounding_points["before"]
                    elif x_list[surrounding_points["before"] + 1] == clipping_line_x_position:
                        surrounding_points["before"] = surrounding_points["before"] + 1
                        surrounding_points["after"] = surrounding_points["before"]
                    else:
                        surrounding_points["after"] = surrounding_points["before"] + 1
                    break
                else:
                    if clipping_line_x_position < x_list[midpoint]:
                        surrounding_points["after"] = midpoint
                    elif clipping_line_x_position > x_list[midpoint]:
                        surrounding_points["before"] = midpoint
                    else:
                        # Line position exactly on a point
                        surrounding_points["after"] = midpoint
                        surrounding_points["before"] = midpoint
                        break
        return surrounding_points
