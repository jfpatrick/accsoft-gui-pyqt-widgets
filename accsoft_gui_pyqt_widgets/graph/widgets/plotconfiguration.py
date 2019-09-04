"""Plot Configuration

Configuration classes for wrapping widget and curve parameters
"""
import numpy as np


class PlotWidgetStyle:
    """
    Enumeration for the different available styles for the widgets
    Subclassing python Enum will lead to errors with the Designer plugin.
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

    @staticmethod
    def get_name(number: int) -> str:
        """
        Checks for all class members that are integer values, if one value
        matches the given integer, its style name will be returned. If no
        value representing an integer value is found
        """
        for member in PlotWidgetStyle.__dict__.keys():
            if not member.startswith('_') and getattr(PlotWidgetStyle, member) == number:
                return member
        return "UNKNOWN PLOTTING STYLE"


class ExPlotWidgetConfig:
    """ Configuration for the PlotWidget

    This configuration object holds information about the cycle and
    the visual representation of the data.
    """

    def __init__(
        self,
        cycle_size: float = 60.0,
        time_progress_line: bool = False,
        plotting_style: int = PlotWidgetStyle.SCROLLING_PLOT,
        scrolling_plot_fixed_x_range: bool = False,
        scrolling_plot_fixed_x_range_offset: float = np.nan,
    ):
        """Create a new configuration object for the PlotWidget

        Args:
            cycle_size: cycle size that is used for drawing each curve
            scrolling_plot_fixed_x_range: flag for a fixed scrolling x range,
                will only be evaluated if the plotting style is SCROLLING_PLOT.
            scrolling_plot_fixed_x_range_offset: x range offset for scrolling x range,
                will only be evaluated if the fixed x range is activated, if negative new points
                will be shown delayed.
            time_progress_line: flag that represents if a line should be
                drawn at the x position of the last timestamp published
            plotting_style: style that is supposed to be used
                for the drawing of the curves in the plot
        """
        self._plotting_style: int = plotting_style
        self._cycle_size: float = cycle_size
        self._time_progress_line: bool = time_progress_line
        self._scrolling_plot_fixed_x_range: bool = scrolling_plot_fixed_x_range
        self._scrolling_plot_fixed_x_range_offset = scrolling_plot_fixed_x_range_offset

    def __str__(self):
        return f"PlotWidgetStyle: ( " \
            f"cycle size: {self.cycle_size}, " \
            f"time progress line: {self.time_progress_line}, " \
            f"plotting_style: {self.plotting_style}, " \
            f"scrolling plot fixed x range: {self.scrolling_plot_fixed_x_range}, " \
            f"scrolling plot fixed x range offset: {self.scrolling_plot_fixed_x_range_offset})"

    @property
    def plotting_style(self) -> int:
        """Property for plotting style"""
        return self._plotting_style

    @plotting_style.setter
    def plotting_style(self, plotting_style: int):
        """Property setter for plotting style"""
        self._plotting_style = plotting_style

    @property
    def cycle_size(self) -> float:
        """Property for cycle size"""
        return self._cycle_size

    @cycle_size.setter
    def cycle_size(self, cycle_size: float):
        """Property setter for cycle size"""
        self._cycle_size = cycle_size

    @property
    def time_progress_line(self) -> bool:
        """Property for time progress line"""
        if self.plotting_style != PlotWidgetStyle.STATIC_PLOT:
            return self._time_progress_line
        else:
            return False

    @time_progress_line.setter
    def time_progress_line(self, time_progress_line: bool):
        """Property setter for time progress line"""
        self._time_progress_line = time_progress_line

    @property
    def scrolling_plot_fixed_x_range(self) -> bool:
        """Property for fixed scrolling x range"""
        if self.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            return self._scrolling_plot_fixed_x_range
        else:
            return False

    @scrolling_plot_fixed_x_range.setter
    def scrolling_plot_fixed_x_range(self, scrolling_plot_fixed_x_range: bool):
        """Property setter for fixed scrolling x range"""
        self._scrolling_plot_fixed_x_range = scrolling_plot_fixed_x_range

    @property
    def scrolling_plot_fixed_x_range_offset(self) -> float:
        """Property for fixed scrolling x range offset"""
        if self.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            if np.isnan(self._scrolling_plot_fixed_x_range_offset):
                return 0.0
            return self._scrolling_plot_fixed_x_range_offset
        else:
            return np.nan

    @scrolling_plot_fixed_x_range_offset.setter
    def scrolling_plot_fixed_x_range_offset(self, scrolling_plot_fixed_x_range_offset: float):
        """Property setter for fixed scrolling x range offset"""
        self._scrolling_plot_fixed_x_range_offset = scrolling_plot_fixed_x_range_offset
