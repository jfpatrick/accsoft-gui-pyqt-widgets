"""Scrolling Bar Chart for live data plotting"""

import abc

import numpy as np
import pyqtgraph

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import BarGraphDataModel
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotcycle import ScrollingPlotCycle


class LiveBarGraphItem(DataModelBasedItem, pyqtgraph.BarGraphItem, metaclass=AbstractDataModelBasedItemMeta):

    """Baseclass for different live bar graph plots"""

    def __init__(
        self,
        data_source: UpdateSource,
        plot_item: pyqtgraph.PlotItem,
        plot_config: ExPlotWidgetConfig,
        timing_source_attached: bool,
        **bargraphitem_kwargs,
    ):
        """ Constructor for the baseclass

        Args:
            data_source: Data Source which the DataModel will be based on
            plot_item: Plot Item that called the constructor
            plot_config: Configuration for the Plot Item that called the constructor
            timing_source_attached: Flag if the PlotItem is attached to a source for Timing Updates
            **bargraphitem_kwargs: Keyword arguments for the BarGraphItem's constructor
        """
        data_model = BarGraphDataModel(data_source=data_source)
        pyqtgraph.BarGraphItem.__init__(self, **bargraphitem_kwargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            timing_source_attached=timing_source_attached,
            parent_plot_item=plot_item,
        )
        self._plot_config: ExPlotWidgetConfig = plot_config

    @staticmethod
    def create(
        plot_item: "ExPlotItem",
        data_source: UpdateSource,
        **bargraph_kwargs,
    ) -> "LiveBarGraphItem":
        """Factory method for creating bargraph object fitting the requested style"""
        plot_config = plot_item.plot_config
        if plot_config.plotting_style.value != PlotWidgetStyle.SCROLLING_PLOT.value:
            raise ValueError(f"{plot_config.plotting_style} is not yet a supported style for this item")
        return ScrollingBarGraphItem(
            plot_item=plot_item,
            plot_config=plot_item.plot_config,
            data_source=data_source,
            timing_source_attached=plot_item.timing_source_attached,
            x=[0.0],
            height=[0.0],
            width=0,
            **bargraph_kwargs,
        )

    @abc.abstractmethod
    def update_timestamp(self, new_timestamp: float) -> None:
        """ Update the timestamp and react to the update

        This function has to be implemented for each subclass

        Args:
            new_timestamp: The new timestamp that is supposed to be reacted to

        Returns:
            None
        """
        pass


class ScrollingBarGraphItem(LiveBarGraphItem):

    """Bar Graph Item to display arriving live data"""

    def __init__(self, **kwargs):
        """ Create a new scrolling bar graph attached to live data

        Args:
            **kwargs: Arguments for baseclass as well as pyqtgraph's BarGraphItem
        """
        super().__init__(**kwargs)
        self._cycle = ScrollingPlotCycle(
            plot_config=self._plot_config, size=self._plot_config.cycle_size
        )

    def update_timestamp(self, new_timestamp: float) -> None:
        """Handle a new timestamp

        Handle a new arriving timestamp that determines what part of the
        data is supposed to be shown.

        Args:
            new_timestamp (float): The new published timestamp
        """
        if new_timestamp >= self._last_timestamp:
            self._last_timestamp = new_timestamp
            self._cycle.number = (
                int(new_timestamp - self._cycle.start) // self._cycle.size
            )
            self._redraw_bars()

    def _redraw_bars(self):
        """Redraw the data as bars

        Select data according to the cycle size and the latest timestamp
        and redraw the bars of the graph from this data.
        """
        self._cycle.update_cycle(self._last_timestamp)
        smallest_distance = self._data_model.get_smallest_distance_between_x_values()
        width = 0.9 * smallest_distance if smallest_distance != np.inf else 1.0
        curve_x, curve_y, height = self._data_model.get_subset(
            start=self._cycle.start, end=self._cycle.end
        )
        if curve_x.size == curve_y.size and curve_x.size > 0:
            self.setOpts(x=curve_x, y=curve_y, height=height, width=width)
