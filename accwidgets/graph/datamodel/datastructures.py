"""
Objects to wrap multiple values belonging together to avoid the ambiguity
in typing and values of dictionaries.
On creation data structures, that are used for emitting data to graphs, emit
warnings in case they are not valid (and can't be drawn in a fitting graph).
This decision is made with PyQtGraph in mind and which values it needs for
drawing. An ValueError is raised in case a critical mistake was made when
creating the new instance of the data structure for example by passing
different length arrays into an .
"""

import warnings
import abc
from typing import List, Union, Optional, Any, NamedTuple, Sequence

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import QObject

from ..util import deprecated_param_alias
from accwidgets.common import AbstractQObjectMeta


class InvalidDataStructureWarning(Warning):
    """
    Warning for an invalid Data Structure. PlottingItemData should emit
    this if they are invalid, which means that they can not be drawn
    in their fitting graph-type.
    """
    pass


class WrongValueWarning(Warning):
    """
    Warning that a value is not as expected.
    """
    pass


class PlottingItemData(QObject, metaclass=AbstractQObjectMeta):

    """Base class for the plotting item entry/entries, f.e. a point/points in a curve

    Entries can be invalid, if missing values can not be replaced with a default value
    that does make sense and is not misleading.
    PlottingItemEntries are based on QObject so they can be used as types in signals.
    Without this, defining signals with them will lead to problems.
    """

    @abc.abstractmethod
    def is_valid(self, warn: bool = False) -> Union[bool, np.ndarray]:
        """Check if the entry with the given values is valid and will be plotted

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            True / Array true at the position, where the entry / entries is valid
        """
        pass


# use this instead of defining default colors by hand
DEFAULT_COLOR = "w"


class PointData(PlottingItemData):

    @deprecated_param_alias(x_value="x", y_value="y")
    def __init__(self, x: float = np.nan, y: float = np.nan, parent=None):
        """
        Data for a 2D point with x and y value

        Emitting and invalid point to a curve will result in the point **being
        dropped.** See :func:`PointData.is_valid` to see in which cases a PointData
        can be invalid.

        Args:
            x: x-value of the point.
            y: y-value of the point.
            parent: Parent object for the base class
        """
        super().__init__(parent=parent)
        self.x: float = x if x is not None else np.nan
        self.y: float = y if y is not None else np.nan
        # Check validity on creation to warn user in case the point is invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ == other.__class__
            and self.x == other.x
            and self.y == other.y
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, y={self.y})"

    def is_valid(self, warn: bool = False) -> bool:
        """Check if the PointData is valid

        A point is invalid, if:
            - x value is NaN and y value is not NaN

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            True if the point is valid
        """
        if np.isnan(self.x) and not np.isnan(self.y):
            if warn:
                msg = "A point with NaN as the x value and a value other than NaN as a y-value " \
                      f"is not valid. If you emit {self} to an curve, " \
                      f"it won't be represented as a point in the curve."
                warnings.warn(msg, InvalidDataStructureWarning)
            return False
        return True

    @property
    def is_nan(self) -> bool:
        """Either the x value or the y value is nan."""
        return np.isnan(self.x) or np.isnan(self.y)


class CurveData(PlottingItemData):

    @deprecated_param_alias(x_values="x", y_values="y")
    def __init__(
            self,
            x: Sequence[float],
            y: Sequence[float],
            parent=None,
    ):
        """Collection of data for points representing a curve.

        Emitting invalid points to a curve will result in the invalid points **being
        dropped.** See :func:`CurveData.is_valid` to see in which cases a point
        can be invalid.

        Args:
            x: list of x values of the points
            y: list of y values of the points
            parent: Parent object for the base class
        """
        super().__init__(parent)
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        if x.size != y.size:
            raise ValueError(f"The curve cannot be created with different count of x"
                             f" ({x.size}) and y values ({y.size}).")
        self.x: np.ndarray = x
        self.y: np.ndarray = y
        # Check validity on creation to warn user in case some points are invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        try:
            return (
                np.allclose(self.x, other.x)
                and np.allclose(self.y, other.y)
            )
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, y={self.y})"

    def is_valid(self, warn: bool = False) -> np.ndarray:
        """Check if all points in the collection are valid

        A point is invalid, if:
            - x value is NaN and y value is not NaN

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            Bool array which contains True, if the point at that index is valid
        """
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, y_data) in enumerate(zip(self.x, self.y)):
            if (x_data is None or np.isnan(x_data)) and (y_data is not None and not np.isnan(y_data)):
                problems.append(f"Point {index}: (x={x_data}, y={y_data})")
                valid_indices[index] = False
        if problems and warn:
            msg = "Points in CurveData with NaN as the x value and a value other than NaN " \
                  "as a y-value is not valid. This applies to the following points: " \
                  "(" + ", ".join(problems) + ") " + \
                  "If you emit these invalid points to a curve, they won't be drawn."
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices


