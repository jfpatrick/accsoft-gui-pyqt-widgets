import pytest
from typing import List
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QAction, QWidget
from qtpy.QtGui import QShowEvent, QHideEvent
from accwidgets.screenshot._menu import make_fallback_actions, LogbookMenu


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
