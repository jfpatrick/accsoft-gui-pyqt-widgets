"""Time spans of different live data plots."""

import abc
import numpy as np
from accwidgets.graph import TimeSpan


class BasePlotTimeSpan(metaclass=abc.ABCMeta):

    def __init__(self, time_span: TimeSpan, start: float = 0.0):
        """
        Base class for different plotting time spans.

        Args:
            time_span: Time span object representing the lower (left) and higher (right) relative time span.
            start: Starting time.
        """
        self._start: float = start
        self._end: float = start + time_span.size
        self._last_time_stamp: float = np.nan
        self.time_span: TimeSpan = time_span
        self._first_time_span_update: bool = True
        self._validate()

    @abc.abstractmethod
    def update(self, timestamp: float):
        """
        Update the inner state based on the given ``timestamp``.

        Args:
            timestamp: Input timestamp.
        """
        pass

    def x_pos(self, timestamp: float) -> float:
        """
        Get the x-position of a timestamp. In most cases this will
        be the timestamp itself, but may differ for some implementations.

        Args:
            timestamp: Input timestamp to derive the x-position of.
        """
        return timestamp

    @property
    def last_timestamp(self) -> float:
        """The most recent timestamp known to the plot."""
        return self._last_time_stamp

    @property
    @abc.abstractmethod
    def start(self) -> float:
        """Right boundary of the time span."""
        pass

    @property
    @abc.abstractmethod
    def end(self) -> float:
        """
        Left boundary of the time span or negative infinite (:obj:`numpy.NINF`),
        if no left boundary exists.
        """
        pass

    def _validate(self):
        """
        Can be overwritten in subclasses, to raise Errors if the passed data
        is not valid for the use case of the subclass.
        """
        pass


class ScrollingPlotTimeSpan(BasePlotTimeSpan):
    """
    Wrapper for time-span-related information in the scrolling plot.
    """

    def update(self, timestamp: float):
        self._last_time_stamp = timestamp
        # We will keep this for the
        self._start = self.start

    @property
    def start(self) -> float:
        if self.time_span.finite:
            return self._last_time_stamp - self.time_span.left_boundary_offset
        else:
            return np.NINF

    @property
    def end(self) -> float:
        if self.time_span.finite:
            return self._last_time_stamp - self.time_span.right_boundary_offset
        else:
            return self._last_time_stamp


class CyclicPlotTimeSpan(BasePlotTimeSpan):

    def __init__(self, time_span: TimeSpan, start: float = 0.0):
        """
        Wrapper for time-span-related information in the cyclic plot.

        Args:
            time_span: Time span object representing the lower (left) and higher (right) relative time span.
            start: Starting time.
        """
        super().__init__(start=start, time_span=time_span)
        self._cycle: float = 0.0

    def update(self, timestamp: float):
        if not np.isnan(timestamp) and not np.isinf(timestamp):
            if timestamp is not None and not np.isnan(timestamp):
                self._last_time_stamp = timestamp
                if self._first_time_span_update and self._start == 0.0:
                    self._start = timestamp
                    self._end = timestamp + self.time_span.size
                    self._first_time_span_update = False
                self._cycle = int(timestamp - self._start) // self.time_span.size

    def x_pos(self, timestamp: float) -> float:
        """
        Get the x-position of a timestamp.

        The positioning of time spans is always in the same x-range.

        Args:
            timestamp: Input timestamp to derive the x-position of.
        """
        return timestamp - self.curr_offset

    @property
    def cycle(self) -> float:
        """Counter of completed cycles."""
        return self._cycle

    @property
    def start(self) -> float:
        return self._start + self._cycle * self.time_span.size

    @property
    def end(self) -> float:
        """Left boundary of the time span."""
        return self.start + self.time_span.size

    @property
    def prev_start(self) -> float:
        """The earliest timestamp that is in the previous time span."""
        return self._start + (self._cycle - 1) * self.time_span.size

    @property
    def prev_end(self) -> float:
        """The latest timestamp that is in the previous time span."""
        return self._end + (self._cycle - 1) * self.time_span.size

    @property
    def curr_offset(self) -> float:
        """The earliest timestamp that is in the current time span."""
        return self.time_span.size * self._cycle

    @property
    def prev_offset(self) -> float:
        """Time difference between the start of the last time span and the start of the first time span."""
        return self.time_span.size * (self._cycle - 1)

    def _validate(self):
        if not self.time_span.finite:
            raise ValueError(f"Infinite Time Spans {self.time_span} are not compatible with a Cyclic Plot.")
