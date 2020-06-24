"""
Base class for modified PlotItems that handle data displaying in the ExtendedPlotWidget
"""

import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, Type, cast

import numpy as np
import pyqtgraph as pg
from pyqtgraph.GraphicsScene.mouseEvents import MouseDragEvent
from qtpy.QtCore import Signal, QRectF, QPointF, Qt
from qtpy.QtWidgets import QGraphicsSceneWheelEvent, QGraphicsRectItem
from qtpy.QtGui import QPen, QPainter

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.axisitems import (
    ExAxisItem,
    RelativeTimeAxisItem,
    TimeAxisItem,
)
from accwidgets.graph.widgets.legenditem import ExLegendItem
from accwidgets.graph.widgets.dataitems.bargraphitem import (
    LiveBarGraphItem,
    AbstractBaseBarGraphItem,
)
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
)
from accwidgets.graph.widgets.dataitems.timestampmarker import (
    AbstractBaseTimestampMarker,
    LiveTimestampMarker,
)
from accwidgets.graph.widgets.dataitems.injectionbaritem import (
    AbstractBaseInjectionBarGraphItem,
    LiveInjectionBarGraphItem,
)
from accwidgets.graph.widgets.dataitems.plotdataitem import (
    LivePlotCurve,
    AbstractBasePlotCurve,
    EditablePlotCurve,
)
from accwidgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accwidgets.graph.datamodel.datastructures import CurveData, PlottingItemData
from accwidgets.graph.widgets.plottimespan import (
    ScrollingPlotTimeSpan,
    CyclicPlotTimeSpan,
    BasePlotTimeSpan,
)

# Mapping of plotting styles to a fitting axis style
_STYLE_TO_AXIS_MAPPING: Dict[int, Type[pg.AxisItem]] = {
    PlotWidgetStyle.STATIC_PLOT: ExAxisItem,
    PlotWidgetStyle.EDITABLE: ExAxisItem,
    PlotWidgetStyle.CYCLIC_PLOT: RelativeTimeAxisItem,
    PlotWidgetStyle.SCROLLING_PLOT: TimeAxisItem,
}


# Mapping of plotting styles to a fitting time span
_STYLE_TO_TIMESPAN_MAPPING: Dict[int, Optional[Type[BasePlotTimeSpan]]] = {
    PlotWidgetStyle.STATIC_PLOT: None,
    PlotWidgetStyle.EDITABLE: None,
    PlotWidgetStyle.CYCLIC_PLOT: CyclicPlotTimeSpan,
    PlotWidgetStyle.SCROLLING_PLOT: ScrollingPlotTimeSpan,
}


@dataclass
class Range:
    min: float
    max: float

    @classmethod
    def from_pg_range(cls, orig: Union[Tuple[float, float], List[float]]):
        return cls(min=orig[0], max=orig[1])

    @property
    def span(self) -> float:
        return self.max - self.min


