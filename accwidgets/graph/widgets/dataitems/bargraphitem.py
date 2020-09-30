"""Scrolling Bar Chart for live data plotting"""

from typing import Type, Dict, Union, cast, List, Tuple, Optional
from copy import copy

import numpy as np
import pyqtgraph as pg

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import (
    LiveBarGraphDataModel,
    StaticBarGraphDataModel,
    AbstractBaseDataModel,
)
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta,
)
from accwidgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from accwidgets.graph.util import deprecated_param_alias
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem


OrthoRange = Union[List[float], Tuple[float, float], None]
FracValue = float
BoundsValue = Tuple[float, float]
BoundsAxisEntry = Tuple[Tuple[FracValue, OrthoRange], BoundsValue]


class AbstractBaseBarGraphItem(DataModelBasedItem, pg.BarGraphItem, metaclass=AbstractDataModelBasedItemMeta):

    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: AbstractBaseDataModel,
            **bargraphitem_kwargs,
    ):
        """Base class for different live bar graph plots.

        Args:
            plot_item: Plot Item that called the constructor
            data_model: Data Model for the Bar Graph Item
            **bargraphitem_kwargs: Keyword arguments for the BarGraphItem's constructor
        """
        self._fixed_bar_width = bargraphitem_kwargs.get("width", np.nan)
        self._boundsCache: List[Optional[BoundsAxisEntry]] = [None, None]
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

    def dataBounds(
            self,
            ax: int,
            frac: FracValue = 1.0,
            orthoRange: OrthoRange = None,
    ) -> Optional[BoundsValue]:
        """
        Declares a method dynamically probed to have proper auto-scaling on bar graphs.
        This method is called by :class:`~pyqtgraph.ViewBox` when auto-scaling.
        NOTE! orthoRange and frac are ignored in this implementation (simply no need for it now).

        Args:
            ax: index of the axis (0 or 1) for which to return this item's data range.
            frac: Specifies what fraction (0.0-1.0) of the total data range to return.
                  By default, the entire range is returned. This allows the :class:`~pyqtgraph.ViewBox`
                  to ignore large spikes in the data when auto-scaling.
            orthoRange: Specifies that only the data within the given range (orthogonal to *ax*)
                        should me measured when returning the data range. (For example, a
                        :class:`~pyqtgrah.ViewBox` might ask what is the y-range of all data
                        with x-values between min and max).

        Returns:
            The range occupied by the data (along a specific axis) in this item.
        """
        if ax not in [0, 1]:
            raise Exception(f"Value for parameter 'ax' must be either 0 or 1. (got {ax})")

        cache = self._boundsCache[ax]
        if cache is not None and cache[0] == (frac, orthoRange):
            return cache[1]

        # Partially taken from pyqtgraph.BarGraphItem.drawPicture
        def asarray(x):
            if x is None or np.isscalar(x) or isinstance(x, np.ndarray):
                return x
            return np.array(x)

        out_min_x, out_max_x, out_min_y, out_max_y = None, None, None, None

        x = asarray(self.opts.get("x"))
        x0 = asarray(self.opts.get("x0"))
        x1 = asarray(self.opts.get("x1"))
        width = asarray(self.opts.get("width"))

        if x0 is None:
            if width is None:
                raise Exception("must specify either x0 or width")
            if x1 is not None:
                x0 = x1 - width
            elif x is not None:
                x0 = x - width / 2.
            else:
                raise Exception("must specify at least one of x, x0, or x1")
        if width is None:
            if x1 is None:
                raise Exception("must specify either x1 or width")
            width = x1 - x0

        y = asarray(self.opts.get("y"))
        y0 = asarray(self.opts.get("y0"))
        y1 = asarray(self.opts.get("y1"))
        height = asarray(self.opts.get("height"))

        if y0 is None:
            if height is None:
                y0 = 0
            elif y1 is not None:
                y0 = y1 - height
            elif y is not None:
                y0 = y - height / 2.
            else:
                y0 = 0
        if height is None:
            if y1 is None:
                raise Exception("must specify either y1 or height")
            height = y1 - y0

        for i in range(len(x0)):

            if np.isscalar(x0):
                x = x0
            else:
                x = x0[i]
            if np.isscalar(y0):
                y = y0
            else:
                y = y0[i]
            if np.isscalar(width):
                w = width
            else:
                w = width[i]
            if np.isscalar(height):
                h = height
            else:
                h = height[i]

            bottom = y
            top = y + h
            miny = min(top, bottom)
            maxy = max(top, bottom)

            left = x
            right = x + w
            minx = min(left, right)
            maxx = max(left, right)

            out_min_x = minx if out_min_x is None else min(out_min_x, minx)
            out_min_y = miny if out_min_y is None else min(out_min_y, miny)
            out_max_x = maxx if out_max_x is None else max(out_max_x, maxx)
            out_max_y = maxy if out_max_y is None else max(out_max_y, maxy)

        b: BoundsValue
        if ax == 0:
            if out_min_x is None or out_max_x is None:
                return None
            b = out_min_x, out_max_x
        else:
            if out_min_y is None or out_max_y is None:
                return None
            b = out_min_y, out_max_y

        self._boundsCache[ax] = cast(BoundsAxisEntry, ((frac, orthoRange), b))
        return b

    def pixelPadding(self) -> float:
        """
        Declares a method dynamically probed to have proper auto-scaling on bar graphs.
        This method is called by :class:`~pyqtgraph.ViewBox` when auto-scaling.

        Returns:
            The size in pixels that this item may draw beyond the values returned by
            :meth:`~AbstractBaseBarGraphItem.dataBounds`.
        """

        # Combination of retrieving pens, as in pyqtgraph.BarGraphItem.drawPicture
        # And calculating padding, as in pyqtgraph.PlotCurveItem.pixelPadding
        pen = self.opts["pen"]
        pens = self.opts["pens"]

        if pen is None and pens is None:
            pen = pg.getConfigOption("foreground")
        pen_obj = pg.mkPen(pen)

        w = 0
        if pen_obj.isCosmetic():
            w += pen_obj.widthF() * 0.7072
        return w

    def setOpts(self, **opts):
        self.invalidateBounds()
        super().setOpts(**opts)

    def viewTransformChanged(self):
        """Declares a method dynamically probed to have invalidate bound caches used for auto-scaling."""
        self.invalidateBounds()
        self.prepareGeometryChange()

    def invalidateBounds(self):
        self._boundsCache = [None, None]


