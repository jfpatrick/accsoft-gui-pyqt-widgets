"""
Widgets and supporting classes to actually be placed inside Qt windows/widgets.
"""

import json
import warnings
import numpy as np
import pyqtgraph as pg
from typing import Dict, Optional, Any, Set, List, Tuple, Union, cast, Sequence
try:
    from numpy.typing import ArrayLike
except ImportError:
    # numpy.typing not available in numpy < 1.20, which we have to support
    # because of the acc-py distro bundled numpy
    ArrayLike = Any
from copy import deepcopy
from dataclasses import dataclass
from qtpy.QtCore import Signal, Slot, Property, Q_ENUM, Qt
from qtpy.QtWidgets import QWidget
from qtpy.QtGui import QPen, QMouseEvent, QColor
from accwidgets import designer_check
from accwidgets.graph import (UpdateSource, PlottingItemDataFactory, ExPlotWidgetConfig, PlotWidgetStyle, TimeSpan,
                              ExPlotItem, PlotItemLayer, LayerIdentification, DEFAULT_BUFFER_SIZE,
                              AbstractBasePlotCurve, LiveBarGraphItem, AbstractBaseBarGraphItem,
                              LiveInjectionBarGraphItem, AbstractBaseInjectionBarGraphItem, LiveTimestampMarker,
                              DataModelBasedItem, ExAxisItem, PointData, CurveData, BarCollectionData,
                              InjectionBarCollectionData)


class SymbolOptions:
    """Symbols that are being rendered as the data points."""

    NoSymbol = 0
    """No symbol is rendered. This is useful to show a continuous curve."""

    Circle = 1
    """Non-filled circle is shown."""

    Square = 2
    """Non-filled square rectangle is shown."""

    Triangle = 3
    """Non-filled triangle is shown."""

    Diamond = 4
    """Non-filled diamong is shown."""

    Plus = 5
    """Cross (or plus) sign is shown."""


@dataclass
class SlotItemStylingOpts:
    """Styling Options for the Slot Items"""
    pen_color: QColor = QColor(255, 255, 255)
    pen_width: int = 1
    pen_style: Qt.PenStyle = Qt.SolidLine
    brush_color: QColor = QColor(255, 255, 255)
    symbol: int = SymbolOptions.NoSymbol


