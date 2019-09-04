"""Scrolling Bar Chart for live data plotting"""

import sys
from typing import Union, List
from copy import deepcopy

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
    PlotWidgetStyle,
)


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
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **bargraphitem_kwargs,
    ):
        """ Constructor for the baseclass

        Args:
            data_source: Data Source which the DataModel will be based on
            plot_item: Plot Item that called the constructor
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
            parent_plot_item=plot_item,
        )

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
        object_to_create_from: "LiveBarGraphItem",
        **bargraph_kwargs,
    ) -> "LiveBarGraphItem":
        """
        Recreate graph item from existing one. The datamodel is shared, but the new graph item
        is fitted to the old graph item's parent plot item's style. If this one has changed
        since the creation of the old graph item, the new graph item will have the new style.

        Args:
            object_to_create_from: object which f.e. datamodel should be taken from
            **bargraph_kwargs: Keyword arguments for the bargraph base class

        Returns:
            New live data bar graph with the datamodel from the old passed one
        """
        plot_config = object_to_create_from._parent_plot_item.plot_config
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LiveBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        # Take opts from old item except ones passed explicitly
        kwargs = deepcopy(object_to_create_from.opts)
        kwargs.update(bargraph_kwargs)
        return item_class(
            plot_item=object_to_create_from._parent_plot_item,
            data_source=object_to_create_from._data_model,
            **kwargs,
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
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_item.plot_config,
            supported_styles=LiveBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_item.plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size,
            **bargraph_kwargs,
        )


class ScrollingBarGraphItem(LiveBarGraphItem):

    """Bar Graph Item to display arriving live data"""

    def update_item(self) -> None:
        """Update item based on the plot items cycle information"""
        if self._fixed_bar_width == -1:
            smallest_distance = self._data_model.get_smallest_distance_between_x_values()
            width = 0.9 * smallest_distance if smallest_distance != np.inf else 1.0
        else:
            width = self._fixed_bar_width
        curve_x, curve_y, height = self._data_model.get_subset(
            start=self._parent_plot_item.cycle.start, end=self._parent_plot_item.cycle.end
        )
        if curve_x.size == curve_y.size and curve_x.size > 0:
            self.setOpts(x=curve_x, y=curve_y, height=height, width=width)
