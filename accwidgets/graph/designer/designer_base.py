"""
Do not import this file as 'from designer_base import *' or similar in
your module that is imported into QtDesigner (See ExPlotWidgetPluginBase
for why). If you want to use something from this module, import it explicitly.
"""

import os
from typing import Type, Optional, List
from qtpy.QtWidgets import QWidget, QAction
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtDesigner import (
    QDesignerFormEditorInterface,
    QPyDesignerCustomWidgetPlugin,
    QExtensionFactory,
    QPyDesignerTaskMenuExtension,
    QExtensionManager
)
from accwidgets import graph as accgraph


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# |                              Extensions                                   |
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Note: The extension classes are not derived from PYDM classes but compatible
#       with them, which makes it much easier to register WidgetsExtensions in
#       Comrad, since both offer the same functions.

class WidgetsExtension:

    def __init__(self, widget: QWidget):
        """Base Wrapper Class for Widgets Extension."""
        self.widget = widget

    def actions(self) -> List[QAction]:
        """
        Actions which are added to the task menu by the extension. Providing this function
        will make the Extension compatible to PYDM Task Menu extensions.
        """
        raise NotImplementedError


class WidgetsTaskMenuExtension(QPyDesignerTaskMenuExtension):

    def __init__(self, widget: QWidget, parent: QWidget):
        """
        Task Menu Extension Base Class.

        Args:
            widget: widget the extension is added to
            parent: parent widget
        """
        super().__init__(parent)
        self.widget = widget
        self.__actions = None
        self.__extensions = []
        extensions = getattr(widget, 'extensions', None)
        if extensions is not None:
            for ex in extensions:
                extension = ex(self.widget)
                self.__extensions.append(extension)

    def taskActions(self) -> List[QAction]:
        """
        Task Actions which are added by an extension.

        Returns:
            List of actions for the widget
        """
        if self.__actions is None:
            self.__actions = []
            for ex in self.__extensions:
                self.__actions.extend(ex.actions())

        return self.__actions

    def preferredEditAction(self):
        if self.__actions is None:
            self.taskActions()
        if self.__actions:
            return self.__actions[0]


class WidgetsExtensionFactory(QExtensionFactory):

    def __init__(self, parent: QWidget=None):
        """Factory of instanciating Task Menu extensions. """
        super().__init__(parent)

    def createExtension(
            self,
            obj: QWidget,
            iid: str,
            parent: QWidget
    ) -> Optional[WidgetsTaskMenuExtension]:
        """
        Create Task Menu Extension instance.

        Args:
            obj: Widget which the extension is associated to.
            iid: What type of extension should be initialized
            parent: Parent Widget for the extension

        Returns:
            Extension instance or None depending of what object and iid are passed
        """
        if not isinstance(obj, accgraph.ExPlotWidget):
            return None

        # For now check the iid for TaskMenu...
        if iid == "org.qt-project.Qt.Designer.TaskMenu":
            return WidgetsTaskMenuExtension(obj, parent)
        # In the future we can expand to the others such as Property and etc
        # When the time comes...  we will need a new PyDMExtension and
        # the equivalent for PyDMTaskMenuExtension classes for the
        # property editor and an elif statement in here to instantiate it...

        return None


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# |                           Designer Plugin                                 |
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _icon(name: str) -> QIcon:
    """ Load icons by their file name from folder 'icons' """
    curr_dir = os.path.abspath(os.path.dirname(__file__))
    icon_path = os.path.join(curr_dir, "icons", f"{name}.ico")
    if not os.path.isfile(icon_path):
        print(f"Warning: Icon '{name}' cannot be found at {str(icon_path)}")
    pixmap = QPixmap(icon_path)
    return QIcon(pixmap)


class ExPlotWidgetPluginBase(QPyDesignerCustomWidgetPlugin):

    # pylint: disable=invalid-name, no-self-use

    def __init__(self, widget_class: Type, extensions: List[Type]):
        """
        Base for ExPlotWidget based plugins for QtDesigner.
        Use the factory method for creating plugin classes from this.
        Make sure this class is not included in your modules namespace
        that is imported from QtDesigner. QtDesigner will try to initialize
        this plugin which will result in an error message.

        Args:
            widget_class: widget class this plugin is based on
        """
        accgraph.designer_check.set_designer()
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        self._widget_class: Type = widget_class
        self.extensions: List[Type] = extensions
        # Will be set in initialize
        self.manager: Optional[QExtensionManager] = None

    def initialize(self, core: QDesignerFormEditorInterface) -> None:
        """
        Implemented from interface, for initializing the plugin exactly once.
        """
        if self.initialized:
            return
        if self.extensions is not None and len(self.extensions) > 0:
            self.manager = core.extensionManager()
            if self.manager:
                self.manager.registerExtensions(
                    WidgetsExtensionFactory(parent=self.manager),
                    'org.qt-project.Qt.Designer.TaskMenu'
                )
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
        try:
            setattr(instance, "extensions", self.extensions)
        except (AttributeError, NameError):
            pass
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


def ex_plot_widget_plugin_factory(widget_class: Type, extensions: List):
    """
    Create a qt designer plugin based on the passed widget class.

    Args:
        widget_class: Widget class that the plugin should be constructed from
        extensions: List of Extensions that the widget should have

    Returns:
        Plugin class based on ExPlotWidgetPlugin
    """

    class Plugin(ExPlotWidgetPluginBase):

        """Plugin Template for creating plugin classes for different widgets"""

        __doc__ = "QtDesigner Plugin for {}".format(widget_class.__name__)

        def __init__(self):
            super(Plugin, self).__init__(
                widget_class=widget_class,
                extensions=extensions
            )

    return Plugin
