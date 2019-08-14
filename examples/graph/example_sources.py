"""
Simple implementations for Data and Timing Sources for example purposes
"""

from datetime import datetime
from typing import List
from enum import Enum

import numpy as np
from qtpy.QtCore import QTimer

import accsoft_gui_pyqt_widgets.graph as accgraph


class LocalTimerTimingSource(accgraph.UpdateSource):
    """Class for sending timing-update signals based on a QTimer instance."""

    def __init__(self, *args, **kwargs):
        """Create new instance of LocalTimerTimingSource.

        Args:
            *args: Delegated to superclass
            **kwargs: Delegated to superclass
        """
        super().__init__(*args, **kwargs)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(1000 / 60)

    def _create_new_value(self) -> None:
        """Emit new timestamp.

        Returns:
            None
        """
        self.sig_timing_update.emit(datetime.now().timestamp())


class OneSecDelayedTimingSource(accgraph.UpdateSource):
    """Class for sending timing-update signals based on a QTimer instance."""

    def __init__(self, *args, **kwargs):
        """Create new instance of LocalTimerTimingSource.

        Args:
            *args: Delegated to superclass
            **kwargs: Delegated to superclass
        """
        super().__init__(*args, **kwargs)
        self.timer = QTimer(self)
        self.delay = 0
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(1000 / 60)

    def _create_new_value(self) -> None:
        """Emit new timestamp.

        Returns:
            None
        """
        self.sig_timing_update.emit(datetime.now().timestamp() - self.delay)
        self.delay = 2.0


class OneSecFutureTimingSource(accgraph.UpdateSource):
    """Class for sending timing-update signals based on a QTimer instance."""

    def __init__(self, *args, **kwargs):
        """Create new instance of LocalTimerTimingSource.

        Args:
            *args: Delegated to superclass
            **kwargs: Delegated to superclass
        """
        super().__init__(*args, **kwargs)
        self.timer = QTimer(self)
        self.delay = 0
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(1000 / 60)

    def _create_new_value(self) -> None:
        """Emit new timestamp.

        Returns:
            None
        """
        self.sig_timing_update.emit(datetime.now().timestamp() + self.delay)
        self.delay = 2.0


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Data Sources ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SinusCurveSourceEmitTypes(Enum):
    """Enumeration for different emitable types ba the SinusCurveSource"""
    POINT = 1
    BAR = 2
    INJECTIONBAR = 3
    INFINITELINE = 4


class SinusCurveSource(accgraph.UpdateSource):
    """Class for sending data-update signals based on random numbers timed by a
    QTimer instance.
    """

    def __init__(
        self,
        y_offset: int,
        x_offset: float,
        updates_per_second: int = 60,
        types_to_emit: List[SinusCurveSourceEmitTypes] = [SinusCurveSourceEmitTypes.POINT],
        *args,
        **kwargs
    ):
        """Constructor

        Args:
            y_offset (int):
            x_offset (float):
            *args: Arguments
            **kwargs: Keyword Arguments
        """
        super().__init__(*args, **kwargs)
        self.sinus_curve = [
            y_val + y_offset
            for y_val in np.sin(
                np.array(np.arange(start=0.0, stop=720.0, step=60 / updates_per_second))
                * np.pi
                / 180.0
            )
        ]
        self.types_to_emit: List[SinusCurveSourceEmitTypes] = types_to_emit
        self.pointer = 0
        self.label_counter = 0
        self.x_offset = x_offset
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_values)
        self.timer.start(1000 / updates_per_second)

    def _create_new_values(self):
        """Create new values fitting to all requested value types"""
        for type in self.types_to_emit:
            self._create_new_value(type)

    def _create_new_value(self, type: SinusCurveSourceEmitTypes) -> None:
        if type == SinusCurveSourceEmitTypes.POINT:
            new_data = accgraph.PointData(
                x_value=datetime.now().timestamp() + self.x_offset,
                y_value=self.sinus_curve[self.pointer],
            )
            self.sig_data_update[accgraph.PointData].emit(new_data)
        elif type == SinusCurveSourceEmitTypes.BAR:
            new_data = accgraph.BarData(
                x_value=datetime.now().timestamp() + self.x_offset,
                y_value=self.sinus_curve[self.pointer],
                height=self.sinus_curve[self.pointer],
            )
            self.sig_data_update[accgraph.BarData].emit(new_data)
        elif type == SinusCurveSourceEmitTypes.INJECTIONBAR:
            new_data = accgraph.InjectionBarData(
                x_value=datetime.now().timestamp() + self.x_offset,
                y_value=self.sinus_curve[self.pointer],
                height=2.0,
                width=0.05,
                top=self.sinus_curve[self.pointer] + 1,
                bottom=self.sinus_curve[self.pointer] - 1,
                label=str(self.label_counter),
            )
            self.sig_data_update[accgraph.InjectionBarData].emit(new_data)
            self.label_counter += 1
        elif type == SinusCurveSourceEmitTypes.INFINITELINE:
            if self.label_counter % 3 == 0:
                color = "g"
                label = "EARLY \n" + f"LEIRDUMP ({self.label_counter})"
            elif self.label_counter % 3 == 1:
                color = "y"
                label = "MDEARLY \n" + f"LEIRDUMP ({self.label_counter})"
            else:
                color = "r"
                label = "NOMINAL \n" + f"LEIRDUMP ({self.label_counter})"
            new_data = accgraph.TimestampMarkerData(
                x_value=datetime.now().timestamp() + self.x_offset,
                color=color,
                label=label,
            )
            self.sig_data_update[accgraph.TimestampMarkerData].emit(new_data)
            self.label_counter += 1
        else:
            raise ValueError(f"Unknown signal type: {self.types_to_emit}")
        self.pointer = (self.pointer + 1) % len(self.sinus_curve)


