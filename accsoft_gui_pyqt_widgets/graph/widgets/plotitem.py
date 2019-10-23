"""
Base class for modified PlotItems that handle data displaying in the ExtendedPlotWidget
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, Type
from itertools import product

import numpy as np
import pyqtgraph as pg
from pyqtgraph.GraphicsScene.mouseEvents import MouseDragEvent
from qtpy.QtCore import Signal, Slot, QRectF
from qtpy.QtWidgets import QGraphicsSceneWheelEvent

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.axisitems import (
    CustomAxisItem,
    RelativeTimeAxisItem,
    TimeAxisItem
)
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.bargraphitem import (
    LiveBarGraphItem,
)
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
)
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.timestampmarker import (
    LiveTimestampMarker,
)
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.injectionbaritem import (
    LiveInjectionBarGraphItem,
)
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.plotdataitem import (
    LivePlotCurve,
    ScrollingPlotCurve
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import PointData
from accsoft_gui_pyqt_widgets.graph.widgets.plottimespan import ScrollingPlotTimeSpan, SlidingPointerTimeSpan, PlottingTimeSpan

_LOGGER = logging.getLogger(__name__)


# Mapping of plotting styles to a fitting axis style
_STYLE_TO_AXIS_MAPPING: Dict[int, Type[pg.AxisItem]] = {
    PlotWidgetStyle.STATIC_PLOT: CustomAxisItem,
    PlotWidgetStyle.SLIDING_POINTER: RelativeTimeAxisItem,
    PlotWidgetStyle.SCROLLING_PLOT: TimeAxisItem,
}


# Mapping of plotting styles to a fitting time span
_STYLE_TO_TIMESPAN_MAPPING: Dict[int, Optional[Type[PlottingTimeSpan]]] = {
    PlotWidgetStyle.STATIC_PLOT: None,
    PlotWidgetStyle.SLIDING_POINTER: SlidingPointerTimeSpan,
    PlotWidgetStyle.SCROLLING_PLOT: ScrollingPlotTimeSpan,
}


class ExPlotItem(pg.PlotItem):
    """PlotItem with additional functionality"""

    def __init__(
        self,
        config: ExPlotWidgetConfig = None,
        timing_source: Optional[UpdateSource] = None,
        axis_items: Optional[Dict[str, pg.AxisItem]] = None,
        **plotitem_kwargs,
    ):
        """Create a new plot item.

        Args:
            config: Configuration for the new plotitem
            timing_source: Source for timing updates
            **plotitem_kwargs: Keyword Arguments that will be passed to PlotItem
        """
        # Pass modified axis for the multilayer movement to function properly
        config = config or ExPlotWidgetConfig()
        if axis_items is None:
            axis_items = {}
        axis_items["left"] = CustomAxisItem(orientation="left")
        axis_items["right"] = CustomAxisItem(orientation="right")
        axis_items["bottom"] = axis_items.get(
            "bottom", self.create_fitting_axis_item(
                config_style=config.plotting_style,
                orientation="bottom"
            )
        )
        axis_items["top"] = axis_items.get(
            "top", self.create_fitting_axis_item(
                config_style=config.plotting_style,
                orientation="top"
            )
        )
        super().__init__(
            axisItems=axis_items,
            viewBox=ExViewBox(),
            **plotitem_kwargs
        )
        self._plot_config: ExPlotWidgetConfig = config
        self._time_span: Optional[PlottingTimeSpan] = self.create_fitting_time_span()
        self._last_timestamp: float = -1.0
        self._time_line: Optional[pg.InfiniteLine] = None
        self._style_specific_objects_already_drawn: bool = False
        self._layers: PlotItemLayerCollection
        self._timing_source_attached: bool
        # Needed for the Sliding Pointer Curve
        self._time_span_start_boundary: Optional[pg.InfiniteLine] = None
        self._time_span_end_boundary: Optional[pg.InfiniteLine] = None
        self._prepare_layers()
        self._prepare_timing_source_attachment(timing_source)
        # If set to false, this flag prevents the scrolling movement on an
        # scrolling plot with a fixed range.
        self._scrolling_fixed_x_range_activated: bool = True
        self._prepare_scrolling_plot_fixed_x_range()
        # This will only be used in combination with the singleCurveValueSlot
        self.single_curve_value_slot_source: Optional[UpdateSource] = None
        self.single_curve_value_slot_curve: Optional[ScrollingPlotCurve] = None

    def _prepare_layers(self):
        """Initialize everything needed for multiple layers"""
        self._layers: PlotItemLayerCollection = PlotItemLayerCollection(self)
        self._layers.add(
            PlotItemLayer(
                plot_item=self,
                view_box=self.vb,
                axis_item=self.getAxis("left"),
                identifier=PlotItemLayer.default_layer_identifier,
            )
        )
        self.vb.sigResized.connect(self.update_layers)
        if isinstance(self.vb, ExViewBox):
            self.vb.set_layer_collection(self._layers)
        self.link_y_range_of_all_layers(link=True)

    def _prepare_timing_source_attachment(self, timing_source: Optional[UpdateSource]):
        """Initialized everything needed for connection to the timing-source"""
        if timing_source:
            self._timing_source_attached = True
            timing_source.sig_timing_update.connect(self.handle_timing_update)
        else:
            self._timing_source_attached = False

    @property
    def timing_source_attached(self):
        """Return bool that indicates, if the plot is attached to a timing source"""
        return self._timing_source_attached

    @property
    def last_timestamp(self):
        """Return the latest timestamp that is known to the plot"""
        return self._last_timestamp

    def _prepare_scrolling_plot_fixed_x_range(self) -> None:
        """
        In the scrolling style the PlotItem offers the possibility to set the
        scrolling movement not by using PyQtGraph's auto ranging, but by setting
        it manually to a fixed x range that moves as new data is appended. This
        will require some modifications to the plot which would otherwise collide
        with this behavior (mainly related to auto ranging).
        """
        self._scrolling_fixed_x_range_activated = True
        if self._config_contains_scrolling_style_with_fixed_x_range():
            self._set_scrolling_plot_fixed_x_range_modifications()
        else:
            self._reset_scrolling_plot_fixed_x_range_modifications()

    def _set_scrolling_plot_fixed_x_range_modifications(self) -> None:
        """
        Activating the fixed x range on a plot item in the scrolling mode
        will result in behavior modifications related to auto ranging.

        These include:
            - 'View All' context menu entry respects the manually set x range
            - the small auto range button on the lower left corner of the plot does
              not simply activate auto range but behaves as 'View All'
        """
        scrolling_range_reset_button = pg.ButtonItem(pg.pixmaps.getPixmap('auto'), 14, self)
        scrolling_range_reset_button.mode = 'auto'
        scrolling_range_reset_button.clicked.connect(self._auto_range_with_scrolling_plot_fixed_x_range)
        self.vb.sigRangeChangedManually.connect(self._handle_zoom_with_scrolling_plot_fixed_x_range)
        self._orig_autoBtn = self.autoBtn
        self.autoBtn = scrolling_range_reset_button
        try:
            self.vb.menu.viewAll.triggered.disconnect(self.autoRange)
        except TypeError:
            pass
        self.vb.menu.viewAll.triggered.connect(self._auto_range_with_scrolling_plot_fixed_x_range)

    def _reset_scrolling_plot_fixed_x_range_modifications(self) -> None:
        """
        Activating the fixed x range on an plot item in the scrolling mode
        will result in modifications related to auto ranging. This function
        will revert all these made changes, if they were made.

        Following modifications are reset:
            - 'View All' context menu entry
            - the small auto range button in the lower left corner of the plot
        """
        try:
            self.autoBtn = self._orig_autoBtn
            self.vb.sigRangeChangedManually.disconnect(self._handle_zoom_with_scrolling_plot_fixed_x_range)
        # AttributeError -> self._orig_autoBtn
        # TypeError      -> failed disconnect
        except (AttributeError, TypeError):
            pass
        try:
            self.vb.menu.viewAll.triggered.disconnect(self._auto_range_with_scrolling_plot_fixed_x_range)
            self.vb.menu.viewAll.triggered.connect(self.autoRange)
        # TypeError -> failed disconnect
        except TypeError:
            pass

    def _auto_range_with_scrolling_plot_fixed_x_range(self):
        """
        autoRange does not know about the x range that has been set manually.
        This function will automatically set the y range and will set the x range
        fitting to the plots configuration.
        """
        self.autoRange(auto_range_x_axis=False)
        self._scrolling_fixed_x_range_activated = True
        self._handle_scrolling_plot_fixed_x_range_update()

    def _handle_zoom_with_scrolling_plot_fixed_x_range(self) -> None:
        """
        If the range changes on a scrolling plot with a fixed x range, the scrolling
        should be stopped. This function sets a flag, that prevents the plot from
        scrolling on updates.
        """
        self._scrolling_fixed_x_range_activated = False

    def update_configuration(self, config: ExPlotWidgetConfig) -> None:
        """Update the plot widgets configuration

        Items that are affected from the configuration change are recreated with
        the new configuration and their old datamodels, so once displayed data is
        not lost. Items that are not affected by the configuration change, mainly
        pure PyQtGraph items, that were added to the plot, are not affected by this
        and will be kept unchanged in the plot.
        """
        if hasattr(self, "_plot_config") and self._plot_config is not None:
            if (
                self._plot_config.time_span != config.time_span
                or self._plot_config.scrolling_plot_fixed_x_range_offset != config.scrolling_plot_fixed_x_range_offset
                or self._plot_config.plotting_style != config.plotting_style
            ):
                self._plot_config = config
                self._remove_child_items_affected_from_style_change()
                self._recreate_child_items_with_new_config()
                self._time_span = self.create_fitting_time_span()
                self._update_decorators()
                self._update_bottom_and_top_axis_style(style=config.plotting_style)
            elif self.plot_config.time_progress_line != config.time_progress_line:
                self._plot_config = config
                if config.time_progress_line:
                    self._init_time_line_decorator(timestamp=self._last_timestamp, force=True)
                else:
                    self.removeItem(self._time_line)
                    self._time_line = None
        self._plot_config = config
        self._prepare_scrolling_plot_fixed_x_range()
        self._handle_scrolling_plot_fixed_x_range_update()

    def _remove_child_items_affected_from_style_change(self):
        """ Remove all items that are affected by a new configuration

        Remove all items attached to live data that depend on the plot item's PlottingStyle.
        Items in the plot that are not based on a datamodel and with that not attached to live
        data won't be removed (especially pure PyQtGraph items).
        Additionally all plotting style specific elements like time span boundaries or timing lines
        are removed.
        """
        for layer, item in product(self._layers.get_all(), self.get_all_data_model_based_items()):
            if item.get_layer_identifier() == layer.identifier:
                layer.view_box.removeItem(item)
        self.removeItem(self._time_line)
        if self._time_span is not None:
            for item in [self._time_span_start_boundary, self._time_span_end_boundary]:
                if item is not None:
                    self.removeItem(item)
        self._time_line = None
        self._time_span_start_boundary = None
        self._time_span_end_boundary = None

    def _recreate_child_items_with_new_config(self):
        """
        Replace all items with ones that fit the given config.
        Datamodels are preserved.

        **IMPORTANT**: for this, the items have to be still listed in **PlotItem.items**,
        if they are not, they will not be recreated. After successful recreation the old
        items are removed from PlotItem.items
        """
        for item in self.get_all_data_model_based_items():
            if hasattr(item, "create_from"):
                new_item = item.create_from(object_to_create_from=item)
                layer = item.get_layer_identifier()
                self.addItem(layer=layer, item=new_item)
                self.removeItem(item)

    def _update_decorators(self) -> None:
        """Update the decorators f.e. line representing current timestamp, time span boundaries"""
        if self._last_timestamp:
            self._style_specific_objects_already_drawn = False
            self._draw_style_specific_objects()
        # we have to recreate the new
        self._init_time_line_decorator(timestamp=self._last_timestamp, force=True)

    @property
    def plot_config(self) -> ExPlotWidgetConfig:
        """Configuration of time span and other plot related parameters"""
        return self._plot_config

    @property
    def time_span(self):
        """time span for the current plot"""
        return self._time_span

    def plot(
        self,
        *args,
        clear: bool = False,
        params: Optional[Dict[str, Any]] = None,
     ) -> None:
        """
        Plotting curves in the ExPlotItem should not be done with PlotItem.plot . For plotting
        curve either use ExPlotItem.addCurve or create a curve (PlotDataItem, LivePlotCurve...)
        by hand and add it with ExPlotItem.addItem.

        Add and return a new plot.
        See :func:`PlotDataItem.__init__ <pyqtgraph.PlotDataItem.__init__>` for data arguments

        Extra allowed arguments are:
            clear    - clear all plots before displaying new data
            params   - meta-parameters to associate with this data
        """
        _LOGGER.warning("PlotItem.plot should not be used for plotting curves with the ExPlotItem, "
                        "please use ExPlotItem.addCurve for this purpose.")
        pg.PlotItem.plot(*args, clear=clear, params=params)

    def addCurve(
        self,
        c: Optional[pg.PlotDataItem] = None,
        params: Optional[Dict[str, Any]] = None,
        data_source: Optional[UpdateSource] = None,
        layer_identifier: Optional[str] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **plotdataitem_kwargs,
    ) -> pg.PlotDataItem:
        """Add new curve for live data

        Create a new curve either from static data like PlotItem.plot or a curve
        attached to a live data source.

        Args:
            c: PlotDataItem instance that is added, for backwards compatibility to the original function
            params: params for c, for backwards compatibility to the original function
            data_source: source for new data that the curve should display
            layer_identifier: identifier of the layer the new curve is supposed to be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **plotdataitem_kwargs: Parameters for creating a pure pyqtgraph PlotDataItem

        Returns:
            PlotDataItem or LivePlotCurve instance depending on the passed parameters
        """
        # Catch calls from superclasses deprecated addCurve() expecting a PlotDataItem
        if c and isinstance(c, pg.PlotDataItem):
            _LOGGER.warning("Calling addCurve() for adding an already created PlotDataItem is deprecated, "
                            "please use addItem() for this purpose.")
            params = params or {}
            self.addItem(c, **params)
            return c
        # Create new curve and add it
        else:
            if layer_identifier == "" or layer_identifier is None:
                layer_identifier = PlotItemLayer.default_layer_identifier
            # create curve that is attached to live data
            new_plot: pg.PlotDataItem
            if data_source is not None:
                new_plot = LivePlotCurve.create(
                    plot_item=self,
                    data_source=data_source,
                    buffer_size=buffer_size,
                    **plotdataitem_kwargs,
                )
            elif data_source is None:
                new_plot = pg.PlotDataItem(
                    **plotdataitem_kwargs
                )
            self.addItem(layer=layer_identifier, item=new_plot)
            return new_plot

    def addBarGraph(
        self,
        data_source: Optional[UpdateSource] = None,
        layer_identifier: Optional[str] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **bargraph_kwargs,
    ) -> LiveBarGraphItem:
        """Add a new bargraph attached to a live data source

        Args:
            data_source (UpdateSource): Source emmiting new data the graph should show
            layer_identifier (Optional[str]): Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **bargraph_kwargs: keyword arguments for the BarGraphItem base class

        Returns:
            LiveBarGraphItem that was added to the plot
        """
        new_plot: pg.BarGraphItem
        if data_source is not None:
            new_plot = LiveBarGraphItem.create(
                plot_item=self,
                data_source=data_source,
                buffer_size=buffer_size,
                **bargraph_kwargs,
            )
        else:
            new_plot = pg.BarGraphItem(**bargraph_kwargs)
        if not layer_identifier:
            layer_identifier = ""
        self.addItem(layer=layer_identifier, item=new_plot)
        return new_plot

    def addInjectionBar(
        self,
        data_source: UpdateSource,
        layer_identifier: Optional[str] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **errorbaritem_kwargs,
    ) -> LiveInjectionBarGraphItem:
        """Add a new injection bar graph for live data

        A new injection-bar graph with a datamodel that receives data from the passed source will
        be added to the plotitem

        Args:
            data_source (UpdateSource): Source for data related updates
            layer_identifier (Optional[str]): Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **errorbaritem_kwargs: Keyword arguments for the ErrorBarItems used in the Injectionbars

        Returns:
            New item that was added to the plot
        """
        new_plot: LiveInjectionBarGraphItem = LiveInjectionBarGraphItem.create(
            plot_item=self,
            data_source=data_source,
            buffer_size=buffer_size,
            **errorbaritem_kwargs,
        )
        if not layer_identifier:
            layer_identifier = ""
        self.addItem(layer=layer_identifier, item=new_plot)
        return new_plot

    def addTimestampMarker(
        self,
        *graphicsobjectargs,
        data_source: UpdateSource,
        buffer_size: int = DEFAULT_BUFFER_SIZE
    ) -> LiveTimestampMarker:
        """Add a infinite line item for live data

        A new bar graph with a datamodel that receives data from the passed source will
        be added to the plotitem

        Args:
            data_source (UpdateSource): Source for data related updates,
            buffer_size: maximum count of values the datamodel buffer should hold
            *graphicsobjectargs: Arguments passed to the GraphicsObject base class

        Returns:
            New item that was created
        """
        new_plot: LiveTimestampMarker = LiveTimestampMarker.create(
            *graphicsobjectargs,
            plot_item=self,
            data_source=data_source,
            buffer_size=buffer_size
        )
        self.addItem(layer="", item=new_plot)
        return new_plot

    def clear(self):
        """
        Clear the PlotItem but reinitialize items that are part of the plot.
        These items contain f.e. the time line decorator.
        """
        super().clear()
        self._init_time_line_decorator(timestamp=self._last_timestamp, force=True)

    # ~~~~~~~~~~~~~~~~~~~~~~ Layers ~~~~~~~~~~~~~~~~~~~~~~~~

    def add_layer(
        self,
        identifier: str,
        axis_kwargs: Dict[str, Any] = None,
        axis_label_kwargs: Dict[str, Any] = None,
    ) -> "PlotItemLayer":
        """add a new layer to the plot for plotting a curve in a different range

        Args:
            identifier: string identifier for the new layer
            axis_kwargs: Dictionary with the keyword arguments for the new layer's AxisItem, see AxiItem constructor for more information
            axis_label_kwargs: Dictionary with Keyword arguments passed to setLabel function of the new Axis

        Returns:
            New created layer instance
        """
        if axis_kwargs is None:
            axis_kwargs = {}
        if axis_label_kwargs is None:
            axis_label_kwargs = {}
        new_view_box = ExViewBox()
        new_y_axis = CustomAxisItem("right", parent=self, **axis_kwargs)
        new_y_axis.setZValue(len(self._layers))
        new_layer = PlotItemLayer(
            plot_item=self,
            identifier=identifier,
            view_box=new_view_box,
            axis_item=new_y_axis,
        )
        self._layers.add(new_layer)
        self.layout.addItem(new_y_axis, 2, 2 + len(self._layers))
        self.scene().addItem(new_view_box)
        new_y_axis.linkToView(new_view_box)
        new_view_box.setXLink(self)
        new_y_axis.setLabel(**axis_label_kwargs)
        return new_layer

    def update_layers(self) -> None:
        """Update the other layer's viewbox geometry to fit the PlotItem ones"""
        self._layers.update_view_box_geometries(self)

    def remove_layer(self, layer: Union["PlotItemLayer", str] = "") -> bool:
        """ Remove a existing layer from the PlotItem

        This function need either the layer object as a parameter or the identifier of the object.

        Args:
            layer: Layer object to remove

        Returns:
            True if the layer existed and was removed
        """
        if isinstance(layer, str) and layer != "":
            layer = self._layers.get(layer)
        if not isinstance(layer, PlotItemLayer):
            raise ValueError(
                f"The layer could not be removed, since it does not have the right type ({type(layer).__name__}) "
                f"or the given identifier does not exist."
            )
        self.layout.removeItem(layer.axis_item)
        layer.axis_item.deleteLater()
        layer.axis_item.setParentItem(None)
        self.scene().removeItem(layer.view_box)
        layer.view_box.setParentItem(None)
        return self._layers.remove(layer=layer)

    def addItem(
        self,
        item: Union[pg.GraphicsObject, DataModelBasedItem],
        layer: Optional[Union["PlotItemLayer", str]] = None,
        ignoreBounds: bool = False,
        **kwargs
    ) -> None:
        """ Add an item to a given layer. """
        # Super implementation can be used if layer is not defined
        if self.is_standard_layer(layer=layer):
            super().addItem(item, ignoreBounds=ignoreBounds, **kwargs)
        else:
            self.items.append(item)
            self.dataItems.append(item)
            try:
                if isinstance(layer, str):
                    item.set_layer_information(layer_identifier=layer)
                elif isinstance(layer, PlotItemLayer):
                    item.set_layer_information(layer_identifier=layer.identifier)
            except AttributeError:
                pass
            try:
                if item.implements("plotData"):  # type: ignore
                    self.curves.append(item)
            except AttributeError:
                pass
            if layer is None or isinstance(layer, str):
                layer = self._layers.get(identifier=layer)
            # add to the layer of the ViewBox that we actually want
            layer.view_box.addItem(item=item, **kwargs)

    @staticmethod
    def is_standard_layer(layer: Optional[Union[str, "PlotItemLayer"]]) -> bool:
        """Check if layer identifier is referencing the standard ."""
        if isinstance(layer, str):
            return layer == "" or layer == PlotItemLayer.default_layer_identifier
        elif isinstance(layer, PlotItemLayer):
            return layer.identifier == "" or layer.identifier == PlotItemLayer.default_layer_identifier
        return layer is None

    def get_layer_by_identifier(self, layer_identifier: str) -> "PlotItemLayer":
        """Get layer by its identifier"""
        if layer_identifier == "":
            layer_identifier = PlotItemLayer.default_layer_identifier
        return self._layers.get(layer_identifier)

    def get_all_layers(self) -> List["PlotItemLayer"]:
        """Get all layers added to this plot layer"""
        return self._layers.get_all()

    def get_all_non_standard_layers(self) -> List["PlotItemLayer"]:
        """
        Get all layers added to this plot layer except of the
        layer containing the standard PlotItem ViewBox
        """
        return self._layers.get_all_except_default()

    def link_y_range_of_all_layers(self, link: bool = True) -> None:
        """Link y ranges of all layers's y axis"""
        self._layers.link_y_range_of_all_layers(link)

    # ~~~~~~~~~~~~~~~~~~~~ Update handling ~~~~~~~~~~~~~~~~~~~~~~~~~

    def handle_timing_update(self, timestamp: float) -> None:
        """Handle an update provided by the timing source.

        Handle initial drawing of decorators, redrawing of actual curves have
        to be implemented in the specific subclass.

        Args:
            timestamp: Updated timestamp provided by the timing source
        """
        if self._time_span:
            self._init_time_line_decorator(timestamp=timestamp)
            self._init_relative_time_axis_start(timestamp=timestamp)
            if timestamp >= self._last_timestamp:
                self._last_timestamp = timestamp
                self._time_span.update_time_span(timestamp=self._last_timestamp)
                self._handle_scrolling_plot_fixed_x_range_update()
                self._update_time_line_decorator(
                    timestamp=timestamp, position=self._calc_timeline_drawing_position()
                )
            self._update_children_items_timing()
            self._draw_style_specific_objects()

    # ~~~~~~~~~~~~~~~~~~~~ Decorator Drawing ~~~~~~~~~~~~~~~~~~~~~~~~~

    def _init_time_line_decorator(self, timestamp: float, force: bool = False) -> None:
        """Create a vertical line representing the latest timestamp

        Args:
            timestamp: Position where to create the
            force: If true, a new time line will be created
        """
        if self._plot_config.time_progress_line and (force or self._last_timestamp == -1.0):
            label_opts = {"movable": True, "position": 0.96}
            if self._time_line is not None:
                self.removeItem(self._time_line)
                self._time_line = None
            self._time_line = self.addLine(
                timestamp,
                pen=(pg.mkPen(80, 80, 80)),
                label=datetime.fromtimestamp(timestamp).strftime("%H:%M:%S"),
                labelOpts=label_opts,
            )

    def _update_time_line_decorator(self, timestamp: float, position: float = None) -> None:
        """Move the vertical line representing the current time to a new position

        Redraw the timing line according to a passed timestamp. Alternatively
        the line can also be drawn at a custom position by providing the
        position parameter, if the position is different from the provided
        timestamp (f.e. for the sliding pointer plot)

        Args:
            timestamp: Timestamp of the time that the line represents
            position: Timestamp where the line should be drawn, if None
                -> position = timestamp
        """
        if self._time_line:
            if position is None:
                position = timestamp
            self._time_line.setValue(position)
            if hasattr(self._time_line, "label"):
                self._time_line.label.setText(
                    datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                )

    def _config_contains_scrolling_style_with_fixed_x_range(self) -> bool:
        return(
            self._plot_config.scrolling_plot_fixed_x_range
            and not np.isnan(self._plot_config.scrolling_plot_fixed_x_range_offset)
            and (self._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT)
            and self._scrolling_fixed_x_range_activated
        )

    def _handle_scrolling_plot_fixed_x_range_update(self) -> None:
        """Set the viewboxes x range to the desired range if the start and end point are defined"""
        if self._config_contains_scrolling_style_with_fixed_x_range():
            x_range_min: float = self._last_timestamp - self._plot_config.time_span + self._plot_config.scrolling_plot_fixed_x_range_offset
            x_range_max: float = self._last_timestamp + self._plot_config.scrolling_plot_fixed_x_range_offset
            x_range: Tuple[float, float] = (x_range_min, x_range_max)
            self.getViewBox().setRange(xRange=x_range, padding=0.0)

    def _update_bottom_and_top_axis_style(self, style: int):
        """
        Remove the old top and bottom axes and replace them with ones fitting to
        the passed plotting style.

        Args:
            style: plotting style the new axes should fit to.
        """
        for pos in ["bottom", "top"]:
            new_axis: pg.AxisItem = self.create_fitting_axis_item(
                config_style=style, orientation=pos, parent=self
            )
            if isinstance(new_axis, RelativeTimeAxisItem) and isinstance(self._time_span, SlidingPointerTimeSpan):
                new_axis.set_start_time(self._time_span.start)
            new_axis.linkToView(self.vb)
            # Make the axis update its ticks
            new_axis.linkedViewChanged(view=self.vb)
            old_axis = self.getAxis(pos)
            visible = old_axis.isVisible()
            self.layout.removeItem(old_axis)
            # Remove ownership for the old axis
            old_axis.setParentItem(parent=None)
            old_axis.deleteLater()
            del old_axis
            row = 3 if pos == "bottom" else 1
            self.axes[pos] = {"item": new_axis, "pos": (row, 1)}
            self.layout.addItem(new_axis, row, 1)
            new_axis.setZValue(-1000)
            new_axis.setFlag(new_axis.ItemNegativeZStacksBehindParent)
            # Transfer grid settings to the new axis
            if self.ctrl.xGridCheck.isChecked():
                self.updateGrid()
            # Hide new axis if old one was
            if not visible:
                new_axis.hide()

    def create_fitting_axis_item(
            self,
            config_style: int,
            orientation: str = "bottom",
            parent: Optional["ExPlotItem"] = None
    ) -> pg.AxisItem:
        """Create an axis that fits the given plotting style

        Create instance of the axis associated to the given plotting style in
        STYLE_TO_AXIS_MAPPING. This axis-item can then be passed to the PlotItems
        constructor.

        Args:
            config_style: Plotting style the axis is created for
            orientation: orientation of the axis
            parent: parent item passed to the axis

        Returns:
            Instance of the fitting axis item
        """
        for style, axis in _STYLE_TO_AXIS_MAPPING.items():
            if config_style != style:
                continue
            return axis(orientation=orientation, parent=parent)
        return CustomAxisItem(orientation=orientation, parent=self)

    def create_fitting_time_span(self) -> Optional[PlottingTimeSpan]:
        """Create a time span object fitting to the passed config style.

        Parameters like the time span start are (if possible) taken from the old time span.
        Other parameters are taken from the
        """
        for style, time_span in _STYLE_TO_TIMESPAN_MAPPING.items():
            if self._plot_config.plotting_style != style:
                continue
            time_span_kwargs = {}
            try:
                if self._time_span is not None and self._time_span.start != 0:
                    time_span_kwargs["start"] = self._time_span.start
            except AttributeError:
                pass
            time_span_kwargs["size"] = self._plot_config.time_span
            time_span_kwargs["x_range_offset"] = self._plot_config.scrolling_plot_fixed_x_range_offset
            if time_span:
                return time_span(**time_span_kwargs)
        return None

    def _calc_timeline_drawing_position(self) -> float:
        """For curve styles that might require special positioning for the
        timeline.

        F.e. the timeline for a SlidingPointer Plot will be cyclic, which
        means that its position is not simply the timestamp, but its timestamp
        inside the cyclic drawing area

        Returns:
            position the timeline should be drawn at
        """
        if self._plot_config.plotting_style == PlotWidgetStyle.SLIDING_POINTER:
            return self.time_span.get_current_time_line_x_pos(self._last_timestamp)
        return self._last_timestamp

    def _draw_style_specific_objects(self) -> None:
        """Draw objects f.e. lines that are part of a specific plotting style

        - **Sliding Pointer**: Line at the time span start and end

        Returns:
            None
        """
        if (
            self._plot_config.plotting_style == PlotWidgetStyle.SLIDING_POINTER
            and self._last_timestamp != -1
            and not self._style_specific_objects_already_drawn
        ):
            start = self.time_span.start
            end = start + self._plot_config.time_span
            self._time_span_start_boundary = self.addLine(
                x=start, pen=pg.mkPen(128, 128, 128)
            )
            self._time_span_end_boundary = self.addLine(
                x=end, pen=pg.mkPen(128, 128, 128)
            )
            self._style_specific_objects_already_drawn = True

    def _update_children_items_timing(self) -> None:
        """Update timestamp in all items added to the plotitem"""
        for item in self.items:
            if isinstance(item, DataModelBasedItem):
                item.update_item()

    def _init_relative_time_axis_start(self, timestamp: float):
        """Initialize the start time for the relative time axis.

        Args:
            timestamp: timestamp to set the start time of the axis to
        """
        if self._last_timestamp == -1.0:
            for pos in ["bottom", "top"]:
                axis = self.getAxis(pos)
                if isinstance(axis, RelativeTimeAxisItem):
                    axis.set_start_time(timestamp)

    def get_last_time_stamp(self) -> float:
        """ Get the latest known timestamp """
        return self._last_timestamp

    def get_all_data_model_based_items(self):
        """Get all DataModelBasedItem instances added to the PlotItem
        These are all live-data plotting items. Pure PyQtGraph components or other
        objects are filtered out.

        Returns:
            All items with the fitting type
        """
        return [curve for curve in self.items if isinstance(curve, DataModelBasedItem)]

    def get_live_data_curves(self):
        """Get all live data curves added to the PlotItem

        Returns:
            All items with the fitting type
        """
        return [curve for curve in self.items if isinstance(curve, LivePlotCurve)]

    def get_live_data_bar_graphs(self):
        """Get all live data bar graphs added to the PlotItem

        Returns:
            All items with the fitting type
        """
        return [curve for curve in self.items if isinstance(curve, LiveBarGraphItem)]

    def get_live_data_injection_bars(self):
        """Get all live data injection bars added to the PlotItem

        Returns:
            All items with the fitting type
        """
        return [
            curve
            for curve in self.items
            if isinstance(curve, LiveInjectionBarGraphItem)
        ]

    def get_timestamp_markers(self):
        """Get all live data infinite lines added to the PlotItem

        Returns:
            All items with the fitting type
        """
        return [curve for curve in self.items if isinstance(curve, LiveTimestampMarker)]

    def get_all_viewboxes(self) -> List["ExViewBox"]:
        """Get a list of all ViewBoxes included in the Layer collection"""
        return self._layers.get_view_boxes()

    def handle_add_data_to_single_curve(self, data):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot. If this curve does not yet exist,
        it will be created automatically . The data will be collected by
        the curve and drawn. Further calls with other data will append it
        to the existing one.

        This slot will accept single integer and float values
        and draw them at the timestamp of their arrival.
        """
        if self.single_curve_value_slot_source is None:
            self.single_curve_value_slot_source = UpdateSource()
        if self.single_curve_value_slot_curve is None:
            self.single_curve_value_slot_curve = self.addCurve(
                data_source=self.single_curve_value_slot_source
            )
        new_data = PointData(x_value=datetime.now().timestamp(), y_value=data)
        self.single_curve_value_slot_source.sig_data_update.emit(new_data)


class PlotItemLayer:
    """
    Object that represents a single layer in an PlotItem containing a ViewBox as well as a y axis.
    """

    default_layer_identifier = "plot_item_layer"

    def __init__(
        self,
        plot_item: ExPlotItem,
        view_box: "ExViewBox",
        axis_item: pg.AxisItem,
        identifier: str = default_layer_identifier,
    ):
        self.identifier: str = identifier
        self.view_box: ExViewBox = view_box
        self.axis_item: pg.AxisItem = axis_item
        self.plot_item: pg.PlotItem = plot_item
        # by default the plot will start in auto-range mode
        self.view_box.enableAutoRange(enable=True)

    def __eq__(self, other):
        """Check equality of layers by their identifier."""
        if isinstance(other, str):
            return self.identifier == other
        if isinstance(other, PlotItemLayer):
            return self.identifier == other.identifier
        return False


class PlotItemLayerCollection:
    """Collection for layers added to a plot items identified by a unique string identifier"""

    def __init__(self, plot_item: pg.PlotItem):
        self._plot_item: pg.PlotItem = plot_item
        self._pot_item_viewbox_reference_range: Dict[
            str, List[float]
        ] = {}
        # Flag if the plot item viewboxes range change should be applied to other layers
        self._forward_range_change_to_other_layers: Tuple[bool, bool] = (False, True)
        self._layers: Dict[str, PlotItemLayer] = {}
        # For disconnecting movement again
        self._y_range_slots: Dict[Slot, Signal] = {}
        self._link_y_range_of_all_layers: bool = True
        self._current: int

    def __iter__(self):
        return iter(self._layers.values())

    def __len__(self):
        return len(self._layers)

    def get(self, identifier: Optional[str] = PlotItemLayer.default_layer_identifier) -> PlotItemLayer:
        """ Get layer by its identifier

        None or an empty string as an identifier will return the PlotItem
        layer containing the standard y-axis and viewbox of the PlotItem

        Args:
            identifier: identifier of the layer that should be searched
        """
        if identifier is None or identifier == "":
            identifier = PlotItemLayer.default_layer_identifier
        layer = self._layers.get(identifier, None)
        if layer is not None:
            return layer
        raise KeyError(f"No layer with the identifier '{identifier}'")

    def get_all(self) -> List[PlotItemLayer]:
        """Return a list of all layers"""
        return list(self._layers.values())

    def get_all_except_default(self) -> List[PlotItemLayer]:
        """Return a list of all layers except the default one"""
        layers = self.get_all()
        layers.remove(self.get(identifier=PlotItemLayer.default_layer_identifier))
        return layers

    def add(self, layer: PlotItemLayer) -> None:
        """Add new layer to the collection. A key error is raised if an layer is already
        included that has the same identifier.

        Args:
            layer: object to add

        Returns:
            None
        """
        if layer is None or not layer.identifier:
            raise ValueError(
                "Layer can not be added because it or its identifier is not defined."
            )
        if self._layers.get(layer.identifier, None) is not None:
            raise KeyError(
                f"Layer with the identifier '{layer.identifier}' has already bee added."
                f"Either rename the layer or remove the already existing one before adding."
            )
        self._layers[layer.identifier] = layer
        self._pot_item_viewbox_reference_range[layer.identifier] = layer.axis_item.range

    def remove(self, layer: Union[PlotItemLayer, str] = None) -> bool:
        """ Remove a layer from this collection

        Args:
            layer: Layer instance or identifier to delete

        Returns:
            True if layer was in collection, False if it did not exist
        """
        if isinstance(layer, str):
            layer = self.get(layer)
        for lyr in self:
            if layer == lyr:
                del self._layers[lyr.identifier]
                if self._pot_item_viewbox_reference_range.get(lyr.identifier, None):
                    del self._pot_item_viewbox_reference_range[lyr.identifier]
                del lyr.axis_item
                del lyr.view_box
                del lyr
                return True
        return False

    def update_view_box_geometries(self, plot_item: pg.PlotItem):
        """Update the viewboxes geometry"""
        for layer in self:
            # plot item view box has to be excluded to keep autoRange settings
            if not self._plot_item.is_standard_layer(layer=layer):
                layer.view_box.setGeometry(plot_item.vb.sceneBoundingRect())
                layer.view_box.linkedViewChanged(plot_item.vb, layer.view_box.XAxis)

    def get_view_boxes(self) -> List["ExViewBox"]:
        """Return all layers view boxes as a list"""
        return [layer.view_box for layer in self]

    def link_y_range_of_all_layers(self, link: bool) -> None:
        """ Link movements in all layers in y ranges

        Scale and translate all layers as if they were one, when transformed
        by interaction with the mouse (except if performed on a specific axis)
        When moving the layers each will keep its range relative to the made
        transformation. For example:

        layer 1 with the y-range (0, 1)

        layer 2 with the y-range (-2, 2)

        Moving layer 1 to (1, 2) will translate layer 2's range to (0, 4)

        Args:
            link (bool): True if the layer's should be moved together

        Returns:
            None
        """
        plot_item_layer = self.get()
        if link:
            # filter by range changes that are executed on the
            plot_item_layer.axis_item.sig_vb_mouse_event_triggered_by_axis.connect(
                self._handle_axis_triggered_mouse_event
            )
            plot_item_layer.view_box.sigRangeChangedManually.connect(
                self._handle_layer_manual_range_change
            )
            # when plot item gets moved, check if move other layers should be moved
            plot_item_layer.view_box.sigYRangeChanged.connect(
                self._handle_layer_y_range_change
            )
            for layer in self:
                self._pot_item_viewbox_reference_range[layer.identifier] = layer.axis_item.range
        else:
            # Remove connections again
            plot_item_layer.axis_item.sig_vb_mouse_event_triggered_by_axis.disconnect(
                self._handle_axis_triggered_mouse_event
            )
            plot_item_layer.view_box.sigYRangeChanged.disconnect(
                self._handle_layer_y_range_change
            )

    def set_range_change_forwarding(
            self,
            change_is_manual: Optional[bool] = None,
            mouse_event_valid: Optional[bool] = None
    ) -> None:
        """
        With passing True, a manual range change of the ViewBox of a layer will be applied
        accordingly to all other layers. When passing false, we can prevent manual range
        changes to be applied to other layers.

        This function can f.e. be used to make sure that the flag is not set from a Mouse
        Event on an axis, that set the flag to false which is still activated even though
        we do not care about it anymore.

        Args:
            change_is_manual: the range change was done manually and should be applied
            mouse_event_valid: the mouse event was valid and should be applied (it was
                not performed on a single axis)
        """
        if change_is_manual is not None:
            modified = list(self._forward_range_change_to_other_layers)
            modified[0] = change_is_manual
            self._forward_range_change_to_other_layers = tuple(modified)  # type: ignore
        if mouse_event_valid is not None:
            modified = list(self._forward_range_change_to_other_layers)
            modified[1] = mouse_event_valid
            self._forward_range_change_to_other_layers = tuple(modified)  # type: ignore

    def reset_range_change_forwarding(self) -> None:
        """Set the flag that forwards range changes to true"""
        self.set_range_change_forwarding(
            change_is_manual=False,
            mouse_event_valid=True
        )

    def _handle_axis_triggered_mouse_event(self, mouse_event_on_axis: bool) -> None:
        """ Handle the results of mouse drag event on the axis

        Mouse Events on the Viewbox and Axis are not distinguishable in pyqtgraph. Because of this,
        mouse events on the axis now emit a special signal. Since we only want Mouse Drag events on the
        actual Viewbox to affect the other layers view-range we have to filter out the Mouse
        Drag Events executed on the axis.

        Args:
            mouse_event_on_axis: True if the mouse event was executed while on the axis
        """
        self.set_range_change_forwarding(mouse_event_valid=(not mouse_event_on_axis))

    def _handle_layer_manual_range_change(self, mouse_enabled: List[bool]) -> None:
        """ Make Range update slot available, if range change was done by an Mouse Drag Event

        Args:
            mouse_enabled: List of bools if mouse interaction is enabled on the x, y axis, expected list length is 2
        """
        self.set_range_change_forwarding(change_is_manual=mouse_enabled[1])

    def _handle_layer_y_range_change(
            self,
            moved_viewbox: pg.ViewBox,
            new_range: Tuple[float, float],
            *args
    ) -> None:
        """Handle a view-range change in the PlotItems Viewbox

        If a mouse drag-event has been executed on the PlotItem's Viewbox and not on
        the axis-item we want to move all other layer's viewboxes accordingly and
        respecting their own view-range so all layers move by the same pace.

        Args:
            moved_viewbox: Viewbox that was originally moved
            new_range: new range the ViewBox now shows
            *args: Does not get used, this is just for catching additionally passed arguments
                in case the Event sends more values than expected
        """
        if args:
            _LOGGER.info(f"More values were received than expected: {args}")
        layer = self.get()
        if all(self._forward_range_change_to_other_layers):
            self.apply_range_change_to_other_layers(
                moved_viewbox=moved_viewbox,
                new_range=new_range,
                moved_layer=layer
            )
        self.reset_range_change_forwarding()
        # Update saved range even if not caused by manual update (f.e. by "View All")
        self._pot_item_viewbox_reference_range[layer.identifier][0] = layer.axis_item.range[0]
        self._pot_item_viewbox_reference_range[layer.identifier][1] = layer.axis_item.range[1]

    def apply_range_change_to_other_layers(
            self,
            moved_viewbox: pg.ViewBox,
            new_range: Tuple[float, float],
            moved_layer: PlotItemLayer
    ) -> None:
        """Update the y ranges of all layers

        If a fitting manual movement has been detected, we move the viewboxes of all
        other layers in the way, that all layers seem to move at the same pace and
        keep their view-range (distance between min and max shown value). This results
        in all plots moving seeming as if they were all drawn on the same layer.
        This applies for translations as well as scaling of viewboxes.

        Args:
            moved_viewbox: Viewbox that was originally moved
            new_range: new range the ViewBox now shows
            moved_layer: Layer the moved viewbox belongs to

        Returns:
            None
        """
        moved_viewbox_old_min: float = self._pot_item_viewbox_reference_range[moved_layer.identifier][0]
        moved_viewbox_old_max: float = self._pot_item_viewbox_reference_range[moved_layer.identifier][1]
        moved_viewbox_old_y_length: float = moved_viewbox_old_max - moved_viewbox_old_min
        moved_viewbox_new_min: float = new_range[0]
        moved_viewbox_new_max: float = new_range[1]
        moved_distance_min: float = moved_viewbox_new_min - moved_viewbox_old_min
        moved_distance_max: float = moved_viewbox_new_max - moved_viewbox_old_max
        self._pot_item_viewbox_reference_range[moved_layer.identifier][0] = moved_viewbox_new_min
        self._pot_item_viewbox_reference_range[moved_layer.identifier][1] = moved_viewbox_new_max
        for layer in self:
            if layer.view_box is not moved_viewbox:
                layer_viewbox_old_min: float = layer.axis_item.range[0]
                layer_viewbox_old_max: float = layer.axis_item.range[1]
                layer_viewbox_old_y_length: float = layer_viewbox_old_max - layer_viewbox_old_min
                relation_to_moved_viewbox = (
                    layer_viewbox_old_y_length / moved_viewbox_old_y_length
                )
                layer_viewbox_new_min = (
                    layer_viewbox_old_min
                    + moved_distance_min * relation_to_moved_viewbox
                )
                layer_viewbox_new_max = (
                    layer_viewbox_old_max
                    + moved_distance_max * relation_to_moved_viewbox
                )
                layer.view_box.setRange(
                    yRange=(layer_viewbox_new_min, layer_viewbox_new_max), padding=0.0
                )
                self._pot_item_viewbox_reference_range[layer.identifier][0] = layer_viewbox_new_min
                self._pot_item_viewbox_reference_range[layer.identifier][1] = layer_viewbox_new_max


class ExViewBox(pg.ViewBox):

    """ViewBox with extra functionality for the multi-y-axis plotting"""

    def __init__(self, **viewbox_kwargs):
        """Create a new view box

        Args:
            **viewbox_kwargs: Keyword arguments for the base class ViewBox
        """
        super().__init__(**viewbox_kwargs)
        self._layer_collection: Optional[PlotItemLayerCollection] = None

    def set_layer_collection(self, plotitem_layer_collection: PlotItemLayerCollection):
        """set a collection of layers"""
        self._layer_collection = plotitem_layer_collection

    def set_range_manually(self, **kwargs) -> None:
        """ Set range manually

        Set range, but emit a signal for manual range change to
        to trigger all other layers to be moved simultaneous.

        Args:
            **kwargs: Keyword arguments that ViewBox.setRange accepts

        Returns:
            None
        """
        if not kwargs.get("padding"):
            kwargs["padding"] = 0.0
        if self._layer_collection is not None:
            # If we call this explicitly we do not care about prior set flags for range changes
            self._layer_collection.reset_range_change_forwarding()
        self.sigRangeChangedManually.emit(self.state["mouseEnabled"])
        self.setRange(**kwargs)

    def autoRange(
        self,
        padding: float = None,
        items: Optional[List[pg.GraphicsItem]] = None,
        auto_range_x_axis: bool = True,
        **kwargs
    ) -> None:
        """ Overwritten auto range

        Overwrite standard ViewBox auto-range to automatically set the
        range for the ViewBoxes of all layers. This allows to to view all
        items in the plot without changing their positions to each other that the
        user might have arranged by hand.

        Args:
            padding: padding to use for the auto-range
            items: items to use for the auto ranging
            auto_range_x_axis: should the x axis also be set to automatically?
            **kwargs: Additional Keyword arguments. These won't be used and are only for
                      swallowing f.e. deprecated parameters.

        Returns:
            None
        """
        # item = deprecated param from superclass
        item = kwargs.get("item")
        if item and not items:
            items = [item]
        if self._layer_collection is not None:
            if padding is None:
                padding = 0.05
            plot_item_view_box: ExViewBox = self._layer_collection.get(
                identifier=PlotItemLayer.default_layer_identifier
            ).view_box
            other_viewboxes: List[ExViewBox] = list(
                filter(
                    lambda element: element is not plot_item_view_box and element.addedItems,
                    self._layer_collection.get_view_boxes()
                )
            )
            goal_range: QRectF = plot_item_view_box.childrenBoundingRect(items=items)
            bounds_list: List[QRectF] = []
            for vb in other_viewboxes:
                bounds_list.append(ExViewBox.map_bounding_rectangle_to_other_viewbox(
                    viewbox_to_map_from=vb,
                    viewbox_to_map_to=plot_item_view_box,
                    items=items
                ))
            for bound in bounds_list:
                # Get common bounding rectangle for all items in all layers
                goal_range = goal_range.united(bound)
            # Setting the range with the manual signal will move all other layers accordingly
            if auto_range_x_axis:
                plot_item_view_box.set_range_manually(rect=goal_range, padding=padding)
            else:
                y_range: Tuple[float, float] = (
                    goal_range.bottom(),
                    goal_range.top()
                )
                plot_item_view_box.set_range_manually(yRange=y_range, padding=padding)

    @staticmethod
    def map_bounding_rectangle_to_other_viewbox(
            viewbox_to_map_from: "ExViewBox",
            viewbox_to_map_to: "ExViewBox",
            items: Optional[List[pg.GraphicsItem]]
    ) -> QRectF:
        """
        Map a viewbox bounding rectangle to the coordinates of an other one.
        It is expected that both ViewBoxes have synchronized x ranges, so the
        x range of the mapped bounding rectangle will be the same.

        Args:
            viewbox_to_map_from: viewbox the items are located in
            viewbox_to_map_to: viewbox that the bounding rectangle should
                be mapped to (normally standard plot-item vb)
            items: items which bounding rectangles are used for the mapping

        Returns:
            Bounding rectangle in the standard plotitem viewbox that includes all
            items from all layers.
        """
        bounds: QRectF = viewbox_to_map_from.childrenBoundingRect(items=items)
        y_range_vb_source = (
            viewbox_to_map_from.targetRect().top(),
            viewbox_to_map_from.targetRect().bottom()
        )
        y_range_vb_destination = (
            viewbox_to_map_to.targetRect().top(),
            viewbox_to_map_to.targetRect().bottom()
        )
        y_min_in_destination_vb = ExViewBox.map_y_value_to_other_viewbox(
            source_y_range=y_range_vb_source,
            destination_y_range=y_range_vb_destination,
            y_val_to_map=bounds.bottom()
        )
        y_max_in_destination_vb = ExViewBox.map_y_value_to_other_viewbox(
            source_y_range=y_range_vb_source,
            destination_y_range=y_range_vb_destination,
            y_val_to_map=bounds.top()
        )
        return QRectF(
            bounds.x(), y_min_in_destination_vb,
            bounds.width(), y_max_in_destination_vb - y_min_in_destination_vb
        )

    @staticmethod
    def map_y_value_to_other_viewbox(
        source_y_range: Tuple[float, float],
        destination_y_range: Tuple[float, float],
        y_val_to_map: float
    ) -> float:
        """
        Map a y coordinate to the other layer by setting up the transformation
        between both layers (x coordinate we can skip, since these are always
        showing the same x range in each layer)

        As given we can use the view viewboxes y ranges
        (x -> source vb, y -> destination vb) .
            m * x_1 + c = y_1

            m * x_2 + c = y_2

            -> m = (y_2 - y_1) / (x_2 - x_1)

            -> c = y_1 - m * x_1

        With this we can transform any y coordinate from the source vb to the
        destination vb.

        Args:
            source_y_range: shown view-range from the layer the coordinates
                            are from
            destination_y_range: shown view-range from the layer the coordinates
                                 should be mapped to
            y_val_to_map: Y value to map

        Returns:
            Y coordinate in the destinations ViewBox
        """
        m: float = (destination_y_range[1] - destination_y_range[0]) / \
                   (source_y_range[1] - source_y_range[0])
        c: float = destination_y_range[0] - m * source_y_range[0]
        return m * y_val_to_map + c

    def wheelEvent(
        self,
        ev: QGraphicsSceneWheelEvent,
        axis: Optional[int] = None
    ) -> None:
        """
        Overwritten because we want to make sure the manual range
        change signal comes first. To make sure no flags are set anymore
        from the event we emit a range change signal with unmodified range.

        Args:
            ev: Wheel event that was detected
            axis: integer representing an axis, 0 -> x, 1 -> y
        """
        self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
        super().wheelEvent(ev=ev, axis=axis)
        self.sigRangeChanged.emit(self, self.state['viewRange'])

    def mouseDragEvent(
        self,
        ev: MouseDragEvent,
        axis: Optional[int] = None
    ) -> None:
        """
        Overwritten because we want to make sure the manual range
        change signal comes first. To make sure no flags are set anymore
        from the event we emit a range change signal with unmodified range.

        Args:
            ev: Mouse Drag event that was detected
            axis: integer representing an axis, 0 -> x, 1 -> y
        """
        self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
        super().mouseDragEvent(ev=ev, axis=axis)
        self.sigRangeChanged.emit(self, self.state['viewRange'])
