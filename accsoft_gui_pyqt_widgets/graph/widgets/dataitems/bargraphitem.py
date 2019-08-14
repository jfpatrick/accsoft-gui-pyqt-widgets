"""Scrolling Bar Chart for live data plotting"""

import sys
from typing import Union, List
import abc

import numpy as np
import pyqtgraph

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import BarGraphDataModel
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotcycle import ScrollingPlotCycle


# which plotting style is achieved by which class
plotting_style_to_class_mapping = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingBarGraphItem",
}


class LiveBarGraphItem(DataModelBasedItem, pyqtgraph.BarGraphItem, metaclass=AbstractDataModelBasedItemMeta):

    """Baseclass for different live bar graph plots"""

    supported_plotting_styles: List[PlotWidgetStyle] = list(plotting_style_to_class_mapping.keys())

    def __init__(
        self,
        data_source: Union[UpdateSource, BarGraphDataModel],
        plot_item: pyqtgraph.PlotItem,
        plot_config: ExPlotWidgetConfig,
        timing_source_attached: bool,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **bargraphitem_kwargs,
    ):
        """ Constructor for the baseclass

        Args:
            data_source: Data Source which the DataModel will be based on
            plot_item: Plot Item that called the constructor
            plot_config: Configuration for the Plot Item that called the constructor
            timing_source_attached: Flag if the PlotItem is attached to a source for Timing Updates
            buffer_size: Count of values the item's datamodel's buffer should hold at max
            **bargraphitem_kwargs: Keyword arguments for the BarGraphItem's constructor
        """
        if isinstance(data_source, UpdateSource):
            data_model = BarGraphDataModel(
                data_source=data_source,
                buffer_size=buffer_size
            )
        elif isinstance(data_source, BarGraphDataModel):
            data_model = data_source
        else:
            raise ValueError(
                f"Data Source of type {type(data_source).__name__} can not be used as a source or model for data."
            )
        self._fixed_bar_width = bargraphitem_kwargs.get("width", -1)
        bargraphitem_kwargs = LiveBarGraphItem._prepare_bar_graph_item_params(**bargraphitem_kwargs)
        pyqtgraph.BarGraphItem.__init__(self, **bargraphitem_kwargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            timing_source_attached=timing_source_attached,
            parent_plot_item=plot_item,
        )
        self._plot_config: ExPlotWidgetConfig = plot_config

    @staticmethod
    def _prepare_bar_graph_item_params(**bargraph_kwargs):
        """
        For drawing the BarGraphItem needs some data to display, empty data will
        lead to Errors when trying to set the visible range (which is done when drawing).
        This functions prepares adds some data to avoid this
        """
        if bargraph_kwargs.get("x", None) is None:
            bargraph_kwargs["x"] = np.array([0.0])
        if bargraph_kwargs.get("height", None) is None:
            bargraph_kwargs["height"] = np.array([0.0])
        if bargraph_kwargs.get("width", None) is None:
            bargraph_kwargs["width"] = np.array([0.0])
        return bargraph_kwargs

    @staticmethod
    def create_from(
        plot_config: ExPlotWidgetConfig,
        object_to_create_from: "LiveBarGraphItem",
        **bargraph_kwargs,
    ) -> "LiveBarGraphItem":
        """ Create a bargraph from another one

        Factory method for creating bargraph object from a config and an existing object from the
        same baseclass.

        Args:
            plot_config: Configuration of the plot the item should be created for
            object_to_create_from: object which f.e. datamodel should be taken from
            **bargraph_kwargs: Keyword arguments for the bargraph base class

        Returns:

        """
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LiveBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        if not bargraph_kwargs:
            # contains parameters like pen etc.
            bargraph_kwargs = object_to_create_from.opts
        return item_class(
            plot_item=object_to_create_from._parent_plot_item,
            plot_config=plot_config,
            data_source=object_to_create_from._data_model,
            timing_source_attached=object_to_create_from._timing_source_attached,
            **bargraph_kwargs,
        )

    @staticmethod
    def create(
        plot_item: "ExPlotItem",
        data_source: UpdateSource,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **bargraph_kwargs,
    ) -> "LiveBarGraphItem":
        """ Factory method for creating bar graph object fitting the requested style

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plotitem by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's data model's buffer should hold at max
            **bargraph_kwargs: keyword arguments for the items baseclass

        Returns:
            the created item
        """
        plot_config = plot_item.plot_config
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LiveBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            plot_config=plot_item.plot_config,
            data_source=data_source,
            timing_source_attached=plot_item.timing_source_attached,
            buffer_size=buffer_size,
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
        if self._fixed_bar_width == -1:
            smallest_distance = self._data_model.get_smallest_distance_between_x_values()
            width = 0.9 * smallest_distance if smallest_distance != np.inf else 1.0
        else:
            width = self._fixed_bar_width
        curve_x, curve_y, height = self._data_model.get_subset(
            start=self._cycle.start, end=self._cycle.end
        )
        if curve_x.size == curve_y.size and curve_x.size > 0:
            self.setOpts(x=curve_x, y=curve_y, height=height, width=width)
