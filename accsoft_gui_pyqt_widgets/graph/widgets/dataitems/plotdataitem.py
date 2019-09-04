"""
Module contains different curves that can be added to a PlotItem based on PyQtGraph's PlotDataItem.
"""

import sys
import logging
from typing import Union, List, Tuple, Dict
from copy import copy

import numpy as np
import pyqtgraph

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import CurveDataModel
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import DEFAULT_COLOR
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import (
    CurveData,
    CurveDataWithTime,
    SlidingPointerCurveData
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accsoft_gui_pyqt_widgets.graph.widgets.plotitem import ExPlotItem

_LOGGER = logging.getLogger(__name__)

# which plotting style is achieved by which class
plotting_style_to_class_mapping = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingPlotCurve",
    PlotWidgetStyle.SLIDING_POINTER: "SlidingPointerPlotCurve",
}

# params accepted by the plotdataitem and their fitting params in the curve-item
_plotdataitem_curve_param_mapping = [
    ("pen", "pen"),
    ("shadowPen", "shadowPen"),
    ("fillLevel", "fillLevel"),
    ("fillBrush", "brush"),
    ("antialias", "antialias"),
    ("connect", "connect"),
    ("stepMode", "stepMode"),
]

# params accepted by the plotdataitem and their fitting params in the scatter-plot-item
_plotdataitem_scatter_param_mapping = [
    ("symbolPen", "pen"),
    ("symbolBrush", "brush"),
    ("symbol", "symbol"),
    ("symbolSize", "size"),
    ("data", "data"),
    ("pxMode", "pxMode"),
    ("antialias", "antialias"),
]


