"""
Extended Widget for custom plotting with simple configuration wrappers
"""

from typing import Dict, Optional, Any, Set, List, Tuple, Union, cast, Sequence
from copy import deepcopy
import json
import warnings
from dataclasses import dataclass

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Signal, Slot, Property, Q_ENUM, Qt
from qtpy.QtWidgets import QWidget
from qtpy.QtGui import QPen, QMouseEvent, QColor

from accwidgets.graph.datamodel.connection import UpdateSource, PlottingItemDataFactory
from accwidgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
    TimeSpan,
)
from accwidgets.graph.widgets.plotitem import (
    ExPlotItem,
    PlotItemLayer,
    LayerIdentification,
)
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.plotdataitem import AbstractBasePlotCurve
from accwidgets.graph.widgets.dataitems.bargraphitem import (
    LiveBarGraphItem,
    AbstractBaseBarGraphItem,
)
from accwidgets.graph.widgets.dataitems.injectionbaritem import (
    LiveInjectionBarGraphItem,
    AbstractBaseInjectionBarGraphItem,
)
from accwidgets.graph.widgets.dataitems.timestampmarker import LiveTimestampMarker
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import DataModelBasedItem
from accwidgets.graph.widgets.axisitems import ExAxisItem
from accwidgets.graph.datamodel.datastructures import (
    PointData,
    CurveData,
    BarCollectionData,
    InjectionBarCollectionData,
)
from accwidgets import designer_check


class SymbolOptions:
    NoSymbol = 0
    Circle = 1
    Square = 2
    Triangle = 3
    Diamond = 4
    Plus = 5


@dataclass
class SlotItemStylingOpts:
    """Styling Options for the Slot Items"""
    pen_color: QColor = QColor(255, 255, 255)
    pen_width: int = 1
    pen_style: Qt.PenStyle = Qt.SolidLine
    brush_color: QColor = QColor(255, 255, 255)
    symbol: int = SymbolOptions.NoSymbol


