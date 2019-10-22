from accsoft_gui_pyqt_widgets.graph import ScrollingPlotWidget, SlidingPlotWidget, StaticPlotWidget
import designer_base


ScrollingExPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(widget_class=ScrollingPlotWidget)


SlidingExPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(widget_class=SlidingPlotWidget)


StaticExPlotWidgetPlugin = designer_base.ex_plot_widget_plugin_factory(widget_class=StaticPlotWidget)
