"""
Module containing QtDesigner plugin for different type of graphs.
"""

from accwidgets.graph import ScrollingPlotWidget, CyclicPlotWidget, StaticPlotWidget
from accwidgets.graph.designer import designer_base, designer_extensions


ScrollingPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(
    widget_class=ScrollingPlotWidget,
    extensions=[
        designer_extensions.PlotLayerExtension
    ]
)


CyclicPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(
    widget_class=CyclicPlotWidget,
    extensions=[
        designer_extensions.PlotLayerExtension
    ]
)


StaticPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(
    widget_class=StaticPlotWidget,
    extensions=[
        designer_extensions.PlotLayerExtension
    ]
)
