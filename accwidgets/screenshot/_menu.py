import weakref
import functools
import qtawesome as qta
from typing import Optional, List
from datetime import datetime
from typing_extensions import Protocol, runtime_checkable
from qtpy.QtWidgets import QMenu, QWidget, QAction
from qtpy.QtCore import Signal
from qtpy.QtGui import QShowEvent, QPalette
from pylogbook.models import Event
from ._common import make_activities_summary, make_new_entry_tooltip
from ._model import LogbookModel


@runtime_checkable
class LogbookModelProviderProtocol(Protocol):
    model: LogbookModel
    message: Optional[str]
    max_menu_entries: int
    max_menu_days: int


class LogbookMenu(QMenu):

    event_clicked = Signal(int)
    """
    Signal when a menu entry has been clicked. The argument is the e-logbook event ID. This argument will be -1
    for the new entry creation.
    """

    event_fetch_failed = Signal(str)
    """Notification of the problem retrieving events from the e-logbook. The argument is the error message."""

    def __init__(self,
                 model_provider: LogbookModelProviderProtocol,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._model_provider = weakref.ref(model_provider)

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
        model_provider = self._model_provider()
        if not model_provider:
            return make_fallback_actions("(can't retrieve events)", self)

        text = "Create new entry"
        if not model_provider.message:
            # User interaction will be required (to enter message), emphasize with ellipsis
            text = f"{text}…"
        new_action = QAction(text, self)
        new_action.setIcon(qta.icon("fa.plus", color=self.palette().color(QPalette.Text)))
        new_action.triggered.connect(functools.partial(self.event_clicked.emit, -1))
        new_action.setToolTip(make_new_entry_tooltip(model_provider.model))
        sep = QAction(self)
        sep.setSeparator(True)
        actions = [new_action, sep]

        logbook_events = model_provider.model.get_logbook_events(past_days=model_provider.max_menu_days,
                                                                 max_events=model_provider.max_menu_entries)

        if len(logbook_events) > 0:
            activities_summary = make_activities_summary(model_provider.model)

            today = datetime.now()
            today = today.replace(hour=0,
                                  minute=0,
                                  second=0,
                                  microsecond=0)

            def map_event(event: Event):
                action = QAction(make_menu_title(event=event, today=today), self)
                action.triggered.connect(functools.partial(self.event_clicked.emit, event.event_id))
                action.setToolTip(f"Capture screenshot to existing entry {event.event_id} "
                                  f"in {activities_summary} e-logbook")
                return action

            actions.extend(map(map_event, logbook_events))
        else:
            actions.extend(make_fallback_actions("(no events)", self))

        return actions


def make_fallback_actions(msg: str, parent: QWidget) -> List[QAction]:
    fallback_action = QAction(msg, parent)
    fallback_action.setEnabled(False)
    return [fallback_action]


def make_menu_title(event: Event, today: datetime) -> str:
    date = event.date.strftime("%T")
    compared = event.date.replace(hour=0,
                                  minute=0,
                                  second=0,
                                  microsecond=0)
    diff = today - compared
    suffix: Optional[str]
    if diff.days == 1:
        suffix = "yesterday"
    elif diff.days != 0:
        suffix = event.date.strftime("%b %d")
    else:
        suffix = None
    if suffix is not None:
        date = f"{date} ({suffix})"
    return f"id: {event.event_id!s} @ {date}"
