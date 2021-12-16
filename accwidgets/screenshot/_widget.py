import functools
import qtawesome as qta
from typing import Optional, Union, Iterable
from qtpy.QtCore import Signal, QTimer, Property, QEvent
from qtpy.QtWidgets import QWidget, QToolButton, QInputDialog, QSizePolicy
from qtpy.QtGui import QPalette
from pylogbook.exceptions import LogbookError
from accwidgets.qt import OrientedToolButton
from ._grabber import grab_png_screenshot
from ._common import make_activities_summary
from ._menu import LogbookMenu
from ._model import LogbookModel


ScreenshotButtonSource = Union[QWidget, Iterable[QWidget]]
"""Alias for the possible types of the widgets that can be captured in a screenshot."""


class ScreenshotButton(OrientedToolButton):

    captureFinished = Signal(int)
    """
    Notification of the successful registration of the screenshot.
    The argument is the event ID within e-logbook system.
    """

    captureFailed = Signal(str)
    """Notification of the problem taking a screenshot. The argument is the error message."""

    modelChanged = Signal()
    """Notifies that the underlying model has been updated."""

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 source: Optional[ScreenshotButtonSource] = None,
                 message: Optional[str] = None,
                 model: Optional[LogbookModel] = None):
        """
        A button to take application's screenshot and send it to the e-logbook.

        Args:
            parent: Parent widget to hold this object.
            widget: The widget(s) to grab a screenshot of.
            message: Logbook entry message.
            model: Model that handles communication with the e-logbook.
        """
        super().__init__(parent=parent,
                         primary=QSizePolicy.Preferred,
                         secondary=QSizePolicy.Expanding)
        self._src: Iterable[QWidget] = ()
        self._include_window_decor = True
        self._msg = message
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self._update_icon()

        self._model = model or LogbookModel(parent=self)
        self._connect_model(self._model)

        menu = LogbookMenu(model_provider=self, parent=self)
        menu.setToolTipsVisible(True)
        menu.event_clicked.connect(self._take_delayed_screenshot)
        menu.event_fetch_failed.connect(self.captureFailed)
        self.setMenu(menu)

        if source is not None:
            self.source = source  # Will reset self._src

        self.clicked.connect(self._on_click)

        self._update_ui()

    def _get_message(self) -> Optional[str]:
        return self._msg

    def _set_message(self, message: Optional[str] = None):
        self._msg = message

    message = Property(str, _get_message, _set_message)
    """
    Logbook entry message. Setting this to :obj:`None` (default) will activate a
    UI user prompt when button is pressed.
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
        self.modelChanged.emit()

    model = property(fget=_get_model, fset=_set_model)
    """
    Model that handles interaction with :mod:`pylogbook` and :mod:`pyrbac` libraries.

    When assigning a new model, its ownership is transferred to the widget.
    """

    def _get_source(self) -> ScreenshotButtonSource:
        return self._src

    def _set_source(self, widget: ScreenshotButtonSource):
        self._src = [widget] if isinstance(widget, QWidget) else widget

    source = property(fget=_get_source, fset=_set_source)
    """One or more widgets to take the screenshot of."""

    def _get_include_window_decorations(self) -> bool:
        return self._include_window_decor

    def _set_include_window_decorations(self, new_val: bool):
        self._include_window_decor = new_val

    includeWindowDecorations: bool = Property(bool, _get_include_window_decorations, _set_include_window_decorations)
    """Include window decorations in the screenshot if given :attr:`source` is a :class:`QMainWindow`."""

    def event(self, event: QEvent) -> bool:
        """
        This event handler is reimplemented to react to the external style change, e.g. via QSS, to adjust
        color of the icon. It also implements automatic source detection, when no explicit :attr:`source`
        was provided.

        This is the main event handler; it handles event ``event``. You can reimplement this function in a
        subclass, but we recommend using one of the specialized event handlers instead.

        Args:
            event: Handled event.

        Returns:
            :obj:`True` if the event was recognized, otherwise it returns :obj:`False`. If the recognized event
            was accepted (see :meth:`QEvent.accepted`), any further processing such as event propagation to the
            parent widget stops.
        """
        res = super().event(event)
        if event.type() == QEvent.StyleChange or event.type() == QEvent.PaletteChange:
            # Update this at the end of the event loop, when palette has been synchronized with the updated style
            QTimer.singleShot(0, self._update_icon)
        elif event.type() == QEvent.ParentChange or event.type() == QEvent.Show:
            # Assign window as the default source, if none defined
            # ParentChange generally works when adding the widget programmatically, but does not trigger when
            # instantiated from Designer file. For that, we fall back to show event.
            if not self._src:
                self._src = self.window()
        return res

    def _update_icon(self):
        self.setIcon(qta.icon("fa.book", color=self.palette().color(QPalette.Text)))

    def _take_delayed_screenshot(self, event_id: Optional[int] = None):
        """
        Wait for a short delay before grabbing the screenshot to allow
        time for the pop-up menu to close,
        """
        QTimer.singleShot(100, functools.partial(self._take_screenshot, event_id))

    def _take_screenshot(self, event_id: Optional[int] = None):
        """
        Grab a screenshot of the widget(s) and post them to the logbook.
        """
        try:
            assert bool(self._src), "Source widget(s) for screenshot is undefined"
            if event_id is None:
                message = self._prepare_message()
                assert message, "Logbook message cannot be empty"
                event = self.model.create_logbook_event(message)
            else:
                event = self.model.get_logbook_event(event_id)

            for i, widget in enumerate(self._src):
                png_bytes = grab_png_screenshot(source=widget,
                                                include_window_decorations=self.includeWindowDecorations)
                self.model.attach_screenshot(event=event,
                                             screenshot=png_bytes,
                                             seq=i)

            self.captureFinished.emit(event.event_id)
        except (LogbookError, AssertionError) as e:
            self.captureFailed.emit(str(e))

    def _prepare_message(self) -> str:
        message = self.message
        if not message:
            message, _ = QInputDialog.getText(self, "Logbook", "Enter a logbook message:")
        return message

    def _update_ui(self):
        try:
            self.model.validate()
        except ValueError as e:
            msg = f"ERROR: {e!s}"
            enable = False
        else:
            enable = True
            activities_summary = make_activities_summary(self.model)
            msg = f"Capture screenshot to a new entry in {activities_summary} e-logbook"
        self.setToolTip(msg)
        self.setEnabled(enable)

    def _connect_model(self, model: LogbookModel):
        model.rbac_token_changed.connect(self._update_ui)
        model.activities_changed.connect(self._update_ui)
        model.activities_failed.connect(self.capture_failed)
        model.setParent(self)

    def _disconnect_model(self, model: LogbookModel):
        model.rbac_token_changed.disconnect(self._update_ui)
        model.activities_changed.disconnect(self._update_ui)
        model.activities_failed.disconnect(self.capture_failed)
        if model.parent() is self:
            model.setParent(None)
            model.deleteLater()

    def _on_click(self):
        self._take_delayed_screenshot()
