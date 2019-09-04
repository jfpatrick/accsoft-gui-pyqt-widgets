"""Module for cycles of different live data plots"""

import numpy as np
import abc


class PlottingCycle(metaclass=abc.ABCMeta):
    """
    Base class for different plotting cycles
    """

    def __init__(self, x_range_offset: float = np.nan, start: float = 0.0, size: float = 10.0):
        self.start = start if not np.isnan(start) else 0.0
        self.size = size
        self.end = self.start + self.size
        self._x_range_offset = x_range_offset if not np.isnan(x_range_offset) else 0
        self._first_cycle_update: bool = True
        self.number = 0.0

    @abc.abstractmethod
    def update_cycle(self, timestamp: float):
        """update the information holden by the cycle according to the passed timestamp"""
        pass


class ScrollingPlotCycle(PlottingCycle):

    """
    Wrapper for cycle related information in the sliding pointer
    curve and convenience functions for specific cycle related sizes
    """

    def update_cycle(self, timestamp: float):
        """Update cycle area with the given current time as timestamp"""
        self.start = timestamp - self.size + self._x_range_offset
        self.end = timestamp + self._x_range_offset


class SlidingPointerCycle(PlottingCycle):
    """
    Wrapper for cycle related information in the sliding pointer
    curve and convenience functions for specific cycle related sizes
    """

    def update_cycle(self, timestamp: float):
        """Update cycle area with the given current time as timestamp"""
        if self._first_cycle_update and self.start == 0.0:
            self._first_cycle_update = False
            self.start = self.get_current_time_line_x_pos(timestamp=timestamp)
            self.end = self.start + self.size * (self.number + 1)
        self.number = int(timestamp - self.start) // self.size

    def get_current_time_line_x_pos(self, timestamp) -> float:
        """Get the display position of the vertical line representing the
        current time
        """
        return timestamp - self.current_cycle_offset

    @property
    def current_cycle_start_timestamp(self) -> float:
        """Get first timestamp of the current cycle"""
        return self.start + self.number * self.size

    @property
    def previous_cycle_start_timestamp(self) -> float:
        """Get first timestamp of the previous cycle"""
        return self.start + (self.number - 1) * self.size

    @property
    def current_cycle_end_timestamp(self) -> float:
        """Get last timestamp of the current cycle"""
        return self.end + self.number * self.size

    @property
    def previous_cycle_end_timestamp(self) -> float:
        """Get last timestamp of the previous cycle"""
        return self.end + (self.number - 1) * self.size

    @property
    def current_cycle_offset(self) -> float:
        """Get first timestamp of the previous cycle"""
        return self.size * self.number

    @property
    def previous_cycle_offset(self) -> float:
        """Get the time difference between the last cycle start and the first
        timestamp in the first cycle
        """
        return self.size * (self.number - 1)
