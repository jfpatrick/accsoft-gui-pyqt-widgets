import warnings
from abc import ABCMeta, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Type, Optional, List, TypeVar, Union
from qtpy.QtWidgets import QWidget, QAction
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtDesigner import (
    QDesignerFormEditorInterface,
    QPyDesignerCustomWidgetPlugin,
    QExtensionFactory,
    QPyDesignerTaskMenuExtension,
    QExtensionManager,
    QDesignerFormWindowCursorInterface,
    QDesignerFormWindowInterface,
)
from accwidgets.designer_check import set_designer


class WidgetBoxGroup(Enum):

    LAYOUTS = "Layouts"
    SPACERS = "Spacers"
    BUTTONS = "Buttons"
    ITEM_VIEWS = "Item Views (Model-Based)"
    ITEM_WIDGETS = "Item Widgets (Item-Based)"
    CONTAINERS = "Containers"
    INPUTS = "Input Widgets"
    CHARTS = "Charts"
    INDICATORS = "Display Widgets"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# |                              Extensions                                   |
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class WidgetsExtension(metaclass=ABCMeta):

    def __init__(self, widget: QWidget):
        """
        Base Wrapper Class for Widgets Extension.

        Note: The extension classes are not derived from PyDM classes but compatible
        with them, which makes it much easier to register WidgetsExtensions in
        ComRAD, since both offer the same functions.
        """
        self.widget = widget

    @abstractmethod
    def actions(self) -> List[QAction]:
        """
        Actions which are added to the task menu by the extension. Providing this function
        will make the Extension compatible to PyDM Task Menu extensions.
        """
        pass


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
        self.__actions: Optional[List[QAction]] = None
        self.__extensions: List[WidgetsExtension] = []
        extensions = getattr(widget, "extensions", None)
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

    def __init__(self, parent: QWidget = None):
        """Factory of instantiating Task Menu extensions. """
        super().__init__(parent)

    def createExtension(
            self,
            obj: QWidget,
            iid: str,
            parent: QWidget,
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


def _icon(name: str, base_path: Optional[Path] = None) -> QIcon:
    """ Load icons by their file name from folder 'icons' """
    if base_path is None:
        base_path = Path(__file__).absolute().parent
    icon_path = base_path / "icons" / f"{name}.ico"
    if not icon_path.is_file():
        warnings.warn(f"Icon '{name}' cannot be found at {str(icon_path)}")
    pixmap = QPixmap(str(icon_path))
    return QIcon(pixmap)


_E = TypeVar("_E", bound=WidgetsExtension)


class WidgetDesignerPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self,
                 widget_class: Type[QWidget],
                 group_name: str,
                 extensions: Optional[List[Type[_E]]] = None,
                 is_container: bool = False,
                 tooltip: Optional[str] = None,
                 whats_this: Optional[str] = None,
                 icon_base_path: Optional[Path] = None):
        """
        Base for accwidgets plugins for QtDesigner.
        Use the factory method for creating plugin classes from this.
        Make sure this class is not included in your modules namespace
        that is imported from QtDesigner. QtDesigner will try to initialize
        this plugin which will result in an error message.

        Args:
            widget_class: widget class this plugin is based on
            extensions: list of extensions applied to the widget in Designer
            is_container: whether the widget can accommodate other widgets inside
            group_name: name of the group to put the widget to
            tootip: contents of the tooltip for the widget
            whats_this: contents of the whatsThis for the widget
            icon_base_path: path to the basedir of "icons" folder
        """
        set_designer()
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        self._widget_class: Type = widget_class
        self._group_name = group_name
        self._whats_this = whats_this
        self._icon_base_path = icon_base_path
        self._tooltip = tooltip
        self._is_container = is_container
        self.extensions: List[Type] = extensions or []
        # Will be set in initialize
        self.manager: Optional[QExtensionManager] = None

    def initialize(self, core: QDesignerFormEditorInterface):
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
                    "org.qt-project.Qt.Designer.TaskMenu",
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
            instance.extensions = self.extensions
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
        Name of the section where the widget will be placed to.
        """
        return self._group_name

    def toolTip(self) -> str:
        """Tooltip for the widget provided by this plugin"""
        return self._tooltip or ""

    def whatsThis(self) -> str:
        """
        A longer description of the widget for Qt Designer. By default, this
        is the entire class docstring.
        """
        return self._whats_this or ""

    def isContainer(self) -> bool:
        """
        Return True if this widget can contain other widgets.
        """
        return self._is_container

    def icon(self) -> QIcon:
        """
        Return a QIcon to represent this widget in Qt Designer.
        """
        return _icon(self._widget_class.__name__, base_path=self._icon_base_path)

    def domXml(self) -> str:
        """
        XML Description of the widget's properties.
        """
        return (
            '<widget class="{0}" name="{0}">\n'
            ' <property name="toolTip" >\n'
            "  <string>{1}</string>\n"
            " </property>\n"
            "</widget>\n"
        ).format(self.name(), self.toolTip())

    def includeFile(self) -> str:
        """
        Include the class module for the generated qt code
        """
        return self._widget_class.__module__


_T = TypeVar("_T", bound=WidgetDesignerPlugin)


def create_plugin(widget_class: Type[QWidget],
                  group: Union[str, WidgetBoxGroup],
                  cls: Type[_T] = WidgetDesignerPlugin,
                  extensions: Optional[List[Type[_E]]] = None,
                  is_container: bool = False,
                  tooltip: Optional[str] = None,
                  whats_this: Optional[str] = None,
                  icon_base_path: Optional[Path] = None) -> Type:
    """
    Create a qt designer plugin based on the passed widget class.

    Args:
        widget_class: Widget class that the plugin should be constructed from
        extensions: List of Extensions that the widget should have
        is_container: whether the widget can accommodate other widgets inside
        group: Name of the group to put widget to
        cls: Subclass of :class:`WidgetDesignerPlugin` if you want to customize the behavior of the plugin
        tootip: contents of the tooltip for the widget
        whats_this: contents of the whatsThis for the widget
        icon_base_path: path to the basedir of "icons" folder

    Returns:
        Plugin class based on :class:`WidgetDesignerPlugin`
    """

    class Plugin(cls):  # type: ignore

        """Plugin Template for creating plugin classes for different widgets"""

        __doc__ = "Qt Designer plugin for {}".format(widget_class.__name__)

        def __init__(self):
            super().__init__(widget_class=widget_class,
                             extensions=extensions,
                             group_name=group.value if isinstance(group, WidgetBoxGroup) else group,
                             is_container=is_container,
                             icon_base_path=icon_base_path,
                             tooltip=tooltip,
                             whats_this=whats_this)

    return Plugin


def get_designer_cursor(widget: QWidget) -> Optional[QDesignerFormWindowCursorInterface]:
    form = QDesignerFormWindowInterface.findFormWindow(widget)
    return form.cursor() if form else None
