import datetime
import operator
import functools
from typing import Optional, Union, Tuple, Iterable
from pathlib import Path
from qtpy.QtCore import Signal, QTimer, QByteArray, QBuffer, QIODevice, Property
from qtpy.QtWidgets import QWidget, QMenu, QAction, QApplication, QToolButton, QMainWindow, QInputDialog
from qtpy.QtGui import QShowEvent
from pyrbac import Token
from pylogbook import Client, ActivitiesClient, NamedServer
from pylogbook.exceptions import LogbookError
from pylogbook.models import Activity, ActivitiesType
from accwidgets.qt import make_icon


ScreenshotButtonSource = Union[QWidget, Iterable[QWidget]]
"""Alias for the possible types of the widgets that can be captured in a screenshot."""


class ScreenshotButton(QToolButton):

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
        super().__init__(parent)
        self._src: Iterable[QWidget] = ()
        self._include_window_decor = True
        self._msg = message
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setIcon(make_icon(Path(__file__).parent.absolute() / "icons" / "eLogbook.png"))

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
                if isinstance(widget, QMainWindow) and self._include_window_decor:
                    # Save a screenshot of the whole window including
                    # the window chrome
                    screen = QApplication.primaryScreen()
                    screenshot = screen.grabWindow(0,
                                                   widget.pos().x(),
                                                   widget.pos().y(),
                                                   widget.frameGeometry().width(),
                                                   widget.frameGeometry().height())
                else:
                    # Save a screenshot of just the widget
                    screenshot = widget.grab()

                screenshot_bytes = QByteArray()
                screenshot_buffer = QBuffer(screenshot_bytes)
                screenshot_buffer.open(QIODevice.WriteOnly)
                screenshot.save(screenshot_buffer, "png", quality=100)
                event.attach_content(contents=screenshot_bytes,
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


class LogbookMenu(QMenu):
    event_clicked = Signal(int)
    event_fetch_failed = Signal(str)

    def __init__(self,
                 client: ActivitiesClient,
                 parent: Optional[QWidget] = None):
        """
        A menu to select from previous logbook entries.

        Args:
            client: LogbookWrapper instance.
            parent: Parent widget to hold this object.
        """
        super().__init__(parent)
        self._client = client

    def showEvent(self, event: QShowEvent):
        """
        Override of the menu show event to populate it with the latest
        Logbook entries. The Logbook API doesn't offer a good way to
        keep a local model synchronised with the server, so this just
        refetches the latest entries each time.
        """
        logbook_events = []
        try:
            # Note: specifying a `from_date` improves performance
            start = datetime.datetime.now() - datetime.timedelta(days=1)
            events_pages = self._client.get_events(from_date=start)
            events_pages.page_size = 10
            events_count = events_pages.count
            logbook_events = events_pages.get_page(0)
        except LogbookError as e:
            self.event_fetch_failed.emit(str(e))

        # We must clear here, and must NOT clear in hideEvent, because actions will be destroyed before they trigger
        self.clear()

        if events_count > 0:
            activities = "/".join(map(operator.attrgetter("name"), self._client.activities))
            for logbook_event in logbook_events:
                action = QAction("id: {0} @ {1:%T}".format(str(logbook_event.event_id)[-3:], logbook_event.date), self)
                action.triggered.connect(functools.partial(self.event_clicked.emit, logbook_event.event_id))
                action.setToolTip(f"Capture screenshot to existing entry {logbook_event.event_id} in {activities} e-logbook")
                self.addAction(action)
        else:
            action = QAction("(no events)", self)
            self.addAction(action)

        super().showEvent(event)
