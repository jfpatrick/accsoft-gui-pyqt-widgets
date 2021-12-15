import pytest
from typing import List
from unittest import mock
from datetime import datetime
from dateutil.tz import UTC
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QAction, QWidget
from qtpy.QtGui import QShowEvent, QHideEvent
from accwidgets.screenshot._menu import make_fallback_actions, LogbookMenu, make_menu_title


@pytest.mark.parametrize("fetch1", [[], ["entry1"], ["entry1", "entry2"]])
@pytest.mark.parametrize("fetch2", [[], ["entry1"], ["entry1", "entry2"]])
def test_menu_populates_menu_on_show(qtbot: QtBot, fetch1, fetch2):
    menu = LogbookMenu(model_provider=mock.MagicMock())
    qtbot.add_widget(menu)

    def make_list(entries: List[str]) -> List[QAction]:

        def mapping(entry: str) -> QAction:
            return QAction(entry, menu)

        return list(map(mapping, entries))

    # We are not using qtbot.wait_exposed with menu.show() because QMenu
    # fails to properly show without parent window and times out
    # we are interested solely in showEvent logic anyway.
    actions = make_list(fetch1)
    with mock.patch.object(menu, "_build_event_actions", return_value=actions):
        menu.showEvent(QShowEvent())
        assert menu.actions() == actions

    menu.hideEvent(QHideEvent())
    actions = make_list(fetch2)
    with mock.patch.object(menu, "_build_event_actions", return_value=actions):
        menu.showEvent(QShowEvent())
        assert menu.actions() == actions


@pytest.mark.parametrize("message", ["", "Test message", "(no events)"])
@pytest.mark.parametrize("parent_type", [None, QWidget])
def test_make_fallback_actions(message, parent_type, qtbot: QtBot):
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