class ExPlotWidget(pg.PlotWidget):

    Q_ENUM(SymbolOptions)

    sig_selection_changed = Signal()
    """
    Signal informing about any changes to the current selection of the current
    editable item. If the emitted data is empty, the current selection was
    unselected. The signal will also be emitted, if the current selection has
    been moved around by dragging.

    In general this signal will only be emitted in a editable configuration.
    """

    sig_plot_selected = Signal(bool)
    """
    Signal informing about an entire plot being selected for editing.
    """

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            config: Optional[ExPlotWidgetConfig] = None,
            axis_items: Optional[Dict[str, ExAxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        """Extended PlotWidget

        Extended version of PyQtGraphs PlotWidget with additional functionality
        like adding multiple y-axes as well as convenient live data plotting
        capabilities. Derived from this there exist more specified versions of
        this class that are suitable for specific type of plotting. For example
        the ScrollingPlotWidget which is suitable for displaying arriving data
        in a scrolling plot. This baseclass unifies all these capabilities into
        one widget that is customizable by defining and passing an configuration
        object.

        Note:
        By default some properties the ExPlotWidget offers, are not designable, since
        they only make sense with a single plotting style. In subclasses for designer,
        where they are used, set designable explicitly to True to make them appear in
        the property sheet.

        Args:
            parent: parent item for this widget, will only be passed to base class
            background: background for the widget, will only be passed to base class
            config: Configuration object that defines any parameter that influences the
                    visual representation and the amount of data the plot should show.
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            timing_source: Mainly for live data plotting. This timing source allows
                           to receive timing updates decoupled from any received
                           data.
            **plotitem_kwargs: Params passed to the plot item
        """
        super().__init__(parent=parent, background=background)
        config = config or ExPlotWidgetConfig()
        if axis_items is None:
            axis_items = {}
        self.timing_source = timing_source
        axis_items = axis_items or {}
        # From base class
        self.plotItem: ExPlotItem
        self._init_ex_plot_item(
            axis_items=axis_items,
            config=config,
            timing_source=timing_source,
            **plotitem_kwargs,
        )
        self._wrap_plotitem_functions()
        self._slot_item_styling_opts = SlotItemStylingOpts()

    def addCurve(
            self,
            c: Optional[pg.PlotDataItem] = None,
            params: Optional[Any] = None,
            data_source: Optional[UpdateSource] = None,
            layer: Optional[LayerIdentification] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **plotdataitem_kwargs,
    ) -> pg.PlotDataItem:
        """Add a new curve attached to a source for new data

        Create a curve fitting to the style of the plot and add it to the plot.
        The new curve can be either either created from static data like
        PlotItem.plot or from a data source that handles communication between
        the curve and a source data is coming from. To create a curve attached
        to e.g. live data, pass a fitting data source and to create a curve
        from e.g. a static array, pass keyword arguments from the PlotDataItem.

        Args:

            data_source: source for new data that the curve should display
            layer: identifier of the layer the new curve is supposed to be added to
            buffer_size: maximum count of values the datamodel buffer should hold

            c: PlotDataItem instance that is added, for backwards compatibility
               to the original function
            params: params for c, for backwards compatibility to the original
                    function

            **plotdataitem_kwargs: Parameters for creating a pure pyqtgraph PlotDataItem

        Returns:
            PlotDataItem or LivePlotCurve instance depending on the passed parameters
        """
        return self.plotItem.addCurve(
            c=c,
            params=params,
            data_source=data_source,
            layer=layer,
            buffer_size=buffer_size,
            **plotdataitem_kwargs,
        )

    def addBarGraph(
            self,
            data_source: Optional[UpdateSource] = None,
            layer: Optional[LayerIdentification] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **bargraph_kwargs,
    ) -> LiveBarGraphItem:
        """Add a new curve attached to a source for new data

        Create a bar graph fitting to the style of the plot and add it to the plot.
        The new graph can be either either created from static data like
        PlotItem.plot or from a data source that handles communication between
        the graph and a source data is coming from. To create a bar graph attached
        to e.g. live data, pass a fitting data source and to create a bar graph
        from e.g. a static array, pass keyword arguments from the BarGraphItem.

        Args:
            data_source: Source emitting new data the graph should show
            layer: Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **bargraph_kwargs: keyword arguments for the BarGraphItem base class

        Returns:
            BarGraphItem or LiveBarGraphItem, depending on the passed parameters,
            that was added to the plot.
        """
        return self.plotItem.addBarGraph(
            data_source=data_source,
            layer=layer,
            buffer_size=buffer_size,
            **bargraph_kwargs,
        )

    def addInjectionBar(
            self,
            data_source: UpdateSource,
            layer: Optional[LayerIdentification] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **errorbaritem_kwargs,
    ) -> LiveInjectionBarGraphItem:
        """Add a new injection bar graph

        The new injection bar graph is attached to a source for receiving data
        updates. An injection bar is based on PyQtGraph's ErrorBarItem with the
        ability to add Text Labels.

        Args:
            data_source: Source for data related updates
            layer: Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **errorbaritem_kwargs: Keyword arguments for the ErrorBarItems used in the Injectionbars

        Returns:
            LiveInjectionBarGraphItem that was added to the plot.
        """
        return self.plotItem.addInjectionBar(
            data_source=data_source,
            layer=layer,
            buffer_size=buffer_size,
            **errorbaritem_kwargs,
        )

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
            data_source: Source for data related updates,
            buffer_size: maximum count of values the datamodel buffer should hold
            *graphicsobjectargs: Arguments passed to the GraphicsObject base class

        Returns:
            LiveTimestampMarker that was added to the plot.
        """
        return self.plotItem.addTimestampMarker(
            *graphicsobjectargs,
            data_source=data_source,
            buffer_size=buffer_size,
        )

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
        """Add a new layer to the plot.

        Adding multiple layers to a plot allows to plot different items in
        the same plot in different y ranges. Each layer comes per default
        with a separate y-axis that will be appended on the right side of
        the plot. An once added layer can always be retrieved by its string
        identifier that is chosen when creating the layer. This identifier
        can also be used when setting the view range or other operations on
        the layer.

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
            New created layer
        """
        return self.plotItem.add_layer(
            layer_id=layer_id,
            y_range=y_range,
            y_range_padding=y_range_padding,
            invert_y=invert_y,
            pen=pen,
            link_view=link_view,
            max_tick_length=max_tick_length,
            show_values=show_values,
            text=text,
            units=units,
            unit_prefix=unit_prefix,
            **axis_label_css_kwargs,
        )

    def update_config(self, config: ExPlotWidgetConfig):
        """Update the plot widgets configuration

        Items that are affected from the configuration change are recreated with
        the new configuration and their old datamodels, so once displayed data is
        not lost. Static items, mainly pure PyQtGraph items, that were added to
        the plot, are not affected by this and will be kept unchanged in the plot.

        Args:
            config: The new configuration that should be used by the plot and all
                    its (affected) items
        """
        self.plotItem.update_config(config=config)

    # ~~~~~~~~~~~~~~~~~~ Functionality for editble plots ~~~~~~~~~~~~~~~~~~~~~~

    def mouseDoubleClickEvent(self, ev: QMouseEvent):
        """
        When double clicking a PlotItem, it can be selected as the plot item
        which should be edited. To inform e.g. and editable button bar about
        a selection, a fitting signal is emitted.

        Args:
            ev: Event
        """
        super().mouseDoubleClickEvent(ev)
        self.plotItem.toggle_plot_selection()

    def replace_selection(self, replacement: CurveData):
        """Function to call if the current data selection was changed.

        Args:
            replacement: The data to replace the indices with
        """
        self.plotItem.replace_selection(replacement=replacement)

    @property
    def current_selection_data(self) -> Optional[CurveData]:
        """Get the selected data as a curve data."""
        return self.plotItem.current_selection_data

    @property
    def selection_mode(self) -> bool:
        """
        If the selection mode is enabled, mouse drag events on the view
        box create selection rectangles and do not move the view
        """
        return self.plotItem.selection_mode

    @Slot(bool)
    def set_selection_mode(self, enable: bool):
        """
        If the selection mode is enabled, mouse drag events on the view
        box create selection rectangles and do not move the view
        """
        self.plotItem.selection_mode = enable

    @Slot()
    def send_currents_editable_state(self) -> bool:
        """
        Send the state of the current editable item back to the process it
        received it from. If there was no state change, nothing is sent.

        Returns:
            True if something was sent back
        """
        return self.plotItem.send_currents_editable_state()

    @Slot()
    def send_all_editables_state(self) -> List[bool]:
        """
        Send the states of all editable items to the processes they are
        connected to.

        Returns:
            List of Trues, if the states of all items have been sent
        """
        return self.plotItem.send_all_editables_state()

    # ~~~~~~~~~~ Properties ~~~~~~~~~

    def _get_plot_title(self) -> str:
        """QtDesigner getter function for the PlotItems title"""
        if self.plotItem.titleLabel.isVisible():
            return self.plotItem.titleLabel.text
        return ""

    def _set_plot_title(self, new_val: str):
        """QtDesigner setter function for the PlotItems title"""
        if new_val != self.plotItem.titleLabel.text:
            new_val = new_val.strip()
            if new_val:
                self.plotItem.setTitle(new_val)
            else:
                # will hide the title label
                self.plotItem.setTitle(None)

    plotTitle: str = Property(str, _get_plot_title, _set_plot_title)
    """Title shown at the top of the plot"""

    def _get_show_time_line(self) -> bool:
        """QtDesigner getter function for the PlotItems flag for showing the current timestamp with a line"""
        return self.plotItem.plot_config.time_progress_line

    def _set_show_time_line(self, new_val: bool):
        """QtDesigner setter function for the PlotItems flag for showing the current timestamp with a line"""
        if new_val != self.plotItem.plot_config.time_progress_line:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_progress_line = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    showTimeProgressLine: bool = Property(bool, _get_show_time_line, _set_show_time_line)
    """Vertical Line displaying the current time stamp"""

    def _get_right_time_span_boundary(self) -> float:
        """QtDesigner getter function for the PlotItems time span size"""
        return self.plotItem.plot_config.time_span.right_boundary_offset

    def _set_right_time_span_boundary(self, new_val: float):
        """QtDesigner setter function for the PlotItems time span size"""
        if new_val != self.plotItem.plot_config.time_span.right_boundary_offset:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_span.right_boundary_offset = new_val
            if new_val > new_config.time_span.left_boundary_offset:
                new_config.time_span.left_boundary_offset = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    rightTimeBoundary: float = Property(
        float,
        _get_right_time_span_boundary,
        _set_right_time_span_boundary,
        designable=False,
    )
    """Value of the Left / Lower boundary for the Plot's timestamp"""

    def _get_left_time_span_boundary(self, hide_nans: bool = True) -> float:
        """
        QtDesigner getter function for the PlotItems time span size. When called
        from designer, nan and inf are masked, when called from code, they will
        return the nan and inf values. This is done since inf and nan are not
        displayed very well in the QtDesigner property sheet.

        Args:
            hide_nans: Returns the last not nan value instead of nan / inf, since
                       nan / inf in the property fields is displayed as gibberish
        """
        potential = self.plotItem.plot_config.time_span.left_boundary_offset
        if not designer_check.is_designer():
            hide_nans = False
        if hide_nans and (np.isinf(potential) or np.isnan(potential)):
            try:
                potential = self._left_time_span_boundary_bool_value_cache
            except NameError:
                potential = 60.0
        return potential

    def _set_left_time_span_boundary(self, new_val: float):
        """QtDesigner setter function for the PlotItems time span size"""
        if new_val != self._get_left_time_span_boundary(hide_nans=False):
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_span.left_boundary_offset = new_val
            if new_val < new_config.time_span.right_boundary_offset:
                new_config.time_span.right_boundary_offset = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    leftTimeBoundary: float = Property(
        float,
        _get_left_time_span_boundary,
        _set_left_time_span_boundary,
        designable=False,
    )
    """Value of the Left / Lower boundary for the Plot's timestamp"""

    def _get_left_time_span_boundary_bool(self) -> bool:
        """QtDesigner getter function for the PlotItems time span size"""
        return not np.isinf(self._get_left_time_span_boundary(hide_nans=False))

    def _set_left_time_span_boundary_bool(self, new_val: bool):
        """QtDesigner setter function for the PlotItems time span size"""
        if not new_val:
            potential = self.plotItem.plot_config.time_span.left_boundary_offset
            if potential and not np.isinf(potential):
                self._left_time_span_boundary_bool_value_cache = potential
            self._set_left_time_span_boundary(new_val=np.inf)
        elif np.isinf(self._get_left_time_span_boundary(hide_nans=False)):
            try:
                potential = self._left_time_span_boundary_bool_value_cache
                if potential < self.plotItem.plot_config.time_span.right_boundary_offset:
                    potential = self.plotItem.plot_config.time_span.right_boundary_offset
                self._set_left_time_span_boundary(new_val=potential)
            except NameError:
                self._set_left_time_span_boundary(new_val=60.0)

    leftTimeBoundaryEnabled: bool = Property(
        bool,
        _get_left_time_span_boundary_bool,
        _set_left_time_span_boundary_bool,
        designable=False,
    )
    """Toggle for the Left / Lower boundary for the Plot's timestamp"""

    # ~~~~~~~~~~~~~~~~~ Styling Opts for Slot Items ~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_slot_item_pen_color(self) -> QColor:
        return self._slot_item_styling_opts.pen_color

    def _set_slot_item_pen_color(self, color: QColor):
        self._slot_item_styling_opts.pen_color = color

    def _get_slot_item_pen_width(self) -> int:
        return self._slot_item_styling_opts.pen_width

    def _set_slot_item_pen_width(self, width: int):
        self._slot_item_styling_opts.pen_width = width

    def _get_slot_item_pen_style(self) -> Qt.PenStyle:
        return self._slot_item_styling_opts.pen_style

    def _set_slot_item_pen_style(self, style: Qt.PenStyle):
        self._slot_item_styling_opts.pen_style = style

    def _get_slot_item_symbol(self) -> int:
        return self._slot_item_styling_opts.symbol

    def _get_slot_item_symbol_string(self) -> Optional[str]:
        symbol_string = {
            SymbolOptions.NoSymbol: None,
            SymbolOptions.Circle: "o",
            SymbolOptions.Square: "s",
            SymbolOptions.Triangle: "t",
            SymbolOptions.Diamond: "d",
            SymbolOptions.Plus: "+",
        }
        return symbol_string[self._get_slot_item_symbol()]

    def _set_slot_item_symbol(self, symbol: int):
        self._slot_item_styling_opts.symbol = symbol

    def _get_slot_item_brush_color(self) -> QColor:
        return self._slot_item_styling_opts.brush_color

    def _set_slot_item_brush_color(self, color: QColor):
        self._slot_item_styling_opts.brush_color = color

    # ~~~~~~~~~~ Private ~~~~~~~~~

    def _get_slot_item_pen(self) -> QPen:
        color = self._get_slot_item_pen_color()
        width = self._get_slot_item_pen_width()
        style = self._get_slot_item_pen_style()
        return pg.mkPen(color=color, width=width, style=style)

    def _init_ex_plot_item(
            self,
            config: Optional[ExPlotWidgetConfig] = None,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        """
        Replace the plot item created by the base class with an instance
        of the extended plot item.
        """
        if axis_items is None:
            axis_items = {}
        old_plot_item = self.plotItem
        self.plotItem = ExPlotItem(
            axis_items=axis_items,
            config=config,
            timing_source=timing_source,
            **plotitem_kwargs,
        )
        self.setCentralItem(self.plotItem)
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)
        self.plotItem.sig_selection_changed.connect(self.sig_selection_changed.emit)
        self.plotItem.sig_plot_selected.connect(self.sig_plot_selected.emit)
        del old_plot_item

    def _wrap_plotitem_functions(self):
        """
        For convenience the PlotWidget wraps some functions of the PlotItem
        Since we replace the inner `self.plotItem` we have to change the wrapped
        functions of it as well. This list has to be kept in sync with the
        equivalent in the base class constructor.
        """
        wrap_from_base_class = [
            "addItem", "removeItem", "autoRange", "clear", "setXRange",
            "setYRange", "setRange", "setAspectLocked", "setMouseEnabled",
            "setXLink", "setYLink", "enableAutoRange", "disableAutoRange",
            "setLimits", "register", "unregister", "viewRect",
        ]
        for method in wrap_from_base_class:
            # TODO: Questionable... This are bound methods, right?
            setattr(self, method, getattr(self.plotItem, method))
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)


class GridOrientationOptions:
    Hidden = 0
    X = 1
    Y = 2
    Both = 3


class XAxisSideOptions:
    Hidden = 0
    Top = 1
    Bottom = 2
    Both = 3


class DefaultYAxisSideOptions:
    Hidden = 0
    Left = 1
    Right = 2
    Both = 3


class LegendXAlignmentOptions:
    Left = 0
    Right = 1
    Center = 2


class LegendYAlignmentOptions:
    Top = 0
    Bottom = 1
    Center = 2


class ExPlotWidgetProperties(XAxisSideOptions,
                             DefaultYAxisSideOptions,
                             GridOrientationOptions,
                             LegendXAlignmentOptions,
                             LegendYAlignmentOptions):

    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    XAxisSideOptions = XAxisSideOptions
    DefaultYAxisSideOptions = DefaultYAxisSideOptions
    GridOrientationOptions = GridOrientationOptions
    LegendXAlignmentOptions = LegendXAlignmentOptions
    LegendYAlignmentOptions = LegendYAlignmentOptions

    """
    Do not use this class except as a base class to inject properties in the following
    context:

    SuperPlotWidgetClass(ExPlotWidgetProperties, ExPlotWidget)

    All self.xyz calls are resolved to the fields in ExPlotWidget in this context.
    If you use this class in any other context, these resolutions will fail.
    """

    def _get_show_x_axis(self) -> int:
        """Where is the X Axis of the plot displayed"""
        top = self.getAxis("top").isVisible()  # type: ignore[attr-defined]
        bottom = self.getAxis("bottom").isVisible()  # type: ignore[attr-defined]
        if top and bottom:
            return XAxisSideOptions.Both
        if top and not bottom:
            return XAxisSideOptions.Top
        if not top and bottom:
            return XAxisSideOptions.Bottom
        return XAxisSideOptions.Hidden

    def _set_show_x_axis(self, new_val: int):
        """Where is the X Axis of the plot displayed"""
        if new_val != self._get_show_x_axis():  # type: ignore[has-type]
            if new_val == XAxisSideOptions.Both:
                cast(ExPlotWidget, self).showAxis("top")
                cast(ExPlotWidget, self).showAxis("bottom")
            if new_val == XAxisSideOptions.Top:
                cast(ExPlotWidget, self).showAxis("top")
                cast(ExPlotWidget, self).hideAxis("bottom")
            if new_val == XAxisSideOptions.Bottom:
                cast(ExPlotWidget, self).hideAxis("top")
                cast(ExPlotWidget, self).showAxis("bottom")
            if new_val == XAxisSideOptions.Hidden:
                cast(ExPlotWidget, self).hideAxis("top")
                cast(ExPlotWidget, self).hideAxis("bottom")
            # Update labels through property
            self.axisLabels = self.axisLabels

    xAxisSide: int = Property(XAxisSideOptions, _get_show_x_axis, _set_show_x_axis)
    """Where should the x axis be displayed?"""

    def _get_show_y_axis(self) -> int:
        """Where is the Y Axis of the plot displayed"""
        left = cast(ExPlotWidget, self).getAxis("left").isVisible()  # type: ignore[attr-defined]
        right = cast(ExPlotWidget, self).getAxis("right").isVisible()  # type: ignore[attr-defined]
        if left and right:
            return DefaultYAxisSideOptions.Both
        if left and not right:
            return DefaultYAxisSideOptions.Left
        if not left and right:
            return DefaultYAxisSideOptions.Right
        return DefaultYAxisSideOptions.Hidden

    def _set_show_y_axis(self, new_val: int):
        """Where is the Y Axis of the plot displayed"""
        if new_val != self._get_show_y_axis():  # type: ignore[has-type]
            if new_val == DefaultYAxisSideOptions.Both:
                cast(ExPlotWidget, self).showAxis("left")
                cast(ExPlotWidget, self).showAxis("right")
            if new_val == DefaultYAxisSideOptions.Left:
                cast(ExPlotWidget, self).showAxis("left")
                cast(ExPlotWidget, self).hideAxis("right")
            if new_val == DefaultYAxisSideOptions.Right:
                cast(ExPlotWidget, self).hideAxis("left")
                cast(ExPlotWidget, self).showAxis("right")
            if new_val == DefaultYAxisSideOptions.Hidden:
                cast(ExPlotWidget, self).hideAxis("left")
                cast(ExPlotWidget, self).hideAxis("right")
            # Update labels through property
            self.axisLabels = self.axisLabels

    defaultYAxisSide: int = Property(DefaultYAxisSideOptions, _get_show_y_axis, _set_show_y_axis)
    """Where should the y axis be displayed?"""

    def _get_show_grid(self) -> int:
        """What Axis Grid should be displayed"""
        x_grid = cast(ExPlotWidget, self).plotItem.ctrl.xGridCheck.isChecked()
        y_grid = cast(ExPlotWidget, self).plotItem.ctrl.yGridCheck.isChecked()
        if x_grid and y_grid:
            return GridOrientationOptions.Both
        if x_grid and not y_grid:
            return GridOrientationOptions.X
        if not x_grid and y_grid:
            return GridOrientationOptions.Y
        return GridOrientationOptions.Hidden

    def _set_show_grid(self, new_val: int):
        """What Axis Grid should be displayed"""
        if new_val != self._get_show_grid():
            if new_val == GridOrientationOptions.Both:
                cast(ExPlotWidget, self).plotItem.showGrid(x=True)
                cast(ExPlotWidget, self).plotItem.showGrid(y=True)
            if new_val == GridOrientationOptions.X:
                cast(ExPlotWidget, self).plotItem.showGrid(x=True)
                cast(ExPlotWidget, self).plotItem.showGrid(y=False)
            if new_val == GridOrientationOptions.Y:
                cast(ExPlotWidget, self).plotItem.showGrid(x=False)
                cast(ExPlotWidget, self).plotItem.showGrid(y=True)
            if new_val == GridOrientationOptions.Hidden:
                cast(ExPlotWidget, self).plotItem.showGrid(x=False)
                cast(ExPlotWidget, self).plotItem.showGrid(y=False)

    gridOrientation: int = Property(GridOrientationOptions, _get_show_grid, _set_show_grid)
    """Which Axis' Grid should be displayed"""

    def _get_show_legend(self) -> bool:
        """Does the plot show a legend."""
        legend = cast(Optional[pg.LegendItem], cast(ExPlotWidget, self).plotItem.legend)
        return legend is not None and legend.isVisible()

    def _set_show_legend(self, new_val: bool):
        """If true, the plot shows a legend."""
        if new_val != self._get_show_legend():  # type: ignore[has-type]
            curr_legend = cast(Optional[pg.LegendItem], cast(ExPlotWidget, self).plotItem.legend)
            if new_val:
                if curr_legend is None:
                    cast(ExPlotWidget, self).addLegend(size=None, offset=None)
                    old_pos = self._get_legend_position()
                    self._set_legend_position(
                        x_alignment=old_pos[0],
                        y_alignment=old_pos[1],
                    )
                else:
                    curr_legend.setVisible(True)
            else:
                if curr_legend is not None:
                    curr_legend.setVisible(False)
            cast(ExPlotWidget, self).update()

    showLegend: bool = Property(bool, _get_show_legend, _set_show_legend)
    """Does the plot show a legend which displays the contained items."""

    def _get_legend_position(self) -> Tuple[int, int]:
        """
        Get the legends position in the passed dimension.

        Args:
            index: 0 for X / Horizontal Alignment, 1 for Y / Vertical Alignment

        Returns: position of the axis in the given dimension
        """
        try:
            return self._legend_position_cache
        except (AttributeError, NameError):
            d = (LegendXAlignmentOptions.Left, LegendYAlignmentOptions.Top)
            if cast(ExPlotWidget, self).plotItem.legend is not None:
                self._set_legend_position(x_alignment=d[0], y_alignment=d[1])
            return d

    def _set_legend_position(self, x_alignment: int = -1, y_alignment: int = -1, offset: float = 10.0):
        """
        Set the legends position in the ViewBox. Values smaller 0 are not accepted.
        Values that move the Legend out of the viewable area are not accepted.
        If a value is not accepted it is replaced with the max/min possible value.

        If invalid values are passed for the alignment, no positioning is done.

        If -1 is passed for one of the alignment params, the current position is taken.

        Args:
            x_alignment: Horizontal Alignment (values from LegendXAlignmentOptions)
            y_alignment: Vertical Alignment (values from LegendYAlignmentOptions)
        """
        if x_alignment == -1:
            x_alignment = self._get_legend_x_position()
        if y_alignment == -1:
            y_alignment = self._get_legend_y_position()
        x, y, x_offset, y_offset = np.nan, np.nan, np.nan, np.nan
        # We have to cache the position because there is no elegant way of
        # retrieving it from the LegendItem
        self._legend_position_cache: Tuple[int, int] = (x_alignment, y_alignment)
        if x_alignment == LegendXAlignmentOptions.Left:
            x = 0
            x_offset = offset
        elif x_alignment == LegendXAlignmentOptions.Center:
            x = 0.5
            x_offset = 0
        elif x_alignment == LegendXAlignmentOptions.Right:
            x = 1
            x_offset = -offset
        if y_alignment == LegendYAlignmentOptions.Top:
            y = 0
            y_offset = offset
        elif y_alignment == LegendYAlignmentOptions.Center:
            y = 0.5
            y_offset = 0
        elif y_alignment == LegendYAlignmentOptions.Bottom:
            y = 1
            y_offset = -offset
        legend = cast(ExPlotWidget, self).plotItem.legend
        if True not in np.isnan(np.array([x, y, x_offset, y_offset])) and legend is not None:
            legend.anchor(
                itemPos=(x, y),
                parentPos=(x, y),
                offset=(x_offset, y_offset),
            )

    def _get_legend_x_position(self) -> int:
        return self._get_legend_position()[0]

    def _set_legend_x_position(self, new_val: int):
        self._set_legend_position(x_alignment=new_val)

    legendXAlignment: int = Property(LegendXAlignmentOptions, _get_legend_x_position, _set_legend_x_position)
    """Which position has the top left corner in the x dimension. Is 0, if no legend is displayed."""

    def _get_legend_y_position(self) -> int:
        return self._get_legend_position()[1]

    def _set_legend_y_position(self, new_val: int):
        self._set_legend_position(y_alignment=new_val)

    legendYAlignment: int = Property(LegendYAlignmentOptions, _get_legend_y_position, _set_legend_y_position)
    """Which position has the top left corner in the y dimension. Is 0, if no legend is displayed."""

    # ~~~~~~~~~~ QtDesigner Properties ~~~~~~~~~~

    _reserved_axis_labels_identifiers: Set[str] = {"top", "bottom", "left", "right"}

    _reserved_axis_ranges_identifiers: Set[str] = {"x", "y"}

    def _get_layer_ids(self) -> "QStringList":  # type: ignore # noqa
        """
        QtDesigner getter function for the PlotItems time span

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        return [layer.id for layer in cast(ExPlotWidget, self).plotItem.non_default_layers]

    def _set_layer_ids(self, layers: "QStringList"):  # type: ignore # noqa
        """
        QtDesigner setter function for the PlotItems time span

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        # Check for duplicated values
        if len(layers) != len(set(layers)):
            warnings.warn("Layers can not be updated since you have provided duplicated identifiers for them.")
            return
        # Check for invalid layer identifiers
        for reserved in ExPlotWidgetProperties._reserved_axis_labels_identifiers:
            if reserved in layers:
                warnings.warn(f"Identifier entry '{reserved}' will be ignored since it is reserved.")
                layers.remove(reserved)
        # Update changed identifiers
        self._update_layers(layers)

    layerIDs: List[str] = Property("QStringList", _get_layer_ids, _set_layer_ids, designable=False)
    """List of strings with the additional layer's identifiers"""

    def _get_axis_labels(self) -> str:
        """QtDesigner getter function for the PlotItems axis labels"""
        labels = {}
        for axis in self._reserved_axis_labels_identifiers:
            labels[axis] = cast(ExPlotWidget, self).getAxis(axis).labelText
        for layer in cast(ExPlotWidget, self).plotItem.non_default_layers:
            labels[layer.id] = layer.axis_item.labelText
        return json.dumps(labels)

    def _set_axis_labels(self, new_val: str):
        """QtDesigner setter function for the PlotItems axis labels"""
        try:
            axis_labels: Dict[str, str] = json.loads(new_val)
            for axis, label in axis_labels.items():
                label = axis_labels.get(axis, "").strip()
                try:
                    axis_item = cast(ExPlotWidget, self).plotItem.getAxis(axis)
                except KeyError:
                    warnings.warn(f"Label of axis / layer {axis} could not "
                                  f"be set, since it does not seem to exist.")
                    continue
                if axis_item.isVisible():
                    if label:
                        axis_item.setLabel(label)
                    else:
                        axis_item.labelText = label
                        axis_item.showLabel(False)
                else:
                    axis_item.labelText = label
        except (json.decoder.JSONDecodeError, AttributeError, TypeError):
            # JSONDecodeError and Attribute Errors for JSON decoding
            # TypeError for len() operation on entries that do not support it
            pass

    axisLabels: str = Property(str, _get_axis_labels, _set_axis_labels, designable=False)
    """JSON string with mappings of axis positions and layers to a label text"""

    def _get_axis_ranges(self) -> str:
        """QtDesigner getter function for the PlotItems axis ranges"""
        vb = cast(ExPlotWidget, self).getViewBox()
        auto_ranges_dict = {
            "x": "auto" if vb.autoRangeEnabled()[0] else vb.targetRange()[0],
            "y": "auto" if vb.autoRangeEnabled()[1] else vb.targetRange()[1],
        }
        for layer in cast(ExPlotWidget, self).plotItem.non_default_layers:
            vb = layer.view_box
            auto_ranges_dict[layer.id] = "auto" if vb.autoRangeEnabled()[1] else vb.targetRange()[1]
        return json.dumps(auto_ranges_dict)

    def _set_axis_ranges(self, new_val: str):
        """QtDesigner setter function for the PlotItems axis ranges"""
        try:
            axis_ranges: Dict[str, Tuple[float, float]] = json.loads(new_val)
            for axis, axis_range in axis_ranges.items():
                # Get fitting viewbox
                if axis in ("x", "y"):
                    vb = cast(ExPlotWidget, self).getPlotItem().getViewBox()
                else:
                    try:
                        vb = cast(ExPlotWidget, self).getPlotItem().getViewBox(layer=axis)
                    except KeyError:
                        warnings.warn(f"View Range of axis / layer {axis} could "
                                      f"not be set, since it does not seem to exist.")
                        continue
                # Set auto range / fixed range
                vb.enableAutoRange(axis="x" if axis == "x" else "y",
                                   enable=axis_range == "auto")
                if axis_range != "auto":
                    if axis == "x":
                        vb.setXRange(*axis_range, padding=0.0)
                    else:
                        vb.setYRange(*axis_range, padding=0.0)
        except (json.decoder.JSONDecodeError, AttributeError, TypeError):
            # JSONDecodeError and Attribute Errors for JSON decoding
            # TypeError for len() operation on entries that do not support it
            pass

    axisRanges: str = Property(str, _get_axis_ranges, _set_axis_ranges, designable=False)
    """JSON string with mappings of x, y and layers to a view range"""

    def _update_layers(self, new: List[str]):
        """
        This function removes old layers and adds new ones according to the list
        of passed layers. To make sure items are not dangling in the air without
        an existing parent item, we have to remove them first from the deleted
        layers and then add them to the new ones. We try to make sure items land
        in the correct layer, if the layer e.g. has been renamed, but this
        comes with some caveats, since it is not clear how the new list was
        created from the old one (e.g. has a layer been renamed or was it
        replaced by a entirely new one?). If a layer id exist in both the current
        and the new layer set, it is seen as the same one, even if its position
        has changed.

        Args:
            new: list of new layer identifiers, which will be added to the plot
        """
        old = self._get_layer_ids()
        removed_layer_ids = [l for l in self._get_layer_ids() if l not in new]
        added_layer_ids = [l for l in new if l not in self._get_layer_ids()]
        items_to_move: List[DataModelBasedItem] = []
        if removed_layer_ids or added_layer_ids:
            # Any layer change at all
            for name in old:
                # Take ownership of items before deleting their ViewBox
                items_to_move += cast(ExPlotWidget, self).plotItem.layer(name).view_box.addedItems
                for item in cast(ExPlotWidget, self).plotItem.layer(name).view_box.addedItems:
                    item.setParentItem(cast(ExPlotWidget, self).plotItem.getViewBox())
                # Now we can safely remove the layer's view-box
                cast(ExPlotWidget, self).plotItem.remove_layer(name)
            for name in new:
                cast(ExPlotWidget, self).plotItem.add_layer(name)
                # Put items back to their layers, for the ones where the layer has not changed
                items_to_add = [item for item in items_to_move if item.layer_id == name]
                for item in items_to_add:
                    try:
                        cast(ExPlotWidget, self).addItem(item=item, layer=name)
                        items_to_move.remove(item)
                    except RuntimeError:
                        warnings.warn(f"Item could not be removed: {item.label}")
        if removed_layer_ids and added_layer_ids:
            for old_name, new_name in zip(removed_layer_ids, added_layer_ids):
                # If layer was renamed -> move item to new layer
                item_from_this_layer = [item for item in items_to_move if item.layer_id == old_name]
                for item in item_from_this_layer:
                    cast(ExPlotWidget, self).addItem(item=item, layer=new_name)
                    items_to_move.remove(item)
        # Catch all items that could not be assigned and add them to the default layer
        for item in items_to_move:
            cast(ExPlotWidget, self).plotItem.getViewBox().addItem(item)

    @staticmethod
    def diff(list1, list2):
        return list(set(list1).symmetric_difference(set(list2)))


class ScrollingPlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    SymbolOptions = SymbolOptions

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            time_span: Union[TimeSpan, float, None] = 60.0,
            time_progress_line: bool = False,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        """
        The ScrollingPlotWidget is equivalent to an ExPlotWidget which's
        configuration contains the scrolling plot style. Additionally some
        properties are offered that are specific to this plotting style.
        When switching the ExPlotWidget, passing a fitting configuration
        can achieve the same results as using these properties.

        Args:
            parent: parent item for this widget, will only be passed to base class
            background: background for the widget, will only be passed to base class
            time_span: data from which time span should be displayed in the plot.
                       The default time span is 60.0 seconds.
            time_progress_line: If true, the current timestamp will represented as a
                                vertical line in the plot
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            timing_source: Mainly for live data plotting. This timing source allows
                           to receive timing updates decoupled from any received
                           data.
            **plotitem_kwargs: Params passed to the plot item
        """
        config = ExPlotWidgetConfig(
            plotting_style=PlotWidgetStyle.SCROLLING_PLOT,
            time_span=time_span,
            time_progress_line=time_progress_line,
        )
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(
            self,
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            timing_source=timing_source,
            **plotitem_kwargs,
        )

    rightTimeBoundary: float = Property(
        float,
        ExPlotWidget._get_right_time_span_boundary,
        ExPlotWidget._set_right_time_span_boundary,
    )
    """Value of the Left / Lower boundary for the Plot's timestamp"""

    leftTimeBoundary: float = Property(
        float,
        ExPlotWidget._get_left_time_span_boundary,
        ExPlotWidget._set_left_time_span_boundary,
    )
    """Toggle for the Left / Lower boundary for the Plot's timestamp"""

    leftTimeBoundaryEnabled: bool = Property(
        bool,
        ExPlotWidget._get_left_time_span_boundary_bool,
        ExPlotWidget._set_left_time_span_boundary_bool,
        doc="This is a test",
    )
    """Toggle for the Left / Lower boundary for the Plot's timestamp"""

    # ~~~~~~~~~~~~~~~ pushData slot ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pushDataItemPenColor: QColor = Property(
        QColor,
        ExPlotWidget._get_slot_item_pen_color,
        ExPlotWidget._set_slot_item_pen_color,
    )
    """Pen color for the item displaying data through the 'pushData' slot"""

    pushDataItemPenWidth: int = Property(
        int,
        ExPlotWidget._get_slot_item_pen_width,
        ExPlotWidget._set_slot_item_pen_width,
    )
    """Pen width for the item displaying data through the 'pushData' slot"""

    pushDataItemPenStyle: Qt.PenStyle = Property(
        Qt.PenStyle,
        ExPlotWidget._get_slot_item_pen_style,
        ExPlotWidget._set_slot_item_pen_style,
    )
    """Pen line style for the item displaying data through 'pushData' the slot"""

    pushDataItemBrushColor: str = Property(
        QColor,
        ExPlotWidget._get_slot_item_brush_color,
        ExPlotWidget._set_slot_item_brush_color,
    )
    """Brush color for the item displaying data through the 'pushData' slot"""

    pushDataItemSymbol: int = Property(
        SymbolOptions,
        ExPlotWidget._get_slot_item_symbol,
        ExPlotWidget._set_slot_item_symbol,
    )
    """Symbol for the item displaying data through 'pushData' the slot"""

    @Slot(float)
    @Slot(int)
    @Slot(tuple)
    @Slot(list)
    @Slot(np.ndarray)
    @Slot(PointData)
    def pushData(self,
                 data: Union[int, float, Sequence[float], PointData]):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot. If this curve does not yet exist,
        it will be created automatically . The data will be collected by
        the curve and drawn. Further calls with other data will append it
        to the existing one.

        This slot will accept single integer and float values
        and draw them at the timestamp of their arrival.

        To propagate an additional x value, put it in second position in an
        array: [y, x]
        """
        if not isinstance(data, PointData):
            data = cast(PointData,
                        PlottingItemDataFactory.transform(PointData, data))  # type: ignore
        self.plotItem.plot_data_on_single_data_item(
            data=data,
            # ignore, bc mypy wants concrete class
            item_type=AbstractBasePlotCurve,  # type: ignore
            pen=self._get_slot_item_pen(),
            symbolPen=self._get_slot_item_pen(),
            symbolBrush=pg.mkBrush(self._get_slot_item_brush_color()),
            symbol=self._get_slot_item_symbol_string(),
        )


class CyclicPlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    SymbolOptions = SymbolOptions

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            time_span: Union[TimeSpan, float, None] = 60.0,
            time_progress_line: bool = False,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        """
        The ScrollingPlotWidget is equivalent to an ExPlotWidget which's
        configuration contains the cylic plot style. Additionally some
        properties are offered that are specific to this plotting style.
        When switching the ExPlotWidget, passing a fitting configuration
        can achieve the same results as using these properties.

        Args:
            parent: parent item for this widget, will only be passed to base class
            background: background for the widget, will only be passed to base class
            time_span: data from which time span should be displayed in the plot.
                       The default time span is 60.0 seconds.
            time_progress_line: If true, the current timestamp will represented as a
                                vertical line in the plot
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            timing_source: Mainly for live data plotting. This timing source allows
                           to receive timing updates decoupled from any received
                           data.
            **plotitem_kwargs: Params passed to the plot item
        """
        config = ExPlotWidgetConfig(
            plotting_style=PlotWidgetStyle.CYCLIC_PLOT,
            time_span=time_span,
            time_progress_line=time_progress_line,
        )
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(
            self,
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            timing_source=timing_source,
            **plotitem_kwargs,
        )

    leftBoundary: float = Property(
        float,
        ExPlotWidget._get_left_time_span_boundary,
        ExPlotWidget._set_left_time_span_boundary,
    )
    """Toggle for the Left / Lower boundary for the Plot's timestamp"""

    def _get_left_time_span_boundary_bool(self, **kwargs) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at cyclic plot, "
                          "since a cyclic plot can not be drawn without both boundaries defined.")
        return False

    def _set_left_time_span_boundary_bool(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at cyclic plot, "
                          "since a cyclic plot can not be drawn without both boundaries defined.")

    leftBoundaryEnabled: bool = Property(
        bool,
        _get_left_time_span_boundary_bool,
        _set_left_time_span_boundary_bool,
        designable=False,
    )
    """DO NOT USE WITH A CYCLIC PLOT."""

    # ~~~~~~~~~~~~~~~ pushData slot ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pushDataItemPenColor: QColor = Property(
        QColor,
        ExPlotWidget._get_slot_item_pen_color,
        ExPlotWidget._set_slot_item_pen_color,
    )
    """Pen color for the item displaying data through the 'pushData' slot"""

    pushDataItemPenWidth: int = Property(
        int,
        ExPlotWidget._get_slot_item_pen_width,
        ExPlotWidget._set_slot_item_pen_width,
    )
    """Pen width for the item displaying data through the 'pushData' slot"""

    pushDataItemPenStyle: Qt.PenStyle = Property(
        Qt.PenStyle,
        ExPlotWidget._get_slot_item_pen_style,
        ExPlotWidget._set_slot_item_pen_style,
    )
    """Pen line style for the item displaying data through the 'pushData' slot"""

    pushDataItemBrushColor: str = Property(
        QColor,
        ExPlotWidget._get_slot_item_brush_color,
        ExPlotWidget._set_slot_item_brush_color,
    )
    """Brush color for the item displaying data through the 'pushData' slot"""

    pushDataItemSymbol: int = Property(
        SymbolOptions,
        ExPlotWidget._get_slot_item_symbol,
        ExPlotWidget._set_slot_item_symbol,
    )
    """Symbol for the item displaying data through the 'pushData' slot"""

    @Slot(float)
    @Slot(int)
    @Slot(tuple)
    @Slot(list)
    @Slot(np.ndarray)
    @Slot(PointData)
    def pushData(self,
                 data: Union[int, float, Tuple, List, np.ndarray, PointData]):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot. If this curve does not yet exist,
        it will be created automatically . The data will be collected by
        the curve and drawn. Further calls with other data will append it
        to the existing one.

        This slot will accept single integer and float values
        and draw them at the timestamp of their arrival.

        To propagate an additional x value, put it in second position in an
        array: [y, x]
        """
        if not isinstance(data, PointData):
            data = PlottingItemDataFactory.transform(PointData, data)  # type: ignore
        self.plotItem.plot_data_on_single_data_item(
            data=data,
            # ignore, bc mypy wants concrete class
            item_type=AbstractBasePlotCurve,  # type: ignore
            pen=self._get_slot_item_pen(),
            symbolPen=self._get_slot_item_pen(),
            symbolBrush=pg.mkBrush(self._get_slot_item_brush_color()),
            symbol=self._get_slot_item_symbol_string(),
        )


class StaticPlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            **plotitem_kwargs,
    ):
        """
        The StaticPlotWidget is equivalent to an ExPlotWidget which's
        configuration contains the static plot style. Properties that do
        not have any effect on the ExPlotWidget in this plotting style, are
        explicitly hidden in Qt Designer.

         Args:
            parent: parent item for this widget, will only be passed to base class
            background: background for the widget, will only be passed to base class
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            **plotitem_kwargs: Params passed to the plot item
        """
        config = ExPlotWidgetConfig(
            plotting_style=PlotWidgetStyle.STATIC_PLOT,
        )
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(
            self,
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            **plotitem_kwargs,
        )

    def _get_show_time_line(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'setShowTimeLine' is not supposed to be used with at static plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")
        return False

    def _set_show_time_line(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'setShowTimeLine' is not supposed to be used with at static plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")

    showTimeProgressLine: bool = Property(bool, _get_show_time_line, _set_show_time_line, designable=False)
    """Vertical Line displaying the current time stamp, not supported by the static plotting style"""

    def _get_time_span(self) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'timeSpan' is not supposed to be used with at static plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")
        return 0.0

    def _set_time_span(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'timeSpan' is not supposed to be used with at static plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")

    timeSpan: float = Property(float, _get_time_span, _set_time_span, designable=False)
    """Range from which the plot displays data, not supported by the static plotting style"""

    def _get_right_time_span_boundary(self) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'rightBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")
        return False

    def _set_right_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'rightBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")

    rightBoundary: float = Property(
        float,
        _get_right_time_span_boundary,
        _set_right_time_span_boundary,
        designable=False,
    )
    """Value of the Left / Lower boundary for the Plot's timestamp"""

    def _get_left_time_span_boundary(self, hide_nans: bool = True) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")

    leftBoundary: float = Property(
        float,
        _get_left_time_span_boundary,
        _set_left_time_span_boundary,
        designable=False,
    )
    """Toggle for the Left / Lower boundary for the Plot's timestamp"""

    def _get_left_time_span_boundary_bool(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary_bool(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")

    leftBoundaryEnabled: bool = Property(
        bool,
        _get_left_time_span_boundary_bool,
        _set_left_time_span_boundary_bool,
        designable=False,
    )

    # ~~~~~~~~~~~~ replaceData ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    replaceDataItemPenColor: QColor = Property(
        QColor,
        ExPlotWidget._get_slot_item_pen_color,
        ExPlotWidget._set_slot_item_pen_color,
    )
    """Pen color for the item displaying data through the 'replaceData' slot"""

    replaceDataItemPenWidth: int = Property(
        int,
        ExPlotWidget._get_slot_item_pen_width,
        ExPlotWidget._set_slot_item_pen_width,
    )
    """Pen width for the item displaying data through the 'replaceData' slot"""

    replaceDataItemPenStyle: Qt.PenStyle = Property(
        Qt.PenStyle,
        ExPlotWidget._get_slot_item_pen_style,
        ExPlotWidget._set_slot_item_pen_style,
    )
    """Pen line style for the item displaying data through 'replaceData' the slot"""

    replaceDataItemBrushColor: str = Property(
        QColor,
        ExPlotWidget._get_slot_item_brush_color,
        ExPlotWidget._set_slot_item_brush_color,
    )

    """Brush color for the item displaying data through the 'replaceData' slot"""

    replaceDataItemSymbol: int = Property(
        SymbolOptions,
        ExPlotWidget._get_slot_item_symbol,
        ExPlotWidget._set_slot_item_symbol,
    )
    """Symbol for the item displaying data through 'replaceData' the slot"""

    @Slot(np.ndarray)
    @Slot(CurveData)
    def replaceDataAsCurve(self,
                           data: Union[Sequence[float], CurveData]):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot. If this curve does not yet exist,
        it will be created automatically . The data will be collected by
        the curve and drawn.
        A full curve is expected as either a 2D numpy array or a CurveData
        object. The curve will replace all data shown prior to its arrival.
        """
        if not isinstance(data, CurveData):
            data = cast(CurveData,
                        PlottingItemDataFactory.transform(CurveData, data))  # type: ignore
        self.plotItem.plot_data_on_single_data_item(
            data=data,
            # ignore, bc mypy wants concrete class
            item_type=AbstractBasePlotCurve,  # type: ignore
            pen=self._get_slot_item_pen(),
            symbolPen=self._get_slot_item_pen(),
            symbolBrush=pg.mkBrush(self._get_slot_item_brush_color()),
            symbol=self._get_slot_item_symbol_string(),
        )

    @Slot(BarCollectionData)
    def replaceDataAsBarGraph(self, data: BarCollectionData):
        """
        This slot exposes the possibility to draw data on a
        single bar graph in the plot. If this bar_graph does not yet exist,
        it will be created automatically. The data will be collected by
        the bar graph and drawn.
        """
        self.plotItem.plot_data_on_single_data_item(
            data=data,
            # ignore, bc mypy wants concrete class
            item_type=AbstractBaseBarGraphItem,  # type: ignore
            pen=self._get_slot_item_pen(),
            brush=pg.mkBrush(self._get_slot_item_brush_color()),
        )

    @Slot(InjectionBarCollectionData)
    def replaceDataAsInjectionBars(self,
                                   data: InjectionBarCollectionData):
        """
        This slot exposes the possibility to draw data on a single injection
        bar graph in the plot. If this graph does not yet exist, it will be
        created automatically. The data will be collected by the graph and
        drawn.
        """
        self.plotItem.plot_data_on_single_data_item(
            data=data,
            # ignore, bc mypy wants concrete class
            item_type=AbstractBaseInjectionBarGraphItem,  # type: ignore
            pen=self._get_slot_item_pen(),
        )


class EditablePlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            **plotitem_kwargs,
    ):
        """
        The EditablePlotWidget is equivalent to an ExPlotWidget which's
        configuration contains the editable plot style. Properties that do
        not have any effect on the ExPlotWidget in this plotting style, are
        explicitly hidden in Qt Designer.

         Args:
            parent: parent item for this widget, will only be passed to base class
            background: background for the widget, will only be passed to base class
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            **plotitem_kwargs: Params passed to the plot item
        """
        config = ExPlotWidgetConfig(
            plotting_style=PlotWidgetStyle.EDITABLE,
        )
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(
            self,
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            **plotitem_kwargs,
        )

    def _get_show_time_line(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'showTimeProgressLine' is not supposed to be used with at editable plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")
        return False

    def _set_show_time_line(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'showTimeProgressLine is not supposed to be used with at editable plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")

    showTimeProgressLine: bool = Property(bool, _get_show_time_line, _set_show_time_line, designable=False)
    """Vertical Line displaying the current time stamp, not supported by the editable plotting style"""

    def _get_time_span(self) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'timeSpan' is not supposed to be used with at editable plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")
        return 0.0

    def _set_time_span(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'timeSpan' is not supposed to be used with at editable plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")

    timeSpan: float = Property(float, _get_time_span, _set_time_span, designable=False)
    """Range from which the plot displays data, not supported by the editable plotting style"""

    def _get_right_time_span_boundary(self) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'rightBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")
        return False

    def _set_right_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'rightBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")

    rightBoundary: float = Property(
        float,
        _get_right_time_span_boundary,
        _set_right_time_span_boundary,
        designable=False,
    )
    """Value of the Left / Lower boundary for the Plot's timestamp"""

    def _get_left_time_span_boundary(self, hide_nans: bool = True) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")

    leftBoundary: float = Property(
        float,
        _get_left_time_span_boundary,
        _set_left_time_span_boundary,
        designable=False,
    )
    """Toggle for the Left / Lower boundary for the Plot's timestamp"""

    def _get_left_time_span_boundary_bool(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary_bool(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")

    leftBoundaryEnabled: bool = Property(
        bool,
        _get_left_time_span_boundary_bool,
        _set_left_time_span_boundary_bool,
        designable=False,
    )
