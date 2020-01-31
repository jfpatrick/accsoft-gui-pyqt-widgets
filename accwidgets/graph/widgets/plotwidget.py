"""
Extended Widget for custom plotting with simple configuration wrappers
"""

from typing import Dict, Optional, Any, Set, List, Tuple, Union, cast
from copy import deepcopy
import json
import warnings

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Slot, Property, Q_ENUM
from qtpy.QtWidgets import QWidget
from qtpy.QtGui import QPen

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
    TimeSpan,
)
from accwidgets.graph.widgets.plotitem import ExPlotItem, PlotItemLayer, LayerIdentification
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.bargraphitem import LiveBarGraphItem
from accwidgets.graph.widgets.dataitems.injectionbaritem import LiveInjectionBarGraphItem
from accwidgets.graph.widgets.dataitems.timestampmarker import LiveTimestampMarker
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import DataModelBasedItem
from accwidgets.graph.widgets.axisitems import ExAxisItem
from accwidgets import designer_check


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
            **errorbaritem_kwargs,
        )

    def addTimestampMarker(  # pylint: disable=invalid-name
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
    showTimeProgressLine: bool = Property(bool, _get_show_time_line, _set_show_time_line)
    """Vertical Line displaying the current time stamp"""

    def _get_right_time_span_boundary(self) -> float:
        """QtDesigner getter function for the PlotItems time span size"""
        return self.plotItem.plot_config.time_span.right_boundary_offset

    def _set_right_time_span_boundary(self, new_val: float) -> None:
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
                print("No value cached")
                potential = 60.0
        return potential

    def _set_left_time_span_boundary(self, new_val: float) -> None:
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

    def _set_left_time_span_boundary_bool(self, new_val: bool) -> None:
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

    # ~~~~~~~~~~ Private ~~~~~~~~~

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
            "setLimits", "register", "unregister", "viewRect",
        ]
        for method in wrap_from_base_class:
            setattr(self, method, getattr(self.plotItem, method))
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)

