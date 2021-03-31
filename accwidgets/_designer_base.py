from codecs import decode
from dataclasses import dataclass
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Type, Optional, List, TypeVar, Union, Dict, cast
from qtpy.QtWidgets import QWidget, QAction, QMessageBox, QApplication
from qtpy.QtGui import QIcon
from qtpy.QtCore import QObject, QMetaMethod, QByteArray
from qtpy.QtDesigner import (
    QDesignerFormEditorInterface,
    QPyDesignerCustomWidgetPlugin,
    QExtensionFactory,
    QPyDesignerTaskMenuExtension,
    QPyDesignerMemberSheetExtension,
    QExtensionManager,
    QDesignerFormWindowCursorInterface,
    QDesignerFormWindowInterface,
)
from accwidgets.designer_check import set_designer, is_designer
from accwidgets._api import disable_assert_cache
from accwidgets.qt import make_icon


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

    # This is a special category name hardcoded into Qt Designer. Category with this name will not appear
    # in the widget box. In Qt sources you can find it in
    # qttools/src/designer/src/components/widgetbox/widgetboxtreewidget.cpp, declared on line 70 and used
    # on lines 613, 630
    HIDDEN = "[invisible]"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# |                              Extensions                                   |
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class WidgetsTaskMenuExtension(ABC):

    def __init__(self, widget: QWidget):
        """
        Base Wrapper Class for Widgets Task menu Extension.

        Note: The extension classes are not derived from PyDM classes but compatible
        with them, which makes it much easier to register WidgetsExtensions in
        ComRAD, since both offer the same functions.

        Args:
            widget: Related widget.
        """
        self.widget = widget

    @abstractmethod
    def actions(self) -> List[QAction]:
        """
        Actions which are added to the task menu by the extension. Providing this function
        will make the Extension compatible to PyDM Task Menu extensions.
        """
        pass


