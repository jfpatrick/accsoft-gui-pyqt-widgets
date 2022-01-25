from typing import Optional, cast
from qtpy.QtCore import Signal, Property
from qtpy.QtWidgets import QWidget, QToolButton, QSizePolicy, QAction
from accwidgets.qt import OrientedToolButton
from ._action import ScreenshotAction
from ._common import ScreenshotSource
from ._model import LogbookModel


class ScreenshotButton(OrientedToolButton):

    captureFinished = Signal(int)
    """
    Notification of the successful registration of the screenshot.
    The argument is the event ID within e-logbook system.
    """

    captureFailed = Signal(str)
    """Notification of the problem taking a screenshot. The argument is the error message."""

    eventFetchFailed = Signal(str)
    """Notification of the problem retrieving events from the e-logbook. The argument is the error message."""

    modelChanged = Signal()
    """Notifies that the underlying model has been updated."""

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 action: Optional[ScreenshotAction] = None):
        """
        A button to take application's screenshot and send it to the e-logbook.

        Args:
            parent: Parent widget to hold this object.
            action: Action that is connected with the button and that actually handles the screenshot functionality.
        """
        super().__init__(parent=parent,
                         primary=QSizePolicy.Preferred,
                         secondary=QSizePolicy.Expanding)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setDefaultAction(action or ScreenshotAction(parent=self))

    def _get_message(self) -> Optional[str]:
        try:
            return self._compatible_action.message
        except AssertionError:
            return None

    def _set_message(self, message: Optional[str] = None):
        self._compatible_action.message = message

    message = Property(str, _get_message, _set_message)
    """
    Logbook entry message. Setting this to :obj:`None` (default) will activate a
    UI user prompt when button is pressed.

    This is a convenience property to access
    :attr:`ScreenshotAction.message <accwidgets.screenshot.ScreenshotAction.message>`.

    Raises:
        AssertionError: When setting the property and the :meth:`~QToolButton.defaultAction` of this widget is not of
                        type :class:`~accwidgets.screenshot.ScreenshotAction` or a subclass.
    """

    def _get_source(self) -> ScreenshotSource:
        return self._compatible_action.source

    def _set_source(self, widget: ScreenshotSource):
        self._compatible_action.source = widget

    source = property(fget=_get_source, fset=_set_source)
    """
    One or more widgets to take the screenshot of. If multiple sources are defined, they will be attached as separate
    files to the same e-logbook event.

    Source(s) can be an instance of the window (:class:`QMainWindow`), or subwidgets that represent only part of the
    window.

    When this property is left empty, the main application window will be used as a default source.

    This is a convenience property to access
    :attr:`ScreenshotAction.source <accwidgets.screenshot.ScreenshotAction.source>`.

    Raises:
        AssertionError: When :meth:`~QToolButton.defaultAction` of this widget is not of
                        type :class:`~accwidgets.screenshot.ScreenshotAction` or a subclass.
    """

    def _get_include_window_decorations(self) -> bool:
        try:
            return self._compatible_action.include_window_decorations
        except AssertionError:
            return False

    def _set_include_window_decorations(self, new_val: bool):
        self._compatible_action.include_window_decorations = new_val

    includeWindowDecorations: bool = Property(bool, _get_include_window_decorations, _set_include_window_decorations)
    """
    Include window decorations in the screenshot if given :attr:`source` is a :class:`QMainWindow`.

    Window decorations are specific for every desktop environment, but typically include a title bar and a frame
    around the window.

    This is a convenience property to access
    :attr:`ScreenshotAction.source <accwidgets.screenshot.ScreenshotAction.source>`.

    Raises:
        AssertionError: When setting the property and the :meth:`~QToolButton.defaultAction` of this widget is not of
                        type :class:`~accwidgets.screenshot.ScreenshotAction` or a subclass.
    """

    def _get_max_entries(self) -> int:
        return self._compatible_action.max_menu_entries

    def _set_max_entries(self, new_val: int):
        self._compatible_action.max_menu_entries = new_val

    maxMenuEntries: int = Property(int, _get_max_entries, _set_max_entries)
    """
    Limit of existing e-logbook entries displayed in the menu. This filter works together with :attr:`maxMenuDays`.

    This is a convenience property to access
    :attr:`ScreenshotAction.max_menu_entries <accwidgets.screenshot.ScreenshotAction.max_menu_entries>`.

    Raises:
        AssertionError: When :meth:`~QToolButton.defaultAction` of this widget is not of
                        type :class:`~accwidgets.screenshot.ScreenshotAction` or a subclass.
    """

    def _get_max_days(self) -> int:
        return self._compatible_action.max_menu_days

    def _set_max_days(self, new_val: int):
        self._compatible_action.max_menu_days = new_val

    maxMenuDays: int = Property(int, _get_max_days, _set_max_days)
    """
    Limit of recent days to collect the existing e-logbook entries that are then displayed in the menu. This filter
    works together with :attr:`maxMenuEntries`.

    This is a convenience property to access
    :attr:`ScreenshotAction.max_menu_days <accwidgets.screenshot.ScreenshotAction.max_menu_days>`.

    Raises:
        AssertionError: When :meth:`~QToolButton.defaultAction` of this widget is not of
                        type :class:`~accwidgets.screenshot.ScreenshotAction` or a subclass.
    """

    def _get_model(self) -> LogbookModel:
        return self._compatible_action.model

    def _set_model(self, new_val: LogbookModel):
        self._compatible_action.model = new_val

    model = property(fget=_get_model, fset=_set_model)
    """
    Model that handles interaction with :mod:`pylogbook` and :mod:`pyrbac` libraries.

    When assigning a new model, its ownership is transferred to the associated action.

    This is a convenience property to access
    :attr:`ScreenshotAction.model <accwidgets.screenshot.ScreenshotAction.model>`.

    Raises:
        AssertionError: When :meth:`~QToolButton.defaultAction` of this widget is not of
                        type :class:`~accwidgets.screenshot.ScreenshotAction` or a subclass.
    """

    def setDefaultAction(self, action: QAction):
        """
        Sets the default action.

        If a tool button has a default action, the action defines the following properties of the button:

        * :attr:`~QAbstractButton.checkable`
        * :attr:`~QAbstractButton.checked`
        * :attr:`~QWidget.enabled`
        * :attr:`~QWidget.font`
        * :attr:`~QAbstractButton.icon`
        * :attr:`~QToolButton.popupMode` (assuming the action has a menu)
        * :attr:`~QWidget.statusTip`
        * :attr:`~QAbstractButton.text`
        * :attr:`~QWidget.toolTip`
        * :attr:`~QWidget.whatsThis`

        Other properties, such as :attr:`~QAbstractButton.autoRepeat`, are not affected by actions.

        Args:
            action: Default action to set.
        """
        current_action = super().defaultAction()
        model_changed = False
        if isinstance(current_action, ScreenshotAction):
            self._disconnect_action(current_action)
            model_changed = True
        super().setDefaultAction(action)
        if isinstance(action, ScreenshotAction):
            self._connect_action(action)
            if action.parent() is None:
                action.setParent(self)
            model_changed = True
        if model_changed:
            self.modelChanged.emit()

    @property
    def _compatible_action(self) -> ScreenshotAction:
        current_action = cast(ScreenshotAction, super().defaultAction())
        assert_action(current_action)
        return current_action

    def _connect_action(self, action: ScreenshotAction):
        action.capture_finished.connect(self.captureFinished)
        action.capture_failed.connect(self.captureFailed)
        action.event_fetch_failed.connect(self.eventFetchFailed)
        action.model_changed.connect(self.modelChanged)

    def _disconnect_action(self, action: ScreenshotAction):
        action.capture_finished.disconnect(self.captureFinished)
        action.capture_failed.disconnect(self.captureFailed)
        action.event_fetch_failed.disconnect(self.eventFetchFailed)
        action.model_changed.disconnect(self.modelChanged)


def assert_action(current_action: QAction):
    assert isinstance(current_action, ScreenshotAction), "Cannot retrieve/update " \
                                                         f"{ScreenshotAction.__name__}-related property " \
                                                         "on the action " \
                                                         f"of type {type(current_action).__name__}"
