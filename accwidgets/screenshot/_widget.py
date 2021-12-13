import datetime

from typing import Optional, Union, List
from pathlib import Path
from accwidgets.qt import make_icon
from functools import partial
from pyrbac import Token
from pylogbook import Client, ActivitiesClient, NamedServer
from pylogbook.exceptions import LogbookError
from pylogbook.models import Activity, ActivitiesType

from qtpy.QtCore import Signal, QTimer, QEvent, QByteArray, QBuffer, QIODevice
from qtpy.QtWidgets import QWidget, QMenu, QAction, QApplication, QToolButton, QMainWindow, QInputDialog


class ScreenshotButton(QToolButton):

    capture_succeeded = Signal(int)
    capture_failed = Signal(str)

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 widget: Optional[Union[QWidget, List[QWidget]]] = None,
                 message: Optional[str] = None,
                 activities: Optional[ActivitiesType] = None,
                 server_url: Union[str, NamedServer] = NamedServer.PRO,
                 rbac_token: Optional[Token] = None,
                 chrome: bool = True):
        """
        A button to take application's screenshot and send it to the e-logbook.

        Args:
            parent: Parent widget to hold this object.
            widget: The widget(s) to grab a screenshot of.
            message: Logbook entry message.
            activities: Logbook activities.
            server_url: Logbook server URL.
            rbac_token: RBAC token.
            chrome: Include the window chrome if widget is a QMainWindow.
        """
        super().__init__(parent)

        self.set_widget(widget)
        self.set_message(message)
        self.chrome = chrome

        self._client = Client(server_url=server_url, rbac_token='')
        self._ac_client = ActivitiesClient(client=self._client, activities=[])

        self.set_activities(activities)
        self.set_rbac_token(rbac_token)

        self.menu = LogbookMenu(self._ac_client, parent=self)
        self.menu.setToolTipsVisible(True)
        self.setMenu(self.menu)
        self.menu.capture.connect(partial(self._screenshot_after_delay, True))
        self.menu.capture_failed.connect(self.capture_failed.emit)

        self.setPopupMode(QToolButton.MenuButtonPopup)

        self.setIcon(make_icon(Path(__file__).parent.absolute() / 'icons' / 'eLogbook.png'))

        self.clicked.connect(self._screenshot_after_delay)

    def _screenshot_after_delay(self, checked: bool, event_id: Optional[int] = None):
        """
        Wait for a short delay before grabbing the screenshot to allow
        time for the pop-up menu to close,
        """
        QTimer.singleShot(100, partial(self._screenshot, event_id))

    def _screenshot(self, event_id: Optional[int] = None):
        """
        Grab a screenshot of the widget(s) and post them to the logbook.
        """
        try:
            if event_id is None:
                if self.message is None:
                    message, ok = QInputDialog.getText(self, 'Logbook', 'Enter a logbook message:')
                else:
                    message = self.message
                if not message:
                    raise ValueError('Logbook message cannot be empty')
                event = self._ac_client.add_event(message)
            else:
                event = self._client.get_event(event_id)

            if self.widgets is not None:
                for i, widget in enumerate(self.widgets):
                    if isinstance(widget, QMainWindow) and self.chrome:
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
                    screenshot.save(screenshot_buffer, 'png', quality=100)
                    event.attach_content(contents=screenshot_bytes,
                                         mime_type='image/png',
                                         name='capture_{0}.png'.format(i))

            self.capture_succeeded.emit(event.event_id)
        except (LogbookError, ValueError) as e:
            self.capture_failed.emit(str(e))

    def set_message(self, message: Optional[str] = None):
        """
        Set the logbook entry message.

        Args:
            message: The message to use for the logbook entry.
        """
        self.message = message

    def set_widget(self, widget: Optional[Union[QWidget, List[QWidget]]] = None):
        """
        Set the widget(s) to post a screenshot of.

        Args:
            widget: Widget (or list of widgets).
        """
        if isinstance(widget, QWidget):
            self.widgets = [widget]
        else:
            self.widgets = widget

    def set_rbac_token(self, rbac_token: Token):
        """
        Set the RBAC token.

        Args:
            rbac_token: RBAC token.
        """
        self._client.rbac_b64_token = '' if rbac_token is None else rbac_token
        self._update_activities()
        self._update_tooltip()
        self._update_enabled()

    def clear_rbac_token(self):
        """
        Clear the RBAC token.
        """
        self._client.rbac_b64_token = ''
        self._update_tooltip()
        self._update_enabled()

    def activities(self) -> List[Activity]:
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
        self._activities = [] if activities is None else activities
        self._update_activities()
        self._update_tooltip()
        self._update_enabled()

    def _update_activities(self):
        """
        Update the activities in the ActivitiesClient.
        """
        if self._rbac_token_valid() and self._activities is not None:
            self._ac_client.activities = self._activities
            self._activities = None

    def _rbac_token_valid(self):
        """
        Check if the RBAC token is not empty.
        """
        return self._client.rbac_b64_token != ''

    def _update_tooltip(self):
        """
        Update the button tooltip.
        """
        if not self._rbac_token_valid():
            self.setToolTip('ERROR: RBAC login is required to write to the e-logbook')
        elif not self.activities():
            self.setToolTip('ERROR: No e-logbook activity is defined')
        else:
            activities = '/'.join([a.name for a in self.activities()])
            self.setToolTip('Capture screenshot to a new entry in {0} e-logbook'.format(activities))

    def _update_enabled(self):
        """
        Update the button enabled status.
        """
        if self.activities() and self._rbac_token_valid():
            self.setEnabled(True)
        else:
            self.setDisabled(True)


class LogbookMenu(QMenu):
    capture = Signal(int)
    capture_failed = Signal(str)

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

    def showEvent(self, event: QEvent):
        """
        Override of the menu show event to populate it with the latest
        Logbook entries. The Logbook API doesn't offer a good way to
        keep a local model synchronised with the server, so this just
        refetches the latest entries each time.
        """
        events = []
        try:
            # Note: specifying a `from_date` improves performance
            start = datetime.datetime.now() - datetime.timedelta(days=1)
            events_pages = self._client.get_events(from_date=start)
            events_pages.page_size = 10
            events_count = events_pages.count
            events = events_pages.get_page(0)
        except LogbookError as e:
            self.capture_failed.emit(str(e))

        self.clear()

        if events_count > 0:
            activities = '/'.join([a.name for a in self._client.activities])
            for e in events:
                action = QAction('id: {0} @ {1:%H:%M:%S}'.format(str(e.event_id)[-3:], e.date), self)
                action.triggered.connect(partial(self.capture.emit, e.event_id))
                action.setToolTip('Capture screenshot to existing entry {0} in {1} e-logbook'.format(e.event_id,
                                                                                                     activities))
                self.addAction(action)
        else:
            action = QAction('(no events)', self)
            self.addAction(action)

        super().showEvent(event)