class WidgetsMemberSheetExtension(QPyDesignerMemberSheetExtension):  # Cannot inherit multiple classes, because low-level PyQt breaks

    @dataclass
    class Info:
        """Auxiliary storage class for cached modifications."""

        group: str
        """Group name of the member."""

        visible: bool = True
        """Is member visible in the Qt Designer."""

    def __init__(self, widget: QWidget, parent: QWidget):
        """
        This is a re-implementation of Qt Designer's standard member sheet extension class,
        to allow minor modifications without rewriting everything (because all
        :class:`QPyDesignerMemberSheetExtension` methods are abstract).
        Reference implementation of C++ class from Qt Designer is in
        qt5/qttools/src/designer/src/lib/shared/qdesigner_membersheet_p.h,
        qt5/qttools/src/designer/src/lib/shared/qdesigner_membersheet.cpp,

        Args:
            widget: Widget the extension is added to.
            parent: Owning object.
        """
        super().__init__(parent)
        self.meta = widget.metaObject()
        self.info_hash: Dict[int, WidgetsMemberSheetExtension.Info] = {}

    def count(self) -> int:
        """
        Returns the extension's number of member functions.

        Returns:
            Number of member functions.
        """
        return self.meta.methodCount()

    def declaredInClass(self, index: int) -> str:
        """
        Returns the name of the class in which the member function with the given index is declared.

        Args:
            index: Index of the member function.

        Returns:
            Name of the declaring class.
        """
        member = self.meta.method(index).methodSignature()
        meta = self.meta

        while True:
            tmp = meta.superClass()
            if not tmp:
                break
            if tmp.indexOfMethod(member) == -1:
                break
            meta = tmp
        return meta.className()

    def indexOf(self, name: str) -> int:
        """
        Returns the index of the member function specified by the given name.

        Args:
            name: Name of the member function.

        Returns:
            Index of the member function.
        """
        return self.meta.indexOfMethod(name)

    def inheritedFromWidget(self, index: int) -> bool:
        """
        Returns :obj:`True` if the member function with the given index is inherited from :class:`QWidget`,
        otherwise :obj:`False`.

        Args:
            index: Index of the member function.

        Returns:
            Whether the function is inherited from :class:`QWidget`.
        """
        class_name = self.declaredInClass(index)
        return class_name == QWidget.__name__ or class_name == QObject.__name__

    def isSignal(self, index: int) -> bool:
        """
        Returns :obj:`True` if the member function with the given index is a signal, otherwise :obj:`False`.

        Args:
            index: Index of the member function.

        Returns:
            Whether the function is a signal.
        """
        return self.meta.method(index).methodType() == QMetaMethod.Signal

    def isSlot(self, index: int) -> bool:
        """
        Returns :obj:`True` if the member function with the given index is a slot, otherwise :obj:`False`.

        Args:
            index: Index of the member function.

        Returns:
            Whether the function is a slot.
        """
        return self.meta.method(index).methodType() == QMetaMethod.Slot

    def isVisible(self, index: int) -> bool:
        """
        Returns :obj:`True` if the member function with the given index is visible in Qt Designer's signal
        and slot editor, otherwise :obj:`False`.

        Args:
            index: Index of the member function.

        Returns:
            Whether the function should be visible in Qt Designer.
        """
        try:
            return self.info_hash[index].visible
        except KeyError:
            pass

        method = self.meta.method(index)
        return method.methodType() == QMetaMethod.Signal or method.access() == QMetaMethod.Public

    def memberGroup(self, index: int) -> str:
        """
        Returns the name of the member group specified for the function with the given index.

        Args:
            index: Index of the member function.

        Returns:
            Group name.
        """
        return self.ensure_info(index).group

    def memberName(self, index: int) -> str:
        """
        Returns the name of the member function with the given index.

        Args:
            index: Index of the member function.

        Returns:
            Name of the member function.
        """
        return self.meta.method(index).tag()

    def parameterNames(self, index: int) -> List[QByteArray]:
        """
        Returns the parameter names of the member function with the given index, as a :class:`QByteArray` list.

        Args:
            index: Index of the member function.

        Returns:
            List of parameter names.
        """
        return self.meta.method(index).parameterNames()

    def parameterTypes(self, index: int) -> List[QByteArray]:
        """
        Returns the parameter types of the member function with the given index, as a :class:`QByteArray` list.

        Args:
            index: Index of the member function.

        Returns:
            List of parameter types.
        """
        return self.meta.method(index).parameterTypes()

    def setMemberGroup(self, index: int, group: str):
        """
        Sets the member group of the member function with the given index, to group.

        Args:
            index: Index of the member function.
            group: New group name.
        """
        self.ensure_info(index).group = group

    def setVisible(self, index: int, visible: bool):
        """
        If visible is :obj:`True`, the member function with the given index is visible in Qt Designer's
        signals and slots editing mode; otherwise the member function is hidden.

        Args:
            index: Index of the member function.
            visible: New visibility value.
        """
        self.ensure_info(index).visible = visible

    def signature(self, index: int) -> str:
        """
        Returns the signature of the member function with the given index.

        Args:
            index: Index of the member function.

        Returns:
            Method signature string.
        """
        return decode(self.meta.normalizedSignature(self.meta.method(index).methodSignature()))

    def ensure_info(self, index: int) -> "WidgetsMemberSheetExtension.Info":
        """
        Convenience method to create a cache entry in the hash.

        Args:
            index: Index of the member function.

        Returns:
            Existing cache entry, or a newly created one, if did not exist before.
        """
        try:
            info = self.info_hash[index]
        except KeyError:
            info = WidgetsMemberSheetExtension.Info(group="")
            self.info_hash[index] = info
        return info


class HidePrivateSignalsExtension(WidgetsMemberSheetExtension):

    def __init__(self, widget: QWidget, parent: QWidget):
        """
        This extension will prevent all non-public signals from appearing in Qt Designer's
        signals and slots editing mode. Signals are considered non-public if their names
        start with the underscore.

        Args:
            widget: Widget the extension is added to.
            parent: Owning object.
        """
        super().__init__(widget=widget, parent=parent)

        for idx in range(self.count()):
            if self.isSignal(idx) and self.isVisible(idx) and self.signature(idx).startswith("_"):
                self.setVisible(idx, False)