class LivePlotCurve(DataModelBasedItem, pyqtgraph.PlotDataItem, metaclass=AbstractDataModelBasedItemMeta):
    """Base class for different live data curves."""

    supported_plotting_styles: List[int] = [*plotting_style_to_class_mapping]

    def __init__(
        self,
        plot_item: "ExPlotItem",
        data_source: Union[UpdateSource, CurveDataModel],
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        pen=DEFAULT_COLOR,
        **plotdataitem_kwargs,
    ):
        """ Constructor for the base class

        Args:
            plot_item: plot item the curve should fit to
            data_source: source the curve receives data from
            buffer_size: count of values the curve's data model's buffer should hold at max
            pen: pen the curve should be drawn with, is part of the plotdataitem baseclass parameters
            **plotdataitem_kwargs: keyword arguments fo the base class
        """
        if isinstance(data_source, UpdateSource):
            data_model = CurveDataModel(
                data_source=data_source,
                buffer_size=buffer_size,
            )
        elif isinstance(data_source, CurveDataModel):
            data_model = data_source
        else:
            raise ValueError(
                f"Data Source of type {type(data_source)} can not be used as a source or model for data."
            )
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        pyqtgraph.PlotDataItem.__init__(self, pen=pen, **plotdataitem_kwargs)
        self.opts["connect"] = "finite"
        # Save drawn data for testing purposes
        self._data_item_data: CurveData
        if pen is not None:
            self.setPen(pen)

    @staticmethod
    def create_from(
        object_to_create_from: "LivePlotCurve",
        **plotdataitem_kwargs,
    ) -> "LivePlotCurve":
        """
        Recreate graph item from existing one. The datamodel is shared, but the new graph item
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
            supported_styles=LivePlotCurve.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        # Take opts from old item except ones passed explicitly
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(plotdataitem_kwargs)
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
        **plotdataitem_kwargs,
    ) -> "LivePlotCurve":
        """Factory method for creating curve object fitting to the given plotitem.

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plotitem by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's datamodel's buffer should hold at max
            **buffer_size: keyword arguments for the items baseclass

        Returns:
            the created item
        """
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_item.plot_config,
            supported_styles=LivePlotCurve.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_item.plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size,
            **plotdataitem_kwargs,
        )

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
        for orig_key, curve_key in _plotdataitem_curve_param_mapping:
            curve_arguments[curve_key] = self.opts[orig_key]
        scatter_arguments: Dict = {}
        for orig_key, scatter_key in _plotdataitem_scatter_param_mapping:
            if orig_key in self.opts:
                scatter_arguments[scatter_key] = self.opts[orig_key]
        if self.opts.get("pen") is not None or (self.opts.get("brush") is not None and self.opts.get("fillLevel") is not None):
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


class SlidingPointerPlotCurve(LivePlotCurve):
    """PlotDataItem extension for the Sliding Pointer Plotting Style

    Displays data as a sliding pointer widget similar to a heart rate
    monitor. The graph itself stays fixed in position and has a fixed length
    that it does not exceed. As soon as the drawing reaches the end, the graph
    gets redrawn beginning from the start. The old curve gets incrementally
    overwritten by the new values. The x-values of all lines in the graph will
    be shifted backwards according to the cycle length (like x % cycle_length)
    so the area with the curve does not move.
    """

    def __init__(self, **kwargs):
        """Create a new SlidingPointer curve."""
        super().__init__(**kwargs)
        # Curves after clipping (data actually drawn)
        self._clipped_curve_old: CurveData = CurveData(np.array([]), np.array([]))
        self._clipped_curve_new: CurveData = CurveData(np.array([]), np.array([]))

    def equals(self, other: "SlidingPointerPlotCurve") -> bool:
        """Compare two Sliding Pointer Curves's content

        Explanation why not __eq__():

        Class needs to be hashable since it is used as a key in PyQtGraph
        If we would override the __eq__ function based on the values of
        the object we would either make the class not hashable or hashable
        based on the values of the object, since A == B -> hash(A) == hash(B),
        which would not be the case if we hash by identity. Such an
        implementation would lead to a modifiable object hash, which is definitely
        not what we want.
        """
        if (self.__class__ != other.__class__
            or other.get_full_buffer() != self.get_full_buffer()
            or other.get_new_curve_buffer() != self.get_new_curve_buffer()
            or other.get_old_curve_buffer() != self.get_old_curve_buffer()
        ):
            return False
        try:
            return (
                np.allclose(
                    other.get_last_drawn_data().old_curve.y_values,
                    self.get_last_drawn_data().old_curve.y_values,
                ) and np.allclose(
                    other.get_last_drawn_data().old_curve.x_values,
                    self.get_last_drawn_data().old_curve.x_values,
                ) and np.allclose(
                    other.get_last_drawn_data().new_curve.x_values,
                    self.get_last_drawn_data().new_curve.x_values,
                ) and np.allclose(
                    other.get_last_drawn_data().new_curve.y_values,
                    self.get_last_drawn_data().new_curve.y_values,
                )
            )
        except ValueError:
            return False

    def update_item(self) -> None:
        """Update item based on the plot items cycle information"""
        self._update_new_curve_data_item()
        if self._parent_plot_item.cycle.number > 0:
            self._update_old_curve_data_item()
        self._redraw_curve()

    def _redraw_curve(self) -> None:
        """ Redraw the curve with the current data

        For drawing the new and old curve a single PlotCurveItem is used.
        The cut between both curves is achieved with a np.nan value as a
        separator in combination with finite connection passed to the
        PlotCurveItem.

        Returns:
            None
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
        start = self._parent_plot_item.cycle.current_cycle_start_timestamp
        end = self._parent_plot_item.last_timestamp
        x_values, y_values = self._data_model.get_clipped_subset(
            start=start, end=end
        )
        self._clipped_curve_new = CurveData(
            x_values=x_values - self._parent_plot_item.cycle.current_cycle_offset,
            y_values=y_values,
        )

    def _update_old_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        start = self._parent_plot_item.last_timestamp - self._parent_plot_item.cycle.size
        end = self._parent_plot_item.cycle.previous_cycle_end_timestamp
        x_values, y_values = self._data_model.get_clipped_subset(
            start=start, end=end
        )
        self._clipped_curve_old = CurveData(
            x_values=x_values - self._parent_plot_item.cycle.previous_cycle_offset,
            y_values=y_values,
        )

    # Testing utilities

    def get_last_drawn_data(self) -> SlidingPointerCurveData:
        """Return a dictionary holding the data passed to the PlotDataItem. This
        can be used to find out, what the PlotDataItems are showing.

        Returns:
            Dictionary mapping the description where the points are displayed to
            a list of points
        """
        return SlidingPointerCurveData(
            self._clipped_curve_old,
            self._clipped_curve_new
        )

    def get_full_buffer(self) -> CurveDataWithTime:
        """
        Get the full curve that is saved in the data model.
        """
        x_values, y_values = self._data_model.get_full_data_buffer()
        return CurveDataWithTime(
            timestamps=x_values, x_values=np.array([]), y_values=y_values
        )

    def get_new_curve_buffer(self) -> CurveDataWithTime:
        """
        Return a list of points (without interpolating the ends)
        from the data model that are part of the new curve.
        """
        x_values, y_values = self._data_model.get_subset(
            start=self._parent_plot_item.cycle.current_cycle_start_timestamp,
            end=self._parent_plot_item.cycle.current_cycle_end_timestamp,
        )
        return CurveDataWithTime(
            timestamps=x_values,
            x_values=x_values - self._parent_plot_item.cycle.current_cycle_offset,
            y_values=y_values,
        )

    def get_old_curve_buffer(self) -> CurveDataWithTime:
        """
        Return a list of points (without interpolating the ends)
        from the data model that are part of the old curve.
        """
        x_values, y_values = self._data_model.get_subset(
            start=self._parent_plot_item.cycle.previous_cycle_start_timestamp,
            end=self._parent_plot_item.cycle.previous_cycle_end_timestamp,
        )
        return CurveDataWithTime(
            timestamps=x_values,
            x_values=x_values - self._parent_plot_item.cycle.previous_cycle_offset,
            y_values=y_values,
        )

    def get_last_time_stamp(self) -> float:
        """Return last timestamp received by the curve"""
        return self._parent_plot_item.last_timestamp


