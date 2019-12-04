"""
Module containing QtDesigner plugin for different type of graphs.
"""

from accwidgets.graph import ScrollingPlotWidget, SlidingPlotWidget, StaticPlotWidget
import designer_base


ScrollingExPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(widget_class=ScrollingPlotWidget)


SlidingExPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(widget_class=SlidingPlotWidget)


StaticExPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(widget_class=StaticPlotWidget)
