"""
These data structures are used to transport values from the update sources
into the plot widgets avoiding ambiguity what is the type of displayed data item.
Data structures also validate that they are used for appropriate plot types.
"""

import warnings
import numpy as np
import pyqtgraph as pg
from abc import ABC, abstractmethod
from typing import List, Union, Any, Sequence, Dict
from copy import deepcopy
from ..util import deprecated_param_alias


class InvalidDataStructureWarning(Warning):
    """
    Data structure misuse warning. Data from inappropriate data structures
    cannot be rendered since there exists ambiguity or uncertainty of what the data represents.
    """
    pass


class InvalidValueWarning(Warning):
    """
    Unexpected value. This is a non-critical case (hence, not an exception), where certain values
    cannot be processed, e.g. color value cannot be applied by PyQtGraph because it cannot recognize it.
    """
    pass


class PlottingItemData(ABC):
    """
    Base class for the plotting item entry/entries, e.g. a point/points in a curve.

    Entries can be invalid, if missing values (gaps) cannot be replaced with a default value.
    """

    @abstractmethod
    def is_valid(self, warn: bool = False) -> Union[bool, np.ndarray]:
        """
        Check if the entry with the given values is valid and will be plotted.

        Args:
            warn: Should emit a warning, if associated data structure is invalid.

        Returns:
            :obj:`True` or array with :obj:`True`/:obj:`False` for entry or entries that are valid.
        """
        pass

    @property
    @abstractmethod
    def is_collection(self) -> bool:
        """
        Check if data structure is a collection, rather than a single value.

        This flag can be simply implemented as a class variable.

        Returns:
            :obj:`True` for data structures that represent a collection.
        """
        pass

    def __deepcopy__(self, memo: Dict):
        """Deep-copy data structure.

        Args:
            memo: Dictionary for correspondence between id's and objects
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result


DEFAULT_COLOR = "w"
"""
Default color for rendered items, when a color is not specified.
It is set as white, because PyQtGraph has a black background by default.
"""


class PointData(PlottingItemData):

    is_collection = False

    @deprecated_param_alias(x_value="x", y_value="y")
    def __init__(self,
                 x: float = np.nan,
                 y: float = np.nan,
                 check_validity: bool = True):
        """
        Container for a 2D point (x, y).

        Emitting an invalid point to a curve will result in the point **being
        dropped**. Point is considered invalid when its x-value is :obj:`~numpy.nan`,
        while its y-value is not :obj:`~numpy.nan`.

        Args:
            x: x-value of the point.
            y: y-value of the point.
            check_validity: Verify point on creation and issue a warning if it's invalid.
        """
        super().__init__()
        self.x: float = x if x is not None else np.nan
        self.y: float = y if y is not None else np.nan
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> bool:
        if np.isnan(self.x) and not np.isnan(self.y):
            if warn:
                msg = f"{self} is not valid and can't be drawn for the following " \
                      f"reasons: A point with NaN as the x value and a value " \
                      f"other than NaN as a y-value is not valid."
                warnings.warn(msg, InvalidDataStructureWarning)
            return False
        return True

    @property
    def is_nan(self) -> bool:
        """Either of point's values is :obj:`~numpy.nan`."""
        return np.isnan(self.x) or np.isnan(self.y)

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ == other.__class__
            and self.x == other.x
            and self.y == other.y
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, y={self.y})"


class CurveData(PlottingItemData):

    is_collection = True

    @deprecated_param_alias(x_values="x", y_values="y")
    def __init__(self,
                 x: Sequence[float],
                 y: Sequence[float],
                 check_validity: bool = True):
        """
        Collection of data points representing a curve.

        Emitting a sequence with invalid points to a curve will result in the invalid points **being
        dropped**. Point in a sequence is considered invalid when its x-value is either :obj:`None`
        or :obj:`~numpy.nan`, while its y-value is neither.

        Args:
            x: List of x-values for all points of the curve.
            y: List of y-values for all points of the curve.
            check_validity: Verify data on creation and issue a warning if it's invalid.
        """
        super().__init__()
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        if x.size != y.size:
            raise ValueError(f"The curve cannot be created with different count of x"
                             f" ({x.size}) and y values ({y.size}).")
        self.x: np.ndarray = x
        self.y: np.ndarray = y
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> np.ndarray:
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, y_data) in enumerate(zip(self.x, self.y)):
            if (x_data is None or np.isnan(x_data)) and (y_data is not None and not np.isnan(y_data)):
                if warn:
                    problems.append(f"Point {index}: (x={x_data}, y={y_data})")
                valid_indices[index] = False
        if problems and warn:
            msg = f"{self} is not valid and can't be drawn for the following " \
                  f"reasons: A point with NaN as the x value and a value " \
                  f"other than NaN as a y-value is not valid. This applies to " \
                  f"the following points: {', '.join(problems)}."
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices

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