class BarData(PlottingItemData):

    @deprecated_param_alias(x_value="x", y_value="y")
    def __init__(
            self,
            height: float,
            x: float = np.nan,
            y: float = np.nan,
            parent=None,
    ):
        """Data of a bar for a bar graph

        Emitting and invalid bar to a bar graph will result in the bar **being
        dropped.** See :func:`BarData.is_valid` to see in which cases a BarData
        can be invalid.

        Args:
            height: height of the bar
            x: x position that represents the center of the bar
            y: y position that represents the center of the bar
            parent: Parent object for the base class
        """
        super().__init__(parent)
        self.height: float = height if height is not None else np.nan
        self.x: float = x if x is not None else np.nan
        # y -> nan has to be replaced with 0, otherwise bar won't be drawn
        self.y: float = y if y is not None and not np.isnan(y) else 0.0
        # Check validity on creation to warn user in case the bar is invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ != other.__class__
            and self.x != other.x
            and self.y != other.y
            and self.height != other.height
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, y={self.y}, height={self.height})"

    def is_valid(self, warn: bool = False) -> bool:
        """Check if the BarData is valid

        A bar is invalid, if missing values can not be replaced with a
        default value that does make sense and is not misleading

        Cases in which a BarData is invalid:
            - x value is NaN
            - height is NaN

        If the y value is NaN, it can be replaced by 0

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            True if the bar is valid
        """
        problems: List[str] = []
        if np.isnan(self.x):
            problems.append("NaN as the x value is not valid")
        if np.isnan(self.height):
            problems.append("NaN as the height is not valid")
        if problems:
            if warn:
                warning_message = f"{self} is invalid for the following reasons: " \
                                  "(" + ", ".join(problems) + ") " + \
                                  "If you emit this bar to bar-graph, it won't be drawn."
                warnings.warn(warning_message, InvalidDataStructureWarning)
            return False
        return True


class BarCollectionData(PlottingItemData):

    @deprecated_param_alias(x_values="x", y_values="y")
    def __init__(
            self,
            x: Sequence[float],
            y: Sequence[float],
            heights: Sequence[float],
            parent=None,
    ):
        """Collection of data for multiple bars

        Emitting invalid bars to a bar graph will result in the invalid bars **being
        dropped.** See :func:`BarCollectionData.is_valid` to see in which cases a point
        can be invalid.

        Args:
            x: list of x positions that represent the center of the bar
            y: list of y positions that represent the center of the bar
            heights: list of bar heights
            parent: Parent object for the base class
        """
        super().__init__(parent)
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        if not isinstance(heights, np.ndarray):
            heights = np.array(heights)
        if not x.size == y.size == heights.size:
            raise ValueError(f"The bar collection cannot be created with different length "
                             f"parameters: ({x.size}, {y.size}, {heights.size}).")
        self.x: np.ndarray = x
        self.y: np.ndarray = np.nan_to_num(y, copy=True)
        self.heights: np.ndarray = heights
        # Check validity on creation to warn user in case some bars are invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        try:
            return (np.allclose(self.x, other.x)
                    and np.allclose(self.y, other.y)
                    and np.array_equal(self.heights, other.heights))
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, " \
            f"y={self.y}, height={self.heights})"

    def is_valid(self, warn: bool = False) -> bool:
        """Check if all bars are valid

        A bar is invalid, if missing values can not be replaced with a
        default value that does make sense and is not misleading

        Cases in which a bar is invalid:
            - x value is NaN
            - height is NaN

        If the y value is NaN, it can be replaced by 0

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            Bool array which contains True, if the bar at that index is valid
        """
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, y_data, height) in enumerate(zip(self.x, self.y, self.heights)):
            if (x_data is None or np.isnan(x_data)) or (height is None or np.isnan(height)):
                problems.append(f"Bar {index}: (x={x_data}, y={y_data}, height={height})")
                valid_indices[index] = False
        if problems and warn:
            msg = "Bars with NaN as x value or height are invalid." \
                  "This applies to the following bars: " \
                  "(" + ", ".join(problems) + ") " + \
                  "If you emit these invalid bars to a bargraph, they won't be drawn."
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices


