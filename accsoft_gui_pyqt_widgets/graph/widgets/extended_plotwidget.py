"""
Extended Widget for custom plotting with simple configuration wrappers
"""

from pyqtgraph import PlotWidget, AxisItem
from .extended_axisitems import TimeAxisItem, RelativeTimeAxisItem
from .extended_plotitem import SlidingPointerPlotItem, ScrollingPlotItem, ExtendedPlotItem
from .plotitem_utils import PlotWidgetStyle, ExtendedPlotWidgetConfig
from ..connection.connection import UpdateSource


class ExtendedPlotWidget(PlotWidget):
    """Extended PlotWidget

    Extended version of PyQtGraphs PlotWidget with additional functionality
    and plotting styles and high level functions for data and timing updates
    provided by fitting Signals.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, timing_source: UpdateSource, data_source: UpdateSource, config: ExtendedPlotWidgetConfig, **kwargs):
        """Constructor

        Create a new instance of ExtendedPlotWidget and prepare everything
        for plotting data in the style provided in the passed configuration

        Args:
            timing_source (UpdateSource): Source timing updates are expected
                from
            data_source (UpdateSource): Source data updates are expected from
            config (ExtendedPlotWidgetConfig): Configuration for how points
                should be plotted
            **kwargs: Passed to superclass
        """
        super().__init__(**kwargs)
        self.config = config
        self.timing_source = timing_source
        self.data_source = data_source
        self.cycle_size = config.cycle_size
        self.plotting_style = config.plotting_style
        self.time_progress_line = config.time_progress_line
        self.h_draw_line = config.h_draw_line
        self.v_draw_line = config.v_draw_line
        self.draw_point = config.draw_point
        if "axisItems" in kwargs:
            self._create_fitting_plotitem(**kwargs)
        else:
            self._create_fitting_plotitem(axisItems={"bottom": self._create_fitting_axis_item()}, **kwargs)

    def append_data(self, x_pos: float, y_pos: float) -> None:
        """Append a new point

        Append new data by passing the value to the inner PlotItem subclass.

        Args:
            x_pos (float): value on the horizontal axis, for example a timestamp
            y_pos (float): value on vertical axis

        Returns:
            None
        """
        self.plotItem.plot_append(x_pos, y_pos)

    def _create_fitting_plotitem(self, **kwargs):
        """Create a PlotItem that fits to the passed configuration

        Args:
            **kwargs: Passed to PlotItem
        """
        if self.plotting_style == PlotWidgetStyle.SLIDING_POINTER:
            self.plotItem: ExtendedPlotItem = SlidingPointerPlotItem(timing_source=self.timing_source,
                                                                     data_source=self.data_source,
                                                                     config=self.config,
                                                                     **kwargs)
        elif self.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            self.plotItem: ExtendedPlotItem = ScrollingPlotItem(timing_source=self.timing_source,
                                                                data_source=self.data_source,
                                                                config=self.config,
                                                                **kwargs)
        self.setCentralItem(self.plotItem)

    def _create_fitting_axis_item(self) -> AxisItem:
        if self.plotting_style == PlotWidgetStyle.SLIDING_POINTER:
            return RelativeTimeAxisItem(orientation="bottom")
        if self.plotting_style == PlotWidgetStyle.SCROLLING_PLOT:
            return TimeAxisItem(orientation="bottom")
        return AxisItem(orientation="bottom")