class LoggingCurveDataSource(accgraph.UpdateSource):
    """LoggingCurveDataSource

    Update source that emulates a system that not only appends live data but also
    older data saved in a logging system that will be emitted on a later point.
    """

    def __init__(self, updates_per_second: int = 60, *args, **kwargs):
        """Constructor

        Args:
            *args: Arguments
            **kwargs: Keyword Arguments
        """
        super().__init__(*args, **kwargs)
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

    def _update_data(self):
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

    def _create_new_value(self):
        if self.current_index < self.data_length:
            self._emit_next_live_point()
            self.current_index += 1
        else:
            self._emit_separator()
            self._emit_data_from_logging_system()
            self.current_index = 0
            self._update_data()

    def _emit_next_live_point(self):
        new_data = accgraph.PointData(
            x_value=self.x_values_live[self.current_index],
            y_value=self.y_values_live[self.current_index],
        )
        self.sig_data_update[accgraph.PointData].emit(new_data)

    def _emit_separator(self):
        separator = accgraph.PointData(x_value=np.nan, y_value=np.nan)
        self.sig_data_update[accgraph.PointData].emit(separator)

    def _emit_data_from_logging_system(self):
        curve = accgraph.CurveData(
            x_values=np.array(self.x_values_logging),
            y_values=np.array(self.y_values_logging),
        )
        self.sig_data_update[accgraph.CurveData].emit(curve)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class ManualDataSource(accgraph.UpdateSource):
    """Data Source for Testing purposes

    Class for sending the right signals to the ExtendedPlotWidget. This
    allows precise control over updates that are sent to the widget compared to
    timer based solutions.
    """

    def create_new_value(self, timestamp: float, value: float) -> None:
        """Manually emit a signal with a given new value.

        Args:
            timestamp (float): timestamp to emit
            value (float): value to emit
        """
        new_data = accgraph.PointData(x_value=timestamp, y_value=value)
        self.sig_data_update[accgraph.PointData].emit(new_data)

    def create_new_injectionbar_data(self, x_value, y_value, height, width, top, bottom, label) -> None:
        """Manually emit a signal with a given new value."""
        new_data = accgraph.InjectionBarData(
            x_value=x_value,
            y_value=y_value,
            height=height,
            width=width,
            top=top,
            bottom=bottom,
            label=label
        )
        self.sig_data_update[accgraph.InjectionBarData].emit(new_data)

    def create_new_infinite_line_data(self, x_value, color, label):
        """Manually emit a signal with a given new value."""
        new_data = accgraph.TimestampMarkerData(
            x_value=x_value,
            color=color,
            label=label
        )
        self.sig_data_update[accgraph.TimestampMarkerData].emit(new_data)


class ManualTimingSource(accgraph.UpdateSource):
    """Timing Source for Testing Purposes

    Class for sending the right signals to the ExtendedPlotWidget. This
    allows precise control over updates that are sent to the widget compared to
    timer based solutions.
    """

    def create_new_value(self, timestamp: float) -> None:
        """Manually emit timestamp

        Args:
            timestamp (float): timestamp to emit
        """
        self.sig_timing_update.emit(timestamp)
