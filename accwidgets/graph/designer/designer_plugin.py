"""
Module containing QtDesigner plugin for different type of graphs.
"""

from pathlib import Path
from accwidgets.graph import ScrollingPlotWidget, CyclicPlotWidget, StaticPlotWidget
from accwidgets.graph.designer import designer_extensions
from accwidgets.designer_base import create_plugin


_GROUP = "Graph"
_TOOLTIP = "Extended Plot Widget with live data plotting capabilities."
_WHATS_THIS = "The Extended Plot Widget is a plotting widget based on PyQtGraph's " \
              "PlotWidget that provides additional functionality like live data " \
              "plotting capabilities, proper multi y axis plotting and more."
_ICON_BASE_PATH = Path(__file__).parent.absolute()


ScrollingPlotWidgetPlugin = create_plugin(
    widget_class=ScrollingPlotWidget,
    extensions=[designer_extensions.PlotLayerExtension],
    group=_GROUP,
    tooltip=_TOOLTIP,
    whats_this=_WHATS_THIS,
    icon_base_path=_ICON_BASE_PATH,
)


CyclicPlotWidgetPlugin = create_plugin(
    widget_class=CyclicPlotWidget,
    extensions=[designer_extensions.PlotLayerExtension],
    group=_GROUP,
    tooltip=_TOOLTIP,
    whats_this=_WHATS_THIS,
    icon_base_path=_ICON_BASE_PATH,
)


StaticPlotWidgetPlugin = create_plugin(
    widget_class=StaticPlotWidget,
    extensions=[designer_extensions.PlotLayerExtension],
    group=_GROUP,
    tooltip=_TOOLTIP,
    whats_this=_WHATS_THIS,
    icon_base_path=_ICON_BASE_PATH,
)
