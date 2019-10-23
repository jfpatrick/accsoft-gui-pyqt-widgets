"""
Different AxisItem implementations for Timestamp based plotting for better readability
"""

from datetime import datetime
from typing import List

from pyqtgraph import AxisItem
from qtpy.QtCore import Signal


class CustomAxisItem(AxisItem):

    """AxisItem with some required extra functions"""

    # Signal for informing later components that
    sig_vb_mouse_event_triggered_by_axis: Signal = Signal(bool)

    def mouseDragEvent(self, event):
        """Make the mouse drag event on the axis distinguishable from the ViewBox one"""
        self.sig_vb_mouse_event_triggered_by_axis.emit(True)
        super().mouseDragEvent(event)

    def wheelEvent(self, ev):
        """Make the mouse click event on the axis distinguishable from the ViewBox one"""
        self.sig_vb_mouse_event_triggered_by_axis.emit(True)
        super().wheelEvent(ev)


# pylint: disable=too-many-ancestors
class TimeAxisItem(AxisItem):
    """Axis Item that shows timestamps as strings in format HH:MM:SS"""

    def tickStrings(
        self, values: List[float], scale: float, spacing: float
    ) -> List[str]:
        """Translate timestamps to human readable times formatted HH:MM:SS

        Args:
            values: Positions from the axis that are supposed to be labeled
            scale: See AxisItem Documentation
            spacing: See AxisItem Documentation

        Returns:
            A list of human readable times
        """
        try:
            return [
                datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values
            ]
        except (ValueError, OSError, OverflowError):
            # Errors appear in datatime.fromtimestamp()
            # ValueError -> year -566 is out of range
            # OSError -> Value too large for data type
            # OverflowError -> timestamp out of range for platform time_t
            return [""]


class RelativeTimeAxisItem(AxisItem):
    """ Relative-Time Axis-Item

    Axis Item that displays timestamps as difference in seconds to an given
    start time. Example: start-time 01:00:00 and tick is 01:00:10 -> "+10s" will
    be displayed at the position of the tick
    """

    def __init__(self, *args, **kwargs):
        """ Create new RelativeTimeAxisItem and set start to 0.
        Args:
            *args: See arguments of AxisItem
            **kwargs: See arguments of AxisItem
        """
        super().__init__(*args, **kwargs)
        self.start = 0

    def set_start_time(self, timestamp) -> None:
        """Sets the start time on which the relative timestamps should be
        calculated from. This has to be done either by hand or as soon as
        the first timestamp get's available.

        Args:
            timestamp: Timestamp that represents the start time

        Returns:
            None
        """
        self.start = timestamp

    def tickStrings(self, values, scale, spacing) -> List[str]:
        """Translate timestamp differences from a point in time to the
        start-time to readable strings in seconds.

        Args:
            values: Positions from the axis that are supposed to be labeled
            scale: See AxisItem Documentation
            spacing: See AxisItem Documentation

        Returns:
            A list of formatted strings that represents the distance in time
            from the time span start
        """
        return [
            ("+" if (value - self.start) > 0 else "")
            + f"{self._cut_to_n_decimals(value - self.start, 2)}s"
            for value in values
        ]

    @staticmethod
    def _cut_to_n_decimals(value: float, decimal_count: int) -> float:
        """Cut off decimals from a given value to a given length.

        Args:
            value (float): Value that should be cut of
            decimal_count (int): Number of decimals that should be left on value

        Returns:
            Value with decimal_count decimals left
        """
        cut_value = value * (10 ** decimal_count) // 1 / (10 ** decimal_count)
        return cut_value
