"""Scrolling Bar Chart for live data plotting"""

from typing import Type, Dict, Optional, cast
from copy import copy

import numpy as np
import pyqtgraph as pg

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import LiveBarGraphDataModel, StaticBarGraphDataModel
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta,
)
from accwidgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem


class AbstractBaseBarGraphItem(DataModelBasedItem, pg.BarGraphItem, metaclass=AbstractDataModelBasedItemMeta):

    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: LiveBarGraphDataModel,
            **bargraphitem_kwargs,
    ):
        """Base class for different live bar graph plots.

        Args:
            plot_item: Plot Item that called the constructor
            data_model: Data Model for the Bar Graph Item
            **bargraphitem_kwargs: Keyword arguments for the BarGraphItem's constructor
        """
        self._fixed_bar_width = bargraphitem_kwargs.get("width", np.nan)
        bargraphitem_kwargs = LiveBarGraphItem._prepare_bar_graph_item_params(**bargraphitem_kwargs)
        pg.BarGraphItem.__init__(self, **bargraphitem_kwargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )

    @classmethod
    def from_plot_item(
            cls,
            plot_item: "ExPlotItem",
            data_source: UpdateSource,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **bargraphitem_kwargs,
    ) -> "AbstractBaseBarGraphItem":
        """Factory method for creating curve object fitting to the given plot item.

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plot item by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's data model's buffer should hold at max
            **bargraphitem_kwargs: keyword arguments for the items base class

        Returns:
            the created item
        """
        subclass = cls.get_subclass_fitting_plotting_style(plot_item=plot_item)
        data_model = subclass.data_model_type(
            data_source=data_source,
            buffer_size=buffer_size,
        )
        return subclass(
            plot_item=plot_item,
            data_model=data_model,
            **bargraphitem_kwargs,
        )


class LiveBarGraphItem(AbstractBaseBarGraphItem):

    data_model_type = LiveBarGraphDataModel

    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_source: Optional[UpdateSource] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            data_model: Optional[LiveBarGraphDataModel] = None,
            **bargraphitem_kwargs,
    ):
        """
        Live Bar Graph Item, abstract base class for all live data bar graphs like
        the scrolling bar graph. Either Data Source of data model have to be set.

        Args:
            plot_item: Plot Item the curve is created for
            data_source: Source updates are passed through.
            buffer_size: Buffer Size.
            data_model: If a valid data model is passed, data source and buffer
                        size are ignored
            **bargraphitem_kwargs: Further Keyword Arguments for the BarGraphItem
        """
        if (data_model is None or not isinstance(data_model, LiveBarGraphDataModel)) and data_source is not None:
            data_model = LiveBarGraphDataModel(
                data_source=data_source,
                buffer_size=buffer_size,
            )
        if data_model is not None:
            super().__init__(
                plot_item=plot_item,
                data_model=data_model,
                **bargraphitem_kwargs,
            )

    @classmethod
    def clone(
            cls: Type["LiveBarGraphItem"],
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
        item_class = LiveBarGraphItem.get_subclass_fitting_plotting_style(
            object_to_create_from._parent_plot_item)
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(bargraph_kwargs)
        return cast(Type[LiveBarGraphItem], item_class)(
            plot_item=object_to_create_from._parent_plot_item,
            data_model=object_to_create_from._data_model,
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

    supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        if self._fixed_bar_width == np.nan:
            smallest_distance = self._data_model.min_dx
            width = 0.9 * smallest_distance if smallest_distance != np.inf else 1.0
        else:
            width = self._fixed_bar_width
        if self._parent_plot_item.time_span is not None:
            curve_x, curve_y, height = self._data_model.subset_for_xrange(
                start=self._parent_plot_item.time_span.start,
                end=self._parent_plot_item.time_span.end,
            )
            if curve_x.size == curve_y.size and curve_x.size > 0:
                self.setOpts(x=curve_x, y=curve_y, height=height, width=width)


class StaticBarGraphItem(AbstractBaseBarGraphItem):

    """
    Bar Graph Item for displaying static data, where new arriving data replaces
    the old one entirely.
    """

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticBarGraphDataModel

    def update_item(self) -> None:
        """Update the item with the data saved in the data model."""
        width = self._fixed_bar_width
        curve_x, curve_y, height = self._data_model.full_data_buffer
        if np.isnan(width):
            width = min(abs(np.ediff1d(curve_x)[1:]))
        if curve_x.size == curve_y.size and curve_x.size > 0:
            self.setOpts(x=curve_x, y=curve_y, height=height, width=width)
