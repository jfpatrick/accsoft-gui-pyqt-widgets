import pytest
from unittest import mock
from typing import Optional, Callable
from asyncio import CancelledError
from datetime import datetime
from dateutil.tz import UTC
from pytestqt.qtbot import QtBot
from qtpy.QtCore import QPoint, QObject
from qtpy.QtWidgets import QAction, QWidget
from pylogbook.models import Event
from pylogbook.exceptions import LogbookError
from accwidgets.screenshot import LogbookModel
from accwidgets.screenshot._menu import (make_fallback_actions, LogbookMenu, make_menu_title, LoadingAction,
                                         ActivityIndicatorWrapper, map_event_action)
from ..async_shim import AsyncMock


@pytest.fixture
def model_provider():

    def _wrapper(message: str):
        provider = mock.MagicMock()
        provider.message = message
        provider.model = mock.MagicMock(spec=LogbookModel)
        provider.max_menu_days = 1
        provider.max_menu_entries = 10
        return provider

    return _wrapper


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_message,expected_first_text", [
    (None, "Create new entry…"),
    ("", "Create new entry…"),
    ("Test message", "Create new entry"),
])
@mock.patch("accwidgets.screenshot._menu.make_new_entry_tooltip", return_value="")
def test_menu_populates_menu_with_loading_item_on_show(_, qtbot: QtBot, provider_message, expected_first_text,
                                                       model_provider):
    provider = model_provider(provider_message)
    menu = LogbookMenu(model_provider=provider)
    qtbot.add_widget(menu)

    assert len(menu.actions()) == 2
    assert menu.actions()[0].text() == ""
    assert not menu.actions()[0].isSeparator()
    assert menu.actions()[1].isSeparator()

    def simulate_show():
        with mock.patch.object(menu, "_fetch_event_actions", new_callable=AsyncMock) as fetch_mock:
            menu.popup(QPoint(0, 0))
            fetch_mock.assert_called_once()
            assert len(menu.actions()) == 3
            assert not isinstance(menu.actions()[0], LoadingAction)
            assert menu.actions()[0].text() == expected_first_text
            assert not menu.actions()[0].isSeparator()
            assert not isinstance(menu.actions()[1], LoadingAction)
            assert menu.actions()[1].isSeparator()
            assert isinstance(menu.actions()[2], LoadingAction)
        menu.hide()

    simulate_show()
    menu.removeAction(menu.actions()[-1])  # Delete dynamic action, later check that re-appears
    simulate_show()
    menu._cancel_running_tasks()


@pytest.mark.parametrize("message", ["", "Test message", "(no events)"])
@pytest.mark.parametrize("parent_type", [None, QWidget])
def test_menu_make_fallback_actions(message, parent_type, qtbot: QtBot):
    if parent_type is not None:
        parent = parent_type()
        qtbot.add_widget(parent)
    else:
        parent = None
    res = make_fallback_actions(msg=message, parent=parent)
    assert isinstance(res, list)
    assert len(res) == 1
    action = res[0]
    assert isinstance(action, QAction)
    assert action.isEnabled() is False
    assert action.text() == message


