import weakref
import functools
import qtawesome as qta
from asyncio import Future, CancelledError
try:
    from asyncio import create_task
except ImportError:
    from asyncio import ensure_future as create_task  # type: ignore
from typing import Optional, List, Iterable
from datetime import datetime
from typing_extensions import Protocol, runtime_checkable
from qtpy.QtWidgets import QMenu, QWidget, QAction, QWidgetAction, QHBoxLayout
from qtpy.QtCore import Signal, QObject
from qtpy.QtGui import QShowEvent, QPalette, QHideEvent
from pylogbook.models import Event
from accwidgets.qt import ActivityIndicator
from accwidgets._async_utils import install_asyncio_event_loop
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
        self._active_logbook_task: Optional[Future] = None
        install_asyncio_event_loop()
        self._create_persistent_actions()

    def showEvent(self, event: QShowEvent):
        # The Logbook API doesn't offer a good way to
        # keep a local model synchronised with the server, so this just
        # re-fetches the latest entries each time (asynchronously).
        action = LoadingAction(self)
        action.setEnabled(False)
        self._update_new_action_with_latest_model()
        self._set_menu_actions([action])
        create_task(self._fetch_event_actions())
        super().showEvent(event)

    def hideEvent(self, event: QHideEvent):
        super().hideEvent(event)
        self._cancel_running_tasks()

    def _update_new_action_with_latest_model(self):
        model_provider = self._model_provider()
        if not model_provider:
            return
        new_action = self.actions()[0]
        new_action.setIcon(qta.icon("fa.plus", color=self.palette().color(QPalette.Text)))
        new_action.setToolTip(make_new_entry_tooltip(model_provider.model))
        text = "Create new entry"
        interactive = not model_provider.message
        if interactive:
            # User interaction will be required (to enter message), emphasize with ellipsis
            text = f"{text}…"
        new_action.setText(text)

    def _create_persistent_actions(self):
        new_action = QAction(self)
        new_action.triggered.connect(functools.partial(self.event_clicked.emit, -1))
        sep = QAction(self)
        sep.setSeparator(True)
        self.addActions([new_action, sep])

    def _clear_dynamic_actions(self):
        actions = self.actions()
        for i in reversed(range(2, len(self.actions()))):
            self.removeAction(actions[i])

    def _set_menu_actions(self, dynamic_actions: Iterable[QAction]):
        self._clear_dynamic_actions()
        self.addActions(dynamic_actions)

    async def _fetch_event_actions(self):
        model_provider = self._model_provider()
        if not model_provider:
            self._set_menu_actions(make_fallback_actions("(can't retrieve events)", self))
            return

        self._active_logbook_task = create_task(
            model_provider.model.get_logbook_events(past_days=model_provider.max_menu_days,
                                                    max_events=model_provider.max_menu_entries),
        )
        try:
            logbook_events = await self._active_logbook_task
        except CancelledError:
            actions = make_fallback_actions("(event retrieval cancelled)", self)
        except Exception as e:  # noqa: B902
            self.event_fetch_failed.emit(str(e))
            actions = make_fallback_actions("Error occurred", self)
        else:
            if len(logbook_events) > 0:
                activities_summary = make_activities_summary(model_provider.model)

                today = datetime.now()
                today = today.replace(hour=0,
                                      minute=0,
                                      second=0,
                                      microsecond=0)

                actions = map(functools.partial(map_event_action,
                                                activities_summary=activities_summary,
                                                today=today,
                                                parent=self),
                              logbook_events)
            else:
                actions = make_fallback_actions("(no events)", self)

        self._set_menu_actions(actions)

    def _cancel_running_tasks(self):
        if self._active_logbook_task is not None:
            self._active_logbook_task.cancel()
            self._active_logbook_task = None

    def __del__(self):
        self._cancel_running_tasks()


class LoadingAction(QWidgetAction):

    def createWidget(self, parent: QWidget):
        widget = ActivityIndicatorWrapper(parent)
        widget.setEnabled(False)
        return widget


class ActivityIndicatorWrapper(QWidget):

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        activity = ActivityIndicator(self)
        activity.setHint("Loading…")
        self.activity = activity
        layout = QHBoxLayout()
        layout.addWidget(activity)
        layout.addStretch()
        self.setLayout(layout)

    def showEvent(self, event: QShowEvent):
        self.activity.startAnimation()
        super().showEvent(event)

    def hideEvent(self, event: QHideEvent):
        super().hideEvent(event)
        self.activity.stopAnimation()

    def __del__(self):
        self.activity.stopAnimation()


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


def map_event_action(event: Event, activities_summary: str, today: datetime, parent: LogbookMenu):
    action = QAction(make_menu_title(event=event, today=today), parent)
    action.triggered.connect(functools.partial(parent.event_clicked.emit, event.event_id))
    regular_id = str(event.event_id)[:-3]
    bold_id = str(event.event_id)[-3:]
    action.setToolTip(f"Capture screenshot to existing entry {regular_id}<b>{bold_id}</b> "
                      f"in <i>{activities_summary}</i> e-logbook")
    return action
