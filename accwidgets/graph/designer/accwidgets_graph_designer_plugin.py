"""
Module containing QtDesigner plugin for different type of graphs.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


skip_plugin = False
try:
    with disable_assert_cache():
        from accwidgets.graph import ScrollingPlotWidget, CyclicPlotWidget, StaticPlotWidget
except ImportError:
    skip_plugin = True


if not skip_plugin:
    from accwidgets.graph.designer import PlotLayerExtension
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _TOOLTIP = "Extended Plot Widget with live data plotting capabilities."
    _WHATS_THIS = "The Extended Plot Widget is a plotting widget based on PyQtGraph's " \
                  "PlotWidget that provides additional functionality like live data " \
                  "plotting capabilities, proper multi y axis plotting and more."
    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    ScrollingPlotWidgetPlugin = create_plugin(widget_class=ScrollingPlotWidget,
                                              extensions=[PlotLayerExtension],
                                              group=WidgetBoxGroup.CHARTS,
                                              tooltip=_TOOLTIP,
                                              whats_this=_WHATS_THIS,
                                              icon_base_path=_ICON_BASE_PATH)

    CyclicPlotWidgetPlugin = create_plugin(widget_class=CyclicPlotWidget,
                                           extensions=[PlotLayerExtension],
                                           group=WidgetBoxGroup.CHARTS,
                                           tooltip=_TOOLTIP,
                                           whats_this=_WHATS_THIS,
                                           icon_base_path=_ICON_BASE_PATH)

    StaticPlotWidgetPlugin = create_plugin(widget_class=StaticPlotWidget,
                                           extensions=[PlotLayerExtension],
                                           group=WidgetBoxGroup.CHARTS,
                                           tooltip=_TOOLTIP,
                                           whats_this=_WHATS_THIS,
                                           icon_base_path=_ICON_BASE_PATH)