class ExPlotItem(pg.PlotItem):

    sig_selection_changed = Signal()
    """
    Signal informing about any changes to the current selection of the current
    editable item. The signal will also be emitted, if the current selection
    has been moved around by dragging.

    In general this signal will only be emitted in an editable plot
    configuration.
    """

    sig_plot_selected = Signal(bool)
    """
    Signal informing about an entire plot being selected for editing.
    """

    def __init__(
        self,
        config: Optional[ExPlotWidgetConfig] = None,
        timing_source: Optional[UpdateSource] = None,
        axis_items: Optional[Dict[str, pg.AxisItem]] = None,
        **plotitem_kwargs,
    ):
        """PlotItem with additional functionality

        Args:
            config: Configuration for the new plotitem
            timing_source: Source for timing updates
            **plotitem_kwargs: Keyword Arguments that will be passed to PlotItem
        """
        # Pass modified axis for the multilayer movement to function properly
        config = config or ExPlotWidgetConfig()
        if axis_items is None:
            axis_items = {}
        # TODO: Why do we force create these? What if user passed it from the outside? Why if we don't need right one?
        axis_items["left"] = ExAxisItem(orientation="left")
        axis_items["right"] = ExAxisItem(orientation="right")
        # FIXME: Create_firrint_axis_items called even when it's not needed
        axis_items["bottom"] = axis_items.get("bottom", self._create_fitting_axis_item(
            config_style=config.plotting_style,
            orientation="bottom",
        ))
        axis_items["top"] = axis_items.get("top", self._create_fitting_axis_item(
            config_style=config.plotting_style,
            orientation="top",
        ))
        viewbox = ExViewBox()
        super().__init__(
            axisItems=axis_items,
            viewBox=viewbox,
            **plotitem_kwargs,
        )
        viewbox.sig_selection.connect(self.select)
        self._plot_config: ExPlotWidgetConfig = config
        self._time_span: Optional[BasePlotTimeSpan] = self._create_fitting_time_span()
        self._time_line: Optional[pg.InfiniteLine] = None
        self._style_specific_objects_already_drawn: bool = False
        self._layers: PlotItemLayerCollection
        self._timing_source_attached: bool
        # Needed for the Cyclic Curve
        self._time_span_start_boundary: Optional[pg.InfiniteLine] = None
        self._time_span_end_boundary: Optional[pg.InfiniteLine] = None
        self._prepare_layers()
        self._prepare_timing_source_attachment(timing_source)
        # If set to false, this flag prevents the scrolling movement on an
        # scrolling plot with a fixed range.
        self._scrolling_fixed_xrange_activated: bool = True
        self.autoBtn: pg.ButtonItem
        self._orig_auto_btn: Optional[pg.ButtonItem] = None
        self._prepare_scrolling_plot_fixed_xrange()
        # This will only be used in combination with the singleCurveValueSlot
        self.single_data_item_slot_source: Optional[UpdateSource] = None
        self.single_value_slot_dataitem: Optional[DataModelBasedItem] = None
        # For editable mode
        self._current_editable: Optional[EditablePlotCurve] = None
        self._plot_selectable: bool = False
        self._plot_selected: bool = False
        self._plot_selected_pen: QPen = pg.mkPen("r", width=6)

    # ~~~~~~~~~~~ Plotting Functions ~~~~~~~~~~~

    def addCurve(
        self,
        c: Optional[pg.PlotDataItem] = None,
        params: Optional[Dict[str, Any]] = None,
        data_source: Optional[UpdateSource] = None,
        layer: Optional["LayerIdentification"] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **plotdataitem_kwargs,
    ) -> pg.PlotDataItem:
        """Add a new curve attached to a source for new data

        Create a curve fitting to the style of the plot and add it to the plot.
        The new curve can be either either created from static data like
        PlotItem.plot or from a data source that handles communication between
        the curve and a source data is coming from. To create a curve attached
        to f.e. live data, pass a fitting data source and to create a curve
        from f.e. a static array, pass keyword arguments from the PlotDataItem.

        Args:
            c: PlotDataItem instance that is added, for backwards compatibility to the original function
            params: params for c, for backwards compatibility to the original function
            data_source: source for new data that the curve should display
            layer: identifier of the layer the new curve is supposed to be added to
            buffer_size: maximum count of values the data model buffer should hold, used for live
                         data displaying.
            **plotdataitem_kwargs: Parameters for creating a pure pyqtgraph PlotDataItem

        Returns:
            PlotDataItem or LivePlotCurve instance depending on the passed parameters
        """
        # Catch calls from superclasses deprecated addCurve() expecting a PlotDataItem
        if c and isinstance(c, pg.PlotDataItem):
            warnings.warn("Calling addCurve() for adding an already created PlotDataItem is deprecated, "
                          "please use addItem() for this purpose.")
            params = params or {}
            self.addItem(item=c, **params)
            return c
        new_plot = pg.PlotDataItem(**plotdataitem_kwargs) if data_source is None else \
            AbstractBasePlotCurve.from_plot_item(plot_item=self,
                                                 data_source=data_source,
                                                 buffer_size=buffer_size,
                                                 **plotdataitem_kwargs)
        self.addItem(layer=layer, item=new_plot)
        return new_plot

    def addBarGraph(
        self,
        data_source: Optional[UpdateSource] = None,
        layer: Optional["LayerIdentification"] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **bargraph_kwargs,
    ) -> LiveBarGraphItem:
        """Add a new curve attached to a source for new data

        Create a bar graph fitting to the style of the plot and add it to the plot.
        The new graph can be either either created from static data like
        PlotItem.plot or from a data source that handles communication between
        the graph and a source data is coming from. To create a bar graph attached
        to f.e. live data, pass a fitting data source and to create a bar graph
        from f.e. a static array, pass keyword arguments from the BarGraphItem.

        Args:
            data_source (UpdateSource): Source emitting new data the graph should show
            layer (Optional[str]): Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **bargraph_kwargs: keyword arguments for the BarGraphItem base class

        Returns:
            BarGraphItem or LiveBarGraphItem, depending on the passed parameters,
            that was added to the plot.
        """
        new_plot = pg.BarGraphItem(**bargraph_kwargs) if data_source is None else \
            AbstractBaseBarGraphItem.from_plot_item(plot_item=self,
                                                    data_source=data_source,
                                                    buffer_size=buffer_size,
                                                    **bargraph_kwargs)
        self.addItem(layer=layer, item=new_plot)
        return new_plot

    def addInjectionBar(
        self,
        data_source: UpdateSource,
        layer: Optional["LayerIdentification"] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **errorbaritem_kwargs,
    ) -> LiveInjectionBarGraphItem:
        """Add a new injection bar graph

        The new injection bar graph is attached to a source for receiving data
        updates. An injection bar is based on PyQtGraph's ErrorBarItem with the
        ability to add Text Labels.

        Args:
            data_source (UpdateSource): Source for data related updates
            layer (Optional[str]): Layer Identifier the curve should be added to
            buffer_size: maximum count of values the data model buffer should hold
            **errorbaritem_kwargs: Keyword arguments for the ErrorBarItems used in the InjectionBars

        Returns:
            LiveInjectionBarGraphItem that was added to the plot.
        """
        new_plot = AbstractBaseInjectionBarGraphItem.from_plot_item(
            plot_item=self,
            data_source=data_source,
            buffer_size=buffer_size,
            **errorbaritem_kwargs,
        )
        self.addItem(layer=layer, item=new_plot)
        return new_plot

    def addTimestampMarker(
        self,
        *graphicsobjectargs,
        data_source: UpdateSource,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
    ) -> LiveTimestampMarker:
        """Add a new timestamp marker sequence to the plot

        The new timestamp marker sequence is attached to a source for receiving
        data updates. A timestamp marker is a vertical infinite line based on
        PyQtGraph's InfiniteLine with a text label at the top. The color of each
        line is controlled by the source for data.

        Args:
            data_source (UpdateSource): Source for data related updates,
            buffer_size: maximum count of values the data model buffer should hold
            *graphicsobjectargs: Arguments passed to the GraphicsObject base class

        Returns:
            LiveTimestampMarker that was added to the plot.
        """
        new_plot: AbstractBaseTimestampMarker = AbstractBaseTimestampMarker.from_plot_item(
            *graphicsobjectargs,
            plot_item=self,
            data_source=data_source,
            buffer_size=buffer_size,
        )
        self.addItem(layer=None, item=new_plot)
        return new_plot

    def addItem(
        self,
        item: Union[pg.GraphicsObject, DataModelBasedItem],
        layer: Optional["LayerIdentification"] = None,
        ignoreBounds: bool = False,
        **kwargs,
    ):
        """
        Add an item to the plot. If no layer is provided, the item
        will be added to the default ViewBox of the PlotItem, if a layer
        is provided, the item will be added to its ViewBox.

        Args:
            item: Item that should be added to the plot
            layer: Either a reference to the layer or its identifier in which's
                   ViewBox the item should be added
            ignoreBounds: should the bounding rectangle of the item be respected
                          when auto ranging the plot
            kwargs: Additional arguments in case the original PyQtGraph API changes
        """
        # Super implementation can be used if layer is not defined
        if self.is_standard_layer(layer=layer):
            super().addItem(item, ignoreBounds=ignoreBounds, **kwargs)
            try:
                item.layer_id = ""
            except AttributeError:
                pass
        else:
            self.items.append(item)
            self.dataItems.append(item)
            try:
                layer = layer if isinstance(layer, PlotItemLayer) else \
                    self.layer(layer_id=layer)
                item.layer_id = layer.id
            except AttributeError:
                pass
            try:
                if item.implements("plotData"):  # type: ignore
                    self.curves.append(item)
            except AttributeError:
                pass
            self.getViewBox(layer=layer).addItem(item=item, ignoreBounds=ignoreBounds, **kwargs)

            # We need to repeat pyqtgraph logic of adding legend items by default here, because it will
            # do so only for native viewBox, but not for additional layers.
            name: Optional[str] = None
            if hasattr(item, "implements") and item.implements("plotData"):  # type: ignore
                name = item.name()  # type: ignore
            if name is not None and hasattr(self, "legend") and self.legend is not None:
                self.legend.addItem(item, name=name)

        if self.editable:
            self._connect_to_editable_item(item=cast(EditablePlotCurve, item))

    def clear(self, clear_decorators: bool = False):
        """
        Clear the PlotItem but reinitialize items that are part of the plot.
        These items contain f.e. the time line decorator.

        Args:
            clear_decorators: If set to False, decorators that are part of
                              the plot are reinitialized. If True, the plot
                              will be completely empty after clearing.
        """
        super().clear()
        if hasattr(self, "legend") and self.legend is not None:
            items = [*self.legend.items]  # Copy to prevent mutation inside the loop
            for item in items:
                self.legend.remove_item_from_legend(item)
        if not clear_decorators and self._time_span is not None:
            self._init_time_line_decorator(timestamp=self.last_timestamp, force=True)

    def removeItem(self, item: pg.GraphicsObject):
        """
        Extend the remove item operation to search for
        the right viewbox in the PlotItem when removing
        the item.

        Args:
            item: item that will be removed from the plot
        """
        if item not in self.items:
            return
        self.items.remove(item)
        if item in self.dataItems:
            self.dataItems.remove(item)
        if item.scene() is not None:
            try:
                view_box = next(vb for vb in self.view_boxes if item in vb.addedItems)
            except StopIteration:
                view_box = self.vb
            view_box.removeItem(item)
        if item in self.curves:
            self.curves.remove(item)
            self.updateDecimation()
            self.updateParamList()

    def plot(self, *args, clear: bool = False, params: Optional[Dict[str, Any]] = None) -> pg.PlotDataItem:
        """ **Warning:** Avoid using this function

        Plotting curves in the ExPlotItem should not be done with PlotItem.plot
        since it is not consistent with the rest of our API, so try to avoid it.
        For plotting curve either create a curve (PlotDataItem, LivePlotCurve...)
        by hand and add it with ExPlotItem.addItem or use ExPlotItem.addCurve and
        pass no UpdateSource but keyword arguments fitting to PyQtGraph's PlotDataItem.

        Add and return a new plot.
        See :func:`PlotDataItem.__init__ <pyqtgraph.PlotDataItem.__init__>` for data arguments

        Args:
            *args: arguments of the PlotDataItem constructor
            clear: clear all plots before displaying new data
            params: meta-parameters to associate with this data
        """
        warnings.warn("PlotItem.plot should not be used for plotting curves with "
                      "the ExPlotItem, please use the PlotDataItem and addItem "
                      "or ExPlotItem.addCurve for this purpose.")
        return pg.PlotItem.plot(*args, clear=clear, params=params)

    def select(self, selection: QRectF):
        """
        Select a data in a specific region in the current editable item.

        Args:
            selection: selected region in scene coordintates
        """
        if self.editable:
            if self.current_editable is not None:
                self.current_editable.select(selection=selection)
        else:
            warnings.warn("Points can only be selected in an editable "
                          "configuration.")

    def send_currents_editable_state(self) -> bool:
        """
        Send the state of the current editable item back to the process it
        received it from. If there was no state change, nothing is sent.

        Returns:
            True if something was sent back
        """
        if self.editable:
            if self.current_editable is not None:
                return self.current_editable.send_current_state()
        else:
            warnings.warn("The state of editable items can only be sent in "
                          "and editable configuration.")
        return False

    def send_all_editables_state(self) -> List[bool]:
        """
        Send the states of all editable items to the processes they are
        connected to.

        Returns:
            List of Trues, if the states of all items have been sent
        """
        if self.editable:
            states_sent = []
            for item in self.editable_items:
                states_sent.append(item.send_current_state())
            return states_sent
        warnings.warn("The state of editable items can only be sent in "
                      "and editable configuration.")
        return []

    def make_selectable(self, selectable: bool):
        """Should the plot be selectable / deselectable?

        Args:
            selectable: True if the plot should be selectable
        """
        self._plot_selectable = selectable

    def toggle_plot_selection(self, select: Optional[bool] = None) -> bool:
        """
        Toggle the drawing of a border around the plot or set it to the passed
        value

        Args:
            select: True if the plot should be selected, if None, selection is
                    toggled
        """
        if select is None:
            select = not self._plot_selected
        if self._plot_selectable:
            self._plot_selected = select
            self.update()
            self.sig_plot_selected.emit(select)
        return select

    def paint(self, painter: QPainter, *args):
        """
        Extend the PlotItem's paint function with the ability to
        render a yellow border around it (for selecting a plot)

        Args:
            painter: QPainter for painting the Plot
            args: positional arguments for PlotItem's paint function
        """
        super().paint(painter, *args)
        if self._plot_selected and self._plot_selectable and self.editable:
            painter.setPen(self._plot_selected_pen)
            painter.drawRect(self.boundingRect())

    def replace_selection(self, replacement: CurveData):
        """Function to call if the current data selection was changed.

        Args:
            replacement: The data to replace the indices with
        """
        if self.current_editable:
            self.current_editable.replace_selection(replacement=replacement)

    @property
    def current_selection_data(self) -> Optional[CurveData]:
        """Get the selected data as a curve data."""
        if self.current_editable:
            return self.current_editable.selection_data
        return None

    @property
    def editable(self) -> bool:
        """Is the plot item in editable plot widget style"""
        return self.plot_config.plotting_style == PlotWidgetStyle.EDITABLE

    @property
    def data_model_items(self) -> List[DataModelBasedItem]:
        """All data model based items added to the PlotItem. Pure PyQtGraph
        components or other objects are filtered out.
        """
        return [curve for curve in self.items if isinstance(curve, DataModelBasedItem)]

    @property
    def live_items(self) -> List[DataModelBasedItem]:
        """All live data items added to the PlotItem. Pure PyQtGraph
        components or other objects are filtered out.
        """
        return [curve for curve in self.items if isinstance(curve, (
            LivePlotCurve,
            LiveBarGraphItem,
            LiveInjectionBarGraphItem,
            LiveTimestampMarker,
        ))]

    @property
    def live_curves(self) -> List[LivePlotCurve]:
        """All live data items added to the PlotItem."""
        return [curve for curve in self.items if isinstance(curve, LivePlotCurve)]

    @property
    def live_bar_graphs(self) -> List[LiveBarGraphItem]:
        """All live data bar graphs added to the PlotItem."""
        return [curve for curve in self.items if isinstance(curve, LiveBarGraphItem)]

    @property
    def live_injection_bars(self) -> List[LiveInjectionBarGraphItem]:
        """All live data injection bars added to the PlotItem."""
        return [
            curve
            for curve in self.items
            if isinstance(curve, LiveInjectionBarGraphItem)
        ]

    @property
    def live_timestamp_markers(self) -> List[LiveTimestampMarker]:
        """All live data infinite lines added to the PlotItem."""
        return [curve for curve in self.items if isinstance(curve, LiveTimestampMarker)]

    @property
    def editable_items(self) -> List[EditablePlotCurve]:
        """All editable items added to the PlotItem. """
        return [i for i in self.items if isinstance(i, EditablePlotCurve)]

    @property
    def current_editable(self) -> Optional[EditablePlotCurve]:
        """The item which is currently edited. If no item has yet been
        selected, the last added editable item will be returned."""
        editables = self.editable_items
        if not editables:
            return None
        if not self._current_editable:
            return editables[-1]
        else:
            return self._current_editable

    @current_editable.setter
    def current_editable(self, editable: EditablePlotCurve):
        """Select the item in which points should be selected and edited.
        Per PlotItem only one item can be edited at a time.

        Args:
            editable: item which should be set as the current editable
        """
        if editable in self.editable_items:
            self._current_editable = editable
        else:
            warnings.warn(f"{editable} seems to be not an editable chart "
                          f"of this plot.")

    @property
    def selection_mode(self) -> bool:
        """
        If the selection mode is enabled, mouse drag events on the view
        box create selection rectangles and do not move the view
        """
        return self.getViewBox().selection_mode

    @selection_mode.setter
    def selection_mode(self, enable: bool):
        """
        If the selection mode is enabled, mouse drag events on the view
        box create selection rectangles and do not move the view
        """
        if not enable and self.current_editable is not None:
            self.current_editable.unselect()
        self.getViewBox().selection_mode = enable

    # ~~~~~~~~~~ Update handling ~~~~~~~~~

    def update_timestamp(self, timestamp: float):
        """Handle an update provided by the timing source.

        Handle initial drawing of decorators, redrawing of actual curves have
        to be implemented in the specific subclass.

        Args:
            timestamp: Updated timestamp provided by the timing source
        """
        if self._time_span:
            self._init_time_line_decorator(timestamp=timestamp)
            self._init_relative_time_axis_start(timestamp=timestamp)
            if np.isnan(self.last_timestamp) or timestamp >= self.last_timestamp:
                self._time_span.update(timestamp=timestamp)
                self._handle_scrolling_plot_fixed_xrange_update()
                self._update_time_line_decorator(
                    timestamp=timestamp,
                    position=self.time_span.x_pos(self.last_timestamp),
                )
            self._update_children_items_timing()
            self._draw_style_specific_objects()

    def plot_data_on_single_data_item(self,
                                      data: PlottingItemData,
                                      item_type: Type[DataModelBasedItem] = AbstractBasePlotCurve,
                                      **styling_kwargs):
        """
        This slot exposes the possibility to draw data on a
        single data item in the plot. If this item does not yet exist,
        it will be created automatically. If data gets appended or not
        is controlled by the plot item's plotting style.

        If the item type switches, the old item is replaced with the new one.

        Args:
            data: data to plot
            item_type: Item type which should represent the data
            styling_kwargs: Keyword arguments passed for styling purposes
        """
        if self.single_data_item_slot_source is None:
            self.single_data_item_slot_source = UpdateSource()
        if not isinstance(self.single_value_slot_dataitem, item_type):
            self.removeItem(self.single_value_slot_dataitem)
            self.single_value_slot_dataitem = None
        if self.single_value_slot_dataitem is None:
            item = item_type.from_plot_item(self,
                                            self.single_data_item_slot_source,
                                            **styling_kwargs)
            self.addItem(item)
            self.single_value_slot_dataitem = item
        self.single_data_item_slot_source.send_data(data)

    # ~~~~~~~~~~ Layers ~~~~~~~~~

    @staticmethod
    def is_standard_layer(layer: Optional["LayerIdentification"]) -> bool:
        """
        Check if layer identifier is referencing the standard. Passing no layer
        results in the layer being the standard layer.
        """
        if isinstance(layer, str):
            return layer in ("", PlotItemLayer.default_layer_id)
        if isinstance(layer, PlotItemLayer):
            return layer.id in ("", PlotItemLayer.default_layer_id)
        return layer is None

    def add_layer(
        self,
        layer_id: str,
        y_range: Optional[Tuple[float, float]] = None,
        y_range_padding: Optional[float] = None,
        invert_y: bool = False,
        pen: Optional[QPen] = None,
        link_view: Optional[pg.ViewBox] = None,
        max_tick_length: int = -5,
        show_values: bool = True,
        text: Optional[str] = None,
        units: Optional[str] = None,
        unit_prefix: Optional[str] = None,
        **axis_label_css_kwargs,
    ) -> "PlotItemLayer":
        """Add a new layer to the plot

        Adding multiple layers to a plot allows to plot different items in
        the same plot in different y ranges. Each layer comes per default
        with a separate y-axis that will be appended on the right side of
        the plot. An once added layer can always be retrieved by its string
        identifier that is chosen when creating the layer. In some function
        this string identifier will also be accepted as a keyword argument
        for executing operations on a layer.

        Args:
            layer_id: string identifier for the new layer, this one can later
                      be used to reference the layer and can be chosen freely

            y_range: set the view range of the new y axis on creation.
                     This is equivalent to calling setYRange(layer=...)
            y_range_padding: Padding to use when setting the y range
            invert_y: Invert the y axis of the newly created layer. This
                      is equivalent to calling invertY(layer=...)

            max_tick_length: maximum length of ticks to draw. Negative values
                             draw into the plot, positive values draw outward.
            link_view: causes the range of values displayed in the axis
                       to be linked to the visible range of a ViewBox.
            show_values: Whether to display values adjacent to ticks
            pen: Pen used when drawing ticks.

            text: The text (excluding units) to display on the label for this
                  axis
            units: The units for this axis. Units should generally be given
                   without any scaling prefix (eg, 'V' instead of 'mV'). The
                   scaling prefix will be automatically prepended based on the
                   range of data displayed.
            unit_prefix: prefix used for units displayed on the axis
            axis_label_css_kwargs: All extra keyword arguments become CSS style
                                   options for the <span> tag which will surround
                                   the axis label and units

        Returns:
            New created layer instance
        """
        new_view_box = ExViewBox()
        new_y_axis_orientation = "right"
        new_y_axis = ExAxisItem(
            orientation=new_y_axis_orientation,
            parent=self,
            pen=pen,
            linkView=link_view,
            maxTickLength=max_tick_length,
            showValues=show_values,
        )
        new_y_axis_position = (2, 2 + len(self._layers))
        new_y_axis.setZValue(len(self._layers))
        new_layer = PlotItemLayer(
            layer_id=layer_id,
            view_box=new_view_box,
            axis_item=new_y_axis,
        )
        self._layers.add(new_layer)
        self.layout.addItem(new_y_axis, *new_y_axis_position)
        self.axes[layer_id] = {
            "item": new_y_axis,
            "pos": (new_y_axis_orientation, new_y_axis_position),
        }
        self.scene().addItem(new_view_box)
        new_y_axis.linkToView(new_view_box)
        new_view_box.setXLink(self)
        new_y_axis.setLabel(
            text=text,
            units=units,
            unitPrefix=unit_prefix,
            **axis_label_css_kwargs,
        )
        new_view_box.sigStateChanged.connect(self.viewStateChanged)
        if y_range is not None:
            self.setYRange(
                min=y_range[0],
                max=y_range[1],
                padding=y_range_padding,
                layer=new_layer,
            )
        if invert_y:
            self.invertY(invert_y, layer=new_layer)
        return new_layer

    def remove_layer(self, layer: "LayerIdentification") -> bool:
        """
        Remove an already added layer by its reference or by its
        given string identifier.

        Args:
            layer: Either the layer by reference or by its identifier

        Returns:
            True if the layer existed and was removed

        Raises:
            KeyError: If an identifier is passed, no layer with the identifier
                      could be found
            Value Error: An object was passed that could not be associated with
                         any layer
        """
        if isinstance(layer, str) and layer != "":
            layer = self._layers.get(layer)
        if not isinstance(layer, PlotItemLayer):
            raise ValueError(f"The layer could not be removed, since it does not have the"
                             f"right type ({type(layer).__name__}) or the given identifier "
                             f"does not exist.")
        self.layout.removeItem(layer.axis_item)
        layer.axis_item.deleteLater()
        layer.axis_item.setParentItem(None)
        self.scene().removeItem(layer.view_box)
        layer.view_box.setParentItem(None)
        return self._layers.remove(layer=layer)

    def layer(self, layer_id: Optional[str] = None) -> "PlotItemLayer":
        """
        Get layer by its identifier. If no identifier is passed, the layer is
        returned, that contains the default view box and y axis of the plot.
        """
        if layer_id == "" or layer_id is None:
            layer_id = PlotItemLayer.default_layer_id
        return self._layers.get(layer_id)

    @property
    def view_boxes(self) -> List["ExViewBox"]:
        """List of all ViewBoxes included in this layer-collection."""
        return self._layers.view_boxes

    @property
    def layers(self) -> List["PlotItemLayer"]:
        """All layers added to this the plot."""
        return self._layers.all

    @property
    def non_default_layers(self) -> List["PlotItemLayer"]:
        """
        All layers added to this plot layer except of the layer
        containing the standard PlotItem ViewBox.
        """
        return self._layers.all_except_default

    # ~~~~~~~~~~ Plot Configuration ~~~~~~~~~

    def update_config(self, config: ExPlotWidgetConfig):
        """Update the plot widgets configuration

        Items that are affected from the configuration change are recreated with
        the new configuration and their old data models, so once displayed data is
        not lost. Static items, mainly pure PyQtGraph items, that were added to
        the plot, are not affected by this and will be kept unchanged in the plot.

        Args:
            config: The new configuration that should be used by the plot and all
                    its (affected) items
        """
        if hasattr(self, "_plot_config") and self._plot_config is not None:
            if (
                self._plot_config.time_span != config.time_span
                or self._plot_config.plotting_style != config.plotting_style
            ):
                self._plot_config = config
                items_to_recreate = self.live_items
                self._remove_child_items_affected_from_style_change()
                self._recreate_child_items_with_new_config(items_to_recreate)
                self._time_span = self._create_fitting_time_span()
                self._update_decorators()
                self._update_bottom_and_top_axis_style(style=config.plotting_style)
            elif self.plot_config.time_progress_line != config.time_progress_line:
                self._plot_config = config
                if config.time_progress_line:
                    timestamp = self.last_timestamp
                    if np.isnan(timestamp):
                        timestamp = 0.0
                    self._init_time_line_decorator(timestamp=timestamp, force=True)
                else:
                    self.removeItem(self._time_line)
                    self._time_line = None
        self._plot_config = config
        self._prepare_scrolling_plot_fixed_xrange()
        self._handle_scrolling_plot_fixed_xrange_update()

    def setRange(
        self,
        rect: Optional[QRectF] = None,
        xRange: Optional[Tuple[float, float]] = None,
        yRange: Optional[Tuple[float, float]] = None,
        padding: Optional[float] = None,
        update: bool = True,
        disableAutoRange: bool = True,
        **layer_y_ranges,
    ):
        """
        Set the visible range of the view. Additionally to setting the x and y
        range, the y range of additional layers of the plot can be set by passing
        their identifier as an keyword argument with the desired range as the value.
        Setting the view range of the layer "a" to 0 as the minimum and 1 as the
        maximum value would be:  setRange(..., a=(0, 1))

        Args:
            rect: The full range that should be visible in the view box.
            xRange: The range that should be visible along the x-axis.
            yRange: The range that should be visible along the y-axis.
            padding: Expand the view by a fraction of the requested range.
                     By default, this value is set between 0.02 and 0.1 depending on
                     the size of the ViewBox.
            update: If True, update the range of the ViewBox immediately.
                    Otherwise, the update is deferred until before the next render.
            disableAutoRange: If True, auto-ranging is disabled. Otherwise, it is left
                              unchanged.
            **layer_y_ranges: Next to setting the xRange and yRange, the y-range of an
                              added layer can be set by passing its identifier as key
                              and a tuple of min and max as the value.
        """
        if rect or xRange or yRange:
            self.getViewBox().setRange(
                rect=rect,
                xRange=xRange,
                yRange=yRange,
                padding=padding,
                update=update,
                disableAutoRange=disableAutoRange,
            )
        for layer_y_range in layer_y_ranges:
            self.getViewBox(layer=layer_y_range).setRange(
                yRange=layer_y_ranges[layer_y_range],
                padding=padding,
                update=update,
                disableAutoRange=disableAutoRange,
            )

    def setYRange(
        self,
        min: float,
        max: float,
        padding: Optional[float] = None,
        update: bool = True,
        layer: Optional["LayerIdentification"] = None,
    ):
        """
        Set the visible Y range of the view. If no layer is passed,
        the range of the default y axis will be moved (normally the
        one on the left side of the plot). By passing a layer, the
        range of the y axis of the layer will be moved.

        Args:
            min: smallest visible value
            max: highest visible value
            padding: padding around the visible range
            update: should the ViewBox be updated immediately
            layer: identifier or layer of which the
        """
        self.getViewBox(layer=layer).setYRange(
            min=min,
            max=max,
            padding=padding,
            update=update,
        )

    def invertY(
        self,
        b: bool,  # TODO: Convert to positional only when PEP-570 is implemented
        layer: Optional["LayerIdentification"] = None,
    ):
        """
        Allows inverting a y-axis. If no layer is passed, the default y axis
        will be inverted (normally the one on the left side of the plot). By
        passing a layer, the y axis of the layer will be inverted.

        Args:
            b: if True, the axis will be inverted
            layer: optional layer of which the y axis should be inverted
        """
        self.getViewBox(layer=layer).invertY(b)

    def setYLink(
        self,
        view: pg.ViewBox,
        layer: Optional["LayerIdentification"] = None,
    ):
        """
        Link the movement of a y axis to another ViewBox. If no layer is passed,
        the default y axis' movement will be linked (normally the one on the left
        side of the plot). By passing a layer, the the movement of the y-axis of
        that layer will be linked.

        Args:
            view: View that the movements in y direction should
                  be transferred to
            layer: In which layer is the y axis which movement should be
                   transferred. If empty, the standard y axis is used.
        """
        self.getViewBox(layer=layer).setYLink(view=view)

    def enableAutoRange(
            self,
            axis: Union[int, str, None] = None,
            enable: Union[bool, float] = True,
            x: Union[bool, float, None] = None,
            y: Union[bool, float, None] = None,
            **layers_y,
    ):
        """
        Extend the PlotItem's standard enableAutoRange for the y axes of
        all layers. This function can be called in two different ways.The
        first one is, to specify an axis and the enable parameter.
        Additionally to enable autoRange for multiple axes, you can specify x
        and y. Next to them you can pass layer identifier in the same way to
        enable autoRange for y-axes of different layers.

        If no axis information is passed at all, all available axes are auto
        ranged enabled, including the y axes of all layers added to the plot.

        Args:
            axis: Either an integer representing an axis (see f.e.
                  pg.Viewbox.XAxis) or the identifier of an layer which y
                  axis should be ranged automatically
            enable: True / False or a float from 0.0 to 1.0 of what amount
                    of the curve should be visible
            x: Instead of axis & enable, you can pass the enable value directly
               here, this allows auto ranging multiple axes with one call
            y: Instead of axis & enable, you can pass the enable value directly
               here, this allows auto ranging multiple axes with one call
            layers_y: Keyword arguments to enable autoRange for the y axes
                      of different layer, as key the layer's identifier is
                      used. This works like the x and y parameter of this
                      function
        """
        # enable auto range for the standard x and y axes
        super().enableAutoRange(
            axis=axis,
            enable=enable,
            x=x,
            y=y,
        )
        if axis is None and x is None and y is None and not layers_y:
            layers_y = {layer.id: True for layer in self.non_default_layers}
        if layers_y is not None and layers_y:
            for key, value in layers_y.items():
                self.getViewBox(layer=key).enableAutoRange(
                    axis=pg.ViewBox.YAxis,
                    enable=value,
                )

    def getViewBox(
            self,
            layer: Optional["LayerIdentification"] = None,
    ) -> "ExViewBox":
        """
        Extend the PlotItem's getViewBox method to also return viewboxes
        of layers if the layer or its identifier is provided.

        Args:
            layer: Either a reference to the layer or its identifier of which
                   the ViewBox should be looked up

        Returns:
            Default view box or the one associated with the passed layer.
        """
        if not layer:
            return super().getViewBox()
        if isinstance(layer, str):
            layer = self.layer(layer_id=layer)
        return layer.view_box

    def updateButtons(self):
        """
        Update the visibility of the auto button. This now also takes
        the autoRange state of ViewBox into consideration, that were
        added with additional layers.
        """
        try:
            show_button = (self._exportOpts is False
                           and self.mouseHovering
                           and not self.buttonsHidden
                           and (not all(self.vb.autoRangeEnabled())
                                or not all(l.view_box.autoRangeEnabled()[1] for l in self.non_default_layers)))
            if show_button:
                self.autoBtn.show()
            else:
                self.autoBtn.hide()
        except RuntimeError:
            pass  # this can happen if the plot has been deleted.

    def addLegend(
            self,
            size: Optional[Tuple[float, float]] = None,
            offset: Tuple[float, float] = (30, 30),
    ) -> ExLegendItem:
        """
        Create a new LegendItem and anchor it over the internal ViewBox.
        Plots will be automatically displayed in the legend if they
        are created with the 'name' argument.

        This overwritten version allows configuring text and background color.

        Args:
            size: Fixed size for the LegendItem
            offset: Static offset for the LegendItem

        Returns:
            ExLegendItem instance which was added to the PlotItem's default
            ViewBox
        """
        self.legend: Optional[ExLegendItem] = ExLegendItem(size=size, offset=offset)
        self.legend.setParentItem(self.getViewBox())
        return self.legend

    @property
    def timing_source_compatible(self) -> bool:
        """
        Can the plot in the current configuration work with timing sources? This is the case in:
            - Scrolling Live Data Plots
            - Cyclic Live Data Plots
        """
        return _STYLE_TO_TIMESPAN_MAPPING.get(self.plot_config.plotting_style) is not None

    @property
    def timing_source_attached(self) -> bool:
        """True, if the plot is attached to a timing source."""
        return self._timing_source_attached

    @property
    def last_timestamp(self) -> float:
        """Latest timestamp that is known to the plot."""
        return self.time_span.last_timestamp

    @property
    def plot_config(self) -> ExPlotWidgetConfig:
        """Configuration of time span and other plot related parameters"""
        return self._plot_config

    @property
    def time_span(self) -> BasePlotTimeSpan:
        """Time span for the current plot"""
        if self._time_span is None:
            raise ValueError("The plot does not have a time span in this configuration.", RuntimeWarning)
        return self._time_span

    # ~~~~~~~~~ Private ~~~~~~~~~~

    def _couple_layers_yrange(self, link: bool = True):
        """Link y ranges of all layers's y axis"""
        self._layers.couple_layers(link)

    def _update_layers(self):
        """Update the other layer's viewbox geometry to fit the PlotItem ones"""
        self._layers._update_view_box_geometries(self)

    def _init_time_line_decorator(self, timestamp: float, force: bool = False):
        """Create a vertical line representing the latest timestamp

        Args:
            timestamp: Position where to create the
            force: If true, a new time line will be created
        """
        if self._plot_config.time_progress_line and (force or np.isnan(self.last_timestamp)):
            label_opts = {"movable": True, "position": 0.96}
            if self._time_line is not None:
                self.removeItem(self._time_line)
                self._time_line = None
            ts = timestamp if not np.isnan(timestamp) else 0.0
            self._time_line = self.addLine(
                ts,
                pen=(pg.mkPen(80, 80, 80)),
                label=datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
                labelOpts=label_opts,
            )

    def _update_time_line_decorator(
            self,
            timestamp: float,
            position: Optional[float] = None,
    ):
        """Move the vertical line representing the current time to a new position

        Redraw the timing line according to a passed timestamp. Alternatively
        the line can also be drawn at a custom position by providing the
        position parameter, if the position is different from the provided
        timestamp (f.e. for the cyclic plot)

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
                self._time_line.label.setText(datetime.fromtimestamp(timestamp).strftime("%H:%M:%S"))

    def _config_contains_scrolling_style_with_fixed_xrange(self) -> bool:
        return(
            self._plot_config.plotting_style == PlotWidgetStyle.SCROLLING_PLOT
            and self._scrolling_fixed_xrange_activated
            and self._plot_config.time_span.finite
        )

    def _handle_scrolling_plot_fixed_xrange_update(self):
        """Set the viewboxes x range to the desired range if the start and end point are defined"""
        if self._config_contains_scrolling_style_with_fixed_xrange() and not np.isnan(self.last_timestamp):
            x_range_min: float = self.last_timestamp - self._plot_config.time_span.left_boundary_offset
            x_range_max: float = self.last_timestamp - self._plot_config.time_span.right_boundary_offset
            x_range: Tuple[float, float] = (x_range_min, x_range_max)
            self.getViewBox().setRange(xRange=x_range, padding=0.0)

    def _update_bottom_and_top_axis_style(self, style: PlotWidgetStyle):
        """
        Remove the old top and bottom axes and replace them with ones fitting to
        the passed plotting style.

        Args:
            style: plotting style the new axes should fit to.
        """
        for pos in ["bottom", "top"]:
            new_axis: pg.AxisItem = self._create_fitting_axis_item(config_style=style, orientation=pos, parent=self)
            if isinstance(new_axis, RelativeTimeAxisItem) and isinstance(self._time_span, CyclicPlotTimeSpan):
                new_axis.start = self._time_span.prev_start
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

    def _create_fitting_axis_item(
            self,
            config_style: PlotWidgetStyle,
            orientation: str = "bottom",
            parent: Optional["ExPlotItem"] = None,
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
        return ExAxisItem(orientation=orientation, parent=self)

    def _create_fitting_time_span(self) -> Optional[BasePlotTimeSpan]:
        """
        Create a time span object fitting to the passed config style. Parameters like the
        time span start and last time stamp are (if possible) taken from the old time span.
        """
        ts = None
        try:
            time_span = _STYLE_TO_TIMESPAN_MAPPING.get(self._plot_config.plotting_style)
            ts = cast(type, time_span)(time_span=self.plot_config.time_span)
            ts.update(self.time_span._start)
            ts.update(self.time_span._last_time_stamp)
        except (AttributeError, TypeError):
            # Attribute Error -> self._plot_config is not yet defined
            #                    (can happen in Qt Designer)
            # Type Error      -> No Time Span Object to initialize
            pass
        return ts

    def _draw_style_specific_objects(self):
        """Draw objects f.e. lines that are part of a specific plotting style

        - **CyclicPlotWidget**: Line at the time span start and end
        """
        if (
            self._plot_config.plotting_style == PlotWidgetStyle.CYCLIC_PLOT
            and not np.isnan(self.last_timestamp)
            and not self._style_specific_objects_already_drawn
        ):
            start = self.time_span._start
            end = self.time_span._end
            self._time_span_start_boundary = self.addLine(x=start, pen=pg.mkPen(128, 128, 128))
            self._time_span_end_boundary = self.addLine(x=end, pen=pg.mkPen(128, 128, 128))
            self._style_specific_objects_already_drawn = True

    def _update_children_items_timing(self):
        """Update timestamp in all items added to the plot item."""
        for item in self.items:
            if isinstance(item, DataModelBasedItem):
                item.update_item()

    def _init_relative_time_axis_start(self, timestamp: float):
        """Initialize the start time for the relative time axis.

        Args:
            timestamp: timestamp to set the start time of the axis to
        """
        if np.isnan(self.last_timestamp):
            for pos in ["bottom", "top"]:
                axis = self.getAxis(pos)
                if isinstance(axis, RelativeTimeAxisItem):
                    axis.start = timestamp

    def _connect_to_editable_item(self, item: EditablePlotCurve):
        """
        Try to connect to an editable item. If the item does not define the
        fitting signals, it will be silently skipped.
        """
        try:
            item.sig_selection_changed.connect(self._handle_curve_selection_change)
        except AttributeError:
            # Non editable items do not have this signal
            pass

    def _disconnect_from_editable_item(self, item: EditablePlotCurve):
        """
        Try to disconnect from an editable item. If the item does not define
        the fitting signals, it will be silently skipped.
        """
        try:
            item.sig_selection_changed.disconnect(self._handle_curve_selection_change)
        except AttributeError:
            pass

    def _handle_curve_selection_change(self):
        """
        Handle the selection change in the current editable item. If this
        slot is executed through sending a signal, the sender will be set as
        the current editable (if it is not already).
        """
        item = self.sender()
        if item and item is not self.current_editable:
            self.current_editable = item
        self.sig_selection_changed.emit()

    def _prepare_layers(self):
        """Initialize everything needed for multiple layers"""
        self._layers = PlotItemLayerCollection(self)
        self._layers.add(PlotItemLayer(
            view_box=self.vb,
            axis_item=self.getAxis("left"),
            layer_id=PlotItemLayer.default_layer_id,
        ))
        self.vb.sigResized.connect(self._update_layers)
        if isinstance(self.vb, ExViewBox):
            self.vb.layers = self._layers
        self._couple_layers_yrange(link=True)

    def _prepare_timing_source_attachment(self, timing_source: Optional[UpdateSource]):
        """Initialized everything needed for connection to the timing-source"""
        if timing_source and self.timing_source_compatible:
            self._timing_source_attached = True
            timing_source.sig_new_timestamp.connect(self.update_timestamp)
        else:
            self._timing_source_attached = False

    def _prepare_scrolling_plot_fixed_xrange(self):
        """
        In the scrolling style the PlotItem offers the possibility to set the
        scrolling movement not by using PyQtGraph's auto ranging, but by setting
        it manually to a fixed x range that moves as new data is appended. This
        will require some modifications to the plot which would otherwise collide
        with this behavior (mainly related to auto ranging).
        """
        self._scrolling_fixed_xrange_activated = True
        if self._config_contains_scrolling_style_with_fixed_xrange():
            self._set_scrolling_plot_fixed_xrange_modifications()
        else:
            self._reset_scrolling_plot_fixed_xrange_modifications()

    def _set_scrolling_plot_fixed_xrange_modifications(self):
        """
        Activating the fixed x range on a plot item in the scrolling mode
        will result in behavior modifications related to auto ranging.

        These include:
            - 'View All' context menu entry respects the manually set x range
            - the small auto range button on the lower left corner of the plot does
              not simply activate auto range but behaves as 'View All'
        """
        scrolling_range_reset_button = pg.ButtonItem(pg.pixmaps.getPixmap("auto"), 14, self)
        scrolling_range_reset_button.mode = "auto"
        scrolling_range_reset_button.clicked.connect(self._auto_range_with_scrolling_plot_fixed_xrange)
        self.vb.sig_xrange_changed.connect(self._stop_scrolling_plot_auto_xrange)
        self._orig_auto_btn = self.autoBtn
        self.autoBtn = scrolling_range_reset_button
        try:
            self.vb.menu.viewAll.triggered.disconnect(self.autoRange)
        except TypeError:
            pass
        self.vb.menu.viewAll.triggered.connect(self._auto_range_with_scrolling_plot_fixed_xrange)

    def _reset_scrolling_plot_fixed_xrange_modifications(self):
        """
        Activating the fixed x range on an plot item in the scrolling mode
        will result in modifications related to auto ranging. This function
        will revert all these made changes, if they were made.

        Following modifications are reset:
            - 'View All' context menu entry
            - the small auto range button in the lower left corner of the plot
        """
        if self._orig_auto_btn:
            self.autoBtn = self._orig_auto_btn
        try:
            self.vb.sig_xrange_changed.disconnect(self._stop_scrolling_plot_auto_xrange)
        except TypeError:
            # TypeError -> failed disconnect
            pass
        try:
            self.vb.menu.viewAll.triggered.disconnect(self._auto_range_with_scrolling_plot_fixed_xrange)
            self.vb.menu.viewAll.triggered.connect(self.autoRange)
        except TypeError:
            # TypeError -> failed disconnect
            pass

    def _auto_range_with_scrolling_plot_fixed_xrange(self):
        """
        autoRange does not know about the x range that has been set manually.
        This function will automatically set the y range and will set the x range
        fitting to the plots configuration.
        """
        self.autoRange(auto_range_x_axis=False)
        self._scrolling_fixed_xrange_activated = True
        self._handle_scrolling_plot_fixed_xrange_update()

    def _stop_scrolling_plot_auto_xrange(self):
        """
        If the range changes on a scrolling plot with a fixed x range, the scrolling
        should be stopped. This function sets a flag, that prevents the plot from
        scrolling on updates.
        """
        self._scrolling_fixed_xrange_activated = False

    def _remove_child_items_affected_from_style_change(self):
        """ Remove all items that are affected by a new configuration

        Remove all items attached to live data that depend on the plot item's PlottingStyle.
        Items in the plot that are not based on a datamodel and with that not attached to live
        data won't be removed (especially pure PyQtGraph items).
        Additionally all plotting style specific elements like time span boundaries or timing lines
        are removed.
        """
        for item in self.live_items:
            self.removeItem(item)
        self.removeItem(self._time_line)
        if self._time_span is not None:
            if self._time_span_start_boundary is not None:
                self.removeItem(self._time_span_start_boundary)
            if self._time_span_end_boundary is not None:
                self.removeItem(self._time_span_end_boundary)
        self._time_line = None
        self._time_span_start_boundary = None
        self._time_span_end_boundary = None

    def _recreate_child_items_with_new_config(self, items_to_recreate: List[DataModelBasedItem]):
        """
        Replace all items with ones that fit the given config.
        Datamodels are preserved.

        **IMPORTANT**: for this, the items have to be still listed in **PlotItem.items**,
        if they are not, they will not be recreated. After successful recreation the old
        items are removed from PlotItem.items
        """
        for item in items_to_recreate:
            try:
                new_item = cast(LivePlotCurve, item).clone(
                    object_to_create_from=cast(LivePlotCurve, item),
                )
                layer = item.layer_id
                self.addItem(layer=layer, item=new_item)
                self.removeItem(item)
            except AttributeError:
                pass

    def _update_decorators(self):
        """Update the decorators f.e. line representing current timestamp, time span boundaries"""
        if not np.isnan(self.last_timestamp):
            self._style_specific_objects_already_drawn = False
            self._draw_style_specific_objects()
        # we have to recreate the new
        self._init_time_line_decorator(timestamp=self.last_timestamp, force=True)


class PlotItemLayer:

    default_layer_id = "plot_item_layer"
    """
    Since all layers must have an identifier, this is the one of the default
    layer that is created on the plot creation.
    """

    def __init__(
        self,
        view_box: "ExViewBox",
        axis_item: pg.AxisItem,
        layer_id: str = default_layer_id,
    ):
        """
        Every item in a plot is drawn in a ViewBox, which's view range is represented
        by an axis item that is connected to update on every view range change in the
        ViewBox. Because of this, adding a new y-axis requires adding an additional
        ViewBox. This ViewBox and the belonging axis is collected in a so called layer.

        Args:
            view_box: ViewBox this layer is referring to
            axis_item: AxisItem this layer is referring to
            layer_id: Name of the layer, which is used to retrieve it from the collection
                      This name can be freely chosen, as long as there does not exist a
                      layer with the same name
        """
        self._layer_id: str = layer_id
        self._axis_item: pg.AxisItem = axis_item
        self._view_box: ExViewBox = view_box
        self._view_box.enableAutoRange(enable=True)

    def __del__(self):
        del self._axis_item
        del self._view_box

    @property
    def id(self) -> str:
        """String identifier for the layer."""
        return self._layer_id

    @property
    def view_box(self) -> "ExViewBox":
        """ViewBox of the layer."""
        return self._view_box

    @property
    def axis_item(self) -> pg.AxisItem:
        """ViewBox of the layer."""
        return self._axis_item

    def __eq__(self, other: Any) -> bool:
        """Check equality of layers by their identifier."""
        if isinstance(other, str):
            return self.id == other
        if isinstance(other, PlotItemLayer):
            return self.id == other.id
        return False


# For the identification of an PlotItemLayer we can either use the
# layer instance itself or its identifier. This Union can be used
# as a type hints for these scenarios.
LayerIdentification = Union[PlotItemLayer, str]


class PlotItemLayerCollection:

    def __init__(self, plot_item: pg.PlotItem):
        """
        Collection for PlotItemLayers added to a PlotItem identified by a
        unique string identifier.

        Args:
            plot_item: PlotItem in which the layers in these collection are located
        """
        self._plot_item = plot_item
        self._vb_ref_ranges: Dict[str, Range] = {}
        """Layer Id to range mapping"""
        # Flag if the plot item viewboxes range change should be applied to other layers
        self._forward_range_change_to_other_layers: Tuple[bool, bool] = (False, True)
        self._layers: Dict[str, PlotItemLayer] = {}

    def __iter__(self):
        return iter(self._layers.values())

    def __len__(self):
        return len(self._layers)

    def get(self, identifier: Optional[str] = None) -> PlotItemLayer:
        """
        Get layer by its identifier.

        Args:
            identifier: Identifier of the layer that should be searched. ``None`` or an empty string will
                        result in the layer containing the standard y-axis and viewbox of the
                        :class:`pyqtgraph.PlotItem`.

        Returns:
            Layer object that is associated with the identifier or the default layer.

        Raises:
            KeyError: Layer with given identifier does not exist.
        """
        identifier = identifier or PlotItemLayer.default_layer_id
        try:
            return self._layers[identifier]
        except KeyError:
            raise KeyError(f"No layer with the identifier '{identifier}'")

    def add(self, layer: PlotItemLayer):
        """
        Add layer object to this collection to keep track of it. This does not automatically add the
        layer to the view box.

        Args:
            layer: Layer to be added.

        Raises:
            KeyError: A layer with the passed identifier does already exist
                      in the collection.
            ValueError: The passed layer can not be added since it is no
                        valid layer
        """
        if layer is None or not layer.id:
            # TODO: Assume layer is never None (as per api)?
            # TODO: Separate errors into 2
            # TODO: All should be ValueError, event Key. (API breaking change). Change docstring as well.
            raise ValueError("Layer can not be added because it or its identifier is not defined.")
        if layer.id in self._layers:
            raise KeyError(f"Layer with the identifier '{layer.id}' has already been added."
                           f"Either rename the layer or remove the already existing one before adding.")
        self._layers[layer.id] = layer
        self._vb_ref_ranges[layer.id] = Range.from_pg_range(layer.axis_item.range)

    def remove(self, layer: Optional[LayerIdentification] = None) -> bool:
        """
        Remove a layer from the collection.

        Args:
            layer: Layer instance or identifier to delete.

        Returns:
            ``True`` if the layer was in collection.

        Raises:
            KeyError: No layer with the passed identifier could be found
        """
        if isinstance(layer, str):
            layer = self.get(layer)
        for lyr in self:
            if layer != lyr:
                continue
            del self._layers[lyr.id]
            if lyr.id in self._vb_ref_ranges:
                del self._vb_ref_ranges[lyr.id]
            # TODO: Feels complicated
            del lyr
            return True
        return False

    def couple_layers(self, link: bool):
        """
        Link movements in all layers in Y-ranges.

        Scale and translate all layers as if they were one, when transformed
        by interaction with the mouse (except if performed on a specific axis)
        When moving the layers each will keep its range relative to the made
        transformation. For example:

        * Layer *L1* with the Y-range (0, 1)
        * Layer *L2* with the Y-range (-2, 2)

        Moving *L1* to (1, 2) will translate *L2*'s range to (0, 4).

        Args:
            link: ``True`` if layers should be moved together.
        """
        layer = self.get()
        if link:
            # filter by range changes that are executed on the
            layer.axis_item.sig_vb_mouse_event_triggered_by_axis.connect(self._handle_axis_triggered_mouse_event)
            layer.view_box.sigRangeChangedManually.connect(self._handle_layer_manual_range_change)
            # when plot item gets moved, check if other layers should be moved
            layer.view_box.sigYRangeChanged.connect(self._handle_layer_y_range_change)
            for layer in self:
                self._vb_ref_ranges[layer.id] = Range.from_pg_range(layer.axis_item.range)
        else:
            # Remove connections again
            layer.axis_item.sig_vb_mouse_event_triggered_by_axis.disconnect(self._handle_axis_triggered_mouse_event)
            layer.view_box.sigYRangeChanged.disconnect(self._handle_layer_y_range_change)
            layer.view_box.sigRangeChangedManually.disconnect(self._handle_layer_manual_range_change)

    @property
    def all(self) -> List[PlotItemLayer]:
        """A list of all layers in this collection."""
        return list(self._layers.values())

    @property
    def all_except_default(self) -> List[PlotItemLayer]:
        """List of all layers except the default one."""
        layers = {**self._layers}
        try:
            del layers[PlotItemLayer.default_layer_id]
        except KeyError:
            pass
        return list(layers.values())

    @property
    def view_boxes(self) -> List["ExViewBox"]:
        """All viewboxes contained in this collection's layers."""
        return [layer.view_box for layer in self]

    def _update_view_box_geometries(self, plot_item: pg.PlotItem):
        for layer in self:
            # plot item view box has to be excluded to keep autoRange settings
            if not self._plot_item.is_standard_layer(layer=layer):
                layer.view_box.setGeometry(plot_item.vb.sceneBoundingRect())
                layer.view_box.linkedViewChanged(plot_item.vb, layer.view_box.XAxis)

    def _set_range_change_forwarding(
            self,
            change_is_manual: Optional[bool] = None,
            mouse_event_valid: Optional[bool] = None,
    ):
        """
        With passing True, a manual range change of the ViewBox of a layer will be applied
        accordingly to all other layers. When passing false, we can prevent manual range
        changes to be applied to other layers.

        This function can e.g. be used to make sure that the flag is not set from a Mouse
        Event on an axis, that set the flag to false which is still activated even though
        we do not care about it anymore.

        Args:
            change_is_manual: the range change was done manually and should be applied
            mouse_event_valid: the mouse event was valid and should be applied (it was
                not performed on a single axis)
        """
        if change_is_manual is not None:
            self._forward_range_change_to_other_layers = change_is_manual, self._forward_range_change_to_other_layers[1]
        if mouse_event_valid is not None:
            self._forward_range_change_to_other_layers = self._forward_range_change_to_other_layers[0], mouse_event_valid

    def _reset_range_change_forwarding(self):
        """Set the flag that forwards range changes to true"""
        self._set_range_change_forwarding(change_is_manual=False,
                                          mouse_event_valid=True)

    def _handle_axis_triggered_mouse_event(self, mouse_event_on_axis: bool):
        """ Handle the results of mouse drag event on the axis

        Mouse Events on the Viewbox and Axis are not distinguishable in pyqtgraph. Because of this,
        mouse events on the axis now emit a special signal. Since we only want Mouse Drag events on the
        actual Viewbox to affect the other layers view-range we have to filter out the Mouse
        Drag Events executed on the axis.

        Args:
            mouse_event_on_axis: True if the mouse event was executed while on the axis
        """
        self._set_range_change_forwarding(mouse_event_valid=(not mouse_event_on_axis))

    def _handle_layer_manual_range_change(self, mouse_enabled: List[bool]):
        """ Make Range update slot available, if range change was done by an Mouse Drag Event

        Args:
            mouse_enabled: List of bools if mouse interaction is enabled on the x, y axis, expected list length is 2
        """
        self._set_range_change_forwarding(change_is_manual=mouse_enabled[1])

    def _handle_layer_y_range_change(self, moved_viewbox: pg.ViewBox, new_range: Tuple[float, float], *args):
        """
        Handle a view-range change in the PlotItems Viewbox

        If a mouse drag-event has been executed on the PlotItem's Viewbox and not on
        the axis-item we want to move all other layer's viewboxes accordingly and
        respecting their own view-range so all layers move by the same pace.

        Args:
            moved_viewbox: Viewbox that was originally moved
            new_range: new range the ViewBox now shows
            *args: Does not get used, this is just for catching additionally
                   passed arguments in case the Event sends more values than
                   expected
        """
        if args:
            warnings.warn(f"More values were received than expected: {args}")
        layer = self.get()
        if all(self._forward_range_change_to_other_layers):
            self._apply_range_change_to_other_layers(
                moved_viewbox=moved_viewbox,
                new_range=Range.from_pg_range(new_range),
                moved_layer=layer,
            )
        self._reset_range_change_forwarding()
        # Update saved range even if not caused by manual update (f.e. by "View All")
        self._vb_ref_ranges[layer.id] = Range.from_pg_range(layer.axis_item.range)

    def _apply_range_change_to_other_layers(
            self,
            moved_viewbox: pg.ViewBox,
            new_range: Range,
            moved_layer: PlotItemLayer,
    ):
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
        """
        prev_range = self._vb_ref_ranges[moved_layer.id]
        self._vb_ref_ranges[moved_layer.id] = new_range
        for layer in self:
            if layer.view_box is not moved_viewbox:
                layer_range = Range.from_pg_range(layer.axis_item.range)
                scale = layer_range.span / prev_range.span
                new_layer_range = Range(min=layer_range.min + (new_range.min - prev_range.min) * scale,
                                        max=layer_range.max + (new_range.max - prev_range.max) * scale)
                layer.view_box.setRange(yRange=(new_layer_range.min, new_layer_range.max), padding=0.0)
                self._vb_ref_ranges[layer.id] = new_layer_range


class ExViewBox(pg.ViewBox):

    sig_selection = Signal(QRectF)
    """
    If the view box is in selection mode, a mouse drag produces a selection
    rectangle for selecting points. This signal will publish this rectangle
    as soon as its completed (the mouse button from the drag is released).
    The selection boundaries is represented in scene coordinates and not
    device coordinates.
    """

    sig_xrange_changed = Signal()
    """This is a replacement for sigRangeChangedManually to disable auto-scrolling only when dragging and zooming in a particular way"""

    def __init__(self, **viewbox_kwargs):
        """
        ViewBox with extra functionality for the multi-y-axis plotting.

        Args:
            **viewbox_kwargs: Keyword arguments for the base class ViewBox
        """
        super().__init__(**viewbox_kwargs)
        # point selection box
        self._selection_box = QGraphicsRectItem(0, 0, 1, 1)
        self._selection_box.setPen(pg.mkPen((255, 0, 0), width=1))
        self._selection_box.setBrush(pg.mkBrush(255, 0, 0, 100))
        self._selection_box.setZValue(1e9)
        self._selection_box.hide()
        self.addItem(self._selection_box, ignoreBounds=True)

        self.selection_mode: bool = False
        """When ``True``, mouse drag events on the view box create selection rectangles and do not move the view"""

        self.layers: Optional[PlotItemLayerCollection] = None
        """Collection of layers that are included in this viewbox."""

    def autoRange(
        self,
        padding: Optional[float] = None,
        items: Optional[List[pg.GraphicsItem]] = None,
        auto_range_x_axis: bool = True,
        **kwargs,
    ):
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
        """
        item = kwargs.get("item")  # deprecated param from superclass
        if item and not items:
            items = [item]
        if self.layers is not None:
            if padding is None:
                padding = 0.05
            primary_vb = self.layers.get(identifier=PlotItemLayer.default_layer_id).view_box
            other_viewboxes = [vb for vb in self.layers.view_boxes if vb is not primary_vb and vb.addedItems]
            target_bounds = primary_vb.childrenBoundingRect(items=items)
            # Get common bounding rectangle for all items in all layers
            for vb in other_viewboxes:
                bounds = vb._bounding_rect_from(another_vb=primary_vb, items=items)
                target_bounds = target_bounds.united(bounds)

            primary_vb.enableAutoRange(x=auto_range_x_axis, y=True)

            # Setting the range with the manual signal will move all other layers accordingly
            if auto_range_x_axis:
                primary_vb.set_range_manually(rect=target_bounds, padding=padding, disableAutoRange=False)
            else:
                y_range = target_bounds.bottom(), target_bounds.top()
                primary_vb.set_range_manually(yRange=y_range, padding=padding, disableAutoRange=False)

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent, axis: Optional[int] = None):
        """
        Overwritten because we want to make sure the manual range
        change signal comes first. To make sure no flags are set anymore
        from the event we emit a range change signal with unmodified range.

        Args:
            ev: Wheel event that was detected
            axis: integer representing an axis, 0 -> x, 1 -> y, None -> both
        """
        if axis != 1:
            self.sig_xrange_changed.emit()
        self.sigRangeChangedManually.emit(self.state["mouseEnabled"])
        super().wheelEvent(ev=ev, axis=axis)
        self.sigRangeChanged.emit(self, self.state["viewRange"])

    def mouseDragEvent(self, ev: MouseDragEvent, axis: Optional[int] = None):
        """
        Overwritten because we want to make sure the manual range
        change signal comes first. To make sure no flags are set anymore
        from the event we emit a range change signal with unmodified range.

        Args:
            ev: Mouse Drag event that was detected
            axis: integer representing an axis, 0 -> x, 1 -> y
        """
        if self.selection_mode:
            self._selection_mouse_drag_event(ev=ev)
        else:
            if axis != 1:
                self.sig_xrange_changed.emit()
            self.sigRangeChangedManually.emit(self.state["mouseEnabled"])
            super().mouseDragEvent(ev=ev, axis=axis)
            self.sigRangeChanged.emit(self, self.state["viewRange"])

    def _selection_mouse_drag_event(self, ev: MouseDragEvent):
        """
        Mouse drag event handler for selecting a region in the view box
        for selecting data. If the selection event is finished, a signal
        is emitted, which contains the selection as a QRectF.

        Args:
            ev: mouse drag event
        """
        ev.accept()
        if ev.button() & (Qt.LeftButton | Qt.MidButton):
            if ev.isFinish():
                self._selection_box.hide()
                top_left = pg.Point(ev.buttonDownPos(ev.button()))
                bottom_right = pg.Point(ev.pos())
                selection = QRectF(top_left, bottom_right)
                # Map the rectangle from the view range to the shown
                # data range
                selection = self.childGroup.mapRectFromParent(selection)
                self.sig_selection.emit(selection)
            else:
                self._update_selection_box(ev.buttonDownPos(), ev.pos())

    def set_range_manually(self, **kwargs):
        """ Set range manually

        Set range, but emit a signal for manual range change to
        to trigger all other layers to be moved simultaneous.

        Args:
            **kwargs: Keyword arguments that ViewBox.setRange accepts
        """
        if not kwargs.get("padding"):
            kwargs["padding"] = 0.0
        if self.layers is not None:
            # If we call this explicitly we do not care about prior set flags for range changes
            self.layers._reset_range_change_forwarding()
        self.sigRangeChangedManually.emit(self.state["mouseEnabled"])
        self.setRange(**kwargs)

    def _bounding_rect_from(
            self,
            another_vb: "ExViewBox",
            items: Optional[List[pg.GraphicsItem]],
    ) -> QRectF:
        """
        Map a view box bounding rectangle to the coordinates of an other one.
        It is expected that both ViewBoxes have synchronized x ranges, so the
        x range of the mapped bounding rectangle will be the same.

        Args:
            another_vb: view box that the bounding rectangle should
                        be mapped to (normally standard plot-item vb)
            items: items which bounding rectangles are used for the mapping

        Returns:
            Bounding rectangle in the standard plot item view box that includes all
            items from all layers.
        """
        bounds: QRectF = self.childrenBoundingRect(items=items)
        target_range = Range(min=another_vb.targetRect().top(),
                             max=another_vb.targetRect().bottom())
        min_target_y = self._map_y_value_to(value=bounds.bottom(), target_range=target_range)
        max_target_y = self._map_y_value_to(value=bounds.top(), target_range=target_range)
        return QRectF(
            bounds.x(), min_target_y,
            bounds.width(), max_target_y - min_target_y,
        )

    def _map_y_value_to(self, value: float, target_range: Range) -> float:
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
            value: Y value to map
            target_range: shown view-range from the layer the coordinates
                                 should be mapped to

        Returns:
            Y coordinate in the destinations ViewBox
        """
        src_range = Range(min=self.targetRect().top(),
                          max=self.targetRect().bottom())
        m: float = target_range.span / src_range.span
        c: float = target_range.min - m * src_range.min
        return m * value + c

    def _update_selection_box(self, top_left: QPointF, bottom_right: QPointF):
        """
        Update the viewboxes selection rectangle.

        Args:
            top_left: Top left coordinate of the selection rectangle.
            bottom_right: Bottom right coordinate of the selection rectangle.
        """
        r = QRectF(top_left, bottom_right)
        r = self.childGroup.mapRectFromParent(r)
        self._selection_box.setPos(r.topLeft())
        self._selection_box.resetTransform()
        self._selection_box.scale(r.width(), r.height())
        self._selection_box.show()
