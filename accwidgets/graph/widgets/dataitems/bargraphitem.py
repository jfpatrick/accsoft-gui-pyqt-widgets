"""Scrolling Bar Chart for live data plotting"""

import sys
from typing import Union, List, Type, Dict
from copy import copy

import numpy as np
import pyqtgraph as pg

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import LiveBarGraphDataModel
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accwidgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem

_PLOTTING_STYLE_TO_CLASS_MAPPING = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingBarGraphItem",
}
"""which plotting style is achieved by which class"""


class LiveBarGraphItem(DataModelBasedItem, pg.BarGraphItem, metaclass=AbstractDataModelBasedItemMeta):

    supported_plotting_styles: List[PlotWidgetStyle] = list(_PLOTTING_STYLE_TO_CLASS_MAPPING.keys())
    """List of plotting styles which are supported by this class's create factory function"""

    def __init__(
        self,
        data_source: Union[UpdateSource, LiveBarGraphDataModel],
        plot_item: "ExPlotItem",
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **bargraphitem_kwargs,
    ):
        """Base class for different live bar graph plots.

        Args:
            data_source: Data Source which the DataModel will be based on
            plot_item: Plot Item that called the constructor
            buffer_size: Count of values the item's datamodel's buffer should hold at max
            **bargraphitem_kwargs: Keyword arguments for the BarGraphItem's constructor
        """
        if isinstance(data_source, UpdateSource):
            data_model = LiveBarGraphDataModel(
                data_source=data_source,
                buffer_size=buffer_size
            )
        elif isinstance(data_source, LiveBarGraphDataModel):
            data_model = data_source
        else:
            raise ValueError(
                f"Data Source of type {type(data_source).__name__} can not be used as a source or model for data."
            )
        self._fixed_bar_width = bargraphitem_kwargs.get("width", -1)
        bargraphitem_kwargs = LiveBarGraphItem._prepare_bar_graph_item_params(**bargraphitem_kwargs)
        pg.BarGraphItem.__init__(self, **bargraphitem_kwargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )

    @staticmethod
    def from_plot_item(
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
            **bargraph_kwargs: keyword arguments for the items base class

        Returns:
            the created item
        """
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_item.plot_config,
            supported_styles=LiveBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = _PLOTTING_STYLE_TO_CLASS_MAPPING[plot_item.plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size,
            **bargraph_kwargs,
        )

    @staticmethod
    def clone(
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
        class_name: str = _PLOTTING_STYLE_TO_CLASS_MAPPING[plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        # Take opts from old item except ones passed explicitly
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(bargraph_kwargs)
        return item_class(
            plot_item=object_to_create_from._parent_plot_item,
            data_source=object_to_create_from._data_model,
            **kwargs,
        )

    @staticmethod
    def _prepare_bar_graph_item_params(**bargraph_kwargs) -> Dict:
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


class ScrollingBarGraphItem(LiveBarGraphItem):

    """Bar Graph Item to display arriving live data"""

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        if self._fixed_bar_width == -1:
            smallest_distance = self._data_model.min_dx
            width = 0.9 * smallest_distance if smallest_distance != np.inf else 1.0
        else:
            width = self._fixed_bar_width
        curve_x, curve_y, height = self._data_model.subset_for_xrange(
            start=self._parent_plot_item.time_span.start, end=self._parent_plot_item.time_span.end
        )
        if curve_x.size == curve_y.size and curve_x.size > 0:
            self.setOpts(x=curve_x, y=curve_y, height=height, width=width)
