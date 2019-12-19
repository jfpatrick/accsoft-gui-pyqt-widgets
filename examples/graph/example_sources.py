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
from typing import List, Optional
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
                x_value=datetime.now().timestamp() + self.x_offset,
                y_value=math.sin(datetime.now().timestamp()) + self.y_offset,
            )
            self.sig_new_data[accgraph.PointData].emit(new_data)
        elif emit_type == SinusCurveSourceEmitTypes.BAR:
            new_data = accgraph.BarData(
                x_value=datetime.now().timestamp() + self.x_offset,
                y_value=math.sin(datetime.now().timestamp()) + self.y_offset,
                height=math.sin(datetime.now().timestamp()) + self.y_offset,
            )
            self.sig_new_data[accgraph.BarData].emit(new_data)
        elif emit_type == SinusCurveSourceEmitTypes.INJECTIONBAR:
            new_data = accgraph.InjectionBarData(
                x_value=datetime.now().timestamp() + self.x_offset,
                y_value=math.sin(datetime.now().timestamp()) + self.y_offset,
                height=2.0,
                width=0.0,
                label=str(self.label_counter),
            )
            self.sig_new_data[accgraph.InjectionBarData].emit(new_data)
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
                x_value=datetime.now().timestamp() + self.x_offset,
                color=color,
                label=label,
            )
            self.sig_new_data[accgraph.TimestampMarkerData].emit(new_data)
            self.label_counter += 1
        else:
            raise ValueError(f"Unknown signal emit_type: {self.types_to_emit}")


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
                np.array(
                    np.arange(start=0.0, stop=720.0, step=60 / self.updates_per_second)
                )
                * np.pi
                / 180.0
            )
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
            x_value=self.x_values_live[self.current_index],
            y_value=self.y_values_live[self.current_index],
        )
        self.sig_new_data[accgraph.PointData].emit(new_data)

    def _emit_separator(self) -> None:
        separator = accgraph.PointData(x_value=np.nan, y_value=np.nan)
        self.sig_new_data[accgraph.PointData].emit(separator)

    def _emit_data_from_logging_system(self) -> None:
        curve = accgraph.CurveData(
            x_values=np.array(self.x_values_logging),
            y_values=np.array(self.y_values_logging),
        )
        self.sig_new_data[accgraph.CurveData].emit(curve)


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
