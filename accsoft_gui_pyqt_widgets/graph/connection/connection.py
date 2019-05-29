"""Module for signal based updates for the graph and implementation"""

from datetime import datetime
import numpy as np
from qtpy.QtCore import QObject, Signal, QTimer


class UpdateSource(QObject):
    """Wrapper for two predefined signals for timing and data updates. This can
    be subclassed to define own timing and data update sources.
    """

    timing_signal = Signal(float)
    data_signal = Signal(dict)


class LocalTimerTimingSource(UpdateSource):
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
        self.timer.start(1000/60)

    def _create_new_value(self) -> None:
        """Emit new timestamp.

        Returns:
            None
        """
        self.timing_signal.emit(datetime.now().timestamp())


class OneSecDelayedTimingSource(UpdateSource):
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
        self.timer.start(1000/60)

    def _create_new_value(self) -> None:
        """Emit new timestamp.

        Returns:
            None
        """
        self.timing_signal.emit(datetime.now().timestamp() - self.delay)
        self.delay = 2.0


class OneSecFutureTimingSource(UpdateSource):
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
        self.timer.start(1000/60)

    def _create_new_value(self) -> None:
        """Emit new timestamp.

        Returns:
            None
        """
        self.timing_signal.emit(datetime.now().timestamp() + self.delay)
        self.delay = 2.0


class SinusCurveSource(UpdateSource):
    """Class for sending data-update signals based on random numbers timed by a
    QTimer instance.
    """

    def __init__(self, *args, **kwargs):
        """Constructor

        Args:
            *args: Arguments
            **kwargs: Keyword Arguments
        """
        super().__init__(*args, **kwargs)
        self.sinus_curve = np.sin(np.array(np.arange(start=0.0, stop=720.0, step=10.0)) * np.pi / 180.)
        self.pointer = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(100)

    def _create_new_value(self) -> None:
        new_data = {
            "x": datetime.now().timestamp(),
            "y": self.sinus_curve[self.pointer],
        }
        self.pointer = (self.pointer + 1) % len(self.sinus_curve)
        self.pointer = (self.pointer + 1) % len(self.sinus_curve)
        self.data_signal.emit(new_data)


class FutureSinCurveSource(SinusCurveSource):

    """Emitting values of a sinus curve with timestamps that are one second in
    the future.
    """

    def _create_new_value(self) -> None:
        new_data = {
            "x": datetime.now().timestamp() + 1.0,
            "y": self.sinus_curve[self.pointer],
        }
        self.pointer = (self.pointer + 1) % len(self.sinus_curve)
        self.pointer = (self.pointer + 1) % len(self.sinus_curve)
        self.data_signal.emit(new_data)


class PastSinCurveSource(SinusCurveSource):

    """Emitting values of a sinus curve with timestamps that are one second in
    the past.
    """

    def _create_new_value(self) -> None:
        new_data = {
            "x": datetime.now().timestamp() - 1.0,
            "y": self.sinus_curve[self.pointer],
        }
        self.pointer = (self.pointer + 1) % len(self.sinus_curve)
        self.pointer = (self.pointer + 1) % len(self.sinus_curve)
        self.data_signal.emit(new_data)
