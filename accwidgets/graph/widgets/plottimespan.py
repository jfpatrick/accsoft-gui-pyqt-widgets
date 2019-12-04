"""Module for time span of different live data plots"""

import abc
import numpy as np


class PlottingTimeSpan(metaclass=abc.ABCMeta):

    def __init__(
            self,
            xrange_offset: float = np.nan,
            start: float = 0.0,
            size: float = 10.0
    ):
        """
        Base class for different plotting time spans.

        Args:
            xrange_offset: Offset for the current time x position
            start: time span start
            size: what time span should be displayed in x direction
        """
        self.start = start if not np.isnan(start) else 0.0
        self.size = size
        self.end = self.start + self.size
        self._xrange_offset = xrange_offset if not np.isnan(xrange_offset) else 0
        self._first_time_span_update: bool = True
        self.number = 0.0

    @abc.abstractmethod
    def update(self, timestamp: float) -> None:
        """update the information holden by the time span according to the passed timestamp."""
        pass

    def x_pos(self, timestamp: float) -> float:
        """Get the x position of an timestamp. In most cases this will
        be the timestamp itself, but for some time span implementations
        this might not be the case."""
        return timestamp


class ScrollingPlotTimeSpan(PlottingTimeSpan):

    """
    Wrapper for time span related information in the sliding pointer
    curve and convenience functions for specific time span related sizes
    """

    def update(self, timestamp: float) -> None:
        """Update time span area with the given current time as timestamp"""
        self.start = timestamp - self.size + self._xrange_offset
        self.end = timestamp + self._xrange_offset


class SlidingPointerTimeSpan(PlottingTimeSpan):
    """
    Wrapper for time span related information in the sliding pointer
    curve and convenience functions for specific time span related sizes
    """

    def update(self, timestamp: float) -> None:
        """Update time span area with the given current time as timestamp"""
        if self._first_time_span_update and self.start == 0.0:
            self._first_time_span_update = False
            self.start = self.x_pos(timestamp=timestamp)
            self.end = self.start + self.size * (self.number + 1)
        self.number = int(timestamp - self.start) // self.size

    def x_pos(self, timestamp: float) -> float:
        """The positioning of time spans is always in the same x range."""
        return timestamp - self.curr_offset

    @property
    def curr_start(self) -> float:
        """Earliest timestamp that is in the current time span."""
        return self.start + self.number * self.size

    @property
    def prev_start(self) -> float:
        """Earliest timestamp that is in the previous time span."""
        return self.start + (self.number - 1) * self.size

    @property
    def curr_end(self) -> float:
        """Latest timestamp that is in the current time span"""
        return self.end + self.number * self.size

    @property
    def prev_end(self) -> float:
        """Latest timestamp that is in the previous time span"""
        return self.end + (self.number - 1) * self.size

    @property
    def curr_offset(self) -> float:
        """Earliest timestamp that is in the previous time span"""
        return self.size * self.number

    @property
    def prev_offset(self) -> float:
        """The time difference between the last time span start and the first
        timestamp in the first time span.
        """
        return self.size * (self.number - 1)
