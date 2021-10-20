"""Configuration classes for the ExPlotWidget"""
import numpy as np
from typing import Union, cast
from dataclasses import dataclass
from accwidgets.graph import PlotWidgetStyle


@dataclass(init=False, repr=False)
class TimeSpan:

    left_boundary_offset: float
    """Offset from the current time stamp for the lower boundary of the plot."""

    right_boundary_offset: float
    """Offset from the current time stamp for the upper boundary of the plot."""

    def __init__(self, left: float = np.inf, right: float = 0.0):
        """
        Object representing a TimeSpan of the form [now - left, now - right].
        The left boundary is optional, if None is passed, all accumulated data
        is displayed. The only "limit" is the amount of data the data model holds.

        The boundaries of the plot are calculated as follows:
            - lower boundary (left side of the plot): **now - left**
            - upper boundary (right side of the plot): **now - right**
        with **now** = the most recent timestamp known to the plot.

        Args:
            left: Offset from the current time stamp for the lower boundary of the plot
            right: Offset from the current time stamp for the upper boundary of the plot

        Raises:
            ValueError: The left boundary points to a more recent time stamp than the right boundary.
        """
        if np.isnan(left):
            left = np.inf
        if np.isnan(right) or np.isinf(right):
            right = 0.0

        if left is not None and left < right:
            raise ValueError(f"The passed left boundary with offset (now - {left}) "
                             f"points to a more recent time stamp than the right "
                             f"boundary with offset (now - {right}).")

        self.left_boundary_offset = cast(float, left)
        self.right_boundary_offset = right

    def __repr__(self):
        """Readable string representation of a ExPlotWidget TimeSpan"""
        left, right = " ", ""
        if self.right_boundary_offset is not None:
            right = f"now - {self.right_boundary_offset}"
        if self.left_boundary_offset is not None:
            left = f"now - {self.left_boundary_offset}"
        return f"[{left}, {right}]"

    @property
    def size(self) -> float:
        """
        Get the delta between right and left boundary, if one or both
        boundaries are not defined, the size is infinite.
        """
        return abs(self.right_boundary_offset - self.left_boundary_offset)

    @property
    def finite(self) -> bool:
        """Does the time span has a defined left boundary?"""
        return not(np.isinf(self.left_boundary_offset) or self.left_boundary_offset is None)


class ExPlotWidgetConfig:

    def __init__(self,
                 time_span: Union[TimeSpan, float, int, None] = 60,
                 plotting_style: PlotWidgetStyle = PlotWidgetStyle.SCROLLING_PLOT,
                 time_progress_line: bool = False):
        """Configuration for the PlotWidget

        The ExPlotWidget offers different types of data representation. This
        configuration object controls which way the ExPlotWidget represents
        the data. Next to that it includes the configuration of the amount of
        data (time span) which is shown by the plot as well as other style
        specific metrics.

        **Defaults:**
            - TimeSpan = 60 seconds.
            - Plotting Style = Scrolling Plot
            - Time Progress Line = Hidden

        The TimeSpan can be None, A Float and a TimeSpan Object. If None, all
        accumulated data in the buffer is displayed. If a Float is passed, data
        of the last n seconds is displayed. For more information about the
        TimeSpan, have a look at its documentation.

        Args:
            time_span: time span that each curve represents.
            time_progress_line: flag that represents if a vertical line should be
                drawn at the x position of the latest known timestamp.
            plotting_style: Style in which the plot's items should handle new arriving data and how
                they will represent them.
        """
        self._plotting_style: PlotWidgetStyle = plotting_style
        self._time_span: TimeSpan = ExPlotWidgetConfig._to_time_span(time_span=time_span)
        self._time_progress_line: bool = time_progress_line

    def __str__(self) -> str:
        return f"PlotWidgetStyle: ( " \
            f"time span: {self.time_span}, " \
            f"time progress line: {self.time_progress_line}, " \
            f"plotting style: {self.plotting_style})"

    @property
    def plotting_style(self) -> PlotWidgetStyle:
        """Style for the plot describing the way to display data."""
        return self._plotting_style

    @plotting_style.setter
    def plotting_style(self, plotting_style: PlotWidgetStyle):
        """Style for the plot describing the way to display data."""
        self._plotting_style = plotting_style

    @property
    def time_span(self) -> TimeSpan:
        """How many seconds of data the plot should show."""
        return self._time_span

    @time_span.setter
    def time_span(self, time_span: Union[TimeSpan, float, int, None]):
        """How many seconds of data the plot should show."""
        self._time_span = ExPlotWidgetConfig._to_time_span(time_span=time_span)

    @staticmethod
    def _to_time_span(time_span: Union[TimeSpan, float, int, None]) -> TimeSpan:
        if time_span is None:
            # Time span without left boundary
            return TimeSpan(right=0.0)
        elif isinstance(time_span, (float, int)):
            return TimeSpan(left=float(time_span), right=0.0)
        else:
            return time_span

    @property
    def time_progress_line(self) -> bool:
        """Should a vertical line represent the most recent received time stamp?"""
        if self.plotting_style != PlotWidgetStyle.STATIC_PLOT:
            return self._time_progress_line
        return False

    @time_progress_line.setter
    def time_progress_line(self, time_progress_line: bool):
        """Should a vertical line represent the most recent received time stamp?"""
        self._time_progress_line = time_progress_line
