"""Module for time span of different live data plots"""

import abc
import numpy as np
from ..widgets.plotconfiguration import TimeSpan


class BasePlotTimeSpan(metaclass=abc.ABCMeta):

    def __init__(
            self,
            time_span: TimeSpan,
            start: float = 0.0,
    ):
        """
        Base class for different plotting time spans.

        Args:
            start: time span start
            time_span: Time Span object representing the lower (left)
                       and higher (right) relative time span
        """
        self._start: float = start
        self._end: float = start + time_span.size
        self._last_time_stamp: float = np.nan
        self.time_span: TimeSpan = time_span
        self._first_time_span_update: bool = True
        self._validate()

    @abc.abstractmethod
    def update(self, timestamp: float):
        """update the information holden by the time span according to the passed timestamp."""
        pass

    def x_pos(self, timestamp: float) -> float:
        """Get the x position of an timestamp. In most cases this will
        be the timestamp itself, but for some time span implementations
        this might not be the case."""
        return timestamp

    @property
    def last_timestamp(self) -> float:
        """The most recent time stamp known to the plot."""
        return self._last_time_stamp

    @property
    @abc.abstractmethod
    def start(self) -> float:
        pass

    @property
    @abc.abstractmethod
    def end(self) -> float:
        pass

    def _validate(self):
        """
        Can be overwritten in subclasses, to raise Errors if the passed data
        is not valid for the use case of the subclass.
        """
        pass


class ScrollingPlotTimeSpan(BasePlotTimeSpan):

    """
    Wrapper for time span related information in the scrolling plot
    and convenience functions for specific time span related sizes
    """

    def update(self, timestamp: float):
        self._last_time_stamp = timestamp
        # We will keep this for the
        self._start = self.start

    @property
    def start(self) -> float:
        """Right boundary for the time span."""
        if self.time_span.finite:
            return self._last_time_stamp - self.time_span.left_boundary_offset
        else:
            return np.NINF

    @property
    def end(self) -> float:
        """
        Left boundary for the time span or negative infinite (numpy.NINF),
        if no left boundary exists."""
        if self.time_span.finite:
            return self._last_time_stamp - self.time_span.right_boundary_offset
        else:
            return self._last_time_stamp


class CyclicPlotTimeSpan(BasePlotTimeSpan):
    """
    Wrapper for time span related information in the cyclic plot
    curve and convenience functions for specific time span related sizes.
    """

    def __init__(
            self,
            time_span: TimeSpan,
            start: float = 0.0,
    ):
        super().__init__(
            start=start,
            time_span=time_span,
        )
        self._cycle: float = 0.0

    def update(self, timestamp: float):
        """Update time span area with the given current time as timestamp"""
        if not np.isnan(timestamp) and not np.isinf(timestamp):
            if timestamp is not None and not np.isnan(timestamp):
                self._last_time_stamp = timestamp
                if self._first_time_span_update and self._start == 0.0:
                    self._start = timestamp
                    self._end = timestamp + self.time_span.size
                    self._first_time_span_update = False
                self._cycle = int(timestamp - self._start) // self.time_span.size

    def x_pos(self, timestamp: float) -> float:
        """The positioning of time spans is always in the same x range."""
        return timestamp - self.curr_offset

    @property
    def cycle(self) -> float:
        """Counter how often we have been completed the cycle"""
        return self._cycle

    @property
    def start(self) -> float:
        return self._start + self._cycle * self.time_span.size

    @property
    def end(self) -> float:
        return self.start + self.time_span.size

    @property
    def prev_start(self) -> float:
        """Earliest timestamp that is in the previous time span."""
        return self._start + (self._cycle - 1) * self.time_span.size

    @property
    def prev_end(self) -> float:
        """Latest timestamp that is in the previous time span"""
        return self._end + (self._cycle - 1) * self.time_span.size

    @property
    def curr_offset(self) -> float:
        """Earliest timestamp that is in the previous time span"""
        return self.time_span.size * self._cycle

    @property
    def prev_offset(self) -> float:
        """The time difference between the last time span start and the first
        timestamp in the first time span.
        """
        return self.time_span.size * (self._cycle - 1)

    def _validate(self):
        if not self.time_span.finite:
            raise ValueError(f"Infinite Time Spans {self.time_span} are not compatible with a Cyclic Plot.")