# TODO: Metaclass abstract?
class ExPlotWidget(pg.PlotWidget):

    Q_ENUM(SymbolOptions)

    sig_selection_changed = Signal()
    """
    Signal informing about any changes to the current selection of the current
    editable item. The signal will also be emitted, if the current selection
    has been moved around by dragging.

    This signal is only used in :class:`EditablePlotWidget`.

    :type: pyqtSignal
    """

    sig_plot_selected = Signal(bool)
    """
    Fired when selection is toggled for editing. Boolean argument stands for select/unselect.

    This signal is only used in :class:`EditablePlotWidget`.

    :type: pyqtSignal
    """

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 background: str = "default",
                 config: Optional[ExPlotWidgetConfig] = None,
                 axis_items: Optional[Dict[str, ExAxisItem]] = None,
                 timing_source: Optional[UpdateSource] = None,
                 **plotitem_kwargs):
        """
        Base class for all the plot widgets.

        This implementation extends :class:`pyqtgraph.PlotWidget` with additional functionality,
        such as support for multiple y-axes, convenient live data plotting
        capabilities. This class is not intended to be used standalone. Instead,
        consider using specialized subclasses, such as :class:`ScrollingPlotWidget`,
        :class:`StaticPlotWidget`, :class:`CyclicPlotWidget` or :class:`EditablePlotWidget`.

        .. note:: By default some properties that this class offers are not designable (not appearing
                  in Qt Designer), since they are relevant only for specific plotting styles. As such,
                  subclasses must override those properties to mark them as designable, if needed.

        Args:
            parent: Owning object.
            background: Background color configuration for the widget. This can be any single argument accepted by
                        :func:`~pyqtgraph.mkColor`. By default, the background color is determined using the
                        ``backgroundColor`` configuration option (see :func:`~pyqtgraph.setConfigOptions`).
            config: Configuration object that defines any parameter that influences the
                    visual representation and the amount of data the plot should show.
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            timing_source: Mainly for live data plotting. This timing source allows
                           receiving timing updates decoupled from any received data.
            **plotitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotItem` constructor.
        """
        super().__init__(parent=parent, background=background)
        config = config or ExPlotWidgetConfig()
        self.timing_source = timing_source
        # From base class
        self.plotItem: ExPlotItem
        self._init_ex_plot_item(axis_items=axis_items,
                                config=config,
                                timing_source=timing_source,
                                **plotitem_kwargs)
        self._wrap_plotitem_functions()
        self._slot_item_styling_opts = SlotItemStylingOpts()

    def addCurve(self,
                 c: Optional[pg.PlotDataItem] = None,
                 params: Optional[Any] = None,
                 data_source: Optional[UpdateSource] = None,
                 layer: Optional[LayerIdentification] = None,
                 buffer_size: int = DEFAULT_BUFFER_SIZE,
                 **plotdataitem_kwargs) -> pg.PlotDataItem:
        """
        Add a new curve attached to a source for receiving new data.

        The new curve can be either created from static data, such as
        :meth:`pyqtgraph.PlotItem.plot`, or from a data source that handles communication
        between the curve and a source data is coming from.

        * To create a curve attached to *live data*, pass a matching ``data_source``
        * To create a curve from a static data array, pass keyword arguments from the :class:`~pyqtgraph.PlotDataItem`
          (as ``**plotdataitem_kwargs``)

        Args:
            c: :class:`~pyqtgraph.PlotDataItem` instance that is added (for backwards compatibility with the original method).
            params: Parameters for ``c`` (for backwards compatibility with the original method) .
            data_source: Source for the incoming data that the curve should represent.
            layer: Identifier of the layer that the new curve belongs to.
            buffer_size: Amount of values that data model's buffer is able to accommodate.
            **plotdataitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotDataItem` constructor.

        Returns:
            :class:`~pyqtgraph.PlotDataItem` or :class:`LivePlotCurve` instance, depending on the input arguments.
        """
        return self.plotItem.addCurve(c=c,
                                      params=params,
                                      data_source=data_source,
                                      layer=layer,
                                      buffer_size=buffer_size,
                                      **plotdataitem_kwargs)

    def addBarGraph(self,
                    data_source: Optional[UpdateSource] = None,
                    layer: Optional[LayerIdentification] = None,
                    buffer_size: int = DEFAULT_BUFFER_SIZE,
                    **bargraph_kwargs) -> LiveBarGraphItem:
        """
        Add a new bar graph attached to a source for receiving new data.

        The new bar graph can be either created from static data, such as
        :meth:`pyqtgraph.PlotItem.plot`, or from a data source that handles communication
        between the curve and a source data is coming from.

        * To create a bar graph attached to *live data*, pass a matching ``data_source``
        * To create a bar graph from a static data array, pass keyword arguments from the :class:`~pyqtgraph.BarGraphItem`
          (as ``**bargraph_kwargs``)

        Args:
            data_source: Source for the incoming data that the bar graph should represent.
            layer: Identifier of the layer that the new bar graph belongs to.
            buffer_size: Amount of values that data model's buffer is able to accommodate.
            **bargraph_kwargs: Keyword arguments for the :class:`~pyqtgraph.BarGraphItem` constructor.

        Returns:
            :class:`~pyqtgraph.BarGraphItem` or :class:`LiveBarGraphItem` instance, depending on the input arguments.
        """
        return self.plotItem.addBarGraph(data_source=data_source,
                                         layer=layer,
                                         buffer_size=buffer_size,
                                         **bargraph_kwargs)

    def addInjectionBar(self,
                        data_source: UpdateSource,
                        layer: Optional[LayerIdentification] = None,
                        buffer_size: int = DEFAULT_BUFFER_SIZE,
                        **errorbaritem_kwargs) -> LiveInjectionBarGraphItem:
        """
        Add a new injection bar attached to a source for receiving new data.

        An injection bar is based on :class:`pyqtgraph.ErrorBarItem` with the additional
        ability to add text labels.

        Args:
            data_source: Source for the incoming data that the injection bar should represent.
            layer: Identifier of the layer that the new injection bar belongs to.
            buffer_size: Amount of values that data model's buffer is able to accommodate.
            **errorbaritem_kwargs: Keyword arguments for the :class:`~pyqtgraph.ErrorBarItem` constructor.

        Returns:
            Injection bar item that was added to the plot.
        """
        return self.plotItem.addInjectionBar(data_source=data_source,
                                             layer=layer,
                                             buffer_size=buffer_size,
                                             **errorbaritem_kwargs)

    def addTimestampMarker(self,
                           *graphicsobjectargs,
                           data_source: UpdateSource,
                           buffer_size: int = DEFAULT_BUFFER_SIZE) -> LiveTimestampMarker:
        """
        Add a new timestamp marker attached to a source for receiving new data.

        A timestamp marker is a vertical infinite line based on
        :class:`pyqtgraph.InfiniteLine` with a text label at the top. The color of each
        line is controlled by the source of the data.

        Args:
            *graphicsobjectargs: Positional arguments for the :class:`~pyqtgraph.GraphicsObject` constructor
                                 (the base class of the marker).
            data_source: Source for the incoming data that the timestamp marker should represent.
            buffer_size: Amount of values that data model's buffer is able to accommodate.

        Returns:
            Timestamp marker that was added to the plot.
        """
        return self.plotItem.addTimestampMarker(*graphicsobjectargs,
                                                data_source=data_source,
                                                buffer_size=buffer_size)

    def add_layer(self,
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
                  **axis_label_css_kwargs) -> "PlotItemLayer":
        """
        Add a new layer to the plot.

        Adding multiple layers to the plot allows display of different items in
        the same plot, but different y-ranges. Each layer comes with its own
        y-axis by default. This axis is appended on the right hand side of
        the plot. Once added, the layer can always be retrieved by its string
        identifier that is chosen when creating the layer.

        Args:
            layer_id: Unique string identifier for the new layer, which later can be
                      used to reference this layer in other method calls.
            y_range: Set the view range of the new y-axis on creation.
                     This is equivalent to calling :meth:`setYRange` with the ``layer`` keyword.
            y_range_padding: Padding to use when setting the y-range.
            invert_y: Invert the y-axis of the newly created layer. This
                      is equivalent to calling meth:`invertY` with the ``layer`` keyword.
            max_tick_length: Maximum length of ticks to draw. Negative values
                             draw into the plot, positive values draw outward.
            link_view: Causes the range of values displayed in the axis
                       to be linked to the visible range of a :class:`~pyqtgraph.ViewBox`.
            show_values: Whether to display values adjacent to ticks.
            pen: Pen used when drawing ticks.
            text: The text (excluding units) to display on the label for this
                  axis.
            units: The units for this axis. Units should generally be given
                   without any scaling prefix (e.g., ``V`` instead of ``mV``). The
                   scaling prefix will be automatically prepended based on the
                   range of data displayed.
            unit_prefix: Prefix used for units displayed on the axis.
            axis_label_css_kwargs: All extra keyword arguments become CSS style
                                   options for the ``<span>`` tag, which will surround
                                   the axis label and units.

        Returns:
            New created layer instance.
        """
        return self.plotItem.add_layer(layer_id=layer_id,
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
                                       **axis_label_css_kwargs)

    def update_config(self, config: ExPlotWidgetConfig):
        """
        Update plot's configuration.

        Items that are affected from the configuration change are recreated with
        the new configuration, preserving their original data models, so that once displayed data is
        not lost. Static items (mainly pure PyQtGraph items) that were added to
        the plot are not affected by this method.

        Args:
            config: The new configuration that should be used by the plot and all
                    its (affected) items.
        """
        self.plotItem.update_config(config=config)

    # ~~~~~~~~~~~~~~~~~~ Functionality for editable plots ~~~~~~~~~~~~~~~~~~~~~~

    def mouseDoubleClickEvent(self, ev: QMouseEvent):
        """
        When double clicking a :class:`~pyqtgraph.PlotItem`, it can be selected as the plot item
        that should be edited. To inform e.g. an editable button bar about the selection, a matching
        signal is emitted.

        Args:
            ev: Double click event.
        """
        super().mouseDoubleClickEvent(ev)
        self.plotItem.toggle_plot_selection()

    def replace_selection(self, replacement: CurveData):
        """
        Replace the current selection with the ``replacement``.

        After the replacement is completed, the selection will be unselected.

        Args:
            replacement: Data which should replace the current selection.
        """
        self.plotItem.replace_selection(replacement=replacement)

    @property
    def current_selection_data(self) -> Optional[CurveData]:
        """Selected data in a curve representation."""
        return self.plotItem.current_selection_data

    @property
    def selection_mode(self) -> bool:
        """
        Marks whether selection mode is enabled.

        In the selection mode, mouse drag events on the viewbox create selection
        rectangles and do not move the view.
        """
        return self.plotItem.selection_mode

    @Slot(bool)
    def set_selection_mode(self, enable: bool):
        """
        Slot to toggle the :attr:`selection_mode`.

        If the selection mode is enabled, mouse drag events on the view
        box create selection rectangles and do not pan the view.

        Args:
            enable: Enable selection mode.
        """
        self.plotItem.selection_mode = enable

    @Slot()
    def send_currents_editable_state(self) -> bool:
        """
        Commit performed changes on the current editable item
        back into the :attr:`~EditableCurveDataModel.data_source`.

        This method does nothing if there were no changes to commit.

        Returns:
            Whether change was successfully committed.
        """
        return self.plotItem.send_currents_editable_state()

    @Slot()
    def send_all_editables_state(self) -> List[bool]:
        """
        Commit performed changes on the all editable items
        back into their relevant :attr:`~EditableCurveDataModel.data_source`.

        Returns:
            List of indicators for each state, whether the change was successfully committed.
        """
        return self.plotItem.send_all_editables_state()

    # ~~~~~~~~~~ Properties ~~~~~~~~~

    def _get_plot_title(self) -> str:
        if self.plotItem.titleLabel.isVisible():
            return self.plotItem.titleLabel.text
        return ""

    def _set_plot_title(self, new_val: str):
        if new_val != self.plotItem.titleLabel.text:
            new_val = new_val.strip()
            if new_val:
                self.plotItem.setTitle(new_val)
            else:
                # will hide the title label
                self.plotItem.setTitle(None)

    plotTitle = Property(str, _get_plot_title, _set_plot_title)
    """
    Title shown at the top of the plot.

    :type: str
    """

    def _get_show_time_line(self) -> bool:
        return self.plotItem.plot_config.time_progress_line

    def _set_show_time_line(self, new_val: bool):
        if new_val != self.plotItem.plot_config.time_progress_line:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_progress_line = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    showTimeProgressLine = Property(bool, fget=_get_show_time_line, fset=_set_show_time_line)
    """
    Show vertical line indicating the current timestamp.

    :type: bool
    """

    def _get_right_time_span_boundary(self) -> float:
        return self.plotItem.plot_config.time_span.right_boundary_offset

    def _set_right_time_span_boundary(self, new_val: float):
        if new_val != self.plotItem.plot_config.time_span.right_boundary_offset:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_span.right_boundary_offset = new_val
            if new_val > new_config.time_span.left_boundary_offset:
                new_config.time_span.left_boundary_offset = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    rightTimeBoundary = Property(float,
                                 fget=_get_right_time_span_boundary,
                                 fset=_set_right_time_span_boundary,
                                 designable=False)
    """
    Value of the right (upper) boundary of the plot's time span.

    :type: float
    """

    def _get_left_time_span_boundary(self, hide_nans: bool = True) -> float:
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
        if new_val != self._get_left_time_span_boundary(hide_nans=False):
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_span.left_boundary_offset = new_val
            if new_val < new_config.time_span.right_boundary_offset:
                new_config.time_span.right_boundary_offset = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    leftTimeBoundary = Property(float,
                                fget=_get_left_time_span_boundary,
                                fset=_set_left_time_span_boundary,
                                designable=False)
    """
    Value of the left (lower) boundary of the plot's time span.

    :type: float
    """

    def _get_left_time_span_boundary_bool(self) -> bool:
        return not np.isinf(self._get_left_time_span_boundary(hide_nans=False))

    def _set_left_time_span_boundary_bool(self, new_val: bool):
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

    leftTimeBoundaryEnabled = Property(bool,
                                       fget=_get_left_time_span_boundary_bool,
                                       fset=_set_left_time_span_boundary_bool,
                                       designable=False)
    """
    Toggle for the left (lower) boundary of the plot's time span.

    This allows choosing between infinite time span into the past, or having a hard border of the oldest timestamps.

    :type: bool
    """

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

    def _init_ex_plot_item(self,
                           config: Optional[ExPlotWidgetConfig] = None,
                           axis_items: Optional[Dict[str, pg.AxisItem]] = None,
                           timing_source: Optional[UpdateSource] = None,
                           **plotitem_kwargs):
        """
        Replace the plot item created by the base class with an instance
        of the extended plot item.
        """
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
    """Enum for grid orientation configuration."""

    Hidden = 0
    """Do not display grid."""

    X = 1
    """Display horizontal lines of the grid."""

    Y = 2
    """Display vertical lines of the grid."""

    Both = 3
    """Display all lines of the grid."""


