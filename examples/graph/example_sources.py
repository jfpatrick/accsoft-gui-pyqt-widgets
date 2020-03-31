"""
UpdateSource is in general the connection between any item
shown in a plot and any source data is coming from. Where
and how which data is acquired is entirely dependent on the
implementation of the Update Source.
For our examples we just create a sinus curve locally. These
implementations then emit single points or parts of the curve
in a passed frequency.
"""

from datetime import datetime
from typing import List, Optional, Callable, Any
from enum import Enum
import math

import numpy as np
from qtpy.QtCore import QTimer

from accwidgets import graph as accgraph


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                                  Data Sources
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SinusCurveSourceEmitTypes(Enum):
    """Enumeration for different emitable types by the SinusCurveSource"""
    POINT = 1
    BAR = 2
    INJECTIONBAR = 3
    INFINITELINE = 4


class SinusCurveSource(accgraph.UpdateSource):
    """
    Example implementation of an UpdateSource for emitting points,
    bars, injection bars in a sinus curve as well as timestamp markers
    in a given frequency.
    """

    def __init__(
        self,
        y_offset: int,
        x_offset: float,
        updates_per_second: int = 60,
        types_to_emit: Optional[List[SinusCurveSourceEmitTypes]] = None,
    ):
        """Create a new UpdateSource emitting a sinus curve over time.

        Args:
            y_offset: move all points in the created sinus curve in y direction
            x_offset: Move all points in the created sinus curve in x direction
            updates_per_second: How many points should be emitted per second
        """
        super().__init__()
        self.types_to_emit: List[SinusCurveSourceEmitTypes] = types_to_emit or [SinusCurveSourceEmitTypes.POINT]
        self.label_counter = 0
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_values)
        self.timer.start(1000 / updates_per_second)

    def _create_new_values(self) -> None:
        """Create new values fitting to all requested value types"""
        for emit_type in self.types_to_emit:
            self._create_new_value(emit_type)

    def _create_new_value(self, emit_type: SinusCurveSourceEmitTypes) -> None:
        if emit_type == SinusCurveSourceEmitTypes.POINT:
            new_data = accgraph.PointData(
                x=datetime.now().timestamp() + self.x_offset,
                y=math.sin(datetime.now().timestamp()) + self.y_offset,
                check_validity=False,
            )
        elif emit_type == SinusCurveSourceEmitTypes.BAR:
            new_data = accgraph.BarData(
                x=datetime.now().timestamp() + self.x_offset,
                y=math.sin(datetime.now().timestamp()) + self.y_offset,
                height=math.sin(datetime.now().timestamp()) + self.y_offset,
                check_validity=False,
            )
        elif emit_type == SinusCurveSourceEmitTypes.INJECTIONBAR:
            new_data = accgraph.InjectionBarData(
                x=datetime.now().timestamp() + self.x_offset,
                y=math.sin(datetime.now().timestamp()) + self.y_offset,
                height=2.0,
                width=0.0,
                label=str(self.label_counter),
                check_validity=False,
            )
            self.label_counter += 1
        elif emit_type == SinusCurveSourceEmitTypes.INFINITELINE:
            if self.label_counter % 3 == 0:
                color = "g"
                label = f"EARLY \nLEIRDUMP ({self.label_counter})"
            elif self.label_counter % 3 == 1:
                color = "y"
                label = f"MDEARLY \nLEIRDUMP ({self.label_counter})"
            else:
                color = "r"
                label = f"NOMINAL \nLEIRDUMP ({self.label_counter})"
            new_data = accgraph.TimestampMarkerData(
                x=datetime.now().timestamp() + self.x_offset,
                color=color,
                label=label,
                check_validity=False,
            )
            self.label_counter += 1
        else:
            raise ValueError(f"Unknown signal emit_type: {self.types_to_emit}")
        self.send_data(new_data)


class LoggingCurveDataSource(accgraph.UpdateSource):
    """LoggingCurveDataSource

    Update source that emulates a system that not only appends live data but also
    older data saved in a logging system that will be emitted on a later point.
    """

    def __init__(self, updates_per_second: int = 60):
        """Constructor

        Args:
            updates_per_second: How many updates per second should be emitted
                                by the data source?
        """
        super().__init__()
        self.updates_per_second = updates_per_second
        self.timer_diff = 1000 / updates_per_second
        self.y_values_live: List[float] = list(
            np.sin(
                np.array(np.arange(start=0.0, stop=720.0, step=60 / self.updates_per_second))
                * np.pi
                / 180.0,
            ),
        )
        self.y_values_logging: List[float] = [y_value * 0.25 for y_value in self.y_values_live]
        delta = self.timer_diff / (1000 * 2)
        start = datetime.now().timestamp()
        self.x_values_live: List[float] = [
            (start + index * delta) for index, value in enumerate(self.y_values_live)
        ]
        self.x_values_logging: List[float] = [
            (start - (len(self.y_values_logging) - (index + 1)) * delta)
            for index, value in enumerate(self.y_values_logging)
        ]
        self._update_data()
        self.data_length: int = len(self.y_values_live)
        self.current_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(self.timer_diff)

    def _update_data(self) -> None:
        last_timestamp = (
            self.x_values_live[-1] if self.x_values_live else datetime.now().timestamp()
        )
        # Half of the actual timer frequency
        delta = self.timer_diff / (1000 * 2)
        self.x_values_logging = [
            (last_timestamp + index * delta)
            for index, value in enumerate(self.y_values_live)
        ]
        last_timestamp = (
            self.x_values_logging[-1]
            if self.x_values_logging
            else datetime.now().timestamp() + delta
        )
        self.x_values_live = [
            (last_timestamp + index * delta)
            for index, value in enumerate(self.y_values_live)
        ]

    def _create_new_value(self) -> None:
        if self.current_index < self.data_length:
            self._emit_next_live_point()
            self.current_index += 1
        else:
            self._emit_separator()
            self._emit_data_from_logging_system()
            self.current_index = 0
            self._update_data()

    def _emit_next_live_point(self) -> None:
        new_data = accgraph.PointData(
            x=self.x_values_live[self.current_index],
            y=self.y_values_live[self.current_index],
            check_validity=False,
        )
        self.send_data(new_data)

    def _emit_separator(self) -> None:
        separator = accgraph.PointData(x=np.nan,
                                       y=np.nan,
                                       check_validity=False)
        self.sig_new_data[accgraph.PointData].emit(separator)

    def _emit_data_from_logging_system(self) -> None:
        curve = accgraph.CurveData(
            x=np.array(self.x_values_logging),
            y=np.array(self.y_values_logging),
            check_validity=False,
        )
        self.send_data(curve)


