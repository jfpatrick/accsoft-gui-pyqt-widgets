"""
Extended Widget for custom plotting with simple configuration wrappers
"""

import itertools
from typing import Dict, Optional, Type

import pyqtgraph as pg

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QGraphicsItem

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.widgets.axisitems import (
    RelativeTimeAxisItem,
    TimeAxisItem,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotitem import ExPlotItem
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.bargraphitem import LiveBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.injectionbaritem import LiveInjectionBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.timestampmarker import LiveTimestampMarker

# Mapping of plotting styles to a fitting axis style
_STYLE_TO_AXIS_MAPPING: Dict[PlotWidgetStyle, Type[pg.AxisItem]] = {
    PlotWidgetStyle.STATIC_PLOT: pg.AxisItem,
    PlotWidgetStyle.SLIDING_POINTER: RelativeTimeAxisItem,
    PlotWidgetStyle.SCROLLING_PLOT: TimeAxisItem,
}


class ExPlotWidget(pg.PlotWidget):
    """Extended PlotWidget

    Extended version of PyQtGraphs PlotWidget with additional functionality
    providing special functionality for live data plotting.
    """

    def __init__(
        self,
        parent: Optional[QGraphicsItem] = None,
        background: str = "default",
        config: ExPlotWidgetConfig = ExPlotWidgetConfig(),
        axis_items: Dict[str, pg.AxisItem] = {},
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
        self.timing_source = timing_source
        self._config = config
        self.plotItem: ExPlotItem
        axis_items = axis_items or {}
        axis_items["bottom"] = axis_items.get("bottom", self._create_fitting_axis_item())
        self.plotItem = ExPlotItem(
            axis_items=axis_items,
            config=config,
            timing_source=timing_source,
            **plotitem_kwargs,
        )
        self.setCentralItem(self.plotItem)
        self._wrap_plotitem_functions()

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
        params: Optional = None,
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

    @Slot(float)
    @Slot(int)
    def singleCurveValueSlot(self, data):
        """Slot that allows to draw data """
        self.plotItem.handle_single_curve_value_slot(data)

    def _create_fitting_axis_item(self) -> pg.AxisItem:
        """Create an axis that fits the given plotting style

        Create instance of the axis associated to the given plotting style in
        STYLE_TO_AXIS_MAPPING. This axis-item can then be passed to the PlotItems
        constructor.

        Returns:
            Instance of the fitting axis item
        """
        for style, axis in _STYLE_TO_AXIS_MAPPING.items():
            if self._config.plotting_style == style:
                return axis(orientation="bottom")
        return pg.AxisItem(orientation="bottom")
