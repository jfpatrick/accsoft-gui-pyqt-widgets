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
import logging
import abc
from typing import List, Union, Optional, Any, NamedTuple

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import QObject

_LOGGER = logging.getLogger(__name__)


class InvalidDataStructureWarning(Warning):
    """
    Warning for an invalid Data Structure. PlottingItemDataStructure should emit
    this if they are invalid, which means that they can not be drawn
    in their fitting graph-type.
    """
    pass


class AbstractQObjectMeta(type(QObject), abc.ABCMeta):  # type: ignore

    """ Metaclass for abstract classes based on QObject

    A class inheriting from QObject with ABCMeta as metaclass will lead to
    an metaclass conflict:

    TypeError: metaclass conflict: the metaclass of a derived class must be
    a (non-strict) subclass of the meta-classes of all its bases
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

    def __init__(self, x_value: float = np.nan, y_value: float = np.nan, parent=None):
        """
        Data for a 2D point with x and y value

        Emitting and invalid point to a curve will result in the point **being
        dropped.** See :func:`PointData.is_valid` to see in which cases a PointData
        can be invalid.

        Args:
            x_value: x-value of the point.
            y_value: y-value of the point.
            parent: Parent object for the base class
        """
        super().__init__(parent=parent)
        self.x_value: float = x_value if x_value is not None else np.nan
        self.y_value: float = y_value if y_value is not None else np.nan
        # Check validity on creation to warn user in case the point is invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ == other.__class__
            and self.x_value == other.x_value
            and self.y_value == other.y_value
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x_value}, y={self.y_value})"

    def is_valid(self, warn: bool = False) -> bool:
        """Check if the PointData is valid

        A point is invalid, if:
            - x value is NaN and y value is not NaN

        Args:
            warn: Should a warning be emitted if the data structure is invalid

        Returns:
            True if the point is valid
        """
        if np.isnan(self.x_value) and not np.isnan(self.y_value):
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
        return np.isnan(self.x_value) or np.isnan(self.y_value)


class CurveData(PlottingItemData):

    def __init__(
            self,
            x_values: Union[List[float], np.ndarray],
            y_values: Union[List[float], np.ndarray],
            parent=None,
    ):
        """Collection of data for points representing a curve.

        Emitting invalid points to a curve will result in the invalid points **being
        dropped.** See :func:`CurveData.is_valid` to see in which cases a point
        can be invalid.

        Args:
            x_values: list of x values of the points
            y_values: list of y values of the points
            parent: Parent object for the base class
        """
        super().__init__(parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(y_values, list):
            y_values = np.array(y_values)
        if x_values.size != y_values.size:
            raise ValueError(f"The curve cannot be created with different count of x"
                             f" ({x_values.size}) and y values ({y_values.size}).")
        self.x_values: np.ndarray = x_values
        self.y_values: np.ndarray = y_values
        # Check validity on creation to warn user in case some points are invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        try:
            return (
                np.allclose(self.x_values, other.x_values)
                and np.allclose(self.y_values, other.y_values)
            )
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x_values}, y={self.y_values})"

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
        valid_indices = np.ones(self.x_values.size, dtype=bool)
        for index, (x_data, y_data) in enumerate(zip(self.x_values, self.y_values)):
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

    def __init__(
            self,
            height: float,
            x_value: float,
            y_value: float = np.nan,
            parent=None,
    ):
        """Data of a bar for a bar graph

        Emitting and invalid bar to a bar graph will result in the bar **being
        dropped.** See :func:`BarData.is_valid` to see in which cases a BarData
        can be invalid.

        Args:
            height: height of the bar
            x_value: x position that represents the center of the bar
            y_value: y position that represents the center of the bar
            parent: Parent object for the base class
        """
        super().__init__(parent)
        self.height: float = height if height is not None else np.nan
        self.x_value: float = x_value if x_value is not None else np.nan
        # y -> nan has to be replaced with 0, otherwise bar won't be drawn
        self.y_value: float = y_value if y_value is not None and not np.isnan(y_value) else 0.0
        # Check validity on creation to warn user in case the bar is invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ != other.__class__
            and self.x_value != other.x_value
            and self.y_value != other.y_value
            and self.height != other.height
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x_value}, y={self.y_value}, height={self.height})"

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
        if np.isnan(self.x_value):
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

    def __init__(
            self,
            x_values: Union[list, np.ndarray],
            y_values: Union[list, np.ndarray],
            heights: Union[list, np.ndarray],
            parent=None,
    ):
        """Collection of data for multiple bars

        Emitting invalid bars to a bar graph will result in the invalid bars **being
        dropped.** See :func:`BarCollectionData.is_valid` to see in which cases a point
        can be invalid.

        Args:
            x_values: list of x positions that represent the center of the bar
            y_values: list of y positions that represent the center of the bar
            heights: list of bar heights
            parent: Parent object for the base class
        """
        super().__init__(parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(y_values, list):
            y_values = np.array(y_values)
        if isinstance(heights, list):
            heights = np.array(heights)
        if not x_values.size == y_values.size == heights.size:
            raise ValueError(f"The bar collection cannot be created with different length "
                             f"parameters: ({x_values.size}, {y_values.size}, {heights.size}).")
        self.x_values: np.ndarray = x_values
        self.y_values: np.ndarray = np.nan_to_num(y_values, copy=True)
        self.heights: np.ndarray = heights
        # Check validity on creation to warn user in case some bars are invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        try:
            return (np.allclose(self.x_values, other.x_values)
                    and np.allclose(self.y_values, other.y_values)
                    and np.array_equal(self.heights, other.heights))
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x_values}, " \
            f"y={self.y_values}, height={self.heights})"

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
        valid_indices = np.ones(self.x_values.size, dtype=bool)
        for index, (x_data, y_data, height) in enumerate(zip(self.x_values, self.y_values, self.heights)):
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

    def __init__(
        self,
        x_value: float,
        y_value: float,
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
            x_value: x position of the center of the bar
            y_value: y position of the center of the bar
            height: length of the vertical line of the bar
            width: length of the vertical line of the bar
            label: text displayed at the top of the bar
            parent: parent item of the base class
        """
        super().__init__(parent)
        self.x_value: float = x_value if x_value is not None else np.nan
        self.y_value: float = y_value if y_value is not None else np.nan
        self.height: float = height if height is not None else np.nan
        self.width: float = width if width is not None else np.nan
        self.label: str = label if label is not None else ""
        # Check validity on creation to warn user in case the injection bar is invalid
        self.is_valid(warn=True)

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ == other.__class__
            and self.x_value == other.x_value
            and self.y_value == other.y_value
            and self.height == other.height
            and self.width == other.width
            and self.label == other.label
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x_value}, y={self.y_value}, " \
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
        if np.isnan(self.x_value):
            problems.append("NaN as the x value is not valid")
        if np.isnan(self.y_value):
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

    def __init__(
        self,
        x_values: Union[List, np.ndarray],
        y_values: Union[List, np.ndarray],
        heights: Union[List, np.ndarray],
        widths: Union[List, np.ndarray],
        labels: Union[List, np.ndarray],
        parent: Optional[QObject] = None,
    ):
        """Collection of data for multiple injection bars.

        Emitting invalid injection bars to a graph will result in the invalid bars **being
        dropped.** See :func:`InjectionBarData.is_valid` to see in which cases a bar
        can be invalid.

        Args:
            x_values: list of x positions of the center of each bar
            y_values: list of y positions of the center of each bar
            heights: list of lengths of the vertical lines of a bar
            widths: list of lengths of the horizontal lines of a bar
            labels: list of texts displayed at the top of each bar
            parent: parent item of the base class
        """
        super().__init__(parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(y_values, list):
            y_values = np.array(y_values)
        if isinstance(heights, list):
            heights = np.array(heights)
        if isinstance(widths, list):
            widths = np.array(widths)
        if isinstance(labels, list):
            labels = np.array(labels)
        if not x_values.size == y_values.size == heights.size == widths.size == labels.size:
            raise ValueError(f"The injection bar collection cannot be created with different length "
                             f"parameters: ({x_values.size}, {y_values.size}, {heights.size},"
                             f"{widths.size}, {labels.size}).")
        self.x_values: np.ndarray = x_values
        self.y_values: np.ndarray = y_values
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
                np.allclose(self.x_values, other.x_values)
                and np.allclose(self.y_values, other.y_values)
                and np.allclose(self.heights, other.heights)
                and np.allclose(self.widths, other.widths)
                and np.array_equal(self.labels, other.labels)
            )
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x_values}, y={self.y_values}, " \
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
        valid_indices = np.ones(self.x_values.size, dtype=bool)
        for index, (x_data, y_data, height, width, label) in enumerate(zip(self.x_values, self.y_values, self.heights, self.widths, self.labels)):
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

    def __init__(
            self,
            x_value: float,
            color: str = DEFAULT_COLOR,
            label: str = "",
            parent=None,
    ):
        """Data for a timestamp marker

        Emitting invalid timestamp markers to a graph will result in the invalid markers **being
        dropped.** See :func:`TimestampMarkerData.is_valid` to see in which cases a marker
        can be invalid.

        Args:
            x_value: x position of the timestamp marker's vertical line
            color: of the vertical line, accepts the same arguments as pyqtgraph's mkColor
            label: text that is shown on the top of the line
            parent: parent item for the base class
        """
        super().__init__(parent)
        self.x_value: float = x_value if x_value is not None else np.nan
        # Catch invalid colors and replace with the default color to prevent exceptions
        try:
            pg.mkColor(color)
        except Exception:  # pylint: disable=broad-except
            # mkColor() raises Exception every time it can not interpret the passed color
            # In these cases we want to fall back to our default color
            _LOGGER.warning(f"Timestamp Marker color '{color}' is replaced with {DEFAULT_COLOR} "
                            f"since '{color}' can not be used as a color.")
            color = DEFAULT_COLOR
        self.color: str = color if color is not None else DEFAULT_COLOR
        self.label: str = label if label is not None else ""
        # Check validity on creation to warn user in case the timestamp marker is invalid
        self.is_valid(warn=True)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.x_value == other.x_value
            and self.label == other.label
            and self.color == other.color
        )

    def __str__(self):
        return f"{type(self).__name__}: " \
            f"(x={self.x_value}, color={self.color}, label={self.label})"

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
        if np.isnan(self.x_value):
            if warn:
                warning_message = "NaN is not a valid x value for the timestamp " \
                                  "marker. If you emit this timeline to an graph, " \
                                  "it won't be drawn."
                warnings.warn(warning_message, InvalidDataStructureWarning)
            return False
        return True