# pylint: disable=no-member,access-member-before-definition,attribute-defined-outside-init


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

    def _set_show_x_axis(self, new_val: int) -> None:
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

    def _set_show_y_axis(self, new_val: int) -> None:
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

    def _set_show_grid(self, new_val: int) -> None:
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
        return cast(ExPlotWidget, self).plotItem.legend is not None

    def _set_show_legend(self, new_val: bool) -> None:
        """If true, the plot shows a legend."""
        if new_val != self._get_show_legend():  # type: ignore[has-type]
            if new_val:
                cast(ExPlotWidget, self).addLegend(size=None, offset=None)
                old_pos = self._get_legend_position()
                self._set_legend_position(
                    x_alignment=old_pos[0],
                    y_alignment=old_pos[1],
                )
            else:
                legend = cast(ExPlotWidget, self).plotItem.legend
                if legend is not None:
                    cast(ExPlotWidget, self).removeItem(legend)
                    legend.deleteLater()
                    cast(ExPlotWidget, self).plotItem.legend = None
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

    def _set_legend_position(self, x_alignment: int = -1, y_alignment: int = -1, offset: float = 10.0) -> None:
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

    def _set_legend_x_position(self, new_val: int) -> None:
        self._set_legend_position(x_alignment=new_val)

    legendXAlignment: int = Property(LegendXAlignmentOptions, _get_legend_x_position, _set_legend_x_position)
    """Which position has the top left corner in the x dimension. Is 0, if no legend is displayed."""

    def _get_legend_y_position(self) -> int:
        return self._get_legend_position()[1]

    def _set_legend_y_position(self, new_val: int) -> None:
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

    def _set_layer_ids(self, layers: "QStringList") -> None:  # type: ignore # noqa
        """
        QtDesigner setter function for the PlotItems time span

        This property is for usage in Qt Designer and its limitations in property
        data type. A better way of achieving this by usage directly from code is
        to use the function add_layer().
        """
        # Check for duplicated values
        if len(layers) != len(set(layers)):
            print("Layers can not be updated since you have provided duplicated identifiers for them.")
            return
        # Check for invalid layer identifiers
        for reserved in ExPlotWidgetProperties._reserved_axis_labels_identifiers:
            if reserved in layers:
                print(f"Identifier entry '{reserved}' will be ignored since it is reserved.")
                layers.remove(reserved)
        # Update changed identifiers
        self._update_layers(layers)

    layerIDs: List[str] = Property("QStringList", _get_layer_ids, _set_layer_ids, designable=False)
    """List of strings with the additional layer's identifiers"""

    def _get_axis_labels(self) -> str:
        """QtDesigner getter function for the PlotItems axis labels"""
        labels = {}
        for axis in self._reserved_axis_labels_identifiers:
            labels.update({axis: cast(ExPlotWidget, self).getAxis(axis).labelText})
        for layer in cast(ExPlotWidget, self).plotItem.non_default_layers:
            labels.update({layer.id: layer.axis_item.labelText})
        return json.dumps(labels)

    def _set_axis_labels(self, new_val: str) -> None:
        """QtDesigner setter function for the PlotItems axis labels"""
        try:
            axis_labels: Dict[str, str] = json.loads(new_val)
            for axis, label in axis_labels.items():
                label = axis_labels.get(axis, "").strip()
                if cast(ExPlotWidget, self).plotItem.getAxis(axis).isVisible():
                    if label:
                        cast(ExPlotWidget, self).plotItem.setLabel(axis=axis, text=label)
                    else:
                        cast(ExPlotWidget, self).plotItem.getAxis(axis).labelText = label
                        cast(ExPlotWidget, self).plotItem.getAxis(axis).showLabel(False)
                else:
                    cast(ExPlotWidget, self).plotItem.getAxis(axis).labelText = label
        except (json.decoder.JSONDecodeError, AttributeError, TypeError):
            # JSONDecodeError and Attribute Errors for JSON decoding
            # TypeError for len() operation on entries that do not support it
            pass

    axisLabels: str = Property(str, _get_axis_labels, _set_axis_labels, designable=False)
    """JSON string with mappings of axis positions and layers to a label text"""

    def _get_axis_ranges(self) -> str:
        """QtDesigner getter function for the PlotItems axis ranges"""
        auto_ranges_dict = {}
        auto_ranges_dict.update({"x": cast(ExPlotWidget, self).getViewBox().targetRange()[0]})
        auto_ranges_dict.update({"y": cast(ExPlotWidget, self).getViewBox().targetRange()[1]})
        for layer in cast(ExPlotWidget, self).plotItem.non_default_layers:
            auto_ranges_dict.update({layer.id: layer.view_box.targetRange()[1]})
        return json.dumps(auto_ranges_dict)

    def _set_axis_ranges(self, new_val: str) -> None:
        """QtDesigner setter function for the PlotItems axis ranges"""
        try:
            axis_ranges: Dict[str, Tuple[float, float]] = json.loads(new_val)
            disable_ar = cast(ExPlotWidget, self).plotItem.getViewBox().autoRangeEnabled()[1]
            cast(ExPlotWidget, self).setRange(
                xRange=axis_ranges.pop("x", None),
                yRange=axis_ranges.pop("y", None),
                padding=0.0,
                disableAutoRange=disable_ar,
            )
            for layer, range_tuple in axis_ranges.items():
                # Check if range was given in the right form
                if layer in self._get_layer_ids():
                    disable_ar = cast(ExPlotWidget, self).plotItem.getViewBox(
                        layer=layer).autoRangeEnabled()[1]
                    cast(ExPlotWidget, self).plotItem.getViewBox(layer=layer).setRange(
                        yRange=range_tuple,
                        padding=0.0,
                        disableAutoRange=disable_ar,
                    )
        except (json.decoder.JSONDecodeError, AttributeError, TypeError):
            # JSONDecodeError and Attribute Errors for JSON decoding
            # TypeError for len() operation on entries that do not support it
            pass

    axisRanges: str = Property(str, _get_axis_ranges, _set_axis_ranges, designable=False)
    """JSON string with mappings of x, y and layers to a view range"""

    def _get_axis_auto_range(self) -> str:
        """QtDesigner getter function for the PlotItems axis ranges"""
        ar_enabled = cast(ExPlotWidget, self).getViewBox().autoRangeEnabled()
        auto_ranges_dict = {
            "x": bool(ar_enabled[0]),
            "y": bool(ar_enabled[1]),
        }
        for layer in cast(ExPlotWidget, self).plotItem.non_default_layers:
            auto_ranges_dict[layer.id] = bool(layer.view_box.autoRangeEnabled()[1])
        return json.dumps(auto_ranges_dict)

    def _set_axis_auto_range(self, new_val: str) -> None:
        """QtDesigner setter function for the PlotItems axis ranges"""
        try:
            axis_auto_range: Dict[str, bool] = json.loads(new_val)
            cast(ExPlotWidget, self).plotItem.enableAutoRange(
                x=axis_auto_range.pop("x", None),
                y=axis_auto_range.pop("y", None),
            )
            for layer, auto_range in axis_auto_range.items():
                # Check if range was given in the right form
                cast(ExPlotWidget, self).plotItem.getViewBox(layer=layer).enableAutoRange(y=auto_range)
        except (json.decoder.JSONDecodeError, AttributeError, TypeError):
            # JSONDecodeError and Attribute Errors for JSON decoding
            # TypeError for len() operation on entries that do not support it
            pass

    axisAutoRange: str = Property(str, _get_axis_auto_range, _set_axis_auto_range, designable=False)
    """JSON string with mappings of x, y and layers to a view range"""

    def _update_layers(self, new: List[str]) -> None:
        """
        Attention: This function can only handle one operation at a time.
        Combinations of adding, removing and renaming layers can't be
        detected clearly.
        """
        old = self._get_layer_ids()
        axis_labels: Dict = json.loads(self.axisLabels)
        axis_auto_range: Dict = json.loads(self.axisAutoRange)
        axis_range: Dict = json.loads(self.axisRanges)
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
                        print(item.label)
        if removed_layer_ids and added_layer_ids:
            # Rename
            for old_name, new_name in zip(removed_layer_ids, added_layer_ids):
                # replace id in dicts
                axis_labels.update({new_name: axis_labels.pop(old_name)})
                axis_auto_range.update({new_name: axis_auto_range.pop(old_name)})
                axis_range.update({new_name: axis_range.pop(old_name)})
                # If layer was renamed -> move item to new layer
                item_from_this_layer = [item for item in items_to_move if item.layer_id == old_name]
                for item in item_from_this_layer:
                    cast(ExPlotWidget, self).addItem(item=item, layer=new_name)
                    items_to_move.remove(item)
        elif removed_layer_ids:
            # Layer(s) removed
            for name in removed_layer_ids:
                # remove old ids from dict
                axis_labels.pop(name)
                axis_auto_range.pop(name)
                axis_range.pop(name)
        self.axisLabels = json.dumps(axis_labels)
        self.axisAutoRange = json.dumps(axis_auto_range)
        self.axisRanges = json.dumps(axis_range)

    @staticmethod
    def diff(list1, list2):
        return list(set(list1).symmetric_difference(set(list2)))