class InjectionBarData(PlottingItemData):

    @deprecated_param_alias(x_value="x", y_value="y")
    def __init__(
        self,
        x: float,
        y: float,
        height: float = np.nan,
        width: float = np.nan,
        label: str = "",
        parent: Optional[QObject] = None,
    ):
        """Data for an injection bar for a injection bar graph.

        Emitting invalid injection bars to a graph will result in the invalid bars **being
        dropped.** See :func:`InjectionBarData.is_valid` to see in which cases a bar
        can be invalid.

        Args:
            x: x position of the center of the bar
            y: y position of the center of the bar
            height: length of the vertical line of the bar
            width: length of the vertical line of the bar
            label: text displayed at the top of the bar
            parent: parent item of the base class
        """
        super().__init__(parent)
        self.x: float = x if x is not None else np.nan
        self.y: float = y if y is not None else np.nan
        self.height: float = height if height is not None else np.nan
        self.width: float = width if width is not None else np.nan
        self.label: str = label if label is not None else ""
        # Check validity on creation to warn user in case the injection bar is invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ == other.__class__
            and self.x == other.x
            and self.y == other.y
            and self.height == other.height
            and self.width == other.width
            and self.label == other.label
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, y={self.y}, " \
            f"height={self.height}, width={self.width}, label={self.label})"

    def is_valid(self, warn: bool = False) -> bool:
        """Check if the injection bar is valid

        A injection bar is invalid, if missing values can not be replaced with a default
        value that does make sense and is not misleading

        Cases in which a InjectionBarData is invalid:
            - x value is NaN
            - y value is NaN

        If the height or width are NaN, they can be replaced with 0.

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            True if the injection bar is valid
        """
        problems: List[str] = []
        if np.isnan(self.x):
            problems.append("NaN as the x value is not valid")
        if np.isnan(self.y):
            problems.append("NaN as the y value is not valid")
        if problems:
            if warn:
                warning_message = f"{self} is invalid for the following reasons: " \
                                  "(" + ", ".join(problems) + ") " + \
                                  "If you emit this injection bar to an graph, it won't be drawn."
                warnings.warn(warning_message, InvalidDataStructureWarning)
            return False
        return True


class InjectionBarCollectionData(PlottingItemData):

    @deprecated_param_alias(x_values="x", y_values="y")
    def __init__(
        self,
        x: Sequence[float],
        y: Sequence[float],
        heights: Sequence[float],
        widths: Sequence[float],
        labels: Sequence[str],
        parent: Optional[QObject] = None,
    ):
        """Collection of data for multiple injection bars.

        Emitting invalid injection bars to a graph will result in the invalid bars **being
        dropped.** See :func:`InjectionBarData.is_valid` to see in which cases a bar
        can be invalid.

        Args:
            x: list of x positions of the center of each bar
            y: list of y positions of the center of each bar
            heights: list of lengths of the vertical lines of a bar
            widths: list of lengths of the horizontal lines of a bar
            labels: list of texts displayed at the top of each bar
            parent: parent item of the base class
        """
        super().__init__(parent)
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        if not isinstance(heights, np.ndarray):
            heights = np.array(heights)
        if not isinstance(widths, np.ndarray):
            widths = np.array(widths)
        if not isinstance(labels, np.ndarray):
            labels = np.array(labels)
        if not x.size == y.size == heights.size == widths.size == labels.size:
            raise ValueError(f"The injection bar collection cannot be created with different length "
                             f"parameters: ({x.size}, {y.size}, {heights.size},"
                             f"{widths.size}, {labels.size}).")
        self.x: np.ndarray = x
        self.y: np.ndarray = y
        self.heights: np.ndarray = np.nan_to_num(heights)
        self.widths: np.ndarray = np.nan_to_num(widths)
        self.labels: np.ndarray = labels
        # Check validity on creation to warn user in case some injection bars are invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        try:
            return (
                np.allclose(self.x, other.x)
                and np.allclose(self.y, other.y)
                and np.allclose(self.heights, other.heights)
                and np.allclose(self.widths, other.widths)
                and np.array_equal(self.labels, other.labels)
            )
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, y={self.y}, " \
            f"heights={self.heights}, widths={self.widths}, labels={self.labels})"

    def is_valid(self, warn: bool = False) -> bool:
        """Check if the injection bars are valid

        An injection bar is invalid, if missing values can not be replaced with a default
        value that does make sense and is not misleading

        Cases in which a injection bar is invalid:
            - x value is NaN
            - y value is NaN

        If the height or width are NaN, they can be replaced with 0, the label with an empty string.

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            Bool array, with true if the injection bar at this index is valid
        """
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, y_data, height, width, label) in enumerate(zip(self.x, self.y, self.heights, self.widths, self.labels)):
            if x_data is None or np.isnan(x_data) or y_data is None or np.isnan(y_data):
                problems.append(f"InjectionBarData {index}: (x={x_data}, y={y_data}, height={height}, width={width}, labels={label})")
                valid_indices[index] = False
        if problems and warn:
            msg = "InjectionBars in InjectionBarData with NaN as x or y value are invalid." \
                  "This applies to the following bars: " \
                  "(" + ", ".join(problems) + ") " + \
                  "If you emit these invalid bars to a graph, they won't be drawn."
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices


