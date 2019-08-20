"""
Extended Widget for custom plotting with simple configuration wrappers
"""

from typing import Dict, Optional, Type

import pyqtgraph as pg

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.widgets.axisitems import (
    RelativeTimeAxisItem,
    TimeAxisItem,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    LivePlotCurveConfig,
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotitem import ExPlotItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.bargraphitem import LiveBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.injectionbaritem import LiveInjectionBarGraphItem
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.infiniteline import LiveTimestampMarker

# Mapping of plotting styles to a fitting axis style
_STYLE_TO_AXIS_MAPPING: Dict[PlotWidgetStyle, Type[pg.AxisItem]] = {
    PlotWidgetStyle.DEFAULT: pg.AxisItem,
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
        config: ExPlotWidgetConfig = ExPlotWidgetConfig(),
        axis_items: Optional[Dict[str, pg.AxisItem]] = {},
        timing_source: Optional[UpdateSource] = None,
        **plotwidget_kwargs,
    ):
        """Create a new plot widget.

        Args:
            timing_source (Optional[UpdateSource]): Optional source for timing
                updates
            config (ExPlotWidgetConfig): Configuration for the plot widget
            **plotwidget_kwargs: Params passed to superclass
        """
        super().__init__(**plotwidget_kwargs)
        self.timing_source = timing_source
        self._config = config
        self.plotItem: ExPlotItem
        axis_items = axis_items or {}
        axis_items["bottom"] = axis_items.get("bottom", self._create_fitting_axis_item())
        self.plotItem = ExPlotItem(
            axis_items=axis_items,
            config=config,
            timing_source=timing_source,
            **plotwidget_kwargs,
        )
        self.setCentralItem(self.plotItem)

    def addCurve(
        self,
        c: Optional[pg.PlotDataItem] = None,
        params: Optional = None,
        data_source: Optional[UpdateSource] = None,
        curve_config: LivePlotCurveConfig = LivePlotCurveConfig(),
        layer_identifier: Optional[str] = None,
        **plotdataitem_kwargs,
    ) -> pg.PlotDataItem:
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
        return self.plotItem.addCurve(
            c=c,
            params=params,
            data_source=data_source,
            curve_config=curve_config,
            layer_identifier=layer_identifier,
            **plotdataitem_kwargs,
        )

    def addBarGraph(
        self,
        data_source: UpdateSource,
        layer_identifier: Optional[str] = None,
        **bargraph_kwargs
    ) -> LiveBarGraphItem:
        """Add a new bargraph attached to a live data source

        Args:
            data_source (UpdateSource): Source emmiting new data the graph should show
            layer_identifier (Optional[str]): Layer Identifier the curve should be added to
            **bargraph_kwargs: keyword arguments for the BarGraphItem base class

        Returns:
            LiveBarGraphItem that was added to the plot
        """
        return self.plotItem.addBarGraph(
            data_source=data_source, layer_identifier=layer_identifier, **bargraph_kwargs
        )

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
        return self.plotItem.addInjectionBar(
            data_source=data_source, layer_identifier=layer_identifier, **errorbaritem_kwargs
        )

    def addTimestampMarker(
        self, *graphicsobjectargs, data_source: UpdateSource
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
        return self.plotItem.addTimestampMarker(*graphicsobjectargs, data_source=data_source)

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
