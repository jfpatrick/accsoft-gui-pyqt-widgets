"""
Module contains different curves that can be added to a PlotItem based on pyqtgraphs PlotDataItem.
"""

import logging
from typing import Dict, Optional
import abc

import numpy as np
import pyqtgraph

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import CurveDataModel
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

_MAX_BUFFER_SIZE = 1000000


class LivePlotCurve(DataModelBasedItem, pyqtgraph.PlotDataItem, metaclass=AbstractDataModelBasedItemMeta):
    """Base class for different live data curves."""

    def __init__(
        self,
        plot_item: pyqtgraph.PlotItem,
        curve_config: LivePlotCurveConfig,
        plot_config: ExPlotWidgetConfig,
        data_source: UpdateSource,
        decorators: CurveDecorators,
        timing_source_attached: bool,
        pen="w",
        **plotdataitem_kwargs,
    ):
        """ Constructor for the base class

        You can use create() for creating a curve fitting to the given config
        """
        DataModelBasedItem.__init__(
            self,
            timing_source_attached=timing_source_attached,
            data_model=CurveDataModel(data_source=data_source),
            parent_plot_item=plot_item,
        )
        pyqtgraph.PlotDataItem.__init__(self, pen=pen, **plotdataitem_kwargs)
        self._parent_plot_item = plot_item
        self._curve_config: LivePlotCurveConfig = curve_config
        self._plot_config: ExPlotWidgetConfig = plot_config
        self._decorators: CurveDecorators = decorators
        # Save drawn data for testing purposes
        self._data_item_data: CurveData
        if pen is not None:
            self.setPen(pen)

    @staticmethod
    def create(
        plot_item: "ExPlotItem",
        data_source: UpdateSource,
        curve_config: LivePlotCurveConfig = LivePlotCurveConfig(),
        **plotdataitem_kwargs,
    ) -> "LivePlotCurve":
        """Factory method for creating curve object fitting to the given plotitem."""
        plot_config = plot_item.plot_config
        unsupported_style = plot_config.plotting_style.value != PlotWidgetStyle.SCROLLING_PLOT.value \
                            and plot_config.plotting_style.value != PlotWidgetStyle.SLIDING_POINTER.value
        if unsupported_style:
            raise TypeError(f"Unsupported plotting style: {plot_config.plotting_style}")
        if plot_config.plotting_style.value == PlotWidgetStyle.SCROLLING_PLOT.value:
            return ScrollingPlotCurve(
                plot_item=plot_item,
                curve_config=curve_config,
                plot_config=plot_config,
                data_source=data_source,
                decorators=CurveDecorators(),
                timing_source_attached=plot_item.timing_source_attached,
                **plotdataitem_kwargs,
            )
        if plot_config.plotting_style.value == PlotWidgetStyle.SLIDING_POINTER.value:
            return SlidingPointerPlotCurve(
                plot_item=plot_item,
                curve_config=curve_config,
                plot_config=plot_config,
                data_source=data_source,
                decorators=CurveDecorators(),
                timing_source_attached=plot_item.timing_source_attached,
                **plotdataitem_kwargs,
            )

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
            **kwargs
    ):
        """Create a new SlidingPointer curve."""
        super().__init__(plot_config=plot_config, **kwargs)
        # Curves after clipping (data actually drawn)
        self._clipped_curve_old: CurveData = CurveData(np.array([]), np.array([]))
        self._clipped_curve_new: CurveData = CurveData(np.array([]), np.array([]))
        size = plot_config.cycle_size
        self._cycle: SlidingPointerCycle = SlidingPointerCycle(size=size)
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
        if data_x.size != 0 and data_y.size != 0:
            data_x = np.concatenate((data_x, np.array([np.nan])))
            data_y = np.concatenate((data_y, np.array([np.nan])))
        if (
            self._clipped_curve_old.x_values.size != 0
            and self._clipped_curve_old.y_values.size != 0
        ):
            data_x = np.concatenate((data_x, self._clipped_curve_old.x_values))
            data_y = np.concatenate((data_y, self._clipped_curve_old.y_values))
        if data_x.size != 0 and data_y.size != 0:
            self.curve.clear()
            self.curve.setData(x=data_x, y=data_y, connect="finite")

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
        **kwargs
    ):
        """Create a new scrolling plot curve. Parameters are the same the ones from the baseclass."""
        super().__init__(plot_config=plot_config, **kwargs)
        self._cycle: ScrollingPlotCycle = ScrollingPlotCycle(
            plot_config=self._plot_config,
            size=plot_config.cycle_size
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
        self.setData({"x": curve_x, "y": curve_y}, connect="finite")
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