class TimestampMarkerData(PlottingItemData):

    @deprecated_param_alias(x_value="x")
    def __init__(
            self,
            x: float,
            color: str = DEFAULT_COLOR,
            label: str = "",
            parent=None,
    ):
        """Data for a timestamp marker

        Emitting invalid timestamp markers to a graph will result in the invalid markers **being
        dropped.** See :func:`TimestampMarkerData.is_valid` to see in which cases a marker
        can be invalid.

        Args:
            x: x position of the timestamp marker's vertical line
            color: of the vertical line, accepts the same arguments as pyqtgraph's mkColor
            label: text that is shown on the top of the line
            parent: parent item for the base class
        """
        super().__init__(parent)
        self.x: float = x if x is not None else np.nan
        # Catch invalid colors and replace with the default color to prevent exceptions
        try:
            pg.mkColor(color)
        except Exception:  # pylint: disable=broad-except
            # mkColor() raises Exception every time it can not interpret the passed color
            # In these cases we want to fall back to our default color
            warnings.warn(f"Timestamp Marker color '{color}' is replaced with {DEFAULT_COLOR} "
                          f"since '{color}' can not be used as a color.", WrongValueWarning)
            color = DEFAULT_COLOR
        self.color: str = color if color is not None else DEFAULT_COLOR
        self.label: str = label if label is not None else ""
        # Check validity on creation to warn user in case the timestamp marker is invalid
        self.is_valid(warn=True)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.x == other.x
            and self.label == other.label
            and self.color == other.color
        )

    def __str__(self):
        return f"{type(self).__name__}: " \
            f"(x={self.x}, color={self.color}, label={self.label})"

    def is_valid(self, warn: bool = False) -> bool:
        """Check if the timestamp marker is valid

        A timestamp marker is invalid, if missing values can not be
        replaced with a default value that does make sense and is not
        misleading.

        Cases in which a marker is invalid:
            - x value is NaN

        Color and labels can be replaced with standard values

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            True if the timestamp marker is valid
        """
        if np.isnan(self.x):
            if warn:
                warning_message = "NaN is not a valid x value for the timestamp " \
                                  "marker. If you emit this timeline to an graph, " \
                                  "it won't be drawn."
                warnings.warn(warning_message, InvalidDataStructureWarning)
            return False
        return True


