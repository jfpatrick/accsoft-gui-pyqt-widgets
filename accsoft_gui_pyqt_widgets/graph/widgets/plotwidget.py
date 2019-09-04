"""
Extended Widget for custom plotting with simple configuration wrappers
"""

import itertools
from typing import Dict, Optional, Any
import copy

import pyqtgraph as pg
import numpy as np

from qtpy.QtCore import Slot, Property, Q_ENUM
from qtpy.QtWidgets import QWidget

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotitem import ExPlotItem
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.bargraphitem import LiveBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.injectionbaritem import LiveInjectionBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.timestampmarker import LiveTimestampMarker


class ExPlotWidget(pg.PlotWidget, PlotWidgetStyle):
    """Extended PlotWidget

    Extended version of PyQtGraphs PlotWidget with additional functionality
    providing special functionality for live data plotting.

    ExPlotWidget subclasses PlotWidgetStyle to have access to its class
    attributes, which are needed for using the ExPlotWidget in QtDesigner
    """

    Q_ENUM(PlotWidgetStyle)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        background: str = "default",
        config: ExPlotWidgetConfig = None,
        axis_items: Optional[Dict[str, pg.AxisItem]] = None,
        timing_source: Optional[UpdateSource] = None,
        **plotitem_kwargs,
    ):
        """Create a new plot widget.

        Args:
            parent: parent item for this widget, will only be passed to baseclass
            background: background for the widget, will only be passed to baseclass
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
        # From baseclass
        self.plotItem: ExPlotItem
        self._init_ex_plot_item(
            axis_items=axis_items,
            config=config,
            timing_source=timing_source,
            **plotitem_kwargs
        )
        self._wrap_plotitem_functions()

    def _init_ex_plot_item(
            self,
            config: ExPlotWidgetConfig = None,
            axis_items: Dict[str, pg.AxisItem] = {},
            timing_source: Optional[UpdateSource] = None,
            **plotitem_kwargs
    ):
        """
        Replace the plot item created by the baseclass with an instance
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
        del old_plot_item

    def update_configuration(self, config: ExPlotWidgetConfig) -> None:
        """
        Replace the PlotWidgets configuration and adapt all added items
        to fit the new configuration (f.e. a changed plotting style, cycle
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
        equivalent in the baseclass constructor.

        Returns:
            None
        """
        wrap_from_baseclass = [
            "addItem", "removeItem", "autoRange", "clear", "setXRange",
            "setYRange", "setRange", "setAspectLocked", "setMouseEnabled",
            "setXLink", "setYLink", "enableAutoRange", "disableAutoRange",
            "setLimits", "register", "unregister", "viewRect"
       ]
        wrap_additionally = [
            "add_layer"
        ]
        for m in itertools.chain(wrap_from_baseclass, wrap_additionally):
            setattr(self, m, getattr(self.plotItem, m))
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)

    def addCurve(
        self,
        c: Optional[pg.PlotDataItem] = None,
        params: Optional[Any] = None,
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
        return self.plotItem.addCurve(
            c=c,
            params=params,
            data_source=data_source,
            layer_identifier=layer_identifier,
            buffer_size=buffer_size,
            **plotdataitem_kwargs,
        )

    def addBarGraph(
        self,
        data_source: Optional[UpdateSource] = None,
        layer_identifier: Optional[str] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **bargraph_kwargs
    ) -> LiveBarGraphItem:
        """Add a new bargraph attached to a live data source

        Args:
            data_source (UpdateSource): Source emitting new data the graph should show
            layer_identifier (Optional[str]): Layer Identifier the curve should be added to
            buffer_size: maximum count of values the datamodel buffer should hold
            **bargraph_kwargs: keyword arguments for the BarGraphItem base class

        Returns:
            LiveBarGraphItem that was added to the plot
        """
        return self.plotItem.addBarGraph(
            data_source=data_source,
            layer_identifier=layer_identifier,
            buffer_size=buffer_size,
            **bargraph_kwargs
        )

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
        return self.plotItem.addInjectionBar(
            data_source=data_source,
            layer_identifier=layer_identifier,
            buffer_size=buffer_size,
            **errorbaritem_kwargs
        )

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
        return self.plotItem.addTimestampMarker(
            *graphicsobjectargs,
            data_source=data_source,
            buffer_size=buffer_size
        )

    # ====================================================================================
    #                Properties for Designer integration
    # ====================================================================================

    def _get_plotting_style(self) -> int:
        """QtDesigner getter function for the PlotItems Plotting style"""
        return self.plotItem.plot_config.plotting_style

    def _set_plotting_style(self, new_val: int):
        """QtDesigner setter function for the PlotItems Plotting Style"""
        if new_val != self.plotItem.plot_config.plotting_style:
            new_config = copy.deepcopy(self.plotItem.plot_config)
            new_config.plotting_style = new_val
            self.plotItem.update_configuration(config=new_config)

    plottingStyle = Property(PlotWidgetStyle, _get_plotting_style, _set_plotting_style)

    def _get_show_time_line(self) -> bool:
        """QtDesigner getter function for the PlotItems flag for showing the current timestamp with a line"""
        return self.plotItem.plot_config.time_progress_line

    def _set_show_time_line(self, new_val: bool):
        """QtDesigner setter function for the PlotItems flag for showing the current timestamp with a line"""
        if new_val != self.plotItem.plot_config.time_progress_line:
            new_config = copy.deepcopy(self.plotItem.plot_config)
            new_config.time_progress_line = new_val
            self.plotItem.update_configuration(config=new_config)

    showTimeProgressLine = Property(bool, _get_show_time_line, _set_show_time_line)

    def _get_cycle_size(self) -> float:
        """QtDesigner getter function for the PlotItems cycle size"""
        return self.plotItem.plot_config.cycle_size

    def _set_cycle_size(self, new_val: float):
        """QtDesigner setter function for the PlotItems cycle size"""
        if new_val != self.plotItem.plot_config.cycle_size:
            new_config = copy.deepcopy(self.plotItem.plot_config)
            new_config.cycle_size = new_val
            self.plotItem.update_configuration(config=new_config)

    xRangeCycleSize = Property(float, _get_cycle_size, _set_cycle_size)

    def _get_fixed_x_range(self) -> bool:
        """QtDesigner getter function for the PlotItems flag for a fixed scrolling x range"""
        return self.plotItem.plot_config.scrolling_plot_fixed_x_range

    def _set_fixed_x_range(self, new_val: bool):
        """QtDesigner setter function for the PlotItems flag for a fixed scrolling x range"""
        if new_val != self.plotItem.plot_config.scrolling_plot_fixed_x_range:
            new_config = copy.deepcopy(self.plotItem.plot_config)
            new_config.scrolling_plot_fixed_x_range = new_val
            self.plotItem.update_configuration(config=new_config)

    scrollingPlotFixedXRange = Property(bool, _get_fixed_x_range, _set_fixed_x_range)

    def _get_x_range_offset(self) -> float:
        """QtDesigner getter function for the PlotItems fixed scrolling x range offset"""
        if np.isnan(self.plotItem.plot_config.scrolling_plot_fixed_x_range_offset):
            return 0.0
        return self.plotItem.plot_config.scrolling_plot_fixed_x_range_offset

    def _set_x_range_offset(self, new_val: float):
        """QtDesigner setter function for the PlotItems fixed scrolling x range offset"""
        if new_val != self.plotItem.plot_config.scrolling_plot_fixed_x_range_offset:
            new_config = copy.deepcopy(self.plotItem.plot_config)
            new_config.scrolling_plot_fixed_x_range_offset = new_val
            self.plotItem.update_configuration(config=new_config)

    scrollingPlotFixedXRangeOffset = Property(float, fget=_get_x_range_offset, fset=_set_x_range_offset, doc="blah blah")

    # ====================================================================================
    #                Slot for simple one curve in Designer
    # ====================================================================================

    @Slot(float)
    @Slot(int)
    def singleCurveValueSlot(self, data):
        """Slot that allows to draw data """
        self.plotItem.handle_single_curve_value_slot(data)