class BarData(PlottingItemData):

    is_collection = False

    @deprecated_param_alias(x_value="x", y_value="y")
    def __init__(self,
                 height: float,
                 x: float = np.nan,
                 y: float = np.nan,
                 check_validity: bool = True):
        """
        Data representing a single bar in a bar graph.

        Emitting an invalid data to a bar graph will result in the entry **being
        dropped**. Bar is considered to be invalid when either its x-value or its height is :obj:`~numpy.nan`
        (:obj:`~numpy.nan` y-values are considered 0).

        Args:
            height: Height of the bar.
            x: x-position that represents the center of the bar.
            y: y-position that represents the center of the bar.
            check_validity: Verify data on creation and issue a warning if it's invalid.
        """
        super().__init__()
        self.height: float = height if height is not None else np.nan
        self.x: float = x if x is not None else np.nan
        # y -> nan has to be replaced with 0, otherwise bar won't be drawn
        self.y: float = y if y is not None and not np.isnan(y) else 0.0
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> bool:
        problems: List[str] = []
        if np.isnan(self.x):
            problems.append("NaN as the x value is not valid")
        if np.isnan(self.height):
            problems.append("NaN as the height is not valid")
        if problems:
            if warn:
                msg = f"{self} is not valid and can't be drawn for the following " \
                      f"reasons: {', '.join(problems)}"
                warnings.warn(msg, InvalidDataStructureWarning)
            return False
        return True

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ != other.__class__
            and self.x != other.x
            and self.y != other.y
            and self.height != other.height
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: (x={self.x}, y={self.y}, height={self.height})"


class BarCollectionData(PlottingItemData):

    is_collection = True

    @deprecated_param_alias(x_values="x", y_values="y")
    def __init__(self,
                 x: Sequence[float],
                 y: Sequence[float],
                 heights: Sequence[float],
                 check_validity: bool = True):
        """
        Collection of data items representing multiple bars.

        Emitting a sequence with invalid items to a bar graph will result in the invalid items **being
        dropped**. Bar is considered to be invalid when either its x-value or its height is :obj:`~numpy.nan`
        (:obj:`~numpy.nan` y-values are considered 0).

        Args:
            x: List of x-positions that represent the centers of the bars.
            y: List of y-positions that represent the centers of the bars.
            check_validity: Verify data on creation and issue a warning if it's invalid.
        """
        super().__init__()
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
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> bool:
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, y_data, height) in enumerate(zip(self.x, self.y, self.heights)):
            if (x_data is None or np.isnan(x_data)) or (height is None or np.isnan(height)):
                if warn:
                    problems.append(f"Bar {index}: (x={x_data}, y={y_data}, height={height})")
                valid_indices[index] = False
        if problems and warn:
            msg = f"{self} is not valid and can't be drawn for the following " \
                  f"reasons: Bars with NaN as x value or height are invalid. " \
                  f"This applies to {', '.join(problems)}"
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices

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


class InjectionBarData(PlottingItemData):

    is_collection = False

    @deprecated_param_alias(x_value="x", y_value="y")
    def __init__(self,
                 x: float,
                 y: float,
                 height: float = np.nan,
                 width: float = np.nan,
                 label: str = "",
                 check_validity: bool = True):
        """
        Data representing a single bar in an injection bar graph. Injection bars are special symbols
        that represent beam injection events in a time-series of accelerator complex.

        Emitting an invalid data to an injection bar graph will result in the entry **being
        dropped**. Injection bar is considered to be invalid when either its x-value or its y-value
        is :obj:`~numpy.nan`.

        Args:
            x: x-position of the center of the bar.
            y: y-position of the center of the bar.
            height: Length of the vertical line of the bar.
            width: Length of the horizontal line of the bar.
            label: Text displayed at the top of the bar.
            check_validity: Verify data on creation and issue a warning if it's invalid.
        """
        super().__init__()
        self.x: float = x if x is not None else np.nan
        self.y: float = y if y is not None else np.nan
        self.height: float = height if height is not None else np.nan
        self.width: float = width if width is not None else np.nan
        self.label: str = label if label is not None else ""
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> bool:
        problems: List[str] = []
        if np.isnan(self.x):
            problems.append("NaN as the x value is not valid")
        if np.isnan(self.y):
            problems.append("NaN as the y value is not valid")
        if problems:
            if warn:
                msg = f"{self} is not valid and can't be drawn for the following " \
                      f"reasons: {', '.join(problems)}"
                warnings.warn(msg, InvalidDataStructureWarning)
            return False
        return True

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