# pylint: enable=no-member,access-member-before-definition,attribute-defined-outside-init


class ScrollingPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

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


class CyclicPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

    Q_ENUM(XAxisSideOptions)
    Q_ENUM(DefaultYAxisSideOptions)
    Q_ENUM(GridOrientationOptions)
    Q_ENUM(LegendXAlignmentOptions)
    Q_ENUM(LegendYAlignmentOptions)

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

    def _set_left_time_span_boundary_bool(self, new_val: bool) -> None:
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


class StaticPlotWidget(ExPlotWidgetProperties, ExPlotWidget):  # type: ignore[misc]

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

    def _set_show_time_line(self, new_val: bool) -> None:
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

    def _set_time_span(self, new_val: float) -> None:
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

    def _set_right_time_span_boundary(self, new_val: float) -> None:
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

    def _set_left_time_span_boundary(self, new_val: float) -> None:
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

    def _set_left_time_span_boundary_bool(self, new_val: bool) -> None:
        if not designer_check.is_designer():
            warnings.warn("Property 'leftBoundaryEnabled' is not supposed to be used with at static plot, "
                          "since it does not use any time span.")

    leftBoundaryEnabled: bool = Property(
        bool,
        _get_left_time_span_boundary_bool,
        _set_left_time_span_boundary_bool,
        designable=False,
    )