class TimestampMarkerCollectionData(PlottingItemData):

    @deprecated_param_alias(x_values="x")
    def __init__(
            self,
            x: Sequence[float],
            colors: Sequence[str],
            labels: Sequence[str],
            parent=None,
    ):
        """Collection of data for timestamp markers

        Emitting invalid timestamp markers to a graph will result in
        the invalid markers **being dropped.** See
        :func:`TimestampMarkerData.is_valid` to see in which cases a marker
        can be invalid.

        Args:
            x: list of x positions of multiple timestamp markers'
                      vertical lines
            colors: list of colors of multiple timestamp markers' vertical
                    lines
            labels: list of labels that are displayed on top of multiple
                    timestamp markers' vertical lines
            parent: parent item for the base class
        """
        super().__init__(parent=parent)
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(colors, np.ndarray):
            colors = np.array(colors)
        if not isinstance(labels, np.ndarray):
            labels = np.array(labels)
        # Catch invalid colors and replace with the default color to prevent exceptions
        for index, color in enumerate(colors):
            try:
                pg.mkColor(color)
            except Exception:  # pylint: disable=broad-except
                # mkColor() raises Exception every time it can not interpret the passed color
                # In these cases we want to fall back to our default color
                warnings.warn(f"Timestamp Marker color '{color}' is replaced with {DEFAULT_COLOR} "
                              f"since '{color}' can not be used as a color.", WrongValueWarning)
                colors[index] = DEFAULT_COLOR
        # Check length of passed sequences
        if not x.size == colors.size == labels.size:
            raise ValueError(f"The timestamp marker collection cannot be created with different length "
                             f"parameters: ({x.size}, {colors.size}, {labels.size})")
        self.x: np.ndarray = x
        self.colors: np.ndarray = colors
        self.labels: np.ndarray = labels
        # Check validity on creation to warn user in case some timestamp markers are invalid
        self.is_valid(warn=True)

    def __eq__(self, other):
        if self._class__ != other.__class__:
            return False
        try:
            return (
                np.allclose(self.x, other.x)
                and np.allclose(self.colors, other.colors)
                and np.allclose(self.labels, other.labels)
            )
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, colors={self.colors}, labels={self.labels})"

    def is_valid(self, warn: bool = False) -> np.ndarray:
        """Check if the timestamp markers are valid

        A marker is invalid, if missing values can not be replaced with a default
        value that does make sense and is not misleading

        Cases in which a timestamp marker is invalid:
            - x value is NaN

        If the color or label are missing, they can be replaced with a default value.

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            Bool Array with True, if the the marker at that position is valid
        """
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, color, label) in enumerate(zip(self.x, self.colors, self.labels)):
            if x_data is None or np.isnan(x_data):
                problems.append(f"TimestampMarker {index}: (x={x_data}, color={color}, labels={label})")
                valid_indices[index] = False
        if problems and warn:
            msg = "Timestamp markers with NaN as x are invalid." \
                  "This applies to the following markers: " \
                  "(" + ", ".join(problems) + ") " + \
                  "If you emit these invalid markers to a graph, they won't be drawn."
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices


# ~~~~~~~~~~~~~~~~~ Data Structures for testing purposes ~~~~~~~~~~~~~~~~~


class CyclicPlotCurveData(NamedTuple):
    """
    Collection of a cyclic curve's old and new curve as
    a named tuple. Mainly used for testing purposes.
    """

    old_curve: CurveData
    new_curve: CurveData


class CurveDataWithTime:

    @deprecated_param_alias(x_values="x", y_values="y")
    def __init__(
            self,
            x: Union[List, np.ndarray],
            y: Union[List, np.ndarray],
            timestamps: Union[List, np.ndarray],
    ):
        """Curve data with x values and timestamps

        Object representing a curve with x and y values as well as an
        additional list of timestamps in case the x position is not equal to the
        timestamp. This happens f.e. in case of the Cyclic Plot

        Args:
            x: x values of the points creating the curve
            y: y values of the points creating the curve
            timestamps: timestamps of the points creating the curve
        """
        if isinstance(x, list):
            x = np.array(x)
        if isinstance(y, list):
            y = np.array(y)
        if isinstance(timestamps, list):
            timestamps = np.array(timestamps)
        if timestamps.size != y.size:
            raise ValueError(f"The curve cannot be created with different count of y "
                             f"({y.size}) and timestamps ({timestamps.size}).")
        self.x: np.ndarray = x
        self.y: np.ndarray = y
        self.timestamps: np.ndarray = timestamps

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        try:
            return(
                np.allclose(self.timestamps, other.timestamps)
                and np.allclose(self.x, other.x)
                and np.allclose(self.y, other.y)
            )
        except ValueError:
            return False