@pytest.mark.parametrize("event_date,expected_title", [
    (datetime(year=2020, day=1, month=1, hour=12, minute=30, second=55, tzinfo=UTC), "id: 123 @ 12:30:55"),
    (datetime(year=2020, day=1, month=1, hour=11, minute=30, second=55, tzinfo=UTC), "id: 123 @ 11:30:55"),
    (datetime(year=2020, day=1, month=1, hour=0, minute=30, second=0, tzinfo=UTC), "id: 123 @ 00:30:00"),
    (datetime(year=2020, day=1, month=1, hour=0, minute=0, second=0, tzinfo=UTC), "id: 123 @ 00:00:00"),
    (datetime(year=2019, day=31, month=12, hour=23, minute=59, second=59, tzinfo=UTC), "id: 123 @ 23:59:59 (yesterday)"),
    (datetime(year=2019, day=31, month=12, hour=12, minute=30, second=55, tzinfo=UTC), "id: 123 @ 12:30:55 (yesterday)"),
    (datetime(year=2019, day=31, month=12, hour=0, minute=0, second=0, tzinfo=UTC), "id: 123 @ 00:00:00 (yesterday)"),
    (datetime(year=2019, day=30, month=12, hour=23, minute=59, second=59, tzinfo=UTC), "id: 123 @ 23:59:59 (Dec 30)"),
    (datetime(year=2018, day=31, month=12, hour=23, minute=59, second=59, tzinfo=UTC), "id: 123 @ 23:59:59 (Dec 31)"),
    (datetime(year=2020, day=2, month=1, hour=0, minute=0, second=0, tzinfo=UTC), "id: 123 @ 00:00:00 (Jan 02)"),
    (datetime(year=2020, day=3, month=1, hour=0, minute=0, second=0, tzinfo=UTC), "id: 123 @ 00:00:00 (Jan 03)"),
])
def test_menu_make_menu_title(event_date, expected_title):
    event = mock.MagicMock()
    event.date = event_date
    event.event_id = "123"
    res = make_menu_title(event=event,
                          today=datetime(year=2020, day=1, month=1, hour=12, minute=30, second=55, tzinfo=UTC))
    assert res == expected_title