class XAxisSideOptions:
    """Enum for the x-axis side configuration."""

    Hidden = 0
    """No x-axis should be displayed."""

    Top = 1
    """x-axis should be placed above the plot."""

    Bottom = 2
    """x-axis should be placed beneath the plot."""

    Both = 3
    """x-axis should be mirrored both above and beneath the plot."""


class DefaultYAxisSideOptions:
    """Enum for the default y-axis side configuration."""

    Hidden = 0
    """No y-axis should be displayed."""

    Left = 1
    """y-axis should be placed on the left from the plot."""

    Right = 2
    """y-axis should be placed on the right from the plot."""

    Both = 3
    """x-axis should be mirrored both on the left and right from the plot."""


class LegendXAlignmentOptions:
    """Enum for the horizontal alignment of the legend."""
    Left = 0
    """Align left."""

    Right = 1
    """Align right."""

    Center = 2
    """Align in the center."""


class LegendYAlignmentOptions:
    """Enum for the vertical alignment of the legend."""
    Top = 0
    """Align top."""

    Bottom = 1
    """Align bottom."""

    Center = 2
    """Align in the center."""


# TODO: Metaclass abc? To enforce subclassing?
class ExPlotWidgetProperties(XAxisSideOptions,
                             DefaultYAxisSideOptions,
                             GridOrientationOptions,
                             LegendXAlignmentOptions,
                             LegendYAlignmentOptions):
    """
    Collection of properties for the :class:`ExPlotWidget` derivatives.

    .. note:: Use this class only to inject properties into custom subclasses, such as:

              .. code-block:: python

                 class SuperPlotWidgetClass(ExPlotWidgetProperties, ExPlotWidget):

              All ``self.<attr>`` calls are resolved to the fields in :class:`ExPlotWidget` in this case.
              If you use this class in any other context, the resolutions will fail.
    """

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

    def _get_show_x_axis(self) -> int:
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

    xAxisSide = Property(XAxisSideOptions, fget=_get_show_x_axis, fset=_set_show_x_axis)
    """
    Indicates the side where the x-axis should be placed. Possible values are :attr:`XAxisSideOptions.Top`,
    :attr:`XAxisSideOptions.Bottom`, :attr:`XAxisSideOptions.Both` and :attr:`XAxisSideOptions.Hidden`.

    :type: int
    """

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

    defaultYAxisSide = Property(DefaultYAxisSideOptions, fget=_get_show_y_axis, fset=_set_show_y_axis)
    """
    Indicates the side where the default y-axis should be placed. Possible values are
    :attr:`DefaultYAxisSideOptions.Left`, :attr:`DefaultYAxisSideOptions.Right`, :attr:`DefaultYAxisSideOptions.Both`
    and :attr:`XAxisSideOptions.Hidden`.

    :type: int
    """

    def _get_show_grid(self) -> int:
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

    gridOrientation = Property(GridOrientationOptions, fget=_get_show_grid, fset=_set_show_grid)
    """
    Indicates the direction of the visible grid lines. Possible values are :attr:`GridOrientationOptions.X`,
    :attr:`GridOrientationOptions.Y`, :attr:`GridOrientationOptions.Both` and :attr:`GridOrientationOptions.Hidden`.

    :type: int
    """

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
                    cast(ExPlotWidget, self).addLegend(size=None,
                                                       offset=None,
                                                       pen=(255, 255, 255, 100),
                                                       brush=(0, 0, 0, 100),
                                                       labelTextColor=(255, 255, 255, 100))
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

    showLegend = Property(bool, fget=_get_show_legend, fset=_set_show_legend)
    """
    Flags whether the legend should be shown.

    :type: bool
    """

    def _get_legend_position(self) -> Tuple[int, int]:
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

    legendXAlignment = Property(LegendXAlignmentOptions, fget=_get_legend_x_position, fset=_set_legend_x_position)
    """
    Indicates the horizontal alignment of the legend. Possible values are :attr:`LegendXAlignmentOptions.Left`,
    :attr:`LegendXAlignmentOptions.Right` and :attr:`LegendXAlignmentOptions.Center`.

    :type: int
    """

    def _get_legend_y_position(self) -> int:
        return self._get_legend_position()[1]

    def _set_legend_y_position(self, new_val: int):
        self._set_legend_position(y_alignment=new_val)

    legendYAlignment = Property(LegendYAlignmentOptions, fget=_get_legend_y_position, fset=_set_legend_y_position)
    """
    Indicates the vertical alignment of the legend. Possible values are :attr:`LegendYAlignmentOptions.Top`,
    :attr:`LegendYAlignmentOptions.Bottom` and :attr:`LegendYAlignmentOptions.Center`.

    :type: int
    """

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

    layerIDs = Property("QStringList", fget=_get_layer_ids, fset=_set_layer_ids, designable=False)
    """
    List of string identifiers of the additional layer.

    :type: ~typing.List[str]
    """

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

    axisLabels = Property(str, fget=_get_axis_labels, fset=_set_axis_labels, designable=False)
    """
    JSON representation of mappings of axis positions and layers to a label text.

    :type: str
    """

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

    axisRanges = Property(str, fget=_get_axis_ranges, fset=_set_axis_ranges, designable=False)
    """
    JSON representation of mappings of x, y and layers to a view range.

    :type: str
    """

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
        removed_layer_ids = [layer for layer in self._get_layer_ids() if layer not in new]
        added_layer_ids = [layer for layer in new if layer not in self._get_layer_ids()]
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


class ScrollingPlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    SymbolOptions = SymbolOptions

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 background: str = "default",
                 time_span: Union[TimeSpan, float, None] = 60.0,
                 time_progress_line: bool = False,
                 axis_items: Optional[Dict[str, pg.AxisItem]] = None,
                 timing_source: Optional[UpdateSource] = None,
                 **plotitem_kwargs):
        """
        This class displays live data that in real time. This data can be represented in multiple ways,
        e.g. as lines, bar graph, injection marks, etc. Data can either contain a timestamp to be
        precise about timing, or such timestamp will be created whenever the widget receives the data.
        It appends data on one side, thus scrolling the view port through time series.

        Args:
            parent: Owning object.
            background: Background color configuration for the widget. This can be any single argument accepted by
                        :func:`~pyqtgraph.mkColor`. By default, the background color is determined using the
                        ``backgroundColor`` configuration option (see :func:`~pyqtgraph.setConfigOptions`).
            time_span: Amount of seconds after which the data is clipped from the plot.
            time_progress_line: If :obj:`True`, the current timestamp will be marked by a vertical line.
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            timing_source: This timing source allows receiving timing updates decoupled from any received
                           data.
            **plotitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotItem` constructor.
        """
        config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.SCROLLING_PLOT,
                                    time_span=time_span,
                                    time_progress_line=time_progress_line)
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(self,
                              parent=parent,
                              background=background,
                              config=config,
                              axis_items=axis_items,
                              timing_source=timing_source,
                              **plotitem_kwargs)

    rightTimeBoundary = Property(float,
                                 fget=ExPlotWidget._get_right_time_span_boundary,
                                 fset=ExPlotWidget._set_right_time_span_boundary)
    """
    Value of the right (upper) boundary of the plot's time span.

    :type: float
    """

    leftTimeBoundary = Property(float,
                                fget=ExPlotWidget._get_left_time_span_boundary,
                                fset=ExPlotWidget._set_left_time_span_boundary)
    """
    Value of the left (lower) boundary of the plot's time span.

    :type: float
    """

    leftTimeBoundaryEnabled = Property(bool,
                                       fget=ExPlotWidget._get_left_time_span_boundary_bool,
                                       fset=ExPlotWidget._set_left_time_span_boundary_bool)
    """
    Toggle for the left (lower) boundary of the plot's time span.

    This allows choosing between infinite time span into the past, or having a hard border of the oldest timestamps.

    :type: bool
    """

    # ~~~~~~~~~~~~~~~ pushData slot ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pushDataItemPenColor = Property(QColor,
                                    fget=ExPlotWidget._get_slot_item_pen_color,
                                    fset=ExPlotWidget._set_slot_item_pen_color)
    """
    Pen color for the item displaying data through the :meth:`pushData` slot.

    :type: QColor
    """

    pushDataItemPenWidth = Property(int,
                                    fget=ExPlotWidget._get_slot_item_pen_width,
                                    fset=ExPlotWidget._set_slot_item_pen_width)
    """
    Pen width for the item displaying data through the :meth:`pushData` slot.

    :type: int
    """

    pushDataItemPenStyle = Property(Qt.PenStyle,
                                    fget=ExPlotWidget._get_slot_item_pen_style,
                                    fset=ExPlotWidget._set_slot_item_pen_style)
    """
    Pen line style for the item displaying data through :meth:`pushData` slot.

    :type: Qt.PenStyle
    """

    pushDataItemBrushColor = Property(QColor,
                                      fget=ExPlotWidget._get_slot_item_brush_color,
                                      fset=ExPlotWidget._set_slot_item_brush_color)
    """
    Brush color for the item displaying data through the :meth:`pushData` slot.

    :type: str
    """

    pushDataItemSymbol = Property(SymbolOptions,
                                  fget=ExPlotWidget._get_slot_item_symbol,
                                  fset=ExPlotWidget._set_slot_item_symbol)
    """
    Symbol for the item displaying data through :meth:`pushData` slot.

    :type: int
    """

    @Slot(float)
    @Slot(int)
    @Slot(tuple)
    @Slot(list)
    @Slot(np.ndarray)
    @Slot(PointData)
    def pushData(self, data: Union[int, float, Sequence[float], PointData]):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot by using conventional PyQt signal-slot connection,
        instead of using an :class:`UpdateSource`. If this plot item does not yet exist,
        it will be created automatically. Further calls will append new data
        to the existing one.

        Args:
            data: :obj:`int` or :obj:`float` values to represent a value that will be bound to the
                  timestamp of their arrival. :class:`PointData` type will specify both x- and y-value.
                  Sequence of floats can be used to specify x-value as well, by passing ``[y, x]`` list.
        """
        if not isinstance(data, PointData):
            data = cast(PointData, PlottingItemDataFactory.transform(PointData, data))  # type: ignore
        self.plotItem.plot_data_on_single_data_item(data=data,
                                                    # ignore, bc mypy wants concrete class
                                                    item_type=AbstractBasePlotCurve,  # type: ignore
                                                    pen=self._get_slot_item_pen(),
                                                    symbolPen=self._get_slot_item_pen(),
                                                    symbolBrush=pg.mkBrush(self._get_slot_item_brush_color()),
                                                    symbol=self._get_slot_item_symbol_string())


class CyclicPlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    SymbolOptions = SymbolOptions

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 background: str = "default",
                 time_span: Union[TimeSpan, float, None] = 60.0,
                 time_progress_line: bool = False,
                 axis_items: Optional[Dict[str, pg.AxisItem]] = None,
                 timing_source: Optional[UpdateSource] = None,
                 **plotitem_kwargs):
        """
        This class is meant to scroll through the same cycle, updating the previous display,
        similar to how heart monitors do it. It is useful for displaying data in the context
        of a cycle of the injector / accelerator.

        Data gets appended at first, until filling up the entire time frame. After it’s full,
        data will be inserted from the beginning.

        Args:
            parent: Owning object.
            background: Background color configuration for the widget. This can be any single argument accepted by
                        :func:`~pyqtgraph.mkColor`. By default, the background color is determined using the
                        ``backgroundColor`` configuration option (see :func:`~pyqtgraph.setConfigOptions`).
            time_span: Length of the cycle in seconds.
            time_progress_line: If :obj:`True`, the current timestamp will be marked by a vertical line.
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            timing_source: This timing source allows receiving timing updates decoupled from any received
                           data.
            **plotitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotItem` constructor.
        """
        config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.CYCLIC_PLOT,
                                    time_span=time_span,
                                    time_progress_line=time_progress_line)
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(self,
                              parent=parent,
                              background=background,
                              config=config,
                              axis_items=axis_items,
                              timing_source=timing_source,
                              **plotitem_kwargs)

    leftTimeBoundary = Property(float,
                                fget=ExPlotWidget._get_left_time_span_boundary,
                                fset=ExPlotWidget._set_left_time_span_boundary)
    """
    Value of the left (lower) boundary of the plot's time span.

    :type: float
    """

    def _get_left_time_span_boundary_bool(self, **kwargs) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundaryEnabled' is not supposed to be used with at cyclic plot, "
                          "since a cyclic plot can not be drawn without both boundaries defined.")
        return False

    def _set_left_time_span_boundary_bool(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundaryEnabled' is not supposed to be used with at cyclic plot, "
                          "since a cyclic plot can not be drawn without both boundaries defined.")

    leftTimeBoundaryEnabled = Property(bool,
                                       fget=_get_left_time_span_boundary_bool,
                                       fset=_set_left_time_span_boundary_bool,
                                       designable=False)
    """
    .. warning:: Do not use this in a cyclic plot.
    """

    # ~~~~~~~~~~~~~~~ pushData slot ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pushDataItemPenColor = Property(QColor,
                                    fget=ExPlotWidget._get_slot_item_pen_color,
                                    fset=ExPlotWidget._set_slot_item_pen_color)
    """
    Pen color for the item displaying data through the :meth:`pushData` slot.

    :type: QColor
    """

    pushDataItemPenWidth = Property(int,
                                    fget=ExPlotWidget._get_slot_item_pen_width,
                                    fset=ExPlotWidget._set_slot_item_pen_width)
    """
    Pen width for the item displaying data through the :meth:`pushData` slot.

    :type: int
    """

    pushDataItemPenStyle = Property(Qt.PenStyle,
                                    fget=ExPlotWidget._get_slot_item_pen_style,
                                    fset=ExPlotWidget._set_slot_item_pen_style)
    """
    Pen line style for the item displaying data through the :meth:`pushData` slot.

    :type: Qt.PenStyle
    """

    pushDataItemBrushColor = Property(QColor,
                                      fget=ExPlotWidget._get_slot_item_brush_color,
                                      fset=ExPlotWidget._set_slot_item_brush_color)
    """
    Brush color for the item displaying data through the :meth:`pushData` slot.

    :type: str
    """

    pushDataItemSymbol = Property(SymbolOptions,
                                  fget=ExPlotWidget._get_slot_item_symbol,
                                  fset=ExPlotWidget._set_slot_item_symbol)
    """
    Symbol for the item displaying data through the :meth:`pushData` slot.

    :type: int
    """

    @Slot(float)
    @Slot(int)
    @Slot(tuple)
    @Slot(list)
    @Slot(np.ndarray)
    @Slot(PointData)
    def pushData(self, data: Union[int, float, ArrayLike, PointData]):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot by using conventional PyQt signal-slot connection,
        instead of using an :class:`UpdateSource`. If this plot item does not yet exist,
        it will be created automatically. Further calls will append new data
        to the existing one.

        Args:
            data: :obj:`int` or :obj:`float` values to represent a value that will be bound to the
                  timestamp of their arrival. :class:`PointData` type will specify both x- and y-value.
                  Sequence of floats can be used to specify x-value as well, by passing ``[y, x]`` list.
        """
        if not isinstance(data, PointData):
            data = PlottingItemDataFactory.transform(PointData, data)  # type: ignore
        self.plotItem.plot_data_on_single_data_item(data=data,
                                                    # ignore, bc mypy wants concrete class
                                                    item_type=AbstractBasePlotCurve,  # type: ignore
                                                    pen=self._get_slot_item_pen(),
                                                    symbolPen=self._get_slot_item_pen(),
                                                    symbolBrush=pg.mkBrush(self._get_slot_item_brush_color()),
                                                    symbol=self._get_slot_item_symbol_string())


class StaticPlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 background: str = "default",
                 axis_items: Optional[Dict[str, pg.AxisItem]] = None,
                 **plotitem_kwargs):
        """
        This type of plot is not moving with time and allows replacing the entire contents of the graph,
        rather than appending points to the existing data set. This makes it perfect for displaying
        waveforms, frequencies, or simply graphs that are recalculated on every tick.

        Args:
            parent: Owning object.
            background: Background color configuration for the widget. This can be any single argument accepted by
                        :func:`~pyqtgraph.mkColor`. By default, the background color is determined using the
                        ``backgroundColor`` configuration option (see :func:`~pyqtgraph.setConfigOptions`).
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            **plotitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotItem` constructor.
        """
        config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.STATIC_PLOT)
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(self,
                              parent=parent,
                              background=background,
                              config=config,
                              axis_items=axis_items,
                              **plotitem_kwargs)

    def _get_show_time_line(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'showTimeProgressLine' is not supposed to be used with at static plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")
        return False

    def _set_show_time_line(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'showTimeProgressLine' is not supposed to be used with at static plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")

    showTimeProgressLine = Property(bool, fget=_get_show_time_line, fset=_set_show_time_line, designable=False)
    """
    Show vertical line indicating the current timestamp.

    :type: bool
    """

    def _get_right_time_span_boundary(self) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'rightTimeBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")
        return False

    def _set_right_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'rightTimeBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")

    rightTimeBoundary = Property(float,
                                 fget=_get_right_time_span_boundary,
                                 fset=_set_right_time_span_boundary,
                                 designable=False)
    """
    .. warning:: Do not use this in a static plot.
    """

    def _get_left_time_span_boundary(self, hide_nans: bool = True) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundary' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")

    leftTimeBoundary = Property(float,
                                fget=_get_left_time_span_boundary,
                                fset=_set_left_time_span_boundary,
                                designable=False)
    """
    .. warning:: Do not use this in a static plot.
    """

    def _get_left_time_span_boundary_bool(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundaryEnabled' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary_bool(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundaryEnabled' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")

    leftTimeBoundaryEnabled = Property(bool,
                                       fget=_get_left_time_span_boundary_bool,
                                       fset=_set_left_time_span_boundary_bool,
                                       designable=False)
    """
    .. warning:: Do not use this in a static plot.
    """

    # ~~~~~~~~~~~~ replaceData ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    replaceDataItemPenColor = Property(QColor,
                                       fget=ExPlotWidget._get_slot_item_pen_color,
                                       fset=ExPlotWidget._set_slot_item_pen_color)
    """
    Pen color for the item displaying data through the :meth:`replaceDataAsCurve`,
    :meth:`replaceDataAsBarGraph`, :meth:`replaceDataAsInjectionBars` slots.

    :type: QColor
    """

    replaceDataItemPenWidth = Property(int,
                                       fget=ExPlotWidget._get_slot_item_pen_width,
                                       fset=ExPlotWidget._set_slot_item_pen_width)
    """
    Pen width for the item displaying data through the :meth:`replaceDataAsCurve`,
    :meth:`replaceDataAsBarGraph`, :meth:`replaceDataAsInjectionBars` slots.

    :type: int
    """

    replaceDataItemPenStyle = Property(Qt.PenStyle,
                                       fget=ExPlotWidget._get_slot_item_pen_style,
                                       fset=ExPlotWidget._set_slot_item_pen_style)
    """
    Pen line style for the item displaying data through the :meth:`replaceDataAsCurve`,
    :meth:`replaceDataAsBarGraph`, :meth:`replaceDataAsInjectionBars` slots.

    :type: Qt.PenStyle
    """

    replaceDataItemBrushColor = Property(QColor,
                                         fget=ExPlotWidget._get_slot_item_brush_color,
                                         fset=ExPlotWidget._set_slot_item_brush_color)
    """
    Brush color for the item displaying data through the :meth:`replaceDataAsCurve`,
    :meth:`replaceDataAsBarGraph`, :meth:`replaceDataAsInjectionBars` slots.

    :type: str
    """

    replaceDataItemSymbol = Property(SymbolOptions,
                                     fget=ExPlotWidget._get_slot_item_symbol,
                                     fset=ExPlotWidget._set_slot_item_symbol)
    """
    Symbol for the item displaying data through the :meth:`replaceDataAsCurve`,
    :meth:`replaceDataAsBarGraph`, :meth:`replaceDataAsInjectionBars` slots.

    :type: int
    """

    @Slot(np.ndarray)
    @Slot(CurveData)
    def replaceDataAsCurve(self, data: Union[Sequence[float], CurveData]):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot by using conventional PyQt signal-slot connection,
        instead of using an :class:`UpdateSource`. If this plot item does not yet exist,
        it will be created automatically. Further calls will replace the existing data with
        the new one.

        Args:
            data: Curve object or a sequence of values representing the curve that will be evenly distributed.
        """
        if not isinstance(data, CurveData):
            data = cast(CurveData, PlottingItemDataFactory.transform(CurveData, data))  # type: ignore
        self.plotItem.plot_data_on_single_data_item(data=data,
                                                    # ignore, bc mypy wants concrete class
                                                    item_type=AbstractBasePlotCurve,  # type: ignore
                                                    pen=self._get_slot_item_pen(),
                                                    symbolPen=self._get_slot_item_pen(),
                                                    symbolBrush=pg.mkBrush(self._get_slot_item_brush_color()),
                                                    symbol=self._get_slot_item_symbol_string())

    @Slot(BarCollectionData)
    def replaceDataAsBarGraph(self, data: BarCollectionData):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot by using conventional PyQt signal-slot connection,
        instead of using an :class:`UpdateSource`. If this plot item does not yet exist,
        it will be created automatically. Further calls will replace the existing data with
        the new one.

        Args:
            data: Collection of bar graphs.
        """
        self.plotItem.plot_data_on_single_data_item(data=data,
                                                    # ignore, bc mypy wants concrete class
                                                    item_type=AbstractBaseBarGraphItem,  # type: ignore
                                                    pen=self._get_slot_item_pen(),
                                                    brush=pg.mkBrush(self._get_slot_item_brush_color()))

    @Slot(InjectionBarCollectionData)
    def replaceDataAsInjectionBars(self, data: InjectionBarCollectionData):
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot by using conventional PyQt signal-slot connection,
        instead of using an :class:`UpdateSource`. If this plot item does not yet exist,
        it will be created automatically. Further calls will replace the existing data with
        the new one.

        Args:
            data: Collection of injection bars.
        """
        self.plotItem.plot_data_on_single_data_item(data=data,
                                                    # ignore, bc mypy wants concrete class
                                                    item_type=AbstractBaseInjectionBarGraphItem,  # type: ignore
                                                    pen=self._get_slot_item_pen())


