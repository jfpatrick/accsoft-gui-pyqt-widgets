"""
Module contains different curves that can be added to a PlotItem based on PyQtGraph's PlotDataItem.
"""

import sys
import logging
from typing import Union, List, Tuple, Dict, Type, cast
from copy import copy

import numpy as np
import pyqtgraph as pg

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import LiveCurveDataModel
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.datamodel.datastructures import DEFAULT_COLOR, CurveData
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta,
)
from accwidgets.graph.widgets.plotconfiguration import PlotWidgetStyle
from accwidgets.graph.widgets.plottimespan import CyclicPlotTimeSpan
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem

_LOGGER = logging.getLogger(__name__)

_PLOTTING_STYLE_TO_CLASS_MAPPING = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingPlotCurve",
    PlotWidgetStyle.CYCLIC_PLOT: "CyclicPlotCurve",
}
"""which plotting style is achieved by which class"""

# params accepted by the plotdataitem and their fitting params in the curve-item
_PLOTDATAITEM_CURVE_PARAM_MAPPING = [
    ("pen", "pen"),
    ("shadowPen", "shadowPen"),
    ("fillLevel", "fillLevel"),
    ("fillBrush", "brush"),
    ("antialias", "antialias"),
    ("connect", "connect"),
    ("stepMode", "stepMode"),
]

# params accepted by the plotdataitem and their fitting params in the scatter-plot-item
_PLOTDATAITEM_SCATTER_PARAM_MAPPING = [
    ("symbolPen", "pen"),
    ("symbolBrush", "brush"),
    ("symbol", "symbol"),
    ("symbolSize", "size"),
    ("data", "data"),
    ("pxMode", "pxMode"),
    ("antialias", "antialias"),
]


