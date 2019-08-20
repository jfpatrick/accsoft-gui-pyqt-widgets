"""Datastructures

Objects to wrap multiple values belonging together to avoid the ambiguity
in typing and values of dictionaries.
"""

from typing import List, Union
from collections import namedtuple

import numpy as np
import pyqtgraph
from qtpy.QtCore import QObject


class CurveData(QObject):
    """Simple List of x and y points representing a curve."""

    def __init__(self, x_values: Union[list, np.ndarray], y_values: Union[list, np.ndarray], parent: QObject = None):
        """Create new Curve with x and y values

        Args:
            x_values: x values of points in curve
            y_values: y values of points in curve
        """
        super().__init__(parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(y_values, list):
            y_values = np.array(y_values)
        self.x_values: np.ndarray = x_values
        self.y_values: np.ndarray = y_values

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        try:
            return (
                np.allclose(self.x_values, other.x_values)
                and np.allclose(self.y_values, other.y_values)
            )
        except ValueError:
            return False


class CurveDataWithTime(CurveData):
    """Object representing a simple curve with x and y values as well as an
    additional list of timestamps in case the x position is not equal to the
    timestamp. This happens f.e. in case of the Sliding Pointer Plot
    """

    def __init__(self, timestamps: Union[List, np.ndarray], **kwargs):
        """Create new Curve with timestamps

        Args:
            timestamps: timestamps of the points creating the curve
            **kwargs: arguments passed to CurveData
        """
        super().__init__(**kwargs)
        if isinstance(timestamps, list):
            timestamps = np.array(timestamps)
        self.timestamps: np.ndarray = timestamps

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        try:
            return(
                np.allclose(self.timestamps, other.timestamps)
                and np.allclose(self.x_values, other.x_values)
                and np.allclose(self.y_values, other.y_values)
            )
        except ValueError:
            return False


class PointData(QObject):
    """Simple 2D point with x and y value"""

    def __init__(self, x_value: float = np.nan, y_value: float = np.nan, parent: QObject = None):
        """Create a new point

        Args:
            x_value (float): x value of the point
            y_value (float): y value of the point
        """
        super().__init__(parent)
        self.x_value: float = x_value
        self.y_value: float = y_value

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.x_value == other.x_value
            and self.y_value == other.y_value
        )

    def contains_nan(self):
        """Check if one of the values representing the point is nan."""
        return np.isnan(self.x_value) or np.isnan(self.y_value)


class BarData(QObject):
    """Simple Bar from an BarGraph"""

    def __init__(self, x_value: float = np.nan, y_value: float = np.nan, height: float = np.nan, parent: QObject = None):
        """Create a new point

        Args:
            x_value (float): x value of the bar
            y_value (float): y value of the bar
            height (float): height of the bar
        """
        super().__init__(parent)
        self.x_value: float = x_value
        self.y_value: float = y_value
        self.height: float = height

    def __eq__(self, other):
        return (
            self.__class__ != other.__class__
            and self.x_value != other.x_value
            and self.y_value != other.y_value
            and self.height != other.height
        )

    def contains_nan(self):
        """Check if one of the values representing the point is nan."""
        return np.isnan(self.x_value) or np.isnan(self.y_value) or np.isnan(self.height)


class BarCollectionData(QObject):
    """Simple Bar from an BarGraph"""

    def __init__(self, x_values: np.ndarray, y_values: np.ndarray, heights: np.ndarray, parent: QObject = None):
        """Create a new point

        Args:
            x_values (np.ndarray): x values of the bars
            y_values (np.ndarray): y values of the bars
            heights (np.ndarray): heights of the bars
        """
        super().__init__(parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(y_values, list):
            y_values = np.array(y_values)
        if isinstance(heights, list):
            heights = np.array(heights)
        self.x_values: np.ndarray = x_values
        self.y_values: np.ndarray = y_values
        self.heights: np.ndarray = heights

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        try:
            return (
               np.allclose(self.x_values, other.x_values)
               and np.allclose(self.y_values, other.y_values)
               and np.array_equal(self.heights, other.heights)
            )
        except ValueError:
            return False


class InjectionBarData(QObject):
    """Simple collection of bars for a bargraph"""

    def __init__(
        self,
        x_value: float = np.nan,
        y_value: float = np.nan,
        height: float = np.nan,
        width: float = np.nan,
        top: float = np.nan,
        bottom: float = np.nan,
        label: str = "",
        parent: QObject = None,
    ):
        """Create a new injectionbar object"""
        super().__init__(parent)
        self.x_value: float = x_value
        self.y_value: float = y_value
        self.height: float = height
        self.width: float = width
        self.top: float = top if not np.isnan(top) else (y_value + height)
        self.bottom: float = bottom if not np.isnan(bottom) else y_value
        self.label: str = label

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.x_value == other.x_value
            and self.y_value == other.y_value
            and self.height == other.height
            and self.label == other.label
            and self.bottom == other.bottom
            and self.top == other.top
            and self.width == other.width
        )

    def contains_nan(self):
        """Check if one of the values representing the point is nan."""
        return np.isnan(self.x_value) or np.isnan(self.y_value) or np.isnan(self.height)


