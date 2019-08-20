"""
Base class for modified PlotItems that handle data displaying in the ExtendedPlotWidget
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pyqtgraph
from qtpy.QtCore import Signal, Slot

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
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
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.infiniteline import (
    LiveTimestampMarker,
)
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.injectionbaritem import (
    LiveInjectionBarGraphItem,
)
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.plotdataitem import (
    LivePlotCurve,
    SlidingPointerPlotCurve,
)
from accsoft_gui_pyqt_widgets.graph.widgets.datastructures import CurveDecorators
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    LivePlotCurveConfig,
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)

_LOGGER = logging.getLogger(__name__)

_MAX_BUFFER_SIZE = 1000000


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
            config (ExPlotWidgetConfig): Configuration for the new plotitem
            timing_source (UpdateSource): Source for timing updates
            **plotitem_kwargs: Keyword Arguments that will be passed to PlotItem
        """
        # Pass modified axis for the multilayer movement to function properly
        axis_items["left"] = CustomAxisItem(orientation="left")
        super().__init__(axisItems=axis_items, **plotitem_kwargs)
        self._time_progress_line = config.time_progress_line
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
        if not np.isnan(self._plot_config.x_range_offset):
            self.setMouseEnabled(x=False)
            self.vb.enableAutoRange(axis=pyqtgraph.ViewBox.YAxis, enable=True)

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
        _LOGGER.warn("PlotItem.plot should not be used for plotting curves with the ExPlotItem, "
                     "please use ExPlotItem.addCurve for this purpose.")
        pyqtgraph.PlotItem.plot(*args, clear=clear, params=params)

    def addCurve(
        self,
        c: Optional[pyqtgraph.PlotDataItem] = None,
        params: Optional = None,
        data_source: Optional[UpdateSource] = None,
        curve_config: LivePlotCurveConfig = LivePlotCurveConfig(),
        layer_identifier: Optional[str] = None,
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
        data_source: UpdateSource,
        layer_identifier: Optional[str] = None,
        **bargraph_kwargs,
    ) -> LiveBarGraphItem:
        """Add a new bargraph attached to a live data source

        Args:
            data_source (UpdateSource): Source emmiting new data the graph should show
            layer_identifier (Optional[str]): Layer Identifier the curve should be added to
            **bargraph_kwargs: keyword arguments for the BarGraphItem base class

        Returns:
            LiveBarGraphItem that was added to the plot
        """
        if data_source is not None:
            new_plot: LiveBarGraphItem = LiveBarGraphItem.create(
                plot_item=self,
                data_source=data_source,
                layer_identifier=layer_identifier,
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
        **errorbaritem_kwargs,
    ) -> LiveInjectionBarGraphItem:
        """Add a new injection bar graph for live data

        A new injection-bar graph with a datamodel that receives data from the passed source will
        be added to the plotitem

        Args:
            data_source (UpdateSource): Source for data related updates
            layer_identifier (Optional[str]): Layer Identifier the curve should be added to
            **errorbaritem_kwargs: Keyword arguments for the ErrorBarItems used in the Injectionbars

        Returns:
            New item that was added to the plot
        """
        new_plot: LiveInjectionBarGraphItem = LiveInjectionBarGraphItem.create(
            plot_item=self,
            data_source=data_source,
            layer_identifier=layer_identifier,
            **errorbaritem_kwargs,
        )
        if not layer_identifier:
            layer_identifier = ""
        self.addItem(layer=layer_identifier, item=new_plot)
        return new_plot

    def addTimestampMarker(
        self,
        *graphicsobjectargs,
        data_source: UpdateSource
    ) -> LiveTimestampMarker:
        """Add a infinite line item for live data

        A new bar graph with a datamodel that receives data from the passed source will
        be added to the plotitem

        Args:
            data_source (UpdateSource): Source for data related updates,
            *graphicsobjectargs: Arguments passed to the GraphicsObject baseclass

        Returns:
            New item that was created
        """
        new_plot: LiveTimestampMarker = LiveTimestampMarker.create(
            *graphicsobjectargs,
            plot_item=self,
            data_source=data_source,
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
        new_view_box = pyqtgraph.ViewBox()
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
        new_view_box.enableAutoRange(axis=pyqtgraph.ViewBox.YAxis, enable=True)
        return new_layer

    def update_layers(self) -> None:
        """Update the other layer's viewboxe's geometry to fit the PlotItem ones"""
        self._layers.update_view_box_geometries(self)

    def remove_layer(self, layer: Union["PlotItemLayer", str] = "") -> bool:
        """ Remove a existing layer from the PlotItem

        This function need either the layer object as a parameter or the identifier of the object.

        Args:
            layer: Layer object to remove
            layer_identifier: Identifier of the layer that should be removed

        Returns:
            True if the layer existed and was removed
        """

        if isinstance(layer, str) and layer != "":
            layer = self._layers.get(layer)
        if not isinstance(layer, PlotItemLayer):
            raise ValueError(
                f"The layer could not be removed, since it does not have the right type ({type(layer)}) "
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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _init_time_line_decorator(self, timestamp: float) -> None:
        """Create a vertical line representing the latest timestamp

        Args:
            timestamp: Position where to create the
        """
        if self._last_timestamp == -1.0:
            label_opts = {"movable": True, "position": 0.96}
            if self._time_progress_line:
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

    def _handle_fixed_x_range_update(self) -> None:
        """Set the viewboxes x range to the desired range if the start and end point are defined"""
        if not np.isnan(self._plot_config.x_range_offset):
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


class PlotItemLayer:
    """
    Object that represents a single layer in an PlotItem containing a ViewBox as well as a y axis.
    """

    default_layer_identifier = "plot_item_layer"

    def __init__(
        self,
        plot_item: ExPlotItem,
        view_box: pyqtgraph.ViewBox,
        axis_item: pyqtgraph.AxisItem,
        identifier: str = default_layer_identifier,
    ):
        self.identifier: str = identifier
        self.view_box: pyqtgraph.ViewBox = view_box
        self.axis_item: pyqtgraph.AxisItem = axis_item
        self.plot_item: pyqtgraph.PlotItem = plot_item

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
        self._layer_movement_to_apply_on_other_layers: Dict[str, List[bool]] = {}
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
        """Add new layer to the collection. An error is raised if an layer is already
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
        self._layer_movement_to_apply_on_other_layers[layer.identifier] = [True, False]
        self._pot_item_viewbox_reference_range[layer.identifier] = layer.axis_item.range

    def remove(self, layer: Union[PlotItemLayer, str] = None) -> bool:
        """ Remove a layer from this collection

        Args:
            layer: Layer to delete
            layer_identifier: Layer Identifier of the Layer to delete

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
                if self._layer_movement_to_apply_on_other_layers.get(lyr.identifier, None):
                    del self._layer_movement_to_apply_on_other_layers[lyr.identifier]
                del lyr.axis_item
                del lyr.view_box
                del lyr
                return True
        return False

    def update_view_box_geometries(self, plot_item: pyqtgraph.PlotItem):
        """Update the geometry"""
        for layer in self:
            layer.view_box.setGeometry(plot_item.vb.sceneBoundingRect())
            layer.view_box.linkedViewChanged(plot_item.vb, layer.view_box.XAxis)

    def get_view_boxes(self) -> List[pyqtgraph.ViewBox]:
        """Return all layers view boxes as a list"""
        return [layer.view_box for layer in self]

    def link_y_range_of_all_layers(self, link: bool) -> None:
        """ Link movements in all layers in y ranges

        Linking the movement in will result in all layers moving
        together while still maintaining their individual range
        they are showing. This includes translations as well as
        scaling of the layer

        Example:
            layer 1 y range (0, 1)

            layer 2 y range (-2, 2)

            Moving layer 1 to (1, 2) will translate layer 2's range to (0, 4)

        Args:
            link (bool): True if the layer's should move together

        Returns:
            None
        """
        if link:
            for layer in self:
                self._pot_item_viewbox_reference_range[layer.identifier] = layer.axis_item.range

                def axis_slot(*args, lyr=layer):
                    self._handle_axis_triggered_mouse_event(*args, layer=lyr)

                def manual_slot(*args, lyr=layer):
                    self._handle_layer_manual_range_change(*args, layer=lyr)

                def range_change_slot(*args, lyr=layer):
                    self._handle_layer_y_range_change(*args, layer=lyr)

                layer.axis_item.sig_vb_mouse_event_triggered_by_axis.connect(axis_slot)
                layer.view_box.sigRangeChangedManually.connect(manual_slot)
                layer.view_box.sigYRangeChanged.connect(range_change_slot)
                self._y_range_slots[
                    layer.view_box.sigRangeChangedManually
                ] = manual_slot
                self._y_range_slots[layer.view_box.sigYRangeChanged] = range_change_slot
        else:
            for entry in self._y_range_slots.items():
                try:
                    entry[0].disconnect(entry[1])
                except TypeError:
                    pass

    def _handle_axis_triggered_mouse_event(self, mouse_event_on_axis: bool, layer: PlotItemLayer):
        """ Handle the results of mouse drag event on the axis

        Mouse Events on the Viewbox and Axis are not distinguishable in pyqtgraph. Because of this,
        mouse events on the axis now emit a special signal. Since we only want Mouse Drag events on the
        actual Viewbox to affect the other layers view-range we have to filter out the Mouse
        Drag Events executed on the axis.

        Args:
            mouse_event_on_axis: True if the mouse event was executed while on the axis
            layer: Layer the movement was executed in
        """
        self._layer_movement_to_apply_on_other_layers[layer.identifier][0] = not mouse_event_on_axis

    def _handle_layer_manual_range_change(self, mouse_enabled: List[bool], layer: PlotItemLayer) -> None:
        """ Make Range update slot available, if range change was done by an Mouse Drag Event

        Args:
            mouse_enabled: List of bools if mouse interaction is enabled on the x, y axis, expected list length is 2
            layer: Layer the movement was executed in
        """
        self._layer_movement_to_apply_on_other_layers[layer.identifier][1] = mouse_enabled[1]

    def _handle_layer_y_range_change(self, *args, layer: PlotItemLayer):
        """Handle a view-range change in the PlotItems Viewbox

        If a mouse drag-event has been executed on the PlotItem's Viewbox and not on
        the axis-item we want to move all other layer's viewboxes accordingly and
        respecting their own view-range so all layers move by the same pace.
        """
        if (
            self._layer_movement_to_apply_on_other_layers[layer.identifier][0]
            and self._layer_movement_to_apply_on_other_layers[layer.identifier][1]
        ):
            self._layer_movement_to_apply_on_other_layers[layer.identifier] = [True, False]
            self._update_y_ranges(*args, layer_manually_moved=layer)
        else:
            self._layer_movement_to_apply_on_other_layers[layer.identifier][0] = True
        # Update saved range even if not caused by manual update (f.e. by "View All")
        self._pot_item_viewbox_reference_range[layer.identifier][0] = layer.axis_item.range[0]
        self._pot_item_viewbox_reference_range[layer.identifier][1] = layer.axis_item.range[1]

    def _update_y_ranges(self, *args, layer_manually_moved: PlotItemLayer):
        """Update the y ranges of all layers

        If a fitting manual movement has been detected, we move the viewboxes of all
        other layers in the way, that all layers seem to move at the same pace and
        keep their view-range (distance between min and max shown value). This results
        in all plots moving seeming as if they were all drawn on the same layer.
        This applies for translations as well as scaling of viewboxes.
        """
        moved_viewbox = args[0]
        moved_viewbox_old_min: float = self._pot_item_viewbox_reference_range[layer_manually_moved.identifier][0]
        moved_viewbox_old_max: float = self._pot_item_viewbox_reference_range[layer_manually_moved.identifier][1]
        moved_viewbox_old_y_length: float = moved_viewbox_old_max - moved_viewbox_old_min
        moved_viewbox_new_min: float = args[1][0]
        moved_viewbox_new_max: float = args[1][1]
        moved_distance_min: float = moved_viewbox_new_min - moved_viewbox_old_min
        moved_distance_max: float = moved_viewbox_new_max - moved_viewbox_old_max
        self._pot_item_viewbox_reference_range[layer_manually_moved.identifier][0] = moved_viewbox_new_min
        self._pot_item_viewbox_reference_range[layer_manually_moved.identifier][1] = moved_viewbox_new_max
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
