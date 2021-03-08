from typing import Optional, Union, overload, cast, Tuple, TYPE_CHECKING
from pathlib import Path
from qtpy.QtWidgets import (QMainWindow, QWidget, QDockWidget, QMenu, QAction, QMenuBar, QToolBar, QSpacerItem,
                            QSizePolicy, QHBoxLayout)
from qtpy.QtGui import QShowEvent
from qtpy.QtCore import Qt, Property, Slot
from accwidgets._designer_base import _icon, designer_user_error, DesignerUserError
from ._about_dialog import AboutDialog

if TYPE_CHECKING:
    from accwidgets.log_console import LogConsoleDock, LogConsole  # noqa: F401
    from accwidgets.timing_bar import TimingBar  # noqa: F401
    from accwidgets.rbac import RbaButton  # noqa: F401


class ApplicationFrame(QMainWindow):

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 flags: Optional[Union[Qt.WindowFlags, Qt.WindowType]] = None,
                 use_log_console: bool = False,
                 use_timing_bar: bool = False,
                 use_rbac: bool = False):
        """
        Main window of the common CERN accelerator applications.

        Args:
            parent: Parent widget to hold this object.
            flags: Configuration flags to be passed to Qt.
            use_log_console: Display log console drawer in the main window. Set this to :obj:`False` if you are not
                             intending to use the console, to avoid unnecessary allocations.
            use_timing_bar: Display timing cycle indicator in the primary toolbar. Set this to :obj:`False` if you
                            are not intending to use the component, to avoid unnecessary allocations and remote
                            connections.
            use_rbac: Display RBAC authentication widget in the primary toolbar. Set this to :obj:`False` if you
                      are not intending to use the component, to avoid unnecessary allocations and remote connections.
        """
        if flags is None:
            flags = Qt.WindowFlags() | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint

        super().__init__(parent, flags)

        self.__log_console: Optional[QDockWidget] = None
        self.__timing_tool: Optional[Tuple[QAction, "TimingBar"]] = None  # atomically keep both together
        self.__rba_tool: Optional[Tuple[QAction, "RbaButton"]] = None  # atomically keep both together
        self.__app_version: str = "0.0.1"

        self.setWindowIcon(_icon(name=ApplicationFrame.__name__, base_path=Path(__file__).parent.absolute()))

        self.useLogConsole = use_log_console
        self.useRBAC = use_rbac
        self.useTimingBar = use_timing_bar

    @Slot()
    def showAboutDialog(self):
        """
        Display an about dialog.

        This slot can be easily connected to the :class:`QAction`, that is accessible, e.g. from the main menu.
        Override this method to issue a custom about dialog.
        """
        dialog = AboutDialog(app_name=self.windowTitle(),
                             version=self.appVersion,
                             icon=self.windowIcon(),
                             parent=self)
        dialog.exec_()

    @Slot()
    def toggleFullScreen(self):
        """
        Switch between full screen and normal modes.

        This slot can be easily connected to the :class:`QAction`, that is accessible, e.g. from the main menu.
        """

        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def __get_use_log_console(self) -> bool:
        return self.__log_console is not None

    def __set_use_log_console(self, new_val: bool):
        if new_val == self.useLogConsole:
            return

        if not TYPE_CHECKING:
            try:
                with designer_user_error(ImportError, match=_DESIGNER_IMPORT_ERROR):
                    from accwidgets.log_console import LogConsoleDock  # noqa: F811
            except DesignerUserError:
                return
        self.log_console = LogConsoleDock() if new_val else None

    useLogConsole: bool = Property(bool, fget=__get_use_log_console, fset=__set_use_log_console)
    """
    Display log console drawer (placed at the bottom of the window by default).

    This call will instantiate a :class:`~accwidgets.log_console.LogConsoleDock` object.
    If you wish to use a custom log console class, assign it to the :attr:`log_console` property directly.
    """

    def __get_log_console(self) -> Optional["LogConsoleDock"]:
        return self.__log_console

    def __set_log_console(self, new_val: Optional[QWidget]):
        if not TYPE_CHECKING:
            try:
                with designer_user_error(ImportError, match=_DESIGNER_IMPORT_ERROR):
                    from accwidgets.log_console import LogConsoleDock, LogConsole  # noqa: F811
            except DesignerUserError:
                return
        if ((new_val is None and self.__log_console is None)
                or (new_val is not None and self.__log_console is not None
                    and ((isinstance(new_val, QDockWidget) and new_val == self.__log_console)
                         or (not isinstance(new_val, QDockWidget) and new_val == self.__log_console.widget())
                         or (isinstance(new_val, LogConsole) and isinstance(self.__log_console, LogConsoleDock)
                             and new_val == cast(LogConsoleDock, self.__log_console).console)))):
            # Do nothing if trying to assign the same widget
            return

        if self.__log_console is not None:
            view = self.__get_menu_view()
            if view:
                view.removeAction(self.__log_console.toggleViewAction())
            self.removeDockWidget(self.__log_console)
            self.__log_console.deleteLater()
            self.__log_console = None
        if new_val is not None:
            if isinstance(new_val, QDockWidget):
                self.__log_console = new_val
            else:
                self.__log_console = QDockWidget()
                self.__log_console.setWidget(new_val)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.__log_console)
            self.__ensure_log_toggle_action(self.__log_console)

    log_console = property(fget=__get_log_console, fset=__set_log_console)
    """Handle of the log console widget that is integrated in the application frame."""

    def __get_use_rbac(self) -> bool:
        return self.__rba_tool is not None

    def __set_use_rbac(self, new_val: bool):
        if new_val == self.useRBAC:
            return

        if not TYPE_CHECKING:
            try:
                with designer_user_error(ImportError, match=_DESIGNER_IMPORT_ERROR):
                    from accwidgets.rbac import RbaButton  # noqa: F811
            except DesignerUserError:
                return
        self.rba_widget = RbaButton() if new_val else None

    useRBAC: bool = Property(bool, fget=__get_use_rbac, fset=__set_use_rbac)
    """
    Display RBAC toolbar item (placed at the right of the primary toolbar).

    This call will instantiate a :class:`RbaButton` object.
    If you wish to use a custom widget class, assign it to the :attr:`rba_widget` property directly.
    """

    def __get_rba_widget(self) -> Optional["RbaButton"]:
        return None if self.__rba_tool is None else self.__rba_tool[1]

    def __set_rba_widget(self, new_val: Optional[QWidget]):
        if ((new_val is None and self.__rba_tool is None)
                or (new_val is not None and self.__rba_tool is not None and self.__rba_tool[1] == new_val)):
            return

        if self.__rba_tool is not None:
            tool_action, tool_widget = self.__rba_tool
            for associated_widget in tool_action.associatedWidgets():
                if isinstance(associated_widget, QToolBar) and associated_widget.parent() == self:
                    associated_widget.removeAction(tool_action)
            tool_widget.deleteLater()
            self.__rba_tool = None
        if new_val is not None:
            toolbar = self.main_toolbar()
            tool_widget = new_val
            # Always align right (last action)
            cnt = len(toolbar.actions())
            if cnt == 0 or not isinstance(toolbar.widgetForAction(toolbar.actions()[cnt - 1]), ToolBarSpacer):
                # Also use the spacer, to always snap to the right edge
                toolbar.addWidget(ToolBarSpacer())
            tool_action = toolbar.addWidget(tool_widget)
            self.__rba_tool = (tool_action, tool_widget)
        else:
            self.__remove_main_toolbar_if_needed()

    rba_widget = property(fget=__get_rba_widget, fset=__set_rba_widget)
    """Handle of the RBAC toolbar item that is integrated in the primary toolbar."""

    def __get_use_timing_bar(self) -> bool:
        return self.__timing_tool is not None

    def __set_use_timing_bar(self, new_val: bool):
        if new_val == self.useTimingBar:
            return

        if not TYPE_CHECKING:
            try:
                with designer_user_error(ImportError, match=_DESIGNER_IMPORT_ERROR):
                    from accwidgets.timing_bar import TimingBar  # noqa: F811
            except DesignerUserError:
                return
        self.timing_bar = TimingBar() if new_val else None

    useTimingBar: bool = Property(bool, fget=__get_use_timing_bar, fset=__set_use_timing_bar)
    """
    Display timing cycle indicator (placed at the left of the primary toolbar).

    This call will instantiate a :class:`~accwidgets.timing_bar.TimingBar` object.
    If you wish to use a custom widget class, assign it to the :attr:`timing_bar` property directly.
    """

    def __get_timing_bar(self) -> Optional["TimingBar"]:
        return None if self.__timing_tool is None else self.__timing_tool[1]

    def __set_timing_bar(self, new_val: Optional[QWidget]):
        if ((new_val is None and self.__timing_tool is None)
                or (new_val is not None and self.__timing_tool is not None and self.__timing_tool[1] == new_val)):
            return

        if self.__timing_tool is not None:
            tool_action, tool_widget = self.__timing_tool
            # Find the right toolbar:
            for associated_widget in tool_action.associatedWidgets():
                if isinstance(associated_widget, QToolBar) and associated_widget.parent() == self:
                    associated_widget.removeAction(tool_action)
            tool_widget.deleteLater()
            self.__timing_tool = None
        if new_val is not None:
            toolbar = self.main_toolbar()
            tool_widget = new_val
            # Always align left (first action)
            try:
                tool_action = toolbar.insertWidget(toolbar.actions()[0], tool_widget)
            except IndexError:
                tool_action = toolbar.addWidget(tool_widget)
            self.__timing_tool = (tool_action, tool_widget)
        else:
            self.__remove_main_toolbar_if_needed()

    timing_bar = property(fget=__get_timing_bar, fset=__set_timing_bar)
    """Handle of the timing cycle indicator that is integrated in the primary toolbar."""

    def __set_app_version(self, new_val: str):
        self.__app_version = new_val

    appVersion: str = Property(str, fget=lambda self: self.__app_version, fset=__set_app_version)
    """
    Application version that is displayed in the default "About" dialog. You may ignore it,
    when using a custom about dialog, e.g. by overriding :meth:`showAboutDialog`.
    """

    @overload
    def main_toolbar(self) -> QToolBar:
        ...

    @overload  # noqa: F811
    def main_toolbar(self, create: bool) -> Optional[QToolBar]:
        ...

    def main_toolbar(self, create: bool = True) -> Optional[QToolBar]:  # noqa: F811
        """
        Retrieve the existing primary toolbar.

        It is possible to optionally instantiate a new one, if it did not exist previously.

        Args:
            create: Create a new primary toolbar if it does not exist.

        Returns:
            Instance of the toolbar if found or created.
        """
        first_toolbar: Optional[QToolBar] = None
        for toolbar in self.children():
            if isinstance(toolbar, QToolBar):
                if first_toolbar is None:
                    first_toolbar = toolbar
                if cast(QToolBar, toolbar).windowTitle() == self.__MAIN_TOOLBAR_TITLE:
                    return toolbar

        # No toolbar found. Create it, if needed
        if create:
            if first_toolbar is not None:
                new_toolbar = QToolBar(self.__MAIN_TOOLBAR_TITLE)
                self.insertToolBar(first_toolbar, new_toolbar)
            else:
                new_toolbar = self.addToolBar(self.__MAIN_TOOLBAR_TITLE)
            self.__ensure_main_toolbar_toggle_action(new_toolbar)
            return new_toolbar
        else:
            return None

    def removeToolBar(self, toolbar: QToolBar):
        """
        Removes the ``toolbar`` from the main window layout and hides it. Note that the ``toolbar`` is not deleted.

        This reimplementation also unsets RBAC or timing bar indicator usage flags, if the primary toolbar is
        being removed, because those items are intended to be placed inside the primary toolbar.

        Args:
            toolbar: Toolbar to remove.
        """
        if toolbar.windowTitle() == self.__MAIN_TOOLBAR_TITLE:
            # We are removing primary toolbar, make sure no components keep relying on it
            if self.useRBAC:
                self.useRBAC = False
            if self.useTimingBar:
                self.useTimingBar = False
        super().removeToolBar(toolbar)

    def setMenuBar(self, bar: QMenuBar):
        """
        Sets the menu bar for the main window to ``bar``.

        .. note:: Main window takes ownership of the ``bar`` pointer and deletes it at the appropriate time.

        This reimplementation also adds toggle view actions for supported toolbar items, such as RBAC or timing bar
        indicator. These actions become available under "View" top menu. If such menu does not
        exist in the ``bar``, the actions will not be placed.

        Args:
            bar: Menu bar to integrate into the main window.
        """
        super().setMenuBar(bar)
        if self.__log_console:
            self.__ensure_log_toggle_action(self.__log_console)
        main_toolbar = self.main_toolbar(create=False)
        if main_toolbar:
            self.__ensure_main_toolbar_toggle_action(main_toolbar)

    def showEvent(self, ev: QShowEvent):
        """
        This event handler can be reimplemented in a subclass to receive widget show events which are passed
        in the ``ev`` parameter.

        Non-spontaneous show events are sent to widgets immediately before they are shown. The spontaneous show
        events of windows are delivered afterwards.

        .. note:: A widget receives spontaneous show and hide events when its mapping status is changed by the
                  window system, e.g. a spontaneous hide event when the user minimizes the window, and a spontaneous
                  show event when the window is restored again. After receiving a spontaneous hide event, a widget is
                  still considered visible in the sense of :meth:`isVisible`.

        This reimplementation also adds toggle view actions for supported toolbar items, such as RBAC or
        timing bar indicator, just in case when order of creating a menu bar and introducing the toolbar items
        may lead to de-synchronization of the menu items. These actions become available under "View" top menu.
        If such menu does not exist in the ``bar``, the actions will not be placed.

        Args:
            ev: Incoming event.
        """
        super().showEvent(ev)
        if not ev.spontaneous():
            if self.__log_console:
                self.__ensure_log_toggle_action(self.__log_console)
            main_toolbar = self.main_toolbar(create=False)
            if main_toolbar:
                self.__ensure_main_toolbar_toggle_action(main_toolbar)

    def __get_menu_view(self) -> Optional[QMenu]:
        menu_bar: QMenuBar = self.menuBar()
        for action in menu_bar.actions():
            if action.text() == "View" and action.menu() is not None:
                return action.menu()
        return None

    def __ensure_log_toggle_action(self, log_console: QDockWidget):
        view = self.__get_menu_view()
        if view:
            log_console.toggleViewAction().setText("Toggle Log Console")
            view.addAction(log_console.toggleViewAction())

    def __ensure_main_toolbar_toggle_action(self, toolbar: QToolBar):
        view = self.__get_menu_view()
        if view:
            toolbar.toggleViewAction().setText("Toggle Primary Toolbar")
            view.addAction(toolbar.toggleViewAction())

    def __remove_main_toolbar_if_needed(self):
        if self.timing_bar is None and self.rba_widget is None:
            # Remove main toolbar completely, as it is not being used by anything
            toolbar = self.main_toolbar(create=False)
            if toolbar and len(toolbar.actions()) == 0:
                view = self.__get_menu_view()
                if view:
                    view.removeAction(toolbar.toggleViewAction())
                self.removeToolBar(toolbar)
                toolbar.deleteLater()

    __MAIN_TOOLBAR_TITLE = "Primary Toolbar"


class ToolBarSpacer(QWidget):

    def __init__(self, parent: Optional[QWidget] = None,
                 w: int = 0,
                 h: int = 0,
                 h_policy: QSizePolicy = QSizePolicy.Expanding,
                 v_policy: QSizePolicy = QSizePolicy.Expanding):
        """
        Spacer item that can be easily placed in the :class:`QToolBar` programmatically.

        Args:
            parent: Owning object.
            w: Preferred width.
            h: Preferred height.
            h_policy: Horizontal resize policy.
            v_policy: Vertical resize policy.
        """
        super().__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addItem(QSpacerItem(w, h, h_policy, v_policy))


_DESIGNER_IMPORT_ERROR = r"accwidgets.\w+ (is intended|cannot reliably)"
