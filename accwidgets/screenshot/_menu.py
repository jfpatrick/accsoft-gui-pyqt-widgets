import datetime
import operator
import functools
from typing import Optional, List
from qtpy.QtWidgets import QMenu, QWidget, QAction
from qtpy.QtCore import Signal
from qtpy.QtGui import QShowEvent
from pylogbook import ActivitiesClient
from pylogbook.models import Event


class LogbookMenu(QMenu):

    event_clicked = Signal(int)
    """
    Signal when a menu entry has been clicked. The argument is the e-logbook event ID. This argument will be -1
    for the new entry creation.
    """

    event_fetch_failed = Signal(str)
    """Notification of the problem retrieving events from the e-logbook. The argument is the error message."""

    def __init__(self,
                 client: ActivitiesClient,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._client = client

    def showEvent(self, event: QShowEvent):
        # The Logbook API doesn't offer a good way to
        # keep a local model synchronised with the server, so this just
        # re-fetches the latest entries each time.
        try:
            actions = self._build_event_actions()
        except Exception as e:  # noqa: B902
            self.event_fetch_failed.emit(str(e))
            actions = make_fallback_actions("Error occurred (see log output for details)", self)

        # We must clear here, and must NOT clear in hideEvent, because actions will be destroyed before they trigger
        self.clear()
        self.addActions(actions)
        super().showEvent(event)

    def _build_event_actions(self) -> List[QAction]:
        # Note: specifying a `from_date` improves performance
        start = datetime.datetime.now() - datetime.timedelta(days=1)
        events_pages = self._client.get_events(from_date=start)
        events_pages.page_size = 10
        events_count = events_pages.count
        logbook_events = events_pages.get_page(0)

        if events_count > 0:
            activities_summary = "/".join(map(operator.attrgetter("name"), self._client.activities))

            def map_event(event: Event):
                event_id = str(event.event_id)[-3:]
                date = event.date.strftime("%T")
                action = QAction(f"id: {event_id} @ {date}", self)
                action.triggered.connect(functools.partial(self.event_clicked.emit, event.event_id))
                action.setToolTip(f"Capture screenshot to existing entry {event.event_id} "
                                  f"in {activities_summary} e-logbook")
                return action

            return list(map(map_event, logbook_events))

        return make_fallback_actions("(no events)", self)


def make_fallback_actions(msg: str, parent: QWidget) -> List[QAction]:
    fallback_action = QAction(msg, parent)
    fallback_action.setEnabled(False)
    return [fallback_action]
