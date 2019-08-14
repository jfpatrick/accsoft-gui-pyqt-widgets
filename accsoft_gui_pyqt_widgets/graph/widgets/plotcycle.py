"""Module for cycles of different live data plots"""

import numpy as np

from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
)


class ScrollingPlotCycle:

    """
    Wrapper for cycle related information in the sliding pointer
    curve and convenience functions for specific cycle related sizes
    """

    def __init__(
        self,
        plot_config: ExPlotWidgetConfig,
        start: float = 0.0,
        size: float = 10.0,
    ):
        self.start = start if not np.isnan(start) else 0.0
        self.size = size
        self._x_range_offset = (
            plot_config.x_range_offset
            if not np.isnan(plot_config.x_range_offset)
            else 0
        )
        self.end = self.start + self.size

    def update_cycle(self, timestamp: float):
        """Update cycle area with the given current time as timestamp"""
        self.start = timestamp - self.size + self._x_range_offset
        self.end = timestamp + self._x_range_offset


class SlidingPointerCycle:
    """
    Wrapper for cycle related information in the sliding pointer
    curve and convenience functions for specific cycle related sizes
    """

    def __init__(self, start: float = 0.0, size: float = 10.0):
        """Create a new cycle with a starting point and a size"""
        self.start = start if not np.isnan(start) else 0.0
        self.size = size
        self.end = self.start + self.size
        self.number = 0.0

    # TODO: Convert to properties
    def get_current_cycle_start_timestamp(self) -> float:
        """Get first timestamp of the current cycle"""
        return self.start + self.number * self.size

    def get_previous_cycle_start_timestamp(self) -> float:
        """Get first timestamp of the previous cycle"""
        return self.start + (self.number - 1) * self.size

    def get_current_cycle_end_timestamp(self) -> float:
        """Get last timestamp of the current cycle"""
        return self.end + self.number * self.size

    def get_previous_cycle_end_timestamp(self) -> float:
        """Get last timestamp of the previous cycle"""
        return self.end + (self.number - 1) * self.size

    def get_current_cycle_offset(self) -> float:
        """Get first timestamp of the previous cycle"""
        return self.size * self.number

    def get_previous_cycle_offset(self) -> float:
        """Get the time difference between the last cycle start and the first
        timestamp in the first cycle
        """
        return self.size * (self.number - 1)

    def get_current_time_line_x_pos(self, timestamp) -> float:
        """Get the display position of the vertical line representing the
        current time
        """
        return timestamp - self.get_current_cycle_offset()
