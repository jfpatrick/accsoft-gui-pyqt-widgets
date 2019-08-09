"""Plot Configuration

Configuration classes for wrapping widget and curve parameters
"""

from enum import Enum

import numpy as np


class PlotWidgetStyle(Enum):
    """Enumeration for the different available styles for the widgets

    SCROLLING_PLOT: New data gets appended and old one cut. This creates
    a scrolling movement of the graph in positive x direction

    SLIDING_POINTER: A moving line redraws periodically an non moving line
    graph. The old version gets overdrawn as soon as a new point exists that is
    plotted to the same position in x range. The curve is not moving in x
    direction since its x range is fixed.
    """

    DEFAULT = 0
    SCROLLING_PLOT = 1
    SLIDING_POINTER = 2


class ExPlotWidgetConfig:
    """ Configuration for the PlotWidget

    This configuration object holds information about the cycle and
    the visual representation of the data.
    """

    def __init__(
        self,
        cycle_size: float = 60,
        time_progress_line: bool = False,
        plotting_style: PlotWidgetStyle = PlotWidgetStyle.SCROLLING_PLOT,
        x_range_offset: float = np.nan,
    ):
        """Create a new configuration object for the PlotWidget

        Args:
            cycle_size (int): cycle size that is used for drawing each curve
            x_range_offset (float): x range offset for scrolling x range,
                if negative new points will be shown delayed.
            time_progress_line (bool): flag that represents if a line should be
                drawn at the x position of the last timestamp published
            plotting_style (PlotWidgetStyle): style that is supposed to be used
                for the drawing of the curves in the plot
        """
        self.plotting_style: PlotWidgetStyle = plotting_style
        self.cycle_size: float = cycle_size
        self.time_progress_line: bool = time_progress_line
        self.x_range_offset: float = x_range_offset


class LivePlotCurveConfig:
    """ Plot Curve Configuration

    Configuration object for a curves decorators (Lines / Points at the last
    appended datapoint)
    """

    def __init__(
        self,
        draw_vertical_line: bool = False,
        draw_horizontal_line: bool = False,
        draw_point: bool = False,
    ):
        """create new configuration object for a live plot curve

        Args:
            draw_vertical_line (bool): flag if vertical line is supposed to be
                drawn at the position of the last drawn point
            draw_horizontal_line (bool): flag if horizontal is supposed to be
                drawn at the position of the last drawn point
            draw_point (bool): flag if point is supposed to be drawn at the
                position of the last drawn point
        """
        self.draw_vertical_line: bool = draw_vertical_line
        self.draw_horizontal_line: bool = draw_horizontal_line
        self.draw_point: bool = draw_point