class EditablePlotWidget(ExPlotWidgetProperties, ExPlotWidget, SymbolOptions):  # type: ignore[misc]

    Q_ENUM(SymbolOptions)
    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 background: str = "default",
                 axis_items: Optional[Dict[str, pg.AxisItem]] = None,
                 **plotitem_kwargs):
        """
        Editable plot is a static, non-live plot that allows modifying data in an
        interactive way, by dragging individual points or sets of points and
        applying transformations to them via :class:`EditableToolbar`.

        Args:
            parent: Owning object.
            background: Background color configuration for the widget. This can be any single argument accepted by
                        :func:`~pyqtgraph.mkColor`. By default, the background color is determined using the
                        ``backgroundColor`` configuration option (see :func:`~pyqtgraph.setConfigOptions`).
            axis_items: If the standard plot axes should be replaced, pass a dictionary
                        with axes mapped to the position in which they should be put.
            **plotitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotItem` constructor.
        """
        config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.EDITABLE)
        ExPlotWidgetProperties.__init__(self)
        ExPlotWidget.__init__(self,
                              parent=parent,
                              background=background,
                              config=config,
                              axis_items=axis_items,
                              **plotitem_kwargs)

    def _get_show_time_line(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'showTimeProgressLine' is not supposed to be used with at editable plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")
        return False

    def _set_show_time_line(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'showTimeProgressLine' is not supposed to be used with at editable plot. "
                          "Use only with ScrollingPlotWidget and CyclicPlotWidget.")

    showTimeProgressLine: bool = Property(bool, fget=_get_show_time_line, fset=_set_show_time_line, designable=False)
    """
    .. warning:: Do not use this in an editable plot.
    """

    def _get_right_time_span_boundary(self) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'rightTimeBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")
        return False

    def _set_right_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'rightTimeBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")

    rightTimeBoundary: float = Property(float,
                                        fget=_get_right_time_span_boundary,
                                        fset=_set_right_time_span_boundary,
                                        designable=False)
    """
    .. warning:: Do not use this in an editable plot.
    """

    def _get_left_time_span_boundary(self, hide_nans: bool = True) -> float:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary(self, new_val: float):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundary' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")

    leftTimeBoundary: float = Property(float,
                                       fget=_get_left_time_span_boundary,
                                       fset=_set_left_time_span_boundary,
                                       designable=False)
    """
    .. warning:: Do not use this in an editable plot.
    """

    def _get_left_time_span_boundary_bool(self) -> bool:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")
        return False

    def _set_left_time_span_boundary_bool(self, new_val: bool):
        if not designer_check.is_designer():
            warnings.warn("Property 'leftTimeBoundaryEnabled' is not supposed to be used with at editable plot, "
                          "since it does not use any time span.")

    leftTimeBoundaryEnabled: bool = Property(bool,
                                             fget=_get_left_time_span_boundary_bool,
                                             fset=_set_left_time_span_boundary_bool,
                                             designable=False)
    """
    .. warning:: Do not use this in an editable plot.
    """