class TimestampMarkerCollectionData(PlottingItemData):

    def __init__(
            self,
            x_values: Union[List, np.ndarray],
            colors: Union[List, np.ndarray],
            labels: Union[List, np.ndarray],
            parent=None,
    ):
        """Collection of data for timestamp markers

        Emitting invalid timestamp markers to a graph will result in
        the invalid markers **being dropped.** See
        :func:`TimestampMarkerData.is_valid` to see in which cases a marker
        can be invalid.

        Args:
            x_values: list of x positions of multiple timestamp markers'
                      vertical lines
            colors: list of colors of multiple timestamp markers' vertical
                    lines
            labels: list of labels that are displayed on top of multiple
                    timestamp markers' vertical lines
            parent: parent item for the base class
        """
        super().__init__(parent=parent)
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(colors, list):
            colors = np.array(colors)
            # Catch invalid colors and replace with the default color to prevent exceptions
            for index, color in enumerate(colors):
                try:
                    pg.mkColor(color)
                except Exception:  # pylint: disable=broad-except
                    # mkColor() raises Exception every time it can not interpret the passed color
                    # In these cases we want to fall back to our default color
                    _LOGGER.warning(f"Timestamp Marker color '{color}' is replaced with {DEFAULT_COLOR} "
                                    f"since '{color}' can not be used as a color.")
                    colors[index] = DEFAULT_COLOR
        if isinstance(labels, list):
            labels = np.array(labels)
        if not x_values.size == colors.size == labels.size:
            raise ValueError(f"The timestamp marker collection cannot be created with different length "
                             f"parameters: ({x_values.size}, {colors.size}, {labels.size})")
        self.x_values: np.ndarray = x_values
        self.colors: np.ndarray = colors
        self.labels: np.ndarray = labels
        # Check validity on creation to warn user in case some timestamp markers are invalid
        self.is_valid(warn=True)

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

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x_values}, colors={self.colors}, labels={self.labels})"

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
        valid_indices = np.ones(self.x_values.size, dtype=bool)
        for index, (x_data, color, label) in enumerate(zip(self.x_values, self.colors, self.labels)):
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

    def __init__(
            self,
            x_values: Union[List, np.ndarray],
            y_values: Union[List, np.ndarray],
            timestamps: Union[List, np.ndarray],
    ):
        """Curve data with x values and timestamps

        Object representing a curve with x and y values as well as an
        additional list of timestamps in case the x position is not equal to the
        timestamp. This happens f.e. in case of the Cyclic Plot

        Args:
            x_values: x values of the points creating the curve
            y_values: y values of the points creating the curve
            timestamps: timestamps of the points creating the curve
        """
        if isinstance(x_values, list):
            x_values = np.array(x_values)
        if isinstance(y_values, list):
            y_values = np.array(y_values)
        if isinstance(timestamps, list):
            timestamps = np.array(timestamps)
        if timestamps.size != y_values.size:
            raise ValueError(f"The curve cannot be created with different count of y "
                             f"({y_values.size}) and timestamps ({timestamps.size}).")
        self.x_values: np.ndarray = x_values
        self.y_values: np.ndarray = y_values
        self.timestamps: np.ndarray = timestamps

    def __eq__(self, other: Any) -> bool:
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


PlottingItemDataStructure = Union[
    PointData,
    CurveData,
    BarData,
    BarCollectionData,
    InjectionBarData,
    InjectionBarCollectionData,
    TimestampMarkerData,
    TimestampMarkerCollectionData,
]
"""Union with all data-structure classes from this module (useful for type hints in slots)"""
