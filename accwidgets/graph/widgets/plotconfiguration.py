"""Configuration classes for the ExPlotWidget"""
from enum import IntEnum
import numpy as np


class PlotWidgetStyle(IntEnum):
    """
    This enumeration represents all different styles of data representation an
    ExPlotWidget offers.
    """

    STATIC_PLOT = 0
    """Static plotting with pure PyQtGraph plotting items."""
    SCROLLING_PLOT = 1
    """
    New data gets appended and old one cut. This creates
    a scrolling movement of the graph in positive x direction
    """
    SLIDING_POINTER = 2
    """
    A moving line redraws periodically an non moving line
    graph. The old version gets overdrawn as soon as a new point exists that is
    plotted to the same position in x range. The curve is not moving in x
    direction since its x range is fixed.
    """


class ExPlotWidgetConfig:

    def __init__(
        self,
        time_span: float = 60.0,
        time_progress_line: bool = False,
        plotting_style: PlotWidgetStyle = PlotWidgetStyle.SCROLLING_PLOT,
        is_xrange_fixed: bool = False,
        fixed_xrange_offset: float = np.nan,
    ):
        """Configuration for the PlotWidget

        The ExPlotWidget offers different types of data representation. This
        configuration object controls which way the ExPlotWidget represents
        the data. Next to that it includes the configuration of the amount of
        data (time span) which is shown by the plot as well as other style
        specific metrics.

        Args:
            time_span: time span that each curve represents
            is_xrange_fixed: should the plot always show the same x range,
                even if less data is available (in which case he would zoom in the x range)?
                Will only be evaluated if the plotting style is SCROLLING_PLOT!
            fixed_xrange_offset: x range offset for scrolling x range,
                will only be evaluated if the fixed x range is activated. If negative, new points
                will be shown delayed by this offset.
            time_progress_line: flag that represents if a vertical line should be
                drawn at the x position of the latest known timestamp.
            plotting_style: Style in which the plot's items should handle new arriving data and how
                they will represent them.
        """
        self._plotting_style: PlotWidgetStyle = plotting_style
        self._time_span: float = time_span
        self._time_progress_line: bool = time_progress_line
        self._is_xrange_fixed: bool = is_xrange_fixed
        self._fixed_xrange_offset = fixed_xrange_offset

    def __str__(self) -> str:
        return f"PlotWidgetStyle: ( " \
            f"time span: {self.time_span}, " \
            f"time progress line: {self.time_progress_line}, " \
            f"plotting style: {self.plotting_style}, " \
            f"scrolling plot fixed x range: {self.is_xrange_fixed}, " \
            f"scrolling plot fixed x range offset: {self.fixed_xrange_offset})"

    @property
    def plotting_style(self) -> PlotWidgetStyle:
        """Style for the plot describing the way to display data."""
        return self._plotting_style

    @plotting_style.setter
    def plotting_style(self, plotting_style: PlotWidgetStyle) -> None:
        """Style for the plot describing the way to display data."""
        self._plotting_style = plotting_style

    @property
    def time_span(self) -> float:
        """How many seconds of data the plot should show."""
        return self._time_span

    @time_span.setter
    def time_span(self, time_span: float) -> None:
        """How many seconds of data the plot should show."""
        self._time_span = time_span

    @property
    def time_progress_line(self) -> bool:
        """Should a vertical line represent the most recent received time stamp?"""
        if self.plotting_style != PlotWidgetStyle.STATIC_PLOT:
            return self._time_progress_line
        return False

    @time_progress_line.setter
    def time_progress_line(self, time_progress_line: bool) -> None:
        """Should a vertical line represent the most recent received time stamp?"""
        self._time_progress_line = time_progress_line

    @property
    def is_xrange_fixed(self) -> bool:
        """Should the plot show always the same time span, even if less data is available?"""
        if self.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            return self._is_xrange_fixed
        return False

    @is_xrange_fixed.setter
    def is_xrange_fixed(self, is_xrange_fixed: bool) -> None:
        """Should the plot show always the same time span, even if less data is available?"""
        self._is_xrange_fixed = is_xrange_fixed

    @property
    def fixed_xrange_offset(self) -> float:
        """Offset, if the fixed x rang is activated"""
        if self.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            if np.isnan(self._fixed_xrange_offset):
                return 0.0
            return self._fixed_xrange_offset
        return np.nan

    @fixed_xrange_offset.setter
    def fixed_xrange_offset(self, fixed_xrange_offset: float) -> None:
        """Offset, if the fixed x rang is activated"""
        self._fixed_xrange_offset = fixed_xrange_offset