class ScrollingPlotCurve(LivePlotCurve):
    """ Scrolling Plot Curve

    A single curve scrolling towards newer timestamps as new values arrive.
    The shown range has always the same length.
    """

    def equals(self, other: "ScrollingPlotCurve") -> bool:
        """Compare two Scrolling Plot Curves's data

        Explanation why not __eq__():

        Class needs to be hashable since it is used as a key in PyQtGraph
        If we would override the __eq__ function based on the values of
        the object we would either make the class not hashable or hashable
        based on the values of the object, since A == B -> hash(A) == hash(B),
        which would not be the case if we hash by identity. Such an
        implementation would lead to a modifiable object hash, which is definitely
        not what we want.
        """
        return (
            self.__class__ == other.__class__
            and self.get_full_buffer() == other.get_full_buffer()
            and self.get_last_drawn_data() == other.get_last_drawn_data()
        )

    def update_item(self) -> None:
        """Update item based on the plot items cycle information"""
        if self.opts.get("pen", None) is not None:
            # Subset for curve is clipped
            curve_x, curve_y = self._data_model.get_clipped_subset(
                start=self._parent_plot_item.cycle.start, end=self._parent_plot_item.cycle.end
            )
        else:
            # Clipping is not used for scatter plot
            curve_x, curve_y = self._data_model.get_subset(
                start=self._parent_plot_item.cycle.start, end=self._parent_plot_item.cycle.end
            )
        self._set_data(x=curve_x, y=curve_y)
        self._data_item_data = CurveData(x_values=curve_x, y_values=curve_y)

    def get_full_buffer(self):
        """
        Get the full curve that is saved in the data model.
        """
        x_values, y_values = self._data_model.get_full_data_buffer()
        return CurveDataWithTime(
            timestamps=x_values, x_values=np.array([]), y_values=y_values
        )

    def get_last_drawn_data(self) -> CurveData:
        """Get the data of the curve actually passed to draw"""
        return self._data_item_data