class LivePlotCurve(DataModelBasedItem, pg.PlotDataItem, metaclass=AbstractDataModelBasedItemMeta):

    supported_plotting_styles: List[PlotWidgetStyle] = [*_PLOTTING_STYLE_TO_CLASS_MAPPING]
    """List of plotting styles which are supported by this class's create factory function"""

    def __init__(
        self,
        plot_item: "ExPlotItem",
        data_source: Union[UpdateSource, LiveCurveDataModel],
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        pen=DEFAULT_COLOR,
        **plotdataitem_kwargs,
    ):
        """Base class for different live data curves.

        Args:
            plot_item: plot item the curve should fit to
            data_source: source the curve receives data from
            buffer_size: count of values the curve's data model's buffer should
                         hold at max
            pen: pen the curve should be drawn with, is part of the plotdataitem
                 base class parameters
            **plotdataitem_kwargs: keyword arguments fo the base class

        Raises:
            ValueError: The passes data source is not usable as a source for data
        """
        if isinstance(data_source, UpdateSource):
            data_model = LiveCurveDataModel(
                data_source=data_source,
                buffer_size=buffer_size,
            )
        elif isinstance(data_source, LiveCurveDataModel):
            data_model = data_source
        else:
            raise ValueError(f"Data Source of type {type(data_source)} can not be used as a source or model for data.")
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        pg.PlotDataItem.__init__(self, pen=pen, **plotdataitem_kwargs)
        self.opts["connect"] = "finite"
        # Save drawn data for testing purposes
        self._data_item_data: CurveData
        if pen is not None:
            self.setPen(pen)

    @staticmethod
    def from_plot_item(
            plot_item: "ExPlotItem",
            data_source: UpdateSource,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **plotdataitem_kwargs,
    ) -> "LivePlotCurve":
        """Factory method for creating curve object fitting to the given plot item.

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plot item by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's data model's buffer should hold at max
            **buffer_size: keyword arguments for the items base class

        Returns:
            the created item
        """
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_item.plot_config,
            supported_styles=LivePlotCurve.supported_plotting_styles,
        )
        # get class fitting to plotting style and return instance
        class_name: str = _PLOTTING_STYLE_TO_CLASS_MAPPING[plot_item.plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size,
            **plotdataitem_kwargs,
        )

    @staticmethod
    def clone(
        object_to_create_from: "LivePlotCurve",
        **plotdataitem_kwargs,
    ) -> "LivePlotCurve":
        """
        Clone graph item from existing one. The datamodel is shared, but the new graph item
        is fitted to the old graph item's parent plot item's style. If this one has changed
        since the creation of the old graph item, the new graph item will have the new style.

        Args:
            object_to_create_from: object which f.e. datamodel should be taken from
            **plotdataitem_kwargs: Keyword arguments for the PlotDataItem base class

        Returns:
            New live data curve with the datamodel from the old passed one
        """
        plot_config = object_to_create_from._parent_plot_item.plot_config
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LivePlotCurve.supported_plotting_styles,
        )
        # get class fitting to plotting style and return instance
        class_name: str = _PLOTTING_STYLE_TO_CLASS_MAPPING[plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        # Take opts from old item except ones passed explicitly
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(plotdataitem_kwargs)
        return item_class(
            plot_item=object_to_create_from._parent_plot_item,
            data_source=object_to_create_from._data_model,
            **kwargs,
        )

    @property
    def last_timestamp(self) -> float:
        """Last timestamp received by the curve."""
        return self._parent_plot_item.last_timestamp

    def _set_data(self, x: np.ndarray, y: np.ndarray) -> None:
        """ Set data of the inner curve and scatter plot

        PyQtGraph prints RuntimeWarning when the data that is passed to the
        ScatterPlotItem contains NaN values -> for this purpose we strip
        all indices containing NaNs, since it won't make any visual difference,
        because nans won't appear as symbols in the scatter plot.
        The CurvePlotItem will receive the data as usual.

        Args:
            x: x values that are passed to the items
            y: y values that are passed to the items
        """
        # For arguments like symbolPen which have to be transformed to pen and send to the ScatterPlot
        curve_arguments: Dict = {}
        for orig_key, curve_key in _PLOTDATAITEM_CURVE_PARAM_MAPPING:
            curve_arguments[curve_key] = self.opts[orig_key]
        scatter_arguments: Dict = {}
        for orig_key, scatter_key in _PLOTDATAITEM_SCATTER_PARAM_MAPPING:
            if orig_key in self.opts:
                scatter_arguments[scatter_key] = self.opts[orig_key]
        if (self.opts.get("pen") is not None
                or (self.opts.get("brush") is not None
                    and self.opts.get("fillLevel") is not None)):
            self.curve.setData(x=x, y=y, **curve_arguments)
            self.curve.show()
        else:
            self.curve.hide()
        if self.opts.get("symbol") is not None:
            data_x_wo_nans, data_y_wo_nans = LivePlotCurve._without_nan_values(x_values=x, y_values=y)
            self.scatter.setData(x=data_x_wo_nans, y=data_y_wo_nans, **scatter_arguments)
            self.scatter.show()
        else:
            self.scatter.hide()

    @staticmethod
    def _without_nan_values(x_values: np.ndarray, y_values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """ Get (if necessary) copies of the array without NaNs

        Strip arrays of x and y values from nan values. If one of the arrays
        has the value nan at the index n, in both arrays the value at index n
        will be removed. This will make sure both arrays will have the same
        length at the end again.

        Args:
            x_values: x-values that should be stripped from NaNs
            y_values: y-values that should be stripped from NaNs

        Returns:
            Copies of the arrays without any nans. If no NaN's are contained,
            the original arrays are returned.
        """
        if x_values.size != y_values.size:
            raise ValueError("The passed arrays have to be the same length.")
        x_nans = np.isnan(x_values)
        y_nans = np.isnan(y_values)
        combined_nans = x_nans | y_nans
        if True in combined_nans:
            return x_values[~combined_nans], y_values[~combined_nans]
        else:
            return x_values, y_values


class CyclicPlotCurve(LivePlotCurve):

    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_source: Union[UpdateSource, LiveCurveDataModel],
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            pen=DEFAULT_COLOR,
            **plotdataitem_kwargs,
    ):
        """
        PlotDataItem extension for the Cyclic Plotting Style

        Displays data as a cyclic plot widget similar to a heart rate
        monitor. The graph itself stays fixed in position and has a fixed length
        that it does not exceed. As soon as the drawing reaches the end, the graph
        gets redrawn beginning from the start. The old curve gets incrementally
        overwritten by the new values. The x-values of all lines in the graph will
        be shifted backwards according to the time span length (like x % time_span_length)
        so the area with the curve does not move.

        Args:
            plot_item: plot item the curve should fit to
            data_source: source the curve receives data from
            buffer_size: count of values the curve's data model's buffer should
                         hold at max
            pen: pen the curve should be drawn with, is part of the plotdataitem
                 base class parameters
            **plotdataitem_kwargs: keyword arguments fo the base class

        Raises:
            ValueError: The passes data source is not usable as a source for data
        """
        super().__init__(
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size,
            pen=pen,
            **plotdataitem_kwargs,
        )
        # Curves after clipping (data actually drawn)
        self._clipped_curve_old: CurveData = CurveData(np.array([]), np.array([]))
        self._clipped_curve_new: CurveData = CurveData(np.array([]), np.array([]))

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        self._update_new_curve_data_item()
        if cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).cycle > 0:
            self._update_old_curve_data_item()
        self._redraw_curve()

    def _redraw_curve(self) -> None:
        """ Redraw the curve with the current data

        For drawing the new and old curve a single PlotCurveItem is used.
        The cut between both curves is achieved with a np.nan value as a
        separator in combination with finite connection passed to the
        PlotCurveItem.
        """
        data_x: np.ndarray = np.array([])
        data_y: np.ndarray = np.array([])
        if (
            self._clipped_curve_new.x_values.size != 0
            and self._clipped_curve_new.y_values.size != 0
        ):
            data_x = np.concatenate((data_x, self._clipped_curve_new.x_values))
            data_y = np.concatenate((data_y, self._clipped_curve_new.y_values))
        if (
            self._clipped_curve_old.x_values.size != 0
            and self._clipped_curve_old.y_values.size != 0
        ):
            if data_x.size != 0 and data_y.size != 0:
                data_x = np.concatenate((data_x, np.array([np.nan])))
                data_y = np.concatenate((data_y, np.array([np.nan])))
            data_x = np.concatenate((data_x, self._clipped_curve_old.x_values))
            data_y = np.concatenate((data_y, self._clipped_curve_old.y_values))
        if data_x.size != 0 and data_y.size != 0:
            self.clear()
            self._set_data(x=data_x, y=data_y)

    def _update_new_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        start = self._parent_plot_item.time_span.start
        end = self._parent_plot_item.last_timestamp
        x_values, y_values = self._data_model.subset_for_xrange(start=start, end=end, interpolated=True)
        self._clipped_curve_new = CurveData(
            x_values=x_values - cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).curr_offset,
            y_values=y_values,
        )

    def _update_old_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        start = self._parent_plot_item.last_timestamp - self._parent_plot_item.time_span.time_span.size
        end = cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).prev_end
        x_values, y_values = self._data_model.subset_for_xrange(start=start, end=end, interpolated=True)
        self._clipped_curve_old = CurveData(
            x_values=x_values - cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).prev_offset,
            y_values=y_values,
        )


class ScrollingPlotCurve(LivePlotCurve):
    """ Scrolling Plot Curve

    A single curve scrolling towards newer timestamps as new values arrive.
    The shown range has always the same length.
    """

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        if self.opts.get("pen", None) is not None:
            # Subset for curve is clipped
            curve_x, curve_y = self._data_model.subset_for_xrange(
                start=self._parent_plot_item.time_span.start,
                end=self._parent_plot_item.time_span.end,
                interpolated=True,
            )
        else:
            # Clipping is not used for scatter plot
            curve_x, curve_y = self._data_model.subset_for_xrange(start=self._parent_plot_item.time_span.start,
                                                                  end=self._parent_plot_item.time_span.end)
        self._set_data(x=curve_x, y=curve_y)
        self._data_item_data = CurveData(x_values=curve_x, y_values=curve_y)
