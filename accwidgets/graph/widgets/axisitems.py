"""
Different AxisItem implementations for Timestamp based plotting for better readability
"""

from datetime import datetime
from typing import List, Iterable

from pyqtgraph import AxisItem
from pyqtgraph.GraphicsScene.mouseEvents import MouseDragEvent
from qtpy.QtCore import Signal
from qtpy.QtGui import QWheelEvent


class ExAxisItem(AxisItem):

    """AxisItem with some required extra functions"""

    sig_vb_mouse_event_triggered_by_axis: Signal = Signal(bool)
    """Signal that the mouse event was executed on the axis (and not the ViewBox)"""

    def mouseDragEvent(self, event: MouseDragEvent) -> None:
        """Make the mouse drag event on the axis distinguishable from the ViewBox one

        Args:
            event: Mouse drag event executed on the axis
        """
        self.sig_vb_mouse_event_triggered_by_axis.emit(True)
        super().mouseDragEvent(event)

    def wheelEvent(self, ev: QWheelEvent) -> None:
        """Make the mouse click event on the axis distinguishable from the ViewBox one

        Args:
            ev: Wheel event executed on the axis
        """
        self.sig_vb_mouse_event_triggered_by_axis.emit(True)
        super().wheelEvent(ev)


# pylint: disable=too-many-ancestors
class TimeAxisItem(AxisItem):
    """Axis Item that shows timestamps as strings in format HH:MM:SS"""

    def tickStrings(self, values: List[float], scale: float, spacing: float) -> List[str]:
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

    def __init__(self, *args, **kwargs):
        """Relative-Time Axis-Item

        Axis Item that displays timestamps as difference in seconds to an given
        start time. Example: start-time 01:00:00 and tick is 01:00:10 -> "+10s" will
        be displayed at the position of the tick.

        Args:
            *args: Arguments for base class AxisItem
            **kwargs: Arguments for base class AxisItem
        """
        super().__init__(*args, **kwargs)
        self._start = 0.0

    def tickStrings(self, values: Iterable[float], scale: float, spacing: float) -> List[str]:
        """Translate timestamp differences from a point in time to the
        start-time to readable strings in seconds.

        Args:
            values: Positions on the axis that are supposed to be labeled
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

    @property
    def start(self) -> float:
        """Start time on which the relative timestamps should be calculated from."""
        return self._start

    @start.setter
    def start(self, timestamp: float) -> None:
        """Sets the start time on which the relative timestamps should be
        calculated from. This has to be done either by hand or as soon as
        the first timestamp get's available.

        Args:
            timestamp: Timestamp that represents the start time
        """
        self._start = timestamp

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
