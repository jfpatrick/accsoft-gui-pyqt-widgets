"""
Axis items are graphical elements that represent x- and y-axes.
This module implements subclasses that are designed for timestamp-based plotting and better readability.
"""

from datetime import datetime
from typing import List, Iterable
from pyqtgraph import AxisItem
from pyqtgraph.GraphicsScene.mouseEvents import MouseDragEvent
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QGraphicsSceneWheelEvent


class ExAxisItem(AxisItem):
    """Axis item that notifies about wheel events through a dedicated signal."""

    sig_vb_mouse_event_triggered_by_axis: Signal = Signal(bool)
    """Mouse event was executed on this axis (and not the :class:`~pyqtgraph.ViewBox`)."""

    def mouseDragEvent(self, event: MouseDragEvent):
        """
        Event handler for the mouse drag action.

        Args:
            ev: Mouse drag event executed on the axis.
        """
        self.sig_vb_mouse_event_triggered_by_axis.emit(True)
        super().mouseDragEvent(event)

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent):
        """
        Event handler for the mouse wheel rotation.

        Args:
            ev: Wheel event executed on the axis.
        """
        self.sig_vb_mouse_event_triggered_by_axis.emit(True)
        super().wheelEvent(ev)


class TimeAxisItem(AxisItem):
    """Axis item that shows timestamps as strings in format ``HH:MM:SS``."""

    def tickStrings(self, values: List[float], scale: float, spacing: float) -> List[str]:
        """
        Translate timestamps to human readable format ``HH:MM:SS``.

        Args:
            values: Positions on the axis that are supposed to be labeled.
            scale: See :class:`~pyqtgraph.AxisItem` documentation.
            spacing: See :class:`~pyqtgraph.AxisItem` documentation.

        Returns:
            A list of formatted strings for tick labels.
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
        """
        Relative time axis item

        Axis item that displays timestamps as offset from the given start time (:attr:`~RelativeTimeAxisItem.start`)
        in seconds. E.g.:

        * start-time ``01:00:00``
        * tick is ``01:00:10``
        * label becomes ``+10s``

        Args:
            *args: Arguments for base class :class:`~pyqtgraph.AxisItem`.
            **kwargs: Arguments for base class :class:`~pyqtgraph.AxisItem`.
        """
        super().__init__(*args, **kwargs)
        self._start = 0.0

    def tickStrings(self, values: Iterable[float], scale: float, spacing: float) -> List[str]:
        """
        Translate timestamps to offsets from the given start time (:attr:`~RelativeTimeAxisItem.start`) in seconds.

        Args:
            values: Positions on the axis that are supposed to be labeled.
            scale: See :class:`~pyqtgraph.AxisItem` documentation.
            spacing: See :class:`~pyqtgraph.AxisItem` documentation.

        Returns:
            A list of formatted strings for tick labels.
        """
        return [
            ("+" if (value - self.start) > 0 else "")
            + f"{self._cut_to_n_decimals(value - self.start, 2)}s"
            for value in values
        ]

    @property
    def start(self) -> float:
        """Time point to calculate offsets for relative timestamps."""
        return self._start

    @start.setter
    def start(self, timestamp: float):
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
