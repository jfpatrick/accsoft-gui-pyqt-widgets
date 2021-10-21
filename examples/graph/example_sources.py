"""
UpdateSource is in general the connection between any item shown in a plot and any source data is coming from. Where
and how which data is acquired is entirely dependent on the implementation of the Update Source. For our examples
we just create a sinus curve locally. These implementations then emit single points or parts of the curve in a
passed frequency.
"""

import math
import numpy as np
from datetime import datetime
from numpy.typing import ArrayLike
from typing import List, Optional, Callable, Any
from enum import IntEnum, auto
from qtpy.QtCore import QTimer, Qt
from accwidgets.graph import (UpdateSource, PointData, BarData, InjectionBarData, TimestampMarkerData, CurveData,
                              BarCollectionData, InjectionBarCollectionData, TimestampMarkerCollectionData,
                              PlottingItemData)


class SinusCurveSourceEmitTypes(IntEnum):
    """Enumeration for different types that can be emitted by the SinusCurveSource."""
    POINT = auto()
    BAR = auto()
    INJECTION_BAR = auto()
    INFINITE_LINE = auto()


class SinusCurveSource(UpdateSource):

    def __init__(self,
                 y_offset: int,
                 x_offset: float,
                 updates_per_second: int = 60,
                 types_to_emit: Optional[List[SinusCurveSourceEmitTypes]] = None,
                 auto_start: bool = True):
        """
        Example implementation of an UpdateSource for emitting points, bars, injection bars in a sinus curve as well
        as timestamp markers in a given frequency.

        Args:
            y_offset: Move all points in the created sinus curve in y direction.
            x_offset: Move all points in the created sinus curve in x direction.
            updates_per_second: How many points should be emitted per second.
        """
        super().__init__()
        self.types_to_emit: List[SinusCurveSourceEmitTypes] = types_to_emit or [SinusCurveSourceEmitTypes.POINT]
        self.label_counter = 0
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.create_new_values, Qt.DirectConnection)
        if auto_start:
            self.timer.start(1000 / updates_per_second)

    def create_new_values(self):
        for emit_type in self.types_to_emit:
            self.create_new_value(emit_type)

    def create_new_value(self, emit_type: SinusCurveSourceEmitTypes):
        new_data: PlottingItemData
        if emit_type == SinusCurveSourceEmitTypes.POINT:
            new_data = PointData(x=datetime.now().timestamp() + self.x_offset,
                                 y=math.sin(datetime.now().timestamp()) + self.y_offset,
                                 check_validity=False)
        elif emit_type == SinusCurveSourceEmitTypes.BAR:
            new_data = BarData(x=datetime.now().timestamp() + self.x_offset,
                               y=math.sin(datetime.now().timestamp()) + self.y_offset,
                               height=math.sin(datetime.now().timestamp()) + self.y_offset,
                               check_validity=False)
        elif emit_type == SinusCurveSourceEmitTypes.INJECTION_BAR:
            new_data = InjectionBarData(x=datetime.now().timestamp() + self.x_offset,
                                        y=math.sin(datetime.now().timestamp()) + self.y_offset,
                                        height=2.0,
                                        width=0.0,
                                        label=str(self.label_counter),
                                        check_validity=False)
            self.label_counter += 1
        elif emit_type == SinusCurveSourceEmitTypes.INFINITE_LINE:
            if self.label_counter % 3 == 0:
                color = "g"
                label = f"EARLY \nLEIRDUMP ({self.label_counter})"
            elif self.label_counter % 3 == 1:
                color = "y"
                label = f"MDEARLY \nLEIRDUMP ({self.label_counter})"
            else:
                color = "r"
                label = f"NOMINAL \nLEIRDUMP ({self.label_counter})"
            new_data = TimestampMarkerData(x=datetime.now().timestamp() + self.x_offset,
                                           color=color,
                                           label=label,
                                           check_validity=False)
            self.label_counter += 1
        else:
            raise ValueError(f"Unknown signal emit_type: {self.types_to_emit}")
        self.send_data(new_data)