class LiveBarGraphItem(AbstractBaseBarGraphItem):

    data_model_type = LiveBarGraphDataModel

    @deprecated_param_alias(data_source="data_model")
    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: Union[LiveBarGraphDataModel, UpdateSource],
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **bargraphitem_kwargs,
    ):
        """
        Live Bar Graph Item, abstract base class for all live data bar graphs like
        the scrolling bar graph. Either Data Source of data model have to be set.

        Args:
            plot_item: Plot Item the curve is created for
            data_model: Either an Update Source or a already initialized data
                        model
            buffer_size: Buffer size, which will be passed to the data model,
                         will only be used if the data_model is only an Update
                         Source.
            **bargraphitem_kwargs: Further Keyword Arguments for the BarGraphItem
        """
        if isinstance(data_model, UpdateSource):
            data_model = LiveBarGraphDataModel(
                data_source=data_model,
                buffer_size=buffer_size,
            )
        if data_model is not None:
            super().__init__(
                plot_item=plot_item,
                data_model=data_model,
                **bargraphitem_kwargs,
            )
        else:
            raise TypeError("Need either data source or data model to create "
                            f"a {type(self).__name__} instance")

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
            object_to_create_from: object which e.g. datamodel should be taken from
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

    def update_item(self):
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
                self.setOpts(x=curve_x, y0=curve_y, height=height, width=width)


class StaticBarGraphItem(AbstractBaseBarGraphItem):

    """
    Bar Graph Item for displaying static data, where new arriving data replaces
    the old one entirely.
    """

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticBarGraphDataModel

    def update_item(self):
        """Update the item with the data saved in the data model."""
        width = self._fixed_bar_width
        curve_x, curve_y, height = self._data_model.full_data_buffer
        if np.isnan(width):
            width = min(abs(np.ediff1d(curve_x)[1:]))
        if curve_x.size == curve_y.size and curve_x.size > 0:
            self.setOpts(x=curve_x, y0=curve_y, height=height, width=width)