class WidgetsTaskMenuCollectionExtension(QPyDesignerTaskMenuExtension):

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
        self.__extensions: List[WidgetsTaskMenuExtension] = []
        extensions = getattr(widget, "extensions", None)
        if extensions is not None:
            for ex in extensions:
                if not issubclass(ex, WidgetsTaskMenuExtension):
                    continue
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

    def __init__(self, parent: QExtensionManager = None):
        """Factory of instantiating Task Menu extensions."""
        super().__init__(parent)
        self._member_sheet_extension_type: Optional[Type[WidgetsMemberSheetExtension]] = None

    def register_member_sheet_extension(self, extension_type: Type[WidgetsMemberSheetExtension]):
        """
        Register custom member sheet extension type. Only one member sheet extension is allowed to be
        registered per widget.
        """
        self._member_sheet_extension_type = extension_type

    def createExtension(self, obj: QObject, iid: str, parent: QObject) -> Optional[WidgetsTaskMenuCollectionExtension]:
        """
        Create Task Menu Extension instance.

        Args:
            obj: Widget which the extension is associated to.
            iid: What type of extension should be initialized
            parent: Parent Widget for the extension

        Returns:
            Extension instance or None depending of what object and iid are passed
        """
        if iid == "org.qt-project.Qt.Designer.TaskMenu":
            return WidgetsTaskMenuCollectionExtension(obj, parent)
        elif iid == "org.qt-project.Qt.Designer.MemberSheet" and self._member_sheet_extension_type is not None:
            return self._member_sheet_extension_type(obj, parent)
        return None


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# |                           Designer Plugin                                 |
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _icon(name: str, base_path: Optional[Path] = None) -> QIcon:
    """ Load icons by their file name from folder 'icons' """
    if base_path is None:
        base_path = Path(__file__).absolute().parent
    return make_icon(base_path / "icons" / f"{name}.ico")


SupportedExtensionType = Union[WidgetsTaskMenuExtension, WidgetsMemberSheetExtension]


class WidgetDesignerPlugin(QPyDesignerCustomWidgetPlugin):

    CUSTOM_INITIALIZER_METHOD = "_accwidgets_designer_init_"

    def __init__(self,
                 widget_class: Type[QWidget],
                 group_name: str,
                 extensions: Optional[List[Type[SupportedExtensionType]]] = None,
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
        self.extensions: List[Type[SupportedExtensionType]] = extensions or []
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
                factory = WidgetsExtensionFactory(self.manager)
                if any(issubclass(e, WidgetsTaskMenuExtension) for e in self.extensions):
                    self.manager.registerExtensions(factory, "org.qt-project.Qt.Designer.TaskMenu")
                if any(issubclass(e, WidgetsMemberSheetExtension) for e in self.extensions):
                    member_sheet_type = next(e for e in self.extensions if issubclass(e, WidgetsMemberSheetExtension))
                    factory.register_member_sheet_extension(member_sheet_type)
                    self.manager.registerExtensions(factory, "org.qt-project.Qt.Designer.MemberSheet")
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
        try:
            if hasattr(instance, self.CUSTOM_INITIALIZER_METHOD):
                method = getattr(instance, self.CUSTOM_INITIALIZER_METHOD)
                if callable(method):
                    method()
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
                  extensions: Optional[List[Type[SupportedExtensionType]]] = None,
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


def is_inside_designer_canvas(widget: QWidget) -> bool:
    """
    Verify that the widget is not only launched inside designer, but that it actually is rendered on the canvas
    and not e.g. in the Form Preview.

    Args:
        widget: Widget to verify.

    Returns:
        :obj:`True` if it only is rendered in the canvas and not the Designer Form Preview, or outside Designer completely.
    """
    return get_designer_cursor(widget) is not None


class DesignerUserError(Exception):
    """
    Error to be thrown by :func:`designer_user_error`, specifying that GUI error has been shown and further
    execution should be silently prevented (without raising an exception, to not crash the GUI)."""
    pass


@contextmanager
def designer_user_error(error_type: Type[Exception], match: Optional[str] = None):
    """
    Attempt to display error in Qt Designer GUI rather than throwing an exception.
    It has no effect, when block is called outside of Qt Designer.

    Args:
        error_type: Exception type to catch.
        match: Optional string regex pattern in error message to look for.
    """
    if is_designer():
        try:
            with disable_assert_cache():
                yield
        except error_type as e:
            if match is not None:
                import re
                if not re.search(match, str(e)):
                    raise

            for widget in cast(List[QWidget], QApplication.instance().topLevelWidgets()):
                if widget.isVisible():
                    parent = widget
                    break
            else:
                raise

            QMessageBox.warning(parent, "Error occurred", f"This property cannot be used due to error: {e!s}")
            raise DesignerUserError(e)
    else:
        yield
