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

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle
)
from accwidgets.graph.widgets.plotitem import ExPlotItem, PlotItemLayer, LayerIdentification
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.bargraphitem import LiveBarGraphItem
from accwidgets.graph.widgets.dataitems.injectionbaritem import LiveInjectionBarGraphItem
from accwidgets.graph.widgets.dataitems.timestampmarker import LiveTimestampMarker
from accwidgets.graph.widgets.axisitems import ExAxisItem
from accwidgets.graph.designer import designer_check

_LOGGER = logging.getLogger(__name__)


class ExPlotWidget(pg.PlotWidget):

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
        self._layer_ids_from_property: List[str] = []
        self._layers_number: int = 0
        self._layer_axis_labels: Dict[str, str] = {}
        self._standard_axis_labels: Dict[str, str] = {}
        self._layer_axis_ranges: Dict[str, Tuple[Union[float, int], Union[float, int]]] = {}
        self._standard_axis_ranges: Dict[str, Tuple[Union[float, int], Union[float, int]]] = {}
        self._show_axis_top: bool = self.plotItem.getAxis("top").isVisible()
        self._show_axis_right: bool = self.plotItem.getAxis("right").isVisible()
        self._show_axis_bottom: bool = self.plotItem.getAxis("bottom").isVisible()
        self._show_axis_left: bool = self.plotItem.getAxis("left").isVisible()

    def addCurve(  # pylint: disable=invalid-name
            self,
            c: Optional[pg.PlotDataItem] = None,  # pylint: disable=invalid-name
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
        to f.e. live data, pass a fitting data source and to create a curve
        from f.e. a static array, pass keyword arguments from the PlotDataItem.

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

    def addBarGraph(  # pylint: disable=invalid-name
            self,
            data_source: Optional[UpdateSource] = None,
            layer: Optional[LayerIdentification] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **bargraph_kwargs
    ) -> LiveBarGraphItem:
        """Add a new curve attached to a source for new data

        Create a bar graph fitting to the style of the plot and add it to the plot.
        The new graph can be either either created from static data like
        PlotItem.plot or from a data source that handles communication between
        the graph and a source data is coming from. To create a bar graph attached
        to f.e. live data, pass a fitting data source and to create a bar graph
        from f.e. a static array, pass keyword arguments from the BarGraphItem.

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
            **bargraph_kwargs
        )

    def addInjectionBar(  # pylint: disable=invalid-name
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
            **errorbaritem_kwargs
        )

    def addTimestampMarker(  # pylint: disable=invalid-name
            self,
            *graphicsobjectargs,
            data_source: UpdateSource,
            buffer_size: int = DEFAULT_BUFFER_SIZE
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
            buffer_size=buffer_size
        )

    @Slot(float)
    @Slot(int)
    def addDataToSingleCurve(self, data) -> None:  # pylint: disable=invalid-name
        """
        This slot exposes the possibility to draw data on a
        single curve in the plot. If this curve does not yet exist,
        it will be created automatically . The data will be collected by
        the curve and drawn. Further calls with other data will append it
        to the existing one.

        This slot will accept single integer and float values
        and draw them at the timestamp of their arrival.
        """
        self.plotItem.add_data_to_single_curve(data)

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
            **axis_label_css_kwargs
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
            **axis_label_css_kwargs
        )

    def update_config(self, config: ExPlotWidgetConfig) -> None:
        """Update the plot widgets configuration

        Items that are affected from the configuration change are recreated with
        the new configuration and their old datamodels, so once displayed data is
        not lost. Static items, mainly pure PyQtGraph items, that were added to
        the plot, are not affected by this and will be kept unchanged in the plot.

        Args:
            config: The new configuration that should be used by the plot and all
                    its (affected) items
        """
        self._config = config
        self.plotItem.update_config(config=config)

    # ~~~~~~~~~~ Properties ~~~~~~~~~

    def _get_plot_title(self) -> str:
        """QtDesigner getter function for the PlotItems title"""
        if self.plotItem.titleLabel.isVisible():
            return self.plotItem.titleLabel.text
        return ""

    def _set_plot_title(self, new_val: str) -> None:
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

    def _set_show_time_line(self, new_val: bool) -> None:
        """QtDesigner setter function for the PlotItems flag for showing the current timestamp with a line"""
        if new_val != self.plotItem.plot_config.time_progress_line:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_progress_line = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    showTimeProgressLine: bool = Property(bool, _get_show_time_line, _set_show_time_line, designable=False)
    """Vertical Line displaying the current time stamp"""

    def _get_time_span(self) -> float:
        """QtDesigner getter function for the PlotItems time span size"""
        return self.plotItem.plot_config.time_span

    def _set_time_span(self, new_val: float) -> None:
        """QtDesigner setter function for the PlotItems time span size"""
        if new_val != self.plotItem.plot_config.time_span and new_val > 0:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.time_span = new_val
            self.plotItem.update_config(config=new_config)

    # designable false ->   can be used from code but is part of the sub classes property sheet if they
    #                       are set to designable
    timeSpan: float = Property(float, _get_time_span, _set_time_span, designable=False)
    """Range from which the plot displays data"""

    # ~~~~~~~~~~ Private ~~~~~~~~~

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

    def _wrap_plotitem_functions(self) -> None:
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
            "setLimits", "register", "unregister", "viewRect"
        ]
        for method in wrap_from_base_class:
            setattr(self, method, getattr(self.plotItem, method))
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)

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

    def _set_show_x_grid(self, new_val: bool) -> None:
        """QtDesigner setter function for the PlotItems x grid"""
        if new_val != self.plotItem.ctrl.xGridCheck.isChecked():  # type: ignore[attr-defined]
            self.plotItem.showGrid(x=new_val)  # type: ignore[attr-defined]

    showGridX: bool = Property(bool, _get_show_x_grid, _set_show_x_grid)
    """Show a grid in x direction"""

    def _get_show_y_grid(self) -> bool:
        """QtDesigner getter function for the PlotItems y grid"""
        return self.plotItem.ctrl.yGridCheck.isChecked()  # type: ignore[attr-defined]

    def _set_show_y_grid(self, new_val: bool) -> None:
        """QtDesigner setter function for the PlotItems y grid"""
        if new_val != self.plotItem.ctrl.yGridCheck.isChecked():  # type: ignore[attr-defined]
            self.plotItem.showGrid(y=new_val)  # type: ignore[attr-defined]

    showGridY: bool = Property(bool, _get_show_y_grid, _set_show_y_grid)
    """Show a grid in y direction"""

    def _get_show_bottom_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems bottom axis"""
        return self._show_axis_bottom  # type: ignore[has-type]

    def _set_show_bottom_axis(self, new_val: bool) -> None:
        """QtDesigner setter function for showing the PlotItems bottom axis"""
        if new_val != self._show_axis_bottom:  # type: ignore[has-type]
            self._show_axis_bottom = new_val
            self.showAxis("bottom", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showBottomAxis: bool = Property(bool, _get_show_bottom_axis, _set_show_bottom_axis)
    """show the x axis at the bottom"""

    def _get_show_top_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems top axis"""
        return self._show_axis_top   # type: ignore[has-type]

    def _set_show_top_axis(self, new_val: bool) -> None:
        """QtDesigner setter function for showing the PlotItems top axis"""
        if new_val != self._show_axis_top:  # type: ignore[has-type]
            self._show_axis_top = new_val
            self.showAxis("top", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showTopAxis: bool = Property(bool, _get_show_top_axis, _set_show_top_axis)
    """show the x axis at the top"""

    def _get_show_left_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems left axis"""
        return self._show_axis_left  # type: ignore[has-type]

    def _set_show_left_axis(self, new_val: bool) -> None:
        """QtDesigner setter function for showing the PlotItems left axis"""
        if new_val != self._show_axis_left:  # type: ignore[has-type]
            self._show_axis_left = new_val
            self.showAxis("left", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showLeftAxis: bool = Property(bool, _get_show_left_axis, _set_show_left_axis)
    """show the y axis on the left side"""

    def _get_show_right_axis(self) -> bool:
        """QtDesigner getter function for showing the PlotItems right axis"""
        return self._show_axis_right  # type: ignore[has-type]

    def _set_show_right_axis(self, new_val: bool) -> None:
        """QtDesigner setter function for showing the PlotItems right axis"""
        if new_val != self._show_axis_right:  # type: ignore[has-type]
            self._show_axis_right = new_val
            self.showAxis("right", new_val)  # type: ignore[attr-defined]
            self._set_axis_labels(new_val=self._get_axis_labels())  # type: ignore[attr-defined]

    showRightAxis: bool = Property(bool, _get_show_right_axis, _set_show_right_axis)
    """show the y axis on the right side"""

    # ~~~~~~~~~~ QtDesigner Properties ~~~~~~~~~~

    _reserved_axis_labels_identifiers: Set[str] = {
        "top", "bottom", "left", "right", PlotItemLayer.default_layer_id
    }

    _reserved_axis_ranges_identifiers: Set[str] = {"x", "y"}

    def _get_additional_layers_count(self) -> int:
        """
        QtDesigner getter function for the PlotItems count of additional layers

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        return self._layers_number  # type: ignore[has-type]

    def _set_additional_layers_count(self, new_val: int) -> None:
        """
        QtDesigner setter function for the PlotItems count of additional layers

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        if new_val != self._layers_number and new_val >= 0:  # type: ignore[has-type]
            self._layers_number = new_val
            if new_val < len(self._layer_ids_from_property):
                self._set_layer_ids(new_val=self._layer_ids_from_property[:new_val])
            elif new_val > len(self._layer_ids_from_property):
                id_number = 0
                for _ in range(len(self._layer_ids_from_property), new_val):
                    while f"layer_{id_number}" in self._layer_ids_from_property:
                        id_number += 1
                    self._layer_ids_from_property.append(f"layer_{id_number}")
            self._update_layer_from_designer_properties()
            self._update_axis_labels_from_designer_properties()

    additionalLayers: int = Property(int, _get_additional_layers_count, _set_additional_layers_count)
    """count of additional layers next to the plot's default one"""

    def _get_layer_ids(self) -> "QStringList":  # type: ignore # noqa
        """
        QtDesigner getter function for the PlotItems time span

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        return self._layer_ids_from_property

    def _set_layer_ids(self, new_val: "QStringList") -> None:  # type: ignore # noqa
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
        for reserved in ExPlotWidgetProperties._reserved_axis_labels_identifiers:
            if reserved in new_val:
                print(f"Identifier entry '{reserved}' will be ignored since it is reserved.")
                new_val.remove(reserved)
        self._update_axis_labels_and_ranges_dict(new_identifiers=new_val)
        self._layer_ids_from_property = new_val
        self._layers_number = len(new_val)
        self._update_layer_from_designer_properties()
        self._update_axis_labels_from_designer_properties()
        self._update_view_ranges_from_designer_properties()

    layerIDs: List[str] = Property("QStringList", _get_layer_ids, _set_layer_ids)
    """List of strings with the additional layer's identifiers"""

    def _get_axis_labels(self) -> str:
        """QtDesigner getter function for the PlotItems axis labels"""
        return json.dumps(self._axis_labels())

    def _set_axis_labels(self, new_val: str) -> None:
        """QtDesigner setter function for the PlotItems axis labels"""
        try:
            axis_labels = json.loads(new_val)
            self._layer_axis_labels: Dict = {}
            self._standard_axis_labels: Dict = {}
            for entry in axis_labels:
                if entry in ExPlotWidgetProperties._reserved_axis_labels_identifiers:
                    self._standard_axis_labels[entry] = axis_labels[entry]
                else:
                    self._layer_axis_labels[entry] = axis_labels[entry]
            self._update_layer_from_designer_properties()
            self._update_axis_labels_from_designer_properties()
        except (json.decoder.JSONDecodeError, AttributeError):
            pass

    axisLabels: str = Property(str, _get_axis_labels, _set_axis_labels)
    """JSON string with mappings of axis positions and layers to a label text"""

    def _get_axis_ranges(self) -> str:
        """QtDesigner getter function for the PlotItems axis ranges"""
        return json.dumps(self._axis_ranges())

    def _set_axis_ranges(self, new_val: str) -> None:
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
                    if entry in ExPlotWidgetProperties._reserved_axis_ranges_identifiers:
                        self._standard_axis_ranges[entry] = tuple(axis_range)  # type: ignore[assignment]
                    else:
                        self._layer_axis_ranges[entry] = tuple(axis_range)  # type: ignore[assignment]
            self._update_view_ranges_from_designer_properties()
        except (json.decoder.JSONDecodeError, AttributeError, TypeError):
            # JSONDecodeError and Attribute Errors for JSON decoding
            # TypeError for len() operation on entries that do not support it
            pass

    axisRanges: str = Property(str, _get_axis_ranges, _set_axis_ranges)
    """JSON string with mappings of x, y and layers to a view range"""

    # ~~~~~~~~~ Private ~~~~~~~~~

    def _update_axis_labels_and_ranges_dict(self, new_identifiers: List[str]) -> None:
        """
        Update the identifiers in the axis label JSON string based on the list of
        identifiers.
        """
        labels_old = deepcopy(self._layer_axis_labels)
        ranges_old = deepcopy(self._layer_axis_ranges)
        # New and old identifier lists have the same length -> assume identifiers were renamed
        if len(self._layer_ids_from_property) == len(new_identifiers):
            for entry in zip(self._layer_ids_from_property, new_identifiers):
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
        for layer in self.plotItem.non_default_layers:  # type: ignore[attr-defined]
            self.plotItem.remove_layer(layer)  # type: ignore[attr-defined]
        for layer_id in self._layer_ids_from_property:
            self.plotItem.add_layer(layer_id=layer_id)  # type: ignore[attr-defined]

    def _update_axis_labels_from_designer_properties(self) -> None:
        """
        Update the axis labels according to the map set in the designer property.
        "left", "top", "right" and "bottom" refer to the standard PlotItem axis.
        For the axis of the layer use the layer's identifier as a key.
        """
        for entry in self._axis_labels():
            if entry in ExPlotWidgetProperties._reserved_axis_labels_identifiers:
                if (entry != PlotItemLayer.default_layer_id
                        and self.plotItem.getAxis(entry).isVisible()):  # type: ignore[attr-defined]
                    self.plotItem.setLabel(axis=entry, text=f"{self._standard_axis_labels[entry]}")  # type: ignore[attr-defined]
            else:
                try:
                    layer = self.plotItem.layer(layer_id=entry)  # type: ignore[attr-defined]
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
                    layer = self.plotItem.layer(layer_id=entry)  # type: ignore[attr-defined]
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

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            time_span: float = 60.0,
            time_progress_line: bool = False,
            is_xrange_fixed: bool = False,
            fixed_xrange_offset: float = np.nan,
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
            time_span: data from which time span should be displayed in the plot
            time_progress_line: If true, the current timestamp will represented as a
                                vertical line in the plot
            is_xrange_fixed: If true, the x-range will always be the time span. If less
                             data is available, the x range won't be zoom in to it automatically.
            fixed_xrange_offset: If the fixed x range is activated, this options allows to
                                 add or subtract an offset to the time span.
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
            is_xrange_fixed=is_xrange_fixed,
            fixed_xrange_offset=fixed_xrange_offset,
        )
        config.plotting_style = PlotWidgetStyle.SCROLLING_PLOT
        super().__init__(
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            timing_source=timing_source,
            **plotitem_kwargs
        )

    showTimeProgressLine: bool = Property(bool, ExPlotWidget._get_show_time_line, ExPlotWidget._set_show_time_line)
    """Vertical Line displaying the current time stamp"""

    timeSpan: float = Property(float, ExPlotWidget._get_time_span, ExPlotWidget._set_time_span)
    """Range from which the plot displays data"""

    def _get_is_xrange_fixed(self) -> bool:
        """QtDesigner getter function for the PlotItems flag for a fixed scrolling x range"""
        return self.plotItem.plot_config.is_xrange_fixed

    def _set_is_xrange_fixed(self, new_val: bool) -> None:
        """QtDesigner setter function for the PlotItems flag for a fixed scrolling x range"""
        if new_val != self.plotItem.plot_config.is_xrange_fixed:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.is_xrange_fixed = new_val
            self.plotItem.update_config(config=new_config)

    fixedXRange: bool = Property(bool, _get_is_xrange_fixed, _set_is_xrange_fixed)
    """The x axis shows always the same range and does not zoom in if less data is available"""

    def _get_fixed_xrange_offset(self) -> float:
        """QtDesigner getter function for the PlotItems fixed scrolling x range offset"""
        if np.isnan(self.plotItem.plot_config.fixed_xrange_offset):
            return 0.0
        return self.plotItem.plot_config.fixed_xrange_offset

    def _set_fixed_xrange_offset(self, new_val: float) -> None:
        """QtDesigner setter function for the PlotItems fixed scrolling x range offset"""
        if new_val != self.plotItem.plot_config.fixed_xrange_offset:
            new_config = deepcopy(self.plotItem.plot_config)
            new_config.fixed_xrange_offset = new_val
            self.plotItem.update_config(config=new_config)

    fixedXRangeOffset: float = Property(float, _get_fixed_xrange_offset, _set_fixed_xrange_offset)
    """Offset for the Fixed x range"""


class SlidingPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            background: str = "default",
            time_span: float = 60.0,
            time_progress_line: bool = False,
            axis_items: Optional[Dict[str, pg.AxisItem]] = None,
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs,
    ):
        """
        The ScrollingPlotWidget is equivalent to an ExPlotWidget which's
        configuration contains the sliding pointer style. Additionally some
        properties are offered that are specific to this plotting style.
        When switching the ExPlotWidget, passing a fitting configuration
        can achieve the same results as using these properties.

        Args:
            parent: parent item for this widget, will only be passed to base class
            background: background for the widget, will only be passed to base class
            time_span: data from which time span should be displayed in the plot
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
            plotting_style=PlotWidgetStyle.SLIDING_POINTER,
            time_span=time_span,
            time_progress_line=time_progress_line,
        )
        super().__init__(
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            timing_source=timing_source,
            **plotitem_kwargs
        )

    showTimeProgressLine: bool = Property(bool, ExPlotWidget._get_show_time_line, ExPlotWidget._set_show_time_line)
    """Vertical Line displaying the current time stamp"""

    timeSpan: float = Property(float, ExPlotWidget._get_time_span, ExPlotWidget._set_time_span)
    """Range from which the plot displays data"""


class StaticPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

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
        super().__init__(
            parent=parent,
            background=background,
            config=config,
            axis_items=axis_items,
            **plotitem_kwargs
        )

    def _get_show_time_line(self) -> bool:
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'setShowTimeLine' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")
        return False

    def _set_show_time_line(self, new_val: bool) -> None:
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'setShowTimeLine' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")

    showTimeProgressLine: bool = Property(bool, _get_show_time_line, _set_show_time_line, designable=False)
    """Vertical Line displaying the current time stamp, not supported by the static plotting style"""

    def _get_time_span(self) -> float:
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'timeSpan' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")
        return 0.0

    def _set_time_span(self, new_val: float) -> None:
        if not designer_check.is_designer():
            _LOGGER.warning(msg="Property 'timeSpan' is not supposed to be used with at static plot. "
                                "Use only with ScrollingPlotWidget and SlidingPlotWidget.")

    timeSpan: float = Property(float, _get_time_span, _set_time_span, designable=False)
    """Range from which the plot displays data, not supported by the static plotting style"""