class InjectionBarCollectionData(QObject):
    """Simple collection of injectionbars for a injectionbargraph"""

    def __init__(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray,
        heights: np.ndarray,
        widths: np.ndarray,
        tops: np.ndarray,
        bottoms: np.ndarray,
        labels: np.ndarray,
        parent: QObject = None,
    ):
        """Create a new collection of injectionbar object"""
        super().__init__(parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(y_values, list):
            y_values = np.array(y_values)
        if isinstance(heights, list):
            heights = np.array(heights)
        if isinstance(widths, list):
            widths = np.array(widths)
        if isinstance(tops, list):
            tops = np.array(tops)
        if isinstance(bottoms, list):
            bottoms = np.array(bottoms)
        if isinstance(labels, list):
            labels = np.array(labels)
        self.x_values: np.ndarray = x_values
        self.y_values: np.ndarray = y_values
        self.heights: np.ndarray = heights
        self.widths: np.ndarray = widths
        self.tops: np.ndarray = tops
        self.bottoms: np.ndarray = bottoms
        self.labels: np.ndarray = labels

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        try:
            return (
                np.allclose(self.x_values, other.x_values)
                and np.allclose(self.y_values, other.y_values)
                and np.allclose(self.heights, other.heights)
                and np.allclose(self.widths, other.widths)
                and np.allclose(self.tops, other.tops)
                and np.allclose(self.bottoms, other.bottoms)
                and np.array_equal(self.labels, other.labels)
            )
        except ValueError:
            return False


class TimestampMarkerData(QObject):
    """Simple Bar from an BarGraph"""

    def __init__(self, x_value: float = np.nan, color: str = "", label: str = "", parent: QObject = None):
        """Create a new injectionbar datastructure"""
        super().__init__(parent)
        self.x_value: float = x_value
        self.color: str = color
        self.label: str = label

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.x_value == other.x_value
            and self.label == other.label
            and self.color == other.color
        )

    def contains_nan(self):
        """Check if one of the values representing the point is nan."""
        return np.isnan(self.x_value)


class TimestampMarkerCollectionData(QObject):
    """Simple collection of infinite lines"""

    def __init__(self, x_values: np.ndarray, colors: np.ndarray, labels: np.ndarray, parent: QObject = None):
        """Create a new collection of infinite lines"""
        super().__init__(parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(colors, list):
            colors = np.array(colors)
        if isinstance(labels, list):
            labels = np.array(labels)
        self.x_values: np.ndarray = x_values
        self.colors: np.ndarray = colors
        self.labels: np.ndarray = labels

    def __eq__(self, other):
        if self._class__ != other.__class__:
            return False
        try:
            return (
                np.allclose(self.x_values, other.x_values)
                and np.allclose(self.colors, other.colors)
                and np.allclose(self.labels, other.labels)
            )
        except ValueError:
            return False


class CurveDecorators:
    """Collection of decorators of a single curve."""

    def __init__(
        self,
        vertical_line: pyqtgraph.InfiniteLine = None,
        horizontal_line: pyqtgraph.InfiniteLine = None,
        point: pyqtgraph.PlotDataItem = None,
    ):
        """Create a new CurveDecorators object

        Args:
            vertical_line (pyqtgraph.InfiniteLine): vertical line
            horizontal_line (pyqtgraph.InfiniteLine): horizontal line
            point (pyqtgraph.PlotDataItem): point
        """
        self.vertical_line: pyqtgraph.InfiniteLine = vertical_line
        self.horizontal_line: pyqtgraph.InfiniteLine = horizontal_line
        self.point: pyqtgraph.PlotDataItem = point

    def get_all_decorators_as_list(self):
        """Return all decorators in a list"""
        result = []
        if self.vertical_line:
            result.append(self.vertical_line)
        if self.horizontal_line:
            result.append(self.horizontal_line)
        if self.point:
            result.append(self.point)
        return result


# Collection for a sliding pointer curves
SlidingPointerCurveData = namedtuple("SlidingPointerCurveData", "old_curve new_curve")
