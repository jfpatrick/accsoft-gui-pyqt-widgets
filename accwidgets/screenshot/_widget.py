import operator
import functools
import qtawesome as qta
from typing import Optional, Union, Tuple, Iterable
from qtpy.QtCore import Signal, QTimer, Property, QEvent
from qtpy.QtWidgets import QWidget, QToolButton, QInputDialog, QSizePolicy
from qtpy.QtGui import QPalette
from pyrbac import Token
from pylogbook import Client, ActivitiesClient, NamedServer
from pylogbook.exceptions import LogbookError
from pylogbook.models import Activity, ActivitiesType
from accwidgets.qt import OrientedToolButton
from ._grabber import grab_png_screenshot
from ._menu import LogbookMenu


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

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 source: Optional[ScreenshotButtonSource] = None,
                 message: Optional[str] = None,
                 activities: Optional[ActivitiesType] = None,
                 server_url: Union[str, NamedServer] = NamedServer.PRO,
                 rbac_token: Optional[Token] = None):
        """
        A button to take application's screenshot and send it to the e-logbook.

        Args:
            parent: Parent widget to hold this object.
            widget: The widget(s) to grab a screenshot of.
            message: Logbook entry message.
            activities: Logbook activities.
            server_url: Logbook server URL.
            rbac_token: RBAC token.
        """
        super().__init__(parent=parent,
                         primary=QSizePolicy.Preferred,
                         secondary=QSizePolicy.Expanding)
        self._src: Iterable[QWidget] = ()
        self._include_window_decor = True
        self._msg = message
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self._update_icon()

        self._client = Client(server_url=server_url, rbac_token="")
        self._ac_client = ActivitiesClient(client=self._client, activities=[])

        menu = LogbookMenu(self._ac_client, parent=self)
        menu.setToolTipsVisible(True)
        menu.event_clicked.connect(self._take_delayed_screenshot)
        menu.event_fetch_failed.connect(self.captureFailed)
        self.setMenu(menu)

        self.set_activities(activities)
        self.set_rbac_token(rbac_token)
        if source is not None:
            self.source = source  # Will reset self._src

        self.clicked.connect(self._on_click)

    def _get_message(self) -> Optional[str]:
        return self._msg

    def _set_message(self, message: Optional[str] = None):
        self._msg = message

    message = Property(str, _get_message, _set_message)
    """
    Logbook entry message. Setting this to :obj:`None` (default) will activate a
    UI user prompt when button is pressed.
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

    def set_rbac_token(self, rbac_token: Token):
        """
        Set the RBAC token.

        Args:
            rbac_token: RBAC token.
        """
        self._client.rbac_b64_token = "" if rbac_token is None else rbac_token
        self._flush_activities_cache()
        self._update_tooltip()
        self._update_enabled_status()

    def clear_rbac_token(self):
        """
        Clear the RBAC token.
        """
        self._client.rbac_b64_token = ""
        self._update_tooltip()
        self._update_enabled_status()

    def _current_activities(self) -> Tuple[Activity, ...]:
        """
        Get the current activities.
        """
        return self._ac_client.activities

    def set_activities(self, activities: ActivitiesType):
        """
        Set the logbook activities.

        Args:
            activities: The activities.
        """
        self._activities_cache = [] if activities is None else activities
        self._flush_activities_cache()
        self._update_tooltip()
        self._update_enabled_status()

    def event(self, event: QEvent) -> bool:
        """
        This event handler is reimplemented to react to the external style change, e.g. via QSS, to adjust
        color of the icon.

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
                event = self._ac_client.add_event(message)
            else:
                event = self._client.get_event(event_id)

            for i, widget in enumerate(self._src):
                png_bytes = grab_png_screenshot(source=widget,
                                                include_window_decorations=self.includeWindowDecorations)
                event.attach_content(contents=png_bytes,
                                     mime_type="image/png",
                                     name=f"capture_{i}.png")

            self.captureFinished.emit(event.event_id)
        except (LogbookError, AssertionError) as e:
            self.captureFailed.emit(str(e))

    def _prepare_message(self) -> str:
        message = self.message
        if not message:
            message, _ = QInputDialog.getText(self, "Logbook", "Enter a logbook message:")
        return message

    def _flush_activities_cache(self):
        if self._rbac_token_valid() and self._activities_cache is not None:
            self._ac_client.activities = self._activities_cache
            self._activities_cache = None

    def _rbac_token_valid(self):
        return len(self._client.rbac_b64_token) > 0

    def _update_tooltip(self):
        if not self._rbac_token_valid():
            msg = "ERROR: RBAC login is required to write to the e-logbook"
        elif not self._current_activities():
            msg = "ERROR: No e-logbook activity is defined"
        else:
            activities = "/".join(map(operator.attrgetter("name"), self._current_activities()))
            msg = f"Capture screenshot to a new entry in {activities} e-logbook"
        self.setToolTip(msg)

    def _update_enabled_status(self):
        self.setEnabled(bool(self._current_activities() and self._rbac_token_valid()))

    def _on_click(self):
        self._take_delayed_screenshot()
