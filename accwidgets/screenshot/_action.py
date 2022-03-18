import functools
import qtawesome as qta
from asyncio import CancelledError
try:
    from asyncio import create_task
except ImportError:
    from asyncio import ensure_future as create_task  # type: ignore
from typing import Optional, List, cast
from qtpy.QtWidgets import QAction, QWidget, QInputDialog, QApplication, QMainWindow
from qtpy.QtCore import QObject, Signal, QEvent, QTimer
from qtpy.QtGui import QPalette
from pyrbac import Token
from pylogbook.exceptions import LogbookError
from accwidgets._integrations import RbaButtonProtocol
from accwidgets._async_utils import install_asyncio_event_loop
from ._model import LogbookModel
from ._common import ScreenshotSource, make_new_entry_tooltip
from ._menu import LogbookMenu
from ._grabber import grab_png_screenshot


class ScreenshotAction(QAction):

    capture_finished = Signal(int)
    """
    Notification of the successful registration of the screenshot.
    The argument is the event ID within e-logbook system.
    """

    capture_failed = Signal(str)
    """Notification of the problem taking a screenshot. The argument is the error message."""

    event_fetch_failed = Signal(str)
    """Notification of the problem retrieving events from the e-logbook. The argument is the error message."""

    model_changed = Signal()
    """Notifies that the underlying model has been updated."""

    activities_failed = Signal(str)
    """Notifies when the e-logbook activities setting has failed. The argument is the error message."""

    def __init__(self,
                 parent: Optional[QObject] = None,
                 model: Optional[LogbookModel] = None):
        """
        An action to take application's screenshot and send it to the e-logbook.

        Args:
            parent: Parent widget to hold this object.
            model: Model that handles communication with the e-logbook.
        """
        super().__init__(parent)
        self._src: List[QWidget] = []
        self._include_window_decor = False
        self._msg: Optional[str] = None
        self._max_menu_days = 1
        self._max_menu_entries = 10
        self._icon_needs_update = True

        self._model = model or LogbookModel(parent=self)
        self._connect_model(self._model)

        menu = LogbookMenu(model_provider=self)
        menu.setToolTipsVisible(True)
        menu.event_clicked.connect(self._take_delayed_screenshot)
        menu.event_fetch_failed.connect(self.event_fetch_failed)
        self.setMenu(menu)
        self.setText("Screenshot")

        self.triggered.connect(self._on_trigger)

        install_asyncio_event_loop()

        self._update_icon_if_needed()
        self._update_ui()

        QApplication.instance().installEventFilter(self)

    def _get_message(self) -> Optional[str]:
        return self._msg

    def _set_message(self, message: Optional[str] = None):
        self._msg = message

    message = property(fget=_get_message, fset=_set_message)
    """
    Logbook entry message. Setting this to :obj:`None` (default) will activate a
    UI user prompt when the action is triggered.
    """

    def _get_model(self) -> LogbookModel:
        return self._model

    def _set_model(self, new_val: LogbookModel):
        if new_val == self._model:
            return
        self._disconnect_model(self._model)
        self._model = new_val
        self._connect_model(new_val)
        self._update_ui()
        self.model_changed.emit()

    model = property(fget=_get_model, fset=_set_model)
    """
    Model that handles interaction with :mod:`pylogbook` and :mod:`pyrbac` libraries.

    When assigning a new model, its ownership is transferred to the action.
    """

    def _get_source(self) -> ScreenshotSource:
        return self._src

    def _set_source(self, widget: ScreenshotSource):
        self._src = [widget] if isinstance(widget, QWidget) else list(widget)
        self._update_ui()

    source = property(fget=_get_source, fset=_set_source)
    """
    One or more widgets to take the screenshot of. If multiple sources are defined, they will be attached as separate
    files to the same e-logbook event.

    Source(s) can be an instance of the window (:class:`QMainWindow`), or subwidgets that represent only part of the
    window.

    When this property is left empty, the main application window will be used as a default source.
    """

    def _get_include_window_decorations(self) -> bool:
        return self._include_window_decor

    def _set_include_window_decorations(self, new_val: bool):
        self._include_window_decor = new_val

    include_window_decorations = property(fget=_get_include_window_decorations, fset=_set_include_window_decorations)
    """
    Include window decorations in the screenshot if given :attr:`source` is a :class:`QMainWindow`.

    Window decorations are specific for every desktop environment, but typically include a title bar and a frame
    around the window.
    """

    def _get_max_entries(self) -> int:
        return self._max_menu_entries

    def _set_max_entries(self, new_val: int):
        self._max_menu_entries = new_val

    max_menu_entries = property(fget=_get_max_entries, fset=_set_max_entries)
    """
    Limit of existing e-logbook entries displayed in the menu. This filter works together with :attr:`max_menu_days`.
    """

    def _get_max_days(self) -> int:
        return self._max_menu_days

    def _set_max_days(self, new_val: int):
        self._max_menu_days = new_val

    max_menu_days = property(fget=_get_max_days, fset=_set_max_days)
    """
    Limit of recent days to collect the existing e-logbook entries that are then displayed in the menu. This filter
    works together with :attr:`max_menu_entries`.
    """

    def connect_rbac(self, button: RbaButtonProtocol):
        """
        Convenience method to bind the action with a :class:`~accwidgets.rbac.RbaButton` for automatic token
        propagation.

        Args:
            button: Instance of :class:`~accwidgets.rbac.RbaButton` or a compatible class.
        """
        button.loginSucceeded.connect(self._update_rbac_token)
        button.logoutFinished.connect(self._delete_rbac_token)
        button.tokenExpired.connect(self._delete_rbac_token)

    def disconnect_rbac(self, button: RbaButtonProtocol):
        """
        Convenience method to unbind the action from the :class:`~accwidgets.rbac.RbaButton` that was
        previously connected via :meth:`connect_rbac`.

        Args:
            button: Instance of :class:`~accwidgets.rbac.RbaButton` or a compatible class.
        """
        try:
            button.loginSucceeded.disconnect(self._update_rbac_token)
        except TypeError:
            # If was not connected previously, ignore...
            pass
        try:
            button.logoutFinished.disconnect(self._delete_rbac_token)
        except TypeError:
            # If was not connected previously, ignore...
            pass
        try:
            button.tokenExpired.disconnect(self._delete_rbac_token)
        except TypeError:
            # If was not connected previously, ignore...
            pass

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.ApplicationPaletteChange, QEvent.StyleChange, QEvent.PaletteChange):
            if event.type() == QEvent.ApplicationPaletteChange or watched is self.parentWidget() or watched is self.menu():
                # Schedule the update at the end of the event loop, when palette has been synchronized with the updated style
                # We use a flag, in case this event filter fires many times during the same render frame,
                # while only a single icon update is needed
                self._icon_needs_update = True
                QTimer.singleShot(0, self._update_icon_if_needed)
        elif event.type() == QEvent.WindowActivate:
            # Assign window as the default source, if none defined
            if not self.source:
                app = cast(QApplication, QApplication.instance())
                for top_widget in app.topLevelWidgets():
                    if isinstance(top_widget, QMainWindow):
                        window = top_widget
                        break
                else:
                    window = None
                if window is not None:
                    self.source = window

        # Do not call super. In rare cases (e.g. in ApplicationFrame tests) this function can be called after the
        # object is deleted, hence super produces error. But we are expecting False from the super anyway.
        return False

    def _update_icon_if_needed(self):
        if not self._icon_needs_update:
            return
        self._icon_needs_update = False
        widget = self.parentWidget()
        if widget is None:
            # We don't use QApplication, because it's likely to have its color default to black,
            # if styling is done via QSS (because there's no block entry for QApplication). The only
            # possible way to set application-wide color appears to be either QPalette interface, or creating a
            # programmatic theme. Instead, we rely on action's menu, hoping that it will have proper styling, and
            # as action is likely itself to be inside the menu (when without parentWidget), its styling can match
            # without causing confusion.
            widget = self.menu()
        else:
            # In some cases (e.g. in ComRAD's toolbar plugin) parent widget results in the wrong palette,
            # it seems to be more stable when using its window.
            widget = widget.window()
        self.setIcon(qta.icon("fa.book", color=widget.palette().color(QPalette.Text)))

    def _delete_rbac_token(self):
        # These are dedicated methods inside action and not directly to model, to avoid connection confusion,
        # when model of the action changes, but signals from RbaButton are not reconnected
        self.model.reset_rbac_token(None)

    def _update_rbac_token(self, token: Token):
        # These are dedicated methods inside action and not directly to model, to avoid connection confusion,
        # when model of the action changes, but signals from RbaButton are not reconnected
        self.model.reset_rbac_token(token)

    def _take_delayed_screenshot(self, event_id: int = -1):
        """
        Wait for a short delay before grabbing the screenshot to allow
        time for the pop-up menu to close,
        """
        QTimer.singleShot(100, functools.partial(self._take_screenshot, None if event_id == -1 else event_id))

    def _take_screenshot(self, event_id: Optional[int] = None):
        create_task(self._take_screenshot_async(event_id))

    async def _take_screenshot_async(self, event_id: Optional[int]):
        """
        Grab a screenshot of the widget(s) and post them to the logbook.
        """
        try:
            if event_id is None:
                message = self._prepare_message()
                assert message, "Logbook message cannot be empty"
                produce_event_task = create_task(self.model.create_logbook_event(message))
            else:
                produce_event_task = create_task(self.model.get_logbook_event(event_id))
            event = await produce_event_task
            for i, widget in enumerate(self._src):
                png_bytes = grab_png_screenshot(source=widget,
                                                include_window_decorations=self.include_window_decorations)
                await create_task(self.model.attach_screenshot(event=event,
                                                               screenshot=png_bytes,
                                                               seq=i))
            self.capture_finished.emit(event.event_id)
        except (LogbookError, AssertionError) as e:
            self.capture_failed.emit(str(e))
        except CancelledError:
            pass

    def _prepare_message(self) -> str:
        message = self.message
        if not message:
            parent = self.parentWidget()
            if not parent:
                # QInputDialog does not want to take a window as a parent, but if the action does not have a
                # parentWidget we still must provide some sort of widget for parent (at least for styling propagation).
                # The menu is the closes accessible widget that is sure to exist.
                parent = self.menu()
            message, _ = QInputDialog.getText(parent, "Logbook", "Enter a logbook message:")
        return message

    def _update_ui(self):
        try:
            assert bool(self._src), "Source widget(s) for screenshot is undefined"
            self.model.validate()
        except (ValueError, AssertionError) as e:
            msg = f"ERROR: {e!s}"
            enable = False
        else:
            enable = True
            msg = make_new_entry_tooltip(self.model)
        self.setToolTip(msg)
        self.setEnabled(enable)

    def _connect_model(self, model: LogbookModel):
        model.rbac_token_changed.connect(self._update_ui)
        model.activities_changed.connect(self._update_ui)
        model.activities_failed.connect(self._update_ui)
        model.activities_failed.connect(self.activities_failed)
        model.setParent(self)

    def _disconnect_model(self, model: LogbookModel):
        model.rbac_token_changed.disconnect(self._update_ui)
        model.activities_changed.disconnect(self._update_ui)
        model.activities_failed.disconnect(self._update_ui)
        model.activities_failed.disconnect(self.activities_failed)
        if model.parent() is self:
            model.setParent(None)
            model.deleteLater()

    def _on_trigger(self):
        self._take_delayed_screenshot()
