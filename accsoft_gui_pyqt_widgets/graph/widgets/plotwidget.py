"""
Extended Widget for custom plotting with simple configuration wrappers
"""

from typing import Dict, Optional, Any, Set, List, Tuple, Union
from copy import deepcopy
import json
import logging

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Slot, Property
from qtpy.QtWidgets import QWidget
from qtpy.QtGui import QPen

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotitem import ExPlotItem, PlotItemLayer, LayerIdentification
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.bargraphitem import LiveBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.injectionbaritem import LiveInjectionBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.timestampmarker import LiveTimestampMarker
from accsoft_gui_pyqt_widgets.graph.designer import designer_check

_LOGGER = logging.getLogger(__name__)


class ExPlotWidget(pg.PlotWidget):
    """Extended PlotWidget

    Extended version of PyQtGraphs PlotWidget with additional functionality
    providing special functionality for live data plotting.

    ExPlotWidget subclasses PlotWidgetStyle to have access to its class
    attributes, which are needed for using the ExPlotWidget in QtDesigner.

    By default some properties are not designable, since they only make sense
    with a single plotting style. In subclasses for designer, where they are
    used, set designable explicitly to True to make them appear in the property
    sheet.
    """

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            config: Optional[ExPlotWidgetConfig] = None,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        """Create a new plot widget.

        Args:
            parent: parent item for this widget, will only be passed to base class
            background: background for the widget, will only be passed to base class
            timing_source: Optional source for timing
                updates
            config: Configuration for the plot widget
            **plotitem_kwargs: Params passed to the plot item
        """
        super().__init__(parent=parent, background=background)
        config = config or ExPlotWidgetConfig()
        if axis_items is None:
            axis_items = {}
        self.timing_source = timing_source
        self._config = config
        axis_items = axis_items or {}
        # From base class
        self.plotItem: ExPlotItem
        self._init_ex_plot_item(
            axis_items=axis_items,
            config=config,
            timing_source=timing_source,
            **plotitem_kwargs
        )
        self._wrap_plotitem_functions()
        # Fields for keeping track of properties
        self._layer_identifiers_from_property: List[str] = []
        self._layers_number: int = 0
        self._layer_axis_labels: Dict[str, str] = {}
        self._standard_axis_labels: Dict[str, str] = {}
        self._layer_axis_ranges: Dict[str, Tuple[Union[float, int], Union[float, int]]] = {}
        self._standard_axis_ranges: Dict[str, Tuple[Union[float, int], Union[float, int]]] = {}
        self._show_axis_top: bool = self.plotItem.getAxis("top").isVisible()
        self._show_axis_right: bool = self.plotItem.getAxis("right").isVisible()
        self._show_axis_bottom: bool = self.plotItem.getAxis("bottom").isVisible()
        self._show_axis_left: bool = self.plotItem.getAxis("left").isVisible()

    def _init_ex_plot_item(
            self,
            config: Optional[ExPlotWidgetConfig] = None,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs
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
        del old_plot_item

    def update_configuration(self, config: ExPlotWidgetConfig) -> None:
        """
        Replace the PlotWidgets configuration and adapt all added items
        to fit the new configuration (f.e. a changed plotting style, time span
        size ...)

        Args:
            config: New configuration object
        """
        self._config = config
        self.plotItem.update_configuration(config=config)

    def _wrap_plotitem_functions(self) -> None:
        """
        For convenience the PlotWidget wraps some functions of the PlotItem
        Since we replace the inner `self.plotItem` we have to change the wrapped
        functions of it as well. This list has to be kept in sync with the
        equivalent in the base class constructor.

        Returns:
            None
        """
        wrap_from_base_class = [
            "addItem", "removeItem", "autoRange", "clear", "setXRange",
            "setYRange", "setRange", "setAspectLocked", "setMouseEnabled",
            "setXLink", "setYLink", "enableAutoRange", "disableAutoRange",
            "setLimits", "register", "unregister", "viewRect"
        ]
        for method in wrap_from_base_class:
            setattr(self, method, getattr(self.plotItem, method))
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)

    def add_layer(
            self,
            identifier: str,
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
            **axis_label_css_kwargs
    ) -> "PlotItemLayer":
        """add a new layer to the plot for plotting a curve in a different range

        Layer Args:
            identifier: string identifier for the new layer

        Range Setting Args:
            y_range: set the view range of the new y axis on creation.
                     This is equivalent to calling setYRange(layer=...)
            y_range_padding: Padding to use when setting the y range
            invert_y: Invert the y axis of the newly created layer. This
                      is equivalent to calling invertY(layer=...)

        Axis Item Args:
            max_tick_length: maximum length of ticks to draw. Negative values
                             draw into the plot, positive values draw outward.
            link_view: causes the range of values displayed in the axis
                       to be linked to the visible range of a ViewBox.
            show_values: Whether to display values adjacent to ticks
            pen: Pen used when drawing ticks.

        Axis Label Args:
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
        return self.plotItem.add_layer(
            identifier=identifier,
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
            **axis_label_css_kwargs
        )

    def addCurve(  # pylint: disable=invalid-name
            self,
            c: Optional[pg.PlotDataItem] = None,  # pylint: disable=invalid-name
            params: Optional[Any] = None,
            data_source: Optional[UpdateSource] = None,
            layer: Optional[LayerIdentification] = None,
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
            layer: identifier of the layer the new curve is supposed to be added to
            buffer_size: maximum count of values the datamodel buffer should hold
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

    def addBarGraph(  # pylint: disable=invalid-name
            self,
            data_source: Optional[UpdateSource] = None,
            layer: Optional[LayerIdentification] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **bargraph_kwargs
    ) -> LiveBarGraphItem:
        """Add a new bargraph attached to a live data source

        Args:
            data_source: Source emitting new data the graph should show
            layer: Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **bargraph_kwargs: keyword arguments for the BarGraphItem base class

        Returns:
            LiveBarGraphItem that was added to the plot
        """
        return self.plotItem.addBarGraph(
            data_source=data_source,
            layer=layer,
            buffer_size=buffer_size,
            **bargraph_kwargs
        )

    def addInjectionBar(  # pylint: disable=invalid-name
            self,
            data_source: UpdateSource,
            layer: Optional[LayerIdentification] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **errorbaritem_kwargs,
    ) -> LiveInjectionBarGraphItem:
        """Add a new injection bar graph for live data

        A new injection-bar graph with a datamodel that receives data from the passed source will
        be added to the plotitem

        Args:
            data_source: Source for data related updates
            layer: Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **errorbaritem_kwargs: Keyword arguments for the ErrorBarItems used in the Injectionbars

        Returns:
            New item that was added to the plot
        """
        return self.plotItem.addInjectionBar(
            data_source=data_source,
            layer=layer,
            buffer_size=buffer_size,
            **errorbaritem_kwargs
        )

    def addTimestampMarker(  # pylint: disable=invalid-name
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
        return self.plotItem.addTimestampMarker(
            *graphicsobjectargs,
            data_source=data_source,
            buffer_size=buffer_size
        )

    @Slot(float)
    @Slot(int)
    def addDataToSingleCurve(self, data):  # pylint: disable=invalid-name
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot. If this curve does not yet exist,
        it will be created automatically . The data will be collected by
        the curve and drawn. Further calls with other data will append it
        to the existing one.

        This slot will accept single integer and float values
        and draw them at the timestamp of their arrival.
        """
        self.plotItem.handle_add_data_to_single_curve(data)

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

    plotTitle = Property(str, _get_plot_title, _set_plot_title)

    def _get_show_time_line(self) -> bool:
        """QtDesigner getter function for the PlotItems flag for showing the current timestamp with a line"""
        return self.plotItem.plot_config.time_progress_line

    def _set_show_time_line(self, new_val: bool):
        """QtDesigner setter function for the PlotItems flag for showing the current timestamp with a line"""
        if new_val != self.plotItem.plot_config.time_progress_line:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_progress_line = new_val
            self.plotItem.update_configuration(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    showTimeProgressLine = Property(bool, _get_show_time_line, _set_show_time_line, designable=False)

    def _get_time_span(self) -> float:
        """QtDesigner getter function for the PlotItems time span size"""
        return self.plotItem.plot_config.time_span

    def _set_time_span(self, new_val: float):
        """QtDesigner setter function for the PlotItems time span size"""
        if new_val != self.plotItem.plot_config.time_span and new_val > 0:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_span = new_val
            self.plotItem.update_configuration(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    timeSpan = Property(float, _get_time_span, _set_time_span, designable=False)

# pylint: disable=no-member,access-member-before-definition,attribute-defined-outside-init


class ExPlotWidgetProperties:

    """
    Do not use this class except as a base class to inject properties in the following
    context:

    SuperPlotWidgetClass(ExPlotWidgetProperties, ExPlotWidget)

    All self.xyz calls are resolved to the fields in ExPlotWidget in this context.
    If you use this class in any other context, these resolutions will fail.
    """

    def _get_show_x_grid(self) -> bool:
        """QtDesigner getter function for the PlotItems x grid"""
        return self.plotItem.ctrl.xGridCheck.isChecked()  # type: ignore[attr-defined]

    def _set_show_x_grid(self, new_val: bool):
        """QtDesigner setter function for the PlotItems x grid"""
        if new_val != self.plotItem.ctrl.xGridCheck.isChecked():  # type: ignore[attr-defined]
            self.plotItem.showGrid(x=new_val)  # type: ignore[attr-defined]

    showGridX = Property(bool, _get_show_x_grid, _set_show_x_grid)

    def _get_show_y_grid(self) -> bool:
        """QtDesigner getter function for the PlotItems y grid"""
        return self.plotItem.ctrl.yGridCheck.isChecked()  # type: ignore[attr-defined]

    def _set_show_y_grid(self, new_val: bool):
        """QtDesigner setter function for the PlotItems y grid"""
        if new_val != self.plotItem.ctrl.yGridCheck.isChecked():  # type: ignore[attr-defined]
            self.plotItem.showGrid(y=new_val)  # type: ignore[attr-defined]

    showGridY = Property(bool, _get_show_y_grid, _set_show_y_grid)

    def _get_show_bottom_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems bottom axis"""
        return self._show_axis_bottom  # type: ignore[has-type]

    def _set_show_bottom_axis(self, new_val: bool):
        """QtDesigner setter function for showing the PlotItems bottom axis"""
        if new_val != self._show_axis_bottom:  # type: ignore[has-type]
            self._show_axis_bottom = new_val
            self.showAxis("bottom", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showBottomAxis = Property(bool, _get_show_bottom_axis, _set_show_bottom_axis)

    def _get_show_top_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems top axis"""
        return self._show_axis_top   # type: ignore[has-type]

    def _set_show_top_axis(self, new_val: bool):
        """QtDesigner setter function for showing the PlotItems top axis"""
        if new_val != self._show_axis_top:  # type: ignore[has-type]
            self._show_axis_top = new_val
            self.showAxis("top", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showTopAxis = Property(bool, _get_show_top_axis, _set_show_top_axis)

    def _get_show_left_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems left axis"""
        return self._show_axis_left  # type: ignore[has-type]

    def _set_show_left_axis(self, new_val: bool):
        """QtDesigner setter function for showing the PlotItems left axis"""
        if new_val != self._show_axis_left:  # type: ignore[has-type]
            self._show_axis_left = new_val
            self.showAxis("left", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showLeftAxis = Property(bool, _get_show_left_axis, _set_show_left_axis)

    def _get_show_right_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems right axis"""
        return self._show_axis_right  # type: ignore[has-type]

    def _set_show_right_axis(self, new_val: bool):
        """QtDesigner setter function for showing the PlotItems right axis"""
        if new_val != self._show_axis_right:  # type: ignore[has-type]
            self._show_axis_right = new_val
            self.showAxis("right", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showRightAxis = Property(bool, _get_show_right_axis, _set_show_right_axis)

    # ~~~~~~~~~~~ Properties mainly for designer usage ~~~~~~~~~~~

    reserved_axis_labels_identifiers: Set[str] = {
        "top", "bottom", "left", "right", PlotItemLayer.default_layer_identifier
    }

    reserved_axis_ranges_identifiers: Set[str] = {"x", "y"}

    def _get_additional_layers_count(self) -> int:
        """
        QtDesigner getter function for the PlotItems count of additional layers

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        return self._layers_number  # type: ignore[has-type]

    def _set_additional_layers_count(self, new_val: int):
        """
        QtDesigner setter function for the PlotItems count of additional layers

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        if new_val != self._layers_number and new_val >= 0:  # type: ignore[has-type]
            self._layers_number = new_val
            if new_val < len(self._layer_identifiers_from_property):
                self._set_layer_identifiers(new_val=self._layer_identifiers_from_property[:new_val])
            elif new_val > len(self._layer_identifiers_from_property):
                id_number = 0
                for _ in range(len(self._layer_identifiers_from_property), new_val):
                    while f"layer_{id_number}" in self._layer_identifiers_from_property:
                        id_number += 1
                    self._layer_identifiers_from_property.append(f"layer_{id_number}")
            self._update_layer_from_designer_properties()
            self._update_axis_labels_from_designer_properties()

    additionalLayers = Property(int, _get_additional_layers_count, _set_additional_layers_count)

    def _get_layer_identifiers(self) -> "QStringList":  # type: ignore # noqa
        """
        QtDesigner getter function for the PlotItems time span

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        return self._layer_identifiers_from_property

    def _set_layer_identifiers(self, new_val: "QStringList"):  # type: ignore # noqa
        """
        QtDesigner setter function for the PlotItems time span

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        # Check for duplicated values
        if len(new_val) != len(set(new_val)):
            print("Layers can not be updated since you have provided duplicated identifiers for them.")
            return
        # Check for invalid layer identifiers
        for reserved in ExPlotWidgetProperties.reserved_axis_labels_identifiers:
            if reserved in new_val:
                print(f"Identifier entry '{reserved}' will be ignored since it is reserved.")
                new_val.remove(reserved)
        self._update_axis_labels_and_ranges_dict(new_identifiers=new_val)
        self._layer_identifiers_from_property = new_val
        self._layers_number = len(new_val)
        self._update_layer_from_designer_properties()
        self._update_axis_labels_from_designer_properties()
        self._update_view_ranges_from_designer_properties()

    layerIdentifiers = Property("QStringList", _get_layer_identifiers, _set_layer_identifiers)

    def _get_axis_labels(self) -> str:
        """QtDesigner getter function for the PlotItems axis labels"""
        return json.dumps(self._axis_labels())

    def _set_axis_labels(self, new_val: str):
        """QtDesigner setter function for the PlotItems axis labels"""
        try:
            axis_labels = json.loads(new_val)
            self._layer_axis_labels: Dict = {}
            self._standard_axis_labels: Dict = {}
            for entry in axis_labels:
                if entry in ExPlotWidgetProperties.reserved_axis_labels_identifiers:
                    self._standard_axis_labels[entry] = axis_labels[entry]
                else:
                    self._layer_axis_labels[entry] = axis_labels[entry]
            self._update_layer_from_designer_properties()
            self._update_axis_labels_from_designer_properties()
        except (json.decoder.JSONDecodeError, AttributeError):
            pass

    axisLabels = Property(str, _get_axis_labels, _set_axis_labels)

    def _get_axis_ranges(self) -> str:
        """QtDesigner getter function for the PlotItems axis ranges"""
        return json.dumps(self._axis_ranges())

    def _set_axis_ranges(self, new_val: str):
        """QtDesigner setter function for the PlotItems axis ranges"""
        try:
            axis_ranges = json.loads(new_val)
            self._layer_axis_ranges: Dict = {}
            self._standard_axis_ranges: Dict = {}
            for entry in axis_ranges:
                # Check if range was given in the right form
                axis_range = axis_ranges[entry]
                if len(axis_range) == 2 and \
                        isinstance(axis_range[0], (float, int)) and \
                        isinstance(axis_range[1], (float, int)):
                    # Save in fitting array
                    if entry in ExPlotWidgetProperties.reserved_axis_ranges_identifiers:
                        self._standard_axis_ranges[entry] = tuple(axis_range)  # type: ignore[assignment]
                    else:
                        self._layer_axis_ranges[entry] = tuple(axis_range)  # type: ignore[assignment]
            self._update_view_ranges_from_designer_properties()
        except (json.decoder.JSONDecodeError, AttributeError, TypeError):
            # JSONDecodeError and Attribute Errors for JSON decoding
            # TypeError for len() operation on entries that do not support it
            pass

    axisRanges = Property(str, _get_axis_ranges, _set_axis_ranges)

    # ~~~~~~~~~~~~ Utilities for the QtDesigner properties ~~~~~~~~~~~~~~~~~~~~

    def _update_axis_labels_and_ranges_dict(self, new_identifiers: List[str]):
        """
        Update the identifiers in the axis label JSON string based on the list of
        identifiers.
        """
        labels_old = deepcopy(self._layer_axis_labels)
        ranges_old = deepcopy(self._layer_axis_ranges)
        # New and old identifier lists have the same length -> assume identifiers were renamed
        if len(self._layer_identifiers_from_property) == len(new_identifiers):
            for entry in zip(self._layer_identifiers_from_property, new_identifiers):
                # Update label json keys
                if entry[0] != entry[1] and labels_old.get(entry[0]):
                    if entry[0] not in new_identifiers or not labels_old.get(entry[1]):
                        self._layer_axis_labels.pop(entry[0], None)
                    if entry[1]:
                        self._layer_axis_labels[entry[1]] = labels_old.get(entry[0], "")
                # Update range json keys
                if entry[0] != entry[1] and ranges_old.get(entry[0]):
                    if entry[0] not in new_identifiers or not ranges_old.get(entry[1]):
                        self._layer_axis_ranges.pop(entry[0], None)
                    if entry[1]:
                        self._layer_axis_ranges[entry[1]] = ranges_old.get(entry[0], (0.0, 1.0))
        # Length did change -> assume identifiers that are not existing anymore, were deleted
        else:
            # Remove old keys from labels json
            deleted_labels = [item for item in self._layer_axis_labels if item not in set(new_identifiers)]
            for deleted_element in deleted_labels:
                self._layer_axis_labels.pop(deleted_element, None)
            # Remove old keys from range json
            deleted_ranges = [item for item in self._layer_axis_ranges if item not in set(new_identifiers)]
            for deleted_range in deleted_ranges:
                self._layer_axis_ranges.pop(deleted_range, None)

    def _update_layer_from_designer_properties(self) -> None:
        """
        Remove all layers added prior to the PlotItem and add new ones
        according to the layer identifier list property
        """
        for layer in self.plotItem.get_all_non_standard_layers():  # type: ignore[attr-defined]
            self.plotItem.remove_layer(layer)  # type: ignore[attr-defined]
        for layer_identifier in self._layer_identifiers_from_property:
            self.plotItem.add_layer(identifier=layer_identifier)  # type: ignore[attr-defined]

    def _update_axis_labels_from_designer_properties(self) -> None:
        """
        Update the axis labels according to the map set in the designer property.
        "left", "top", "right" and "bottom" refer to the standard PlotItem axis.
        For the axis of the layer use the layer's identifier as a key.
        """
        for entry in self._axis_labels():
            if entry in ExPlotWidgetProperties.reserved_axis_labels_identifiers:
                if (entry != PlotItemLayer.default_layer_identifier
                        and self.plotItem.getAxis(entry).isVisible()):  # type: ignore[attr-defined]
                    self.plotItem.setLabel(axis=entry, text=f"{self._standard_axis_labels[entry]}")  # type: ignore[attr-defined]
            else:
                try:
                    layer = self.plotItem.get_layer(layer_identifier=entry)  # type: ignore[attr-defined]
                    layer.axis_item.setLabel(f"{self._layer_axis_labels[entry]}")
                except KeyError:
                    pass

    def _update_view_ranges_from_designer_properties(self) -> None:
        """
        Update the view ranges of all axis according to the map set in the
        designer property. Use "x" and "y" for the standard PlotItem dimensions
        and the layer identifier for the y dimension of a additional layer.
        """
        for entry in self._axis_ranges():
            if entry in ("x", "X"):
                self.setXRange(*self._axis_ranges()[entry])  # type: ignore[attr-defined]
            elif entry in ("y", "Y"):
                self.setYRange(*self._axis_ranges()[entry])  # type: ignore[attr-defined]
            else:
                try:
                    layer = self.plotItem.get_layer(layer_identifier=entry)  # type: ignore[attr-defined]
                    layer.view_box.setYRange(min=self._axis_ranges()[entry][0], max=self._axis_ranges()[entry][1])
                except KeyError:
                    pass

    def _axis_labels(self) -> Dict[str, str]:
        """Return a dictionary containing the labels of all axis (if explicitly set)."""
        return {**self._standard_axis_labels, **self._layer_axis_labels}

    def _axis_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Return a dictionary containing the view ranges of all axis (if explicitly set)."""
        return {**self._standard_axis_ranges, **self._layer_axis_ranges}

# pylint: enable=no-member,access-member-before-definition,attribute-defined-outside-init


class ScrollingPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

    """
    ExPlotWidget with scrolling plot widget style and the designer properties
    fitting to it.
    For pure PyQt use ExPlotWidget.
    """

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            config: Optional[ExPlotWidgetConfig] = None,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        if config is None:
            config = ExPlotWidgetConfig()
        config.plotting_style = PlotWidgetStyle.SCROLLING_PLOT
        super().__init__(
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            timing_source=timing_source,
            **plotitem_kwargs
        )

    def _get_fixed_x_range(self) -> bool:
        """QtDesigner getter function for the PlotItems flag for a fixed scrolling x range"""
        return self.plotItem.plot_config.scrolling_plot_fixed_x_range

    def _set_fixed_x_range(self, new_val: bool):
        """QtDesigner setter function for the PlotItems flag for a fixed scrolling x range"""
        if new_val != self.plotItem.plot_config.scrolling_plot_fixed_x_range:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.scrolling_plot_fixed_x_range = new_val
            self.plotItem.update_configuration(config=new_config)

    fixedXRange = Property(
        bool,
        _get_fixed_x_range,
        _set_fixed_x_range,
    )

    def _get_x_range_offset(self) -> float:
        """QtDesigner getter function for the PlotItems fixed scrolling x range offset"""
        if np.isnan(self.plotItem.plot_config.scrolling_plot_fixed_x_range_offset):
            return 0.0
        return self.plotItem.plot_config.scrolling_plot_fixed_x_range_offset

    def _set_x_range_offset(self, new_val: float):
        """QtDesigner setter function for the PlotItems fixed scrolling x range offset"""
        if new_val != self.plotItem.plot_config.scrolling_plot_fixed_x_range_offset:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.scrolling_plot_fixed_x_range_offset = new_val
            self.plotItem.update_configuration(config=new_config)

    fixedXRangeOffset = Property(
        float,
        _get_x_range_offset,
        _set_x_range_offset,
    )

    showTimeProgressLine = Property(bool, ExPlotWidget._get_show_time_line, ExPlotWidget._set_show_time_line)

    timeSpan = Property(float, ExPlotWidget._get_time_span, ExPlotWidget._set_time_span)


class SlidingPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

    """
    ExPlotWidget with sliding plot widget style and the designer properties
    fitting to it.
    For pure PyQt use ExPlotWidget.
    """

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            config: Optional[ExPlotWidgetConfig] = None,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        if config is None:
            config = ExPlotWidgetConfig()
        config.plotting_style = PlotWidgetStyle.SLIDING_POINTER
        super().__init__(
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            timing_source=timing_source,
            **plotitem_kwargs
        )

    showTimeProgressLine = Property(bool, ExPlotWidget._get_show_time_line, ExPlotWidget._set_show_time_line)

    timeSpan = Property(float, ExPlotWidget._get_time_span, ExPlotWidget._set_time_span)


class StaticPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

    """
    ExPlotWidget with static plot widget style and the designer properties
    fitting to it.
    For pure PyQt use ExPlotWidget.
    """

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            config: Optional[ExPlotWidgetConfig] = None,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        if config is None:
            config = ExPlotWidgetConfig()
        config.plotting_style = PlotWidgetStyle.STATIC_PLOT
        super().__init__(
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            timing_source=timing_source,
            **plotitem_kwargs
        )

    def _get_show_time_line(self) -> bool:
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'setShowTimeLine' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")
        return False

    def _set_show_time_line(self, new_val: bool):
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'setShowTimeLine' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")

    showTimeProgressLine = Property(
        bool,
        _get_show_time_line,
        _set_show_time_line,
        designable=False
    )

    def _get_time_span(self) -> float:
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'timeSpan' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")
        return 0.0

    def _set_time_span(self, new_val: float):
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'timeSpan' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")

    timeSpan = Property(
        float,
        _get_time_span,
        _set_time_span,
        designable=False
    )
