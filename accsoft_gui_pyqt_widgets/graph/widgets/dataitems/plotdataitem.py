"""
Module contains different curves that can be added to a PlotItem based on PyQtGraph's PlotDataItem.
"""

import sys
import logging
from typing import Union, List, Tuple, Dict
import abc

import numpy as np
import pyqtgraph

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import CurveDataModel
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.widgets.datastructures import (
    CurveData,
    CurveDataWithTime,
    CurveDecorators,
    SlidingPointerCurveData
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    LivePlotCurveConfig,
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotcycle import (
    ScrollingPlotCycle,
    SlidingPointerCycle,
)

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

    supported_plotting_styles: List[PlotWidgetStyle] = list(plotting_style_to_class_mapping.keys())

    def __init__(
        self,
        plot_item: pyqtgraph.PlotItem,
        curve_config: LivePlotCurveConfig,
        plot_config: ExPlotWidgetConfig,
        data_source: Union[UpdateSource, CurveDataModel],
        decorators: CurveDecorators,
        timing_source_attached: bool,
        pen="w",
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **plotdataitem_kwargs,
    ):
        """ Constructor for the base class

        Args:
            plot_item: plot item the curve should fit to
            curve_config: configuration object for the curve decorators
            plot_config: configuration of the passed plot item
            data_source: source the curve receives data from
            decorators: object wrapping all curve decorators
            timing_source_attached: flag if a separate source for timing updates is attached to the plot item
            pen: pen the curve should be drawn with
            buffer_size: count of values the curve's data model's buffer should hold at max
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
            timing_source_attached=timing_source_attached,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        pyqtgraph.PlotDataItem.__init__(self, pen=pen, **plotdataitem_kwargs)
        self.opts["connect"] = "finite"
        self._parent_plot_item = plot_item
        self._curve_config: LivePlotCurveConfig = curve_config
        self._plot_config: ExPlotWidgetConfig = plot_config
        self._decorators: CurveDecorators = decorators
        # Save drawn data for testing purposes
        self._data_item_data: CurveData
        if pen is not None:
            self.setPen(pen)

    @staticmethod
    def create_from(
        plot_config: ExPlotWidgetConfig,
        object_to_create_from: "LivePlotCurve",
        **plotdataitem_kwargs,
    ) -> "LivePlotCurve":
        """Factory method for creating curve object fitting the requested style"""
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LivePlotCurve.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        if not plotdataitem_kwargs:
            plotdataitem_kwargs = object_to_create_from.opts
        return item_class(
            start=object_to_create_from._cycle.start,
            plot_item=object_to_create_from._parent_plot_item,
            curve_config=object_to_create_from._curve_config,
            plot_config=plot_config,
            data_source=object_to_create_from._data_model,
            decorators=object_to_create_from._decorators,
            timing_source_attached=object_to_create_from._timing_source_attached,
            **plotdataitem_kwargs,
        )

    @staticmethod
    def create(
        plot_item: "ExPlotItem",
        data_source: UpdateSource,
        curve_config: LivePlotCurveConfig = LivePlotCurveConfig(),
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
            curve_config: configuration object for the new item
            **buffer_size: keyword arguments for the items baseclass

        Returns:
            the created item
        """
        plot_config = plot_item.plot_config
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LivePlotCurve.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            curve_config=curve_config,
            plot_config=plot_config,
            data_source=data_source,
            decorators=CurveDecorators(),
            timing_source_attached=plot_item.timing_source_attached,
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

    # ~~~~~~~~~~~~~~~~~ Getter functions ~~~~~~~~~~~~~~~~~~

    # TODO: Convert to properties
    def get_decorators(self) -> CurveDecorators:
        """Return Curve Decorators associated to this curve"""
        return self._decorators

    def get_conf(self) -> LivePlotCurveConfig:
        """Get configuration for this particular curve"""
        return self._curve_config

    # ~~~~~~~~~~~~~~~~~ Private functions ~~~~~~~~~~~~~~~~~

    @abc.abstractmethod
    def _redraw_curve(self) -> None:
        """ Redraw the curve with the current parameters

        Returns:
            None
        """
        pass

    def _redraw_decorators(self, curve: CurveData) -> None:
        """Draw all decorators at the given position, if they have been created.

        Args:
            x_pos: X-Position to move the decorators to
            y_pos: Y-Position to move the decorators to
        """
        x_pos = curve.x_values[-1] if curve.x_values.size != 0 else self._cycle.start
        y_pos = curve.y_values[-1] if curve.y_values.size != 0 else 0
        potential_pen = self.opts.get("pen", None)
        if self._decorators.vertical_line is not None:
            self._decorators.vertical_line.setValue(x_pos)
            if (
                self._decorators.vertical_line.currentPen != potential_pen
                and potential_pen is not None
            ):
                self._decorators.vertical_line.setPen(potential_pen)
        if self._decorators.horizontal_line is not None:
            self._decorators.horizontal_line.setValue(y_pos)
            if (
                self._decorators.horizontal_line.currentPen != potential_pen
                and potential_pen is not None
            ):
                self._decorators.horizontal_line.setPen(potential_pen)
        if self._decorators.point is not None:
            self._decorators.point.setData({"x": [x_pos], "y": [y_pos]})
            if (
                self._decorators.point.opts["symbolPen"] != potential_pen
                and potential_pen is not None
            ):
                self._decorators.point.setSymbolPen(potential_pen)


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

    def __init__(
            self,
            plot_config: ExPlotWidgetConfig = ExPlotWidgetConfig(),
            start: float = np.nan,
            **kwargs
    ):
        """Create a new SlidingPointer curve."""
        super().__init__(plot_config=plot_config, **kwargs)
        # Curves after clipping (data actually drawn)
        self._clipped_curve_old: CurveData = CurveData(np.array([]), np.array([]))
        self._clipped_curve_new: CurveData = CurveData(np.array([]), np.array([]))
        size = plot_config.cycle_size
        self._cycle: SlidingPointerCycle = SlidingPointerCycle(
            start=start,
            size=size
        )
        self._first_time_update = True

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

    def update_timestamp(self, new_timestamp: float) -> None:
        """Handle a new timestamp

        Handle a update in the current time triggered by f.e. the timing source.
        With the new timestamp the data subset for the new and old curve are
        updated, clipped and drawn. If the timestamp is older than the current
        known one, it will be ignored and interpreted as delivered too late

        Args:
            new_timestamp (float): The new published timestamp
        """
        if new_timestamp >= self._last_timestamp:
            self._last_timestamp = new_timestamp
            self._handle_initial_time_update()
            self._cycle.number = (
                int(new_timestamp - self._cycle.start) // self._cycle.size
            )
            self._update_new_curve_data_item()
            if self._cycle.number > 0:
                self._update_old_curve_data_item()
            self._redraw_curve()
            self._redraw_decorators(self._clipped_curve_new)

    def _handle_initial_time_update(self) -> None:
        """Handle the first ever timing update received from the timing source

        As soon as the first timestamp is available, cycle information like
        start and end can be set and according decorators are added.
        """
        if self._first_time_update:
            self._first_time_update = False
            if self._cycle.start == 0.0:
                self._cycle.start = self._cycle.get_current_time_line_x_pos(
                    self._last_timestamp
                )
                self._cycle.end = self._cycle.start + self._cycle.size * (
                    self._cycle.number + 1
                )

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
        start = self._cycle.get_current_cycle_start_timestamp()
        end = self._last_timestamp
        x_values, y_values = self._data_model.get_clipped_subset(
            start=start, end=end
        )
        self._clipped_curve_new = CurveData(
            x_values=x_values - self._cycle.get_current_cycle_offset(),
            y_values=y_values,
        )

    def _update_old_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        start = self._last_timestamp - self._cycle.size
        end = self._cycle.get_previous_cycle_end_timestamp()
        x_values, y_values = self._data_model.get_clipped_subset(
            start=start, end=end
        )
        self._clipped_curve_old = CurveData(
            x_values=x_values - self._cycle.get_previous_cycle_offset(),
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
            start=self._cycle.get_current_cycle_start_timestamp(),
            end=self._cycle.get_current_cycle_end_timestamp(),
        )
        return CurveDataWithTime(
            timestamps=x_values,
            x_values=x_values - self._cycle.get_current_cycle_offset(),
            y_values=y_values,
        )

    def get_old_curve_buffer(self) -> CurveDataWithTime:
        """
        Return a list of points (without interpolating the ends)
        from the data model that are part of the old curve.
        """
        x_values, y_values = self._data_model.get_subset(
            start=self._cycle.get_previous_cycle_start_timestamp(),
            end=self._cycle.get_previous_cycle_end_timestamp(),
        )
        return CurveDataWithTime(
            timestamps=x_values,
            x_values=x_values - self._cycle.get_previous_cycle_offset(),
            y_values=y_values,
        )

    def get_cycle(self) -> "SlidingPointerCycle":
        """return the object holding all information about the the cycle"""
        return self._cycle

    def get_last_time_stamp(self) -> float:
        """Return last timestamp received by the curve"""
        return self._last_timestamp


class ScrollingPlotCurve(LivePlotCurve):
    """ Scrolling Plot Curve

    A single curve scrolling towards newer timestamps as new values arrive.
    The shown range has always the same length.
    """

    def __init__(
        self,
        plot_config: ExPlotWidgetConfig = ExPlotWidgetConfig(),
        start: float = np.nan,
        **kwargs
    ):
        """Create a new scrolling plot curve. Parameters are the same the ones from the baseclass."""
        super().__init__(plot_config=plot_config, **kwargs)
        self._cycle: ScrollingPlotCycle = ScrollingPlotCycle(
            plot_config=self._plot_config,
            start=start,
            size=plot_config.cycle_size,
        )

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

    def update_timestamp(self, new_timestamp: float) -> None:
        """Handle a new published timestamp

        Handle a new arriving timestamp and trigger changes in the shown data
        according to new time-information..
        The shown curve will be clipped on both ends according to the passed
        timestamp.

        Args:
            new_timestamp (float): Current time as timestamp
        """
        if new_timestamp >= self._last_timestamp:
            self._last_timestamp = new_timestamp
            self._redraw_curve()
            self._redraw_decorators(self._data_item_data)

    def _redraw_curve(self) -> None:
        """Update the actual drawn data

        Update the data for the inner PlotDataItem and clip the resulting
        curves at the required positions for not overdrawing boundaries.
        """
        self._cycle.update_cycle(self._last_timestamp)
        if self.opts.get("pen", None) is not None:
            # Subset for curve is clipped
            curve_x, curve_y = self._data_model.get_clipped_subset(
                start=self._cycle.start, end=self._cycle.end
            )
        else:
            # Clipping is not used for scatter plot
            curve_x, curve_y = self._data_model.get_subset(
                start=self._cycle.start, end=self._cycle.end
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