@pytest.mark.asyncio
def test_menu_cancels_async_task_on_hide(qtbot: QtBot):
    menu = LogbookMenu(model_provider=mock.MagicMock())
    qtbot.add_widget(menu)
    with mock.patch.object(menu, "_cancel_running_tasks") as cancel_running_tasks:
        # Empty coroutine to avoid putting the task to the event loop, which produces warning about coroutine
        # not awaited
        with mock.patch.object(menu, "_fetch_event_actions", new_callable=AsyncMock):
            menu.popup(QPoint(0, 0))
        cancel_running_tasks.assert_not_called()
        menu.hide()
        cancel_running_tasks.assert_called_once()
    menu._cancel_running_tasks()


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_message,expected_first_text", [
    (None, "Create new entry…"),
    ("", "Create new entry…"),
    ("Test message", "Create new entry"),
])
@pytest.mark.parametrize("events,expected_menu_count,expected_titles,expected_enabled", [
    ([], 3, ["(no events)"], [False]),
    ([1], 3, ["Event 1"], [True]),
    ([1, 2], 4, ["Event 1", "Event 2"], [True, True]),
])
@mock.patch("accwidgets.screenshot._menu.make_activities_summary", return_value="TEST")
def test_menu_updates_menu_after_successful_load(_, qtbot: QtBot, provider_message, expected_first_text,
                                                 events, expected_titles, expected_enabled, expected_menu_count,
                                                 model_provider, event_loop):
    def map_id_to_event(id: int):
        ev = mock.MagicMock(spec=Event)
        ev.event_id = id
        return ev

    provider = model_provider(provider_message)
    provider.model.get_logbook_events = AsyncMock(return_value=list(map(map_id_to_event, events)))

    menu = LogbookMenu(model_provider=provider)
    qtbot.add_widget(menu)

    # Empty coroutine to avoid putting the task to the event loop. However, we still want to trigger actions
    # for creating initial menu for "loading state".
    with mock.patch.object(menu, "_fetch_event_actions", new_callable=AsyncMock) as fetch_mock:
        menu.popup(QPoint(0, 0))
        fetch_mock.assert_called_once()

    returned_actions = {}
    for event_id in events:
        act = QAction(f"Event {event_id}")
        returned_actions[event_id] = act

    def action_side_effect(event, activities_summary, today, parent):
        _ = today, activities_summary, parent
        return returned_actions[event.event_id]

    # This is not the one called (from within showEvent) but we call it redundantly, so that we can explicitly await
    # in this test case, and assume it will populate menu as needed.
    # The fact that it's called from withing showEvent is checked above
    with mock.patch("accwidgets.screenshot._menu.map_event_action", side_effect=action_side_effect):
        # Note this test method is not async, because we would need to await for menu._fetch_event_actions()
        # For some unclear reason, combination of async test case with qtbot in certain order produces a very
        # opaque system error:
        #
        # Exceptions caught in Qt event loop:
        # ________________________________________________________________________________
        # StopIteration
        #
        # The above exception was the direct cause of the following exception:
        #
        # SystemError: <class 'PyQt5.QtGui.QWindow'> returned a result with an error set
        event_loop.run_until_complete(menu._fetch_event_actions())

    assert len(menu.actions()) == expected_menu_count
    assert menu.actions()[0].text() == expected_first_text
    assert not menu.actions()[0].isSeparator()
    assert menu.actions()[1].isSeparator()
    for expected_title, enabled, i in zip(expected_titles, expected_enabled, range(2, 2 + len(expected_titles))):
        action = menu.actions()[i]
        assert action.text() == expected_title
        assert action.isEnabled() == enabled
        assert not isinstance(action, LoadingAction)
    menu._cancel_running_tasks()


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_message,expected_first_text", [
    (None, "Create new entry…"),
    ("", "Create new entry…"),
    ("Test message", "Create new entry"),
])
@pytest.mark.parametrize("error", [ValueError("Test error"), LogbookError("Test error", response=mock.MagicMock())])
def test_menu_updates_menu_after_failure_to_load(qtbot: QtBot, provider_message, expected_first_text, error,
                                                 model_provider, event_loop):
    provider = model_provider(provider_message)
    provider.model.get_logbook_events = AsyncMock(side_effect=error)

    menu = LogbookMenu(model_provider=provider)
    qtbot.add_widget(menu)

    # Empty coroutine to avoid putting the task to the event loop. However, we still want to trigger actions
    # for creating initial menu for "loading state".
    with mock.patch.object(menu, "_fetch_event_actions", new_callable=AsyncMock) as fetch_mock:
        menu.popup(QPoint(0, 0))
        fetch_mock.assert_called_once()

    # This is not the one called (from within showEvent) but we call it redundantly, so that we can explicitly await
    # in this test case, and assume it will populate menu as needed.
    # The fact that it's called from withing showEvent is checked above
    with qtbot.wait_signal(menu.event_fetch_failed) as blocker:
        event_loop.run_until_complete(menu._fetch_event_actions())
    assert blocker.args == ["Test error"]

    assert len(menu.actions()) == 3
    assert menu.actions()[0].text() == expected_first_text
    assert not menu.actions()[0].isSeparator()
    assert menu.actions()[1].isSeparator()
    assert not menu.actions()[2].isEnabled()
    assert not isinstance(menu.actions()[2], LoadingAction)
    assert menu.actions()[2].text() == "Error occurred"
    menu._cancel_running_tasks()


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_message,expected_first_text", [
    (None, "Create new entry…"),
    ("", "Create new entry…"),
    ("Test message", "Create new entry"),
])
def test_menu_updates_menu_after_cancel_loading(qtbot: QtBot, provider_message, expected_first_text,
                                                model_provider, event_loop):
    provider = model_provider(provider_message)
    provider.model.get_logbook_events = AsyncMock(side_effect=CancelledError)

    menu = LogbookMenu(model_provider=provider)
    qtbot.add_widget(menu)

    # Empty coroutine to avoid putting the task to the event loop. However, we still want to trigger actions
    # for creating initial menu for "loading state".
    with mock.patch.object(menu, "_fetch_event_actions", new_callable=AsyncMock) as fetch_mock:
        menu.popup(QPoint(0, 0))
        fetch_mock.assert_called_once()

    # This is not the one called (from within showEvent) but we call it redundantly, so that we can explicitly await
    # in this test case, and assume it will populate menu as needed.
    # The fact that it's called from withing showEvent is checked above
    with qtbot.wait_signal(menu.event_fetch_failed, raising=False, timeout=100) as blocker:
        event_loop.run_until_complete(menu._fetch_event_actions())
    assert not blocker.signal_triggered

    assert len(menu.actions()) == 3
    assert menu.actions()[0].text() == expected_first_text
    assert not menu.actions()[0].isSeparator()
    assert menu.actions()[1].isSeparator()
    assert not menu.actions()[2].isEnabled()
    assert not isinstance(menu.actions()[2], LoadingAction)
    assert menu.actions()[2].text() == "(event retrieval cancelled)"
    menu._cancel_running_tasks()


