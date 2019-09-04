import os
from qtpy import QtGui, QtDesigner
import accsoft_gui_pyqt_widgets.graph as accgraph

print("Loading AccPyQtGraph widgets")


def _icon(name: str) -> QtGui.QIcon:
    """ Load icons by name from folder 'icons' """
    curr_dir = os.path.abspath(os.path.dirname(__file__))
    icon_path = os.path.join(curr_dir, 'icons', f'{name}.ico')

    if not os.path.isfile(icon_path):
        print(f'Warning: Icon "{name}" cannot be found at {str(icon_path)}')
    pixmap = QtGui.QPixmap(icon_path)
    return QtGui.QIcon(pixmap)


class ExPlotWidgetPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """
    Qt Designer Plugin for the ExPlotWidget.
    """

    def __init__(self):
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False

    def initialize(self, core):
        """
        Implemented from interface, for initializing the plugin exactly once.
        """
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        """
        Return True if initialize function has been called successfully.
        """
        return self.initialized

    def createWidget(self, parent) -> accgraph.ExPlotWidget:
        """
        Instantiate the plot widget with the given parent.

        Args:
            parent: Parent widget of instantiated widget

        Returns:
            new instance of the ExPlotWidget
        """
        instance = accgraph.ExPlotWidget(parent=parent)
        return instance

    def name(self):
        """
        Return the class name of the widget.
        """
        return accgraph.ExPlotWidget.__name__

    def group(self):
        """
        Return a common group name so all AccPyQtGraph Widgets are together in
        Qt Designer.
        """
        return 'Charts'

    def toolTip(self):
        """Tooltip for the widget provided by this plugin"""
        return "Extended Plot Widget with live data plotting capabilities."

    def whatsThis(self):
        """
        A longer description of the widget for Qt Designer. By default, this
        is the entire class docstring.
        """
        return "The Extended Plot Widget is a plotting widget based on PyQtGraph's " \
               "PlotWidget that provides additional functionality like live data " \
               "plotting capabilities as well as proper multi y axis plotting."

    def isContainer(self):
        """
        Return True if this widget can contain other widgets.
        """
        return False

    def icon(self):
        """
        Return a QIcon to represent this widget in Qt Designer.
        """
        return _icon("ExPlotWidget")

    def domXml(self):
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

    def includeFile(self):
        """
        Include the class module for the generated qt code
        """
        return accgraph.ExPlotWidget.__module__
