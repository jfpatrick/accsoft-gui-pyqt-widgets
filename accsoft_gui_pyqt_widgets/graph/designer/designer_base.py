"""
Do not import this file as 'from designer_base import *' or similar in
your module that is imported into QtDesigner (See ExPlotWidgetPluginBase
for why). If you want to use something from this module, import it explicitly.
"""

import os
from typing import Type, Optional
from qtpy.QtWidgets import QWidget
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtDesigner import QDesignerFormEditorInterface, QPyDesignerCustomWidgetPlugin
from accsoft_gui_pyqt_widgets.graph.designer import designer_check


def _icon(name: str) -> QIcon:
    """ Load icons by their file name from folder 'icons' """
    curr_dir = os.path.abspath(os.path.dirname(__file__))
    icon_path = os.path.join(curr_dir, "icons", f"{name}.ico")
    if not os.path.isfile(icon_path):
        print(f"Warning: Icon '{name}' cannot be found at {str(icon_path)}")
    pixmap = QPixmap(icon_path)
    return QIcon(pixmap)


class ExPlotWidgetPluginBase(QPyDesignerCustomWidgetPlugin):
    """
    Base for ExPlotWidget based plugins for QtDesigner.
    Use the factory method for creating plugin classes from this.
    Make sure this class is not included in your modules namespace
    that is imported from QtDesigner. QtDesigner will try to initialize
    this plugin which will result in an error message.
    """

    def __init__(self, widget_class: Type):
        designer_check.set_designer()
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        self._widget_class: Type = widget_class

    def initialize(self, core: QDesignerFormEditorInterface) -> None:
        """
        Implemented from interface, for initializing the plugin exactly once.
        """
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self) -> bool:
        """
        Return True if initialize function has been called successfully.
        """
        return self.initialized

    def createWidget(self, parent: Optional[QWidget]) -> QWidget:
        """
        Instantiate the widget with the given parent.

        Args:
            parent: widget that should be used as parent

        Returns:
            New instance of the widget
        """
        instance = self._widget_class(parent=parent)
        return instance

    def name(self) -> str:
        """
        Return the class name of the widget.
        """
        return self._widget_class.__name__

    def group(self) -> str:
        """
        Return a common group name so all AccPyQtGraph Widgets are together in
        Qt Designer.
        """
        return "Graph"

    def toolTip(self) -> str:
        """Tooltip for the widget provided by this plugin"""
        return "Extended Plot Widget with live data plotting capabilities."

    def whatsThis(self) -> str:
        """
        A longer description of the widget for Qt Designer. By default, this
        is the entire class docstring.
        """
        return "The Extended Plot Widget is a plotting widget based on PyQtGraph's " \
               "PlotWidget that provides additional functionality like live data " \
               "plotting capabilities, proper multi y axis plotting and more."

    def isContainer(self) -> bool:
        """
        Return True if this widget can contain other widgets.
        """
        return False

    def icon(self) -> QIcon:
        """
        Return a QIcon to represent this widget in Qt Designer.
        """
        return _icon(self._widget_class.__name__)

    def domXml(self) -> str:
        """
        XML Description of the widget's properties.
        """
        return (
            "<widget class=\"{0}\" name=\"{0}\">\n"
            " <property name=\"toolTip\" >\n"
            "  <string>{1}</string>\n"
            " </property>\n"
            "</widget>\n"
        ).format(self.name(), self.toolTip())

    def includeFile(self) -> str:
        """
        Include the class module for the generated qt code
        """
        return self._widget_class.__module__


def ex_plot_widget_plugin_factory(widget_class: Type):
    """
    Create a qt designer plugin based on the passed widget class.

    Args:
        widget_class: Widget class that the plugin should be constructed from

    Returns:
        Plugin class based on ExPlotWidgetPlugin
    """

    class Plugin(ExPlotWidgetPluginBase):

        __doc__ = "QtDesigner Plugin for {}".format(widget_class.__name__)

        def __init__(self):
            super(Plugin, self).__init__(widget_class=widget_class)

    return Plugin
