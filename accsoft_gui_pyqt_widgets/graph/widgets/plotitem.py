"""
Base class for modified PlotItems that handle data displaying in the ExtendedPlotWidget
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pyqtgraph
from qtpy.QtCore import Signal, Slot, QRectF

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.axisitems import (
    CustomAxisItem,
    RelativeTimeAxisItem,
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
    SlidingPointerPlotCurve,
    ScrollingPlotCurve
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    LivePlotCurveConfig,
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import PointData

_LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class ExPlotItem(pyqtgraph.PlotItem):
    """PlotItem with additional functionality"""

    def __init__(
        self,
        config: ExPlotWidgetConfig = ExPlotWidgetConfig(),
        timing_source: Optional[UpdateSource] = None,
        axis_items: Optional[Dict[str, pyqtgraph.AxisItem]] = None,
        **plotitem_kwargs,
    ):
        """Create a new plot item.

        Args:
            config: Configuration for the new plotitem
            timing_source: Source for timing updates
            **plotitem_kwargs: Keyword Arguments that will be passed to PlotItem
        """
        # Pass modified axis for the multilayer movement to function properly
        axis_items["left"] = CustomAxisItem(orientation="left")
        super().__init__(
            axisItems=axis_items,
            viewBox=ExViewBox(),
            **plotitem_kwargs
        )
        self._plot_config: ExPlotWidgetConfig = config
        self._last_timestamp: float = -1.0
        self._time_line = None
        self._style_specific_objects_already_drawn: bool = False
        self._layers: PlotItemLayerCollection
        self.timing_source_attached: bool
        # Needed for the Sliding Pointer Curve
        self._cycle_start_line: pyqtgraph.InfiniteLine
        self._cycle_end_line: pyqtgraph.InfiniteLine
        self._prepare_layers()
        self._prepare_timing_source_attachment(timing_source)
        self._prepare_scrolling_plot_fixed_scrolling_range()
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
            self.timing_source_attached = True
            timing_source.sig_timing_update.connect(self.handle_timing_update)
        else:
            self.timing_source_attached = False

    def _prepare_scrolling_plot_fixed_scrolling_range(self):
        """Initialize everything for the scrolling plot scrolling movement"""
        if self._config_contains_scrolling_style_with_fixed_range():
            self.setMouseEnabled(x=False)
        else:
            # Enable in case it was disabled with before a config change
            self.setMouseEnabled(x=True)

    def update_configuration(self, config: ExPlotWidgetConfig):
        """Update the plot widgets configuration"""
        if hasattr(self, "_plot_config") and self._plot_config is not None:
            if (
                self._plot_config.cycle_size != config.cycle_size
                or self._plot_config.x_range_offset != config.x_range_offset
                or self._plot_config.plotting_style != config.plotting_style
            ):
                self._plot_config = config
                # clear View boxes of all layers
                for viewbox in self._layers.get_view_boxes():
                    viewbox.clear()
                # update plotting items
                if len(self.items) > 0:
                    self.update_items_to_new_config(config=config)
                # recreated removed time progress line decorator
                self._init_time_line_decorator(timestamp=self._last_timestamp, force=True)
        self._plot_config = config
        self._prepare_scrolling_plot_fixed_scrolling_range()
        self._handle_fixed_x_range_update()

    def update_items_to_new_config(self, config):
        """Replace all items with ones that fit the given config. Cycle's and data models stay get preserved."""
        # Recreate new items based on the old ones
        for item in self.get_all_data_model_based_items():
            if hasattr(item, "create_from"):
                new_item = item.create_from(
                    plot_config=config, object_to_create_from=item
                )
                layer = item.get_layer_identifier()
                self.addItem(layer=layer, item=new_item)
                if self._last_timestamp:
                    self._init_decorators_of_curve(new_item, self._last_timestamp)
                    self._style_specific_objects_already_drawn = False
                    self._draw_style_specific_objects()
                self.removeItem(item)

    @property
    def plot_config(self):
        """Configuration of cycle sizes and other"""
        return self._plot_config

    def plot(
        self,
        *args,
        clear: bool = False,
        params: Optional[Dict] = None,
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
        pyqtgraph.PlotItem.plot(*args, clear=clear, params=params)

    def addCurve(
        self,
        c: Optional[pyqtgraph.PlotDataItem] = None,
        params: Optional = None,
        data_source: Optional[UpdateSource] = None,
        curve_config: LivePlotCurveConfig = LivePlotCurveConfig(),
        layer_identifier: Optional[str] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **plotdataitem_kwargs,
    ) -> pyqtgraph.PlotDataItem:
        """Add new curve for live data

        Create a new curve either from static data like PlotItem.plot or a curve
        attached to a live data source.

        Args:
            c: PlotDataItem instance that is added, for backwards compatibility to the original function
            params: params for c, for backwards compatibility to the original function
            data_source: source for new data that the curve should display
            curve_config: optional configuration for curve decorators
            layer_identifier: identifier of the layer the new curve is supposed to be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **plotdataitem_kwargs: Parameters for creating a pure pyqtgraph PlotDataItem

        Returns:
            PlotDataItem or LivePlotCurve instance depending on the passed parameters
        """
        # Catch calls from superclasses deprecated addCurve() expecting a PlotDataItem
        if c and isinstance(c, pyqtgraph.PlotDataItem):
            _LOGGER.warning("Calling addCurve() for adding an already created PlotDataItem is deprecated, "
                            "please use addItem() for this purpose.")
            self.addItem(c, params)
            return c
        # Create new curve and add it
        else:
            if layer_identifier == "" or layer_identifier is None:
                layer_identifier = PlotItemLayer.default_layer_identifier
            # create curve that is attached to live data
            if data_source is not None and curve_config is not None:
                new_plot: LivePlotCurve = LivePlotCurve.create(
                    plot_item=self,
                    curve_config=curve_config,
                    data_source=data_source,
                    layer_identifier=layer_identifier,
                    buffer_size=buffer_size,
                    **plotdataitem_kwargs,
                )
            elif data_source is None:
                new_plot: pyqtgraph.PlotDataItem = pyqtgraph.PlotDataItem(
                    **plotdataitem_kwargs
                )
            self.addItem(layer=layer_identifier, item=new_plot)
            if self._last_timestamp:
                self._init_decorators_of_curve(new_plot, self._last_timestamp)
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
        if data_source is not None:
            new_plot: LiveBarGraphItem = LiveBarGraphItem.create(
                plot_item=self,
                data_source=data_source,
                buffer_size=buffer_size,
                **bargraph_kwargs,
            )
        else:
            new_plot: pyqtgraph.BarGraphItem = pyqtgraph.BarGraphItem(
                **bargraph_kwargs,
            )
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
            *graphicsobjectargs: Arguments passed to the GraphicsObject baseclass

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

    # ~~~~~~~~~~~~~~~~~~~~~~ Layers ~~~~~~~~~~~~~~~~~~~~~~~~

    def add_layer(
        self,
        identifier: str,
        axis_kwargs: Dict[str, Any] = {},
        axis_label_kwargs: Dict[str, Any] = {},
    ) -> "PlotItemLayer":
        """add a new layer to the plot for plotting a curve in a different range

        Args:
            identifier: string identifier for the new layer
            axis_kwargs: Dictionary with the keyword arguments for the new layer's AxisItem, see AxiItem constructor for more information
            axis_label_kwargs: Dictionary with Keyword arguments passed to setLabel function of the new Axis

        Returns:
            New created layer instance
        """
        new_view_box = ExViewBox()
        new_y_axis = CustomAxisItem("right", **axis_kwargs)
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
        self.scene().removeItem(layer.view_box)
        return self._layers.remove(layer=layer)

    def addItem(
        self,
        item: Union[pyqtgraph.GraphicsObject, DataModelBasedItem],
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
                item.set_layer_information(layer_identifier=layer)
            except AttributeError:
                pass
            try:
                if item.implements("plotData"):
                    self.curves.append(item)
            except AttributeError:
                pass
            if layer is None or isinstance(layer, str):
                layer = self._layers.get(identifier=layer)
            # add to the layer of the ViewBox that we actually want
            layer.view_box.addItem(item=item, **kwargs)

    @staticmethod
    def is_standard_layer(layer: str) -> bool:
        """Check if layer identifier is referencing the standard ."""
        try:
            return layer is None or layer == "" or layer == PlotItemLayer.default_layer_identifier
        except:
            return False

    def get_layer_by_identifier(self, layer_identifier: str) -> "PlotItemLayer":
        """Get layer by its identifier"""
        if layer_identifier == "":
            layer_identifier = PlotItemLayer.default_layer_identifier
        return self._layers.get(layer_identifier)

    def get_all_layers(self) -> List["PlotItemLayer"]:
        """Get all layers added to this plotlayer"""
        return self._layers.get_all()

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
        self._init_time_line_decorator(timestamp=timestamp)
        self._init_line_decorators(timestamp=timestamp)
        if timestamp >= self._last_timestamp:
            self._last_timestamp = timestamp
            self._handle_fixed_x_range_update()
            self._update_time_line_decorator(
                timestamp=timestamp, position=self._calc_timeline_drawing_position()
            )
        self._update_curve_timing(timestamp=self._last_timestamp)
        self._draw_style_specific_objects()

    # ~~~~~~~~~~~~~~~~~~~~ Decorator Drawing ~~~~~~~~~~~~~~~~~~~~~~~~~

    def _init_time_line_decorator(self, timestamp: float, force: bool = False) -> None:
        """Create a vertical line representing the latest timestamp

        Args:
            timestamp: Position where to create the
            force: If true, a new time line will be created
        """
        if force or self._last_timestamp == -1.0:
            label_opts = {"movable": True, "position": 0.96}
            if self._plot_config.time_progress_line:
                self._time_line = self.addLine(
                    timestamp,
                    pen=(pyqtgraph.mkPen(80, 80, 80)),
                    label=datetime.fromtimestamp(timestamp).strftime("%H:%M:%S"),
                    labelOpts=label_opts,
                )
            else:
                self._time_line = self.addLine(
                    timestamp, pen=(pyqtgraph.mkPen(80, 80, 80, 0))
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

    def _config_contains_scrolling_style_with_fixed_range(self):
        """Configuration for a scrolling plot with a fixed x range. """
        x_range = not np.isnan(self._plot_config.x_range_offset)
        scrolling_plot = (
            self._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT
        )
        return x_range and scrolling_plot

    def _handle_fixed_x_range_update(self) -> None:
        """Set the viewboxes x range to the desired range if the start and end point are defined"""
        if self._config_contains_scrolling_style_with_fixed_range():
            x_range_min: float = self._last_timestamp - self._plot_config.cycle_size + self._plot_config.x_range_offset
            x_range_max: float = self._last_timestamp + self._plot_config.x_range_offset
            x_range: Tuple[float, float] = (x_range_min, x_range_max)
            self.getViewBox().setRange(xRange=x_range, padding=0.0)

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
            for curve in self.curves:
                if isinstance(curve, SlidingPointerPlotCurve):
                    return curve.get_cycle().get_current_time_line_x_pos(
                        self._last_timestamp
                    )
        return self._last_timestamp

    def _draw_style_specific_objects(self) -> None:
        """Draw objects f.e. lines that are part of a specific plotting style

        - **Sliding Pointer**: Line at the cycle start and end

        Returns:
            None
        """
        if (
            self._plot_config.plotting_style == PlotWidgetStyle.SLIDING_POINTER
            and not self._style_specific_objects_already_drawn
        ):
            for curve in self.curves:
                if isinstance(curve, SlidingPointerPlotCurve):
                    start = curve.get_cycle().start
                    end = start + self._plot_config.cycle_size
                    self._cycle_start_line = self.addLine(
                        x=start, pen=pyqtgraph.mkPen(128, 128, 128)
                    )
                    self._cycle_end_line = self.addLine(
                        x=end, pen=pyqtgraph.mkPen(128, 128, 128)
                    )
                    self._style_specific_objects_already_drawn = True

    def _update_curve_timing(self, timestamp: float) -> None:
        """Update timestamp in all items added to the plotitem

        Args:
            timestamp: timestamp that is passed to each curve

        Returns:
            None
        """
        for item in self.items:
            if isinstance(item, DataModelBasedItem) and hasattr(
                item, "update_timestamp"
            ):
                item.update_timestamp(new_timestamp=timestamp)

    def _init_line_decorators(self, timestamp: float):
        """Initial drawing of the line decorators for the plot curve

        Args:
            timestamp: timestamp where to draw
        """
        if self._last_timestamp == -1.0:
            for curve in self.curves:
                self._init_decorators_of_curve(curve=curve, timestamp=timestamp)
            axis = self.getAxis("bottom")
            if isinstance(axis, RelativeTimeAxisItem):
                axis.set_start_time(timestamp)

    def _init_decorators_of_curve(self, curve: LivePlotCurve, timestamp: float):
        """ Initialize curve decorators """
        if isinstance(curve, LivePlotCurve):
            decorator = curve.get_decorators()
            if curve.get_conf().draw_vertical_line:
                if decorator.vertical_line:
                    decorator.vertical_line.setPos(pos=timestamp)
                else:
                    decorator.vertical_line = pyqtgraph.InfiniteLine(
                        pos=timestamp, angle=90
                    )
                    self._layers.get(curve.get_layer_identifier()).view_box.addItem(
                        decorator.vertical_line
                    )
            if curve.get_conf().draw_horizontal_line:
                if decorator.horizontal_line:
                    decorator.horizontal_line.setPos(pos=timestamp)
                else:
                    decorator.horizontal_line = pyqtgraph.InfiniteLine(pos=0, angle=0)
                    self._layers.get(curve.get_layer_identifier()).view_box.addItem(
                        decorator.horizontal_line
                    )
            if curve.get_conf().draw_point:
                if not decorator.point:
                    decorator.point = pyqtgraph.PlotDataItem(
                        connect="pairs", symbol="+"
                    )
                    self._layers.get(curve.get_layer_identifier()).view_box.addItem(
                        decorator.point
                    )

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

    def handle_single_curve_value_slot(self, data):
        """Handle arriving data"""
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
        axis_item: pyqtgraph.AxisItem,
        identifier: str = default_layer_identifier,
    ):
        self.identifier: str = identifier
        self.view_box: ExViewBox = view_box
        self.axis_item: pyqtgraph.AxisItem = axis_item
        self.plot_item: pyqtgraph.PlotItem = plot_item
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

    def __init__(self, plot_item: pyqtgraph.PlotItem):
        self._plot_item: pyqtgraph.PlotItem = plot_item
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

    def update_view_box_geometries(self, plot_item: pyqtgraph.PlotItem):
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
            self._forward_range_change_to_other_layers = tuple(modified)
        if mouse_event_valid is not None:
            modified = list(self._forward_range_change_to_other_layers)
            modified[1] = mouse_event_valid
            self._forward_range_change_to_other_layers = tuple(modified)

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
            moved_viewbox: pyqtgraph.ViewBox,
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
            moved_viewbox: pyqtgraph.ViewBox,
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


class ExViewBox(pyqtgraph.ViewBox):

    """ViewBox with extra functionality for the multi-y-axis plotting"""

    def __init__(self, **viewbox_kwargs):
        """Create a new view box

        Args:
            **viewbox_kwargs: Keyword arguments for the baseclass ViewBox
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
        # If we call this explicitly we do not care about prior set flags for range changes
        self._layer_collection.reset_range_change_forwarding()
        self.sigRangeChangedManually.emit(self.state["mouseEnabled"])
        self.setRange(**kwargs)

    def autoRange(
        self,
        padding: float = None,
        items: Optional[List[pyqtgraph.GraphicsItem]] = None,
        item: Optional[pyqtgraph.GraphicsItem] = None
    ) -> None:
        """ Overwritten auto range

        Overwrite standard ViewBox auto-range to automatically set the
        range for the ViewBoxes of all layers. This allows to to view all
        items in the plot without changing their positions to each other that the
        user might have arranged by hand.

        Args:
            padding: padding to use for the auto-range
            items: items to use for the auto ranging
            item: deprecated!

        Returns:
            None
        """
        # Behavior of Superclass method
        if item is not None:
            _LOGGER.warning("ViewBox.autoRange(item=__) is deprecated. Use 'items' argument instead.")
            bounds = self.mapFromItemToView(item, item.boundingRect()).boundingRect()
            if bounds is not None:
                self.setRange(bounds, padding=padding)
        # View all for multiple layers
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
            plot_item_view_box.set_range_manually(rect=goal_range, padding=padding)

    @staticmethod
    def map_bounding_rectangle_to_other_viewbox(
            viewbox_to_map_from: "ExViewBox",
            viewbox_to_map_to: "ExViewBox",
            items: List[pyqtgraph.GraphicsItem]
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