class WaveformSinusSource(accgraph.UpdateSource):

    def __init__(
            self,
            curve_length: int = 100,
            x_start: float = 0.0,
            x_stop: float = 2 * math.pi,
            y_offset: float = 0.0,
            updates_per_second: float = 30,
            type: SinusCurveSourceEmitTypes = SinusCurveSourceEmitTypes.POINT,
    ):
        """
        Update Source which emits different scaled, complete sinus curves.
        Compared to the SinusCurveSource, the curve is not emitted one value
        at a time, but the entire curve, each time with a different scaling.

        X values will stay the same each time

        This source can be f.e. used in Waveform Plots.

        Args:
            curve_length: Amount of x and y values
            x_start: Smallest x value
            x_stop: Biggest x value
            y_offset: Offset in y direction
            updates_per_second: How often per second is a new curve emitted
            type: In what type should the sinus curve be emitted
        """
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_values)
        self.timer.start(1000 / updates_per_second)
        self.type = type
        self.y_offset = y_offset
        self.x = np.linspace(x_start, x_stop, curve_length)
        self.y_base = np.sin(self.x)

    def _create_new_values(self):
        """Create a new value representing a sinus curve in some way."""
        sin = self.y_base * np.sin(datetime.now().timestamp())
        self.send_data(self._create_value(y=sin))

    def _create_value(self, y: np.ndarray):
        """Create a data wrapper based on the requested type."""
        if self.type == SinusCurveSourceEmitTypes.POINT:
            return accgraph.CurveData(
                x=self.x,
                y=y + self.y_offset,
                check_validity=False,
            )
        elif self.type == SinusCurveSourceEmitTypes.BAR:
            return accgraph.BarCollectionData(
                x=self.x,
                y=np.zeros(len(self.x)) + self.y_offset + 0.5 * y,
                heights=y,
                check_validity=False,
            )
        elif self.type == SinusCurveSourceEmitTypes.INJECTIONBAR:
            y = abs(y)
            return accgraph.InjectionBarCollectionData(
                x=self.x,
                y=np.zeros(len(self.x)) + self.y_offset,
                heights=y,
                widths=0.5 * y,
                labels=np.array(["{:.2f}".format(_y) for _y in y]),
                check_validity=False,
            )
        elif self.type == SinusCurveSourceEmitTypes.INFINITELINE:
            sin = np.sin(datetime.now().timestamp())
            r = (self.x[-1] - self.x[0]) / len(self.x)
            x = self.x + sin * r
            return accgraph.TimestampMarkerCollectionData(
                x=x,
                colors=np.array([["r", "g", "b"][i] for i, _ in enumerate(range(len(self.x)))]),
                labels=np.array(["{:.2f}".format(_x) for _x in x]),
                check_validity=False,
            )


class EditableSinusCurveDataSource(accgraph.UpdateSource):

    def __init__(
            self,
            edit_callback: Callable[[np.ndarray], Any] = lambda x: print(x),
    ):
        """
        Update Source which emits a Sinus curve and allows editing.

        **What is the QTimer doing?**
        When we call this constructor, the curve is not yet connected to the
        signal emitting our data. To make sure, that the curve exists at the
        time of calling self.new_data(...), we will use a timer that postpones
        this call until the event loop is running.

        If we want to avoid using QTimer, we can simply move the new_data call
        to a separate function and call it right after we have instantiated our
        curve and passed the update source instance to it.

        Args:
            edit_callback: Function which should be called as soon as the view
                           sends back a value through this update source
        """
        super().__init__()
        self.edit_callback = edit_callback
        x = np.linspace(0, 2 * math.pi, 10)
        y = np.sin(x)
        curve = accgraph.CurveData(x, y, check_validity=False)
        self._timer = QTimer()
        self._timer.singleShot(0, lambda: self.send_data(curve))

    def handle_data_model_edit(self, data: accgraph.CurveData):
        """
        As soon as a value comes back from the view, we will call the edit
        callback passed on initialization with the new values. Normally this
        function would send the values back to the control system.
        """
        self.edit_callback(data)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                                 Timing Source
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class LocalTimerTimingSource(accgraph.UpdateSource):
    """Class for sending timing-update signals based on a QTimer instance."""

    def __init__(self, offset: float = 0.0):
        """Create new instance of LocalTimerTimingSource.

        Args:
            offset: offset of the emitted time to the actual current time
        """
        super().__init__()
        self.timer = QTimer(self)
        self.offset = offset
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(1000 / 60)

    def _create_new_value(self) -> None:
        """Emit new timestamp."""
        self.sig_new_timestamp.emit(datetime.now().timestamp() + self.offset)