class InjectionBarCollectionData(PlottingItemData):

    is_collection = True

    @deprecated_param_alias(x_values="x", y_values="y")
    def __init__(self,
                 x: Sequence[float],
                 y: Sequence[float],
                 heights: Sequence[float],
                 widths: Sequence[float],
                 labels: Sequence[str],
                 check_validity: bool = True):
        """
        Collection of data items representing multiple injection bars.

        Emitting a sequence with invalid items to an injection bar graph will result in the invalid items **being
        dropped**. Injection bar is considered to be invalid when either its x-value or its y-value is
        :obj:`~numpy.nan`.

        Args:
            x: List of x-positions that represent the centers of the bars.
            y: List of y-positions that represent the centers of the bars.
            heights: List of lengths of the vertical lines of the bars.
            widths: List of lengths of the horizontal lines of the bars.
            labels: List of texts displayed at the top of each bar.
            check_validity: Verify data on creation and issue a warning if it's invalid.
        """
        super().__init__()
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
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> bool:
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, y_data, height, width, label) in enumerate(zip(self.x, self.y, self.heights, self.widths, self.labels)):
            if x_data is None or np.isnan(x_data) or y_data is None or np.isnan(y_data):
                if warn:
                    problems.append(f"InjectionBarData {index}: (x={x_data}, y={y_data}, height={height}, width={width}, labels={label})")
                valid_indices[index] = False
        if problems and warn:
            msg = f"{self} is not valid and can't be drawn for the following " \
                  f"reasons: InjectionBarData with NaN as x or y value are " \
                  f"invalid. This applies to {', '.join(problems)}"
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices

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


class TimestampMarkerData(PlottingItemData):

    is_collection = False

    @deprecated_param_alias(x_value="x")
    def __init__(self,
                 x: float,
                 color: str = DEFAULT_COLOR,
                 label: str = "",
                 check_validity: bool = True):
        """
        Data representing a timestamp in the time series (infinite vertical colored line).

        Emitting an invalid timestamp marker data to a graph will result in the entry **being
        dropped**. Timestamp marker is considered to be invalid when its x-value is :obj:`~numpy.nan`.

        Args:
            x: x-position of the timestamp marker's vertical line.
            color: Color of the vertical line in a similar format as :func:`pyqtgraph.mkColor`. Unsupported colors
                   will be automatically replaced with :obj:`DEFAULT_COLOR`.
            label: Text that is shown on the top of the line.
            check_validity: Verify data on creation and issue a warning if it's invalid.
        """
        super().__init__()
        self.x: float = x if x is not None else np.nan
        # Catch invalid colors and replace with the default color to prevent exceptions
        try:
            pg.mkColor(color)
        except Exception:
            # mkColor() raises Exception every time it can not interpret the passed color
            # In these cases we want to fall back to our default color
            warnings.warn(f"Timestamp Marker color '{color}' is replaced with {DEFAULT_COLOR} "
                          f"since '{color}' can not be used as a color.", InvalidValueWarning)
            color = DEFAULT_COLOR
        self.color: str = color if color is not None else DEFAULT_COLOR
        self.label: str = label if label is not None else ""
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> bool:
        if np.isnan(self.x):
            if warn:
                msg = f"{self} is not valid and can't be drawn for the following " \
                      f"reasons: NaN is not a valid x value for the timestamp " \
                      f"marker."
                warnings.warn(msg, InvalidDataStructureWarning)
            return False
        return True

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


class TimestampMarkerCollectionData(PlottingItemData):

    is_collection = True

    @deprecated_param_alias(x_values="x")
    def __init__(self,
                 x: Sequence[float],
                 colors: Sequence[str],
                 labels: Sequence[str],
                 check_validity: bool = True):
        """
        Collection of data items representing a timestamp in the time series (infinite vertical colored lines).

        Emitting a sequence with invalid timestamp markers to a graph will result in the invalid items **being
        dropped**. Timestamp marker is considered to be invalid when its x-value is :obj:`~numpy.nan`.

        Args:
            x: List of x-positions of vertical lines acting as timestamp markers.
            colors: List of colors corresponding to timestamp marker lines.
            labels: List of labels displayed on top of each corresponding marker.
            check_validity: Verify data on creation and issue a warning if it's invalid.
        """
        super().__init__()
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
            except Exception:
                # mkColor() raises Exception every time it can not interpret the passed color
                # In these cases we want to fall back to our default color
                warnings.warn(f"Timestamp Marker color '{color}' is replaced with {DEFAULT_COLOR} "
                              f"since '{color}' can not be used as a color.", InvalidValueWarning)
                colors[index] = DEFAULT_COLOR
        if not x.size == colors.size == labels.size:
            raise ValueError(f"The timestamp marker collection cannot be created with different length "
                             f"parameters: ({x.size}, {colors.size}, {labels.size})")
        self.x: np.ndarray = x
        self.colors: np.ndarray = colors
        self.labels: np.ndarray = labels
        if check_validity:
            self.is_valid(warn=True)

    def is_valid(self, warn: bool = False) -> np.ndarray:
        problems: List[str] = []
        valid_indices = np.ones(self.x.size, dtype=bool)
        for index, (x_data, color, label) in enumerate(zip(self.x, self.colors, self.labels)):
            if x_data is None or np.isnan(x_data):
                if warn:
                    problems.append(f"TimestampMarker {index}: (x={x_data}, color={color}, labels={label})")
                valid_indices[index] = False
        if problems and warn:
            msg = f"{self} is not valid and can't be drawn for the following " \
                  f"reasons: Timestamp markers with NaN as x are invalid. " \
                  f"This applies to {', '.join(problems)}."
            warnings.warn(msg, InvalidDataStructureWarning)
        return valid_indices

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