@pytest.mark.asyncio
def test_menu_populates_menu_on_show_with_error_when_model_provider_is_not_found(qtbot: QtBot, event_loop):
    container = {"a": QObject()}
    menu = LogbookMenu(model_provider=container["a"])
    qtbot.add_widget(menu)
    container["a"].deleteLater()
    del container["a"]

    assert len(menu.actions()) == 2
    assert menu.actions()[0].text() == ""
    assert not menu.actions()[0].isSeparator()
    assert menu.actions()[1].isSeparator()

    with mock.patch("accwidgets.screenshot._menu.create_task") as create_task:
        # This is not the one called (from within showEvent) but we call it redundantly, so that we can explicitly await
        # in this test case, and assume it will populate menu as needed.
        # The fact that it's called from withing showEvent is checked above
        with qtbot.wait_signal(menu.event_fetch_failed, raising=False, timeout=100) as blocker:
            event_loop.run_until_complete(menu._fetch_event_actions())
        assert not blocker.signal_triggered
        create_task.assert_not_called()

    assert len(menu.actions()) == 3
    assert menu.actions()[0].text() == ""
    assert not menu.actions()[0].isSeparator()
    assert menu.actions()[1].isSeparator()
    assert not menu.actions()[2].isEnabled()
    assert not isinstance(menu.actions()[2], LoadingAction)
    assert menu.actions()[2].text() == "(can't retrieve events)"


def test_loading_action_create_widget(qtbot: QtBot, qapp):
    action = LoadingAction(qapp)
    parent = QWidget()
    qtbot.add_widget(parent)
    widget = action.createWidget(parent)
    qtbot.add_widget(widget)
    assert widget.parent() is parent
    assert isinstance(widget, ActivityIndicatorWrapper)


def test_activity_indicator_wrapper_init(qtbot: QtBot):
    widget = ActivityIndicatorWrapper()
    qtbot.add_widget(widget)
    assert widget.activity.hint == "Loading…"
    assert not widget.activity.animating


def test_activity_indicator_wrapper_stops_animation_on_destruction(qtbot: QtBot):
    orig_stop: Optional[Callable[[], None]] = None
    stop_mock = mock.Mock()

    def scope():
        nonlocal orig_stop
        widget = ActivityIndicatorWrapper()
        qtbot.add_widget(widget)
        orig_stop = widget.activity.stopAnimation
        widget.activity.stopAnimation = stop_mock

    stop_mock.assert_not_called()
    scope()
    stop_mock.assert_called_once()
    assert orig_stop is not None
    orig_stop()  # Cleanup


def test_activity_indicator_wrapper_stops_animation_on_hide(qtbot: QtBot):
    widget = ActivityIndicatorWrapper()
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.activity.animating
    widget.hide()
    assert not widget.activity.animating


def test_activity_indicator_wrapper_starts_animation_on_show(qtbot: QtBot):
    widget = ActivityIndicatorWrapper()
    qtbot.add_widget(widget)
    assert not widget.activity.animating
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.activity.animating


@pytest.mark.parametrize("event_id,activities,expected_tooltip", [
    (1, "TEST", "Capture screenshot to existing entry <b>1</b> in <i>TEST</i> e-logbook"),
    (145864, "TEST", "Capture screenshot to existing entry 145<b>864</b> in <i>TEST</i> e-logbook"),
    (145864, "LINAC4/LHC", "Capture screenshot to existing entry 145<b>864</b> in <i>LINAC4/LHC</i> e-logbook"),
])
@mock.patch("accwidgets.screenshot._menu.make_menu_title", return_value="Action title")
def test_map_event_action(_, qtbot: QtBot, event_id, activities, expected_tooltip, model_provider):
    menu = LogbookMenu(model_provider=model_provider(""))
    qtbot.add_widget(menu)
    event = mock.MagicMock()
    event.event_id = event_id
    action = map_event_action(event=event, activities_summary=activities, today=datetime.now(), parent=menu)
    assert action.text() == "Action title"
    assert action.toolTip() == expected_tooltip
    assert action.receivers(action.triggered) > 0