class WaveformSinusSource(UpdateSource):

    def __init__(self,
                 curve_length: int = 100,
                 x_start: float = 0.0,
                 x_stop: float = 2 * math.pi,
                 y_offset: float = 0.0,
                 updates_per_second: float = 30,
                 type: SinusCurveSourceEmitTypes = SinusCurveSourceEmitTypes.POINT):
        """
        Update source that emits different scaled, complete sinus curves. Compared to the SinusCurveSource,
        the curve is not emitted one value at a time, but the entire curve, each time with a different scaling.
        X values will stay the same each time. This source can be e.g. used in Waveform Plots.

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
        sin = self.y_base * np.sin(datetime.now().timestamp())
        self.send_data(self._create_value(y=sin))

    def _create_value(self, y: np.ndarray):
        if self.type == SinusCurveSourceEmitTypes.POINT:
            return CurveData(x=self.x,
                             y=y + self.y_offset,
                             check_validity=False)
        elif self.type == SinusCurveSourceEmitTypes.BAR:
            y_vals: np.ndarray = np.zeros(len(self.x)) + (0.5 * y)
            return BarCollectionData(x=self.x,
                                     y=y_vals + self.y_offset,
                                     heights=y,
                                     check_validity=False)
        elif self.type == SinusCurveSourceEmitTypes.INJECTION_BAR:
            y = abs(y)
            return InjectionBarCollectionData(x=self.x,
                                              y=np.zeros(len(self.x)) + self.y_offset,
                                              heights=y,
                                              widths=0.5 * y,
                                              labels=np.array(["{:.2f}".format(_y) for _y in y]),
                                              check_validity=False)
        elif self.type == SinusCurveSourceEmitTypes.INFINITE_LINE:
            sin = np.sin(datetime.now().timestamp())
            r = (self.x[-1] - self.x[0]) / len(self.x)
            x = self.x + sin * r
            return TimestampMarkerCollectionData(x=x,
                                                 colors=np.array([["r", "g", "b"][i]
                                                                  for i, _ in enumerate(range(len(self.x)))]),
                                                 labels=np.array(["{:.2f}".format(_x) for _x in x]),
                                                 check_validity=False)


class EditableSinusCurveDataSource(UpdateSource):

    def __init__(self, edit_callback: Callable[[ArrayLike], Any] = lambda x: print(x)):
        """
        Update source that emits a sinus curve and allows editing.

        **What is the QTimer doing?**
        When we call this constructor, the curve is not yet connected to the
        signal emitting our data. To make sure, that the curve exists at the
        time of calling self.send_data(...), we will use a timer that postpones
        this call until the event loop is running.

        If we want to avoid using QTimer, we can simply move the new_data call
        to a separate function and call it right after we have instantiated our
        curve and passed the update source instance to it.

        Args:
            edit_callback: Function which should be called as soon as the view
                           sends back a value through this update source.
        """
        super().__init__()
        self.edit_callback = edit_callback
        x = np.linspace(0, 2 * math.pi, 10)
        y = np.sin(x)
        curve = CurveData(x, y, check_validity=False)
        self._timer = QTimer()
        self._timer.singleShot(0, lambda: self.send_data(curve))

    def handle_data_model_edit(self, data: CurveData):
        """
        As soon as a value comes back from the view, we will call the edit
        callback passed on initialization with the new values. Normally this
        function would send the values back to the control system.
        """
        self.edit_callback(data)


class LocalTimerTimingSource(UpdateSource):

    def __init__(self, offset: float = 0.0):
        """
        Class for sending timing-update signals based on a QTimer instance.

        Args:
            offset: offset of the emitted time to the actual current time
        """
        super().__init__()
        self.timer = QTimer(self)
        self.offset = offset
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(1000 / 60)

    def _create_new_value(self):
        self.sig_new_timestamp.emit(datetime.now().timestamp() + self.offset)
