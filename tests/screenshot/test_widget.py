import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QAction, QWidget, QToolButton
from accwidgets.screenshot import ScreenshotButton, ScreenshotAction, LogbookModel
from .fixtures import *  # noqa: F401,F403


class CustomAction(QAction):
    pass


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_type", [None, QWidget])
def test_init(qtbot: QtBot, logbook_model, parent_type):
    parent = None if parent_type is None else parent_type()
    widget = ScreenshotButton(action=ScreenshotAction(model=logbook_model),
                              parent=parent)
    qtbot.add_widget(widget)
    assert widget.popupMode() == QToolButton.MenuButtonPopup
    assert widget.parent() is parent


@pytest.mark.asyncio
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_init_with_implicit_action(_, qtbot: QtBot):
    widget = ScreenshotButton()
    qtbot.add_widget(widget)
    assert isinstance(widget.defaultAction(), ScreenshotAction)
    assert widget.defaultAction().parent() is widget
    assert widget.defaultAction().receivers(widget.defaultAction().capture_finished) > 0
    assert widget.defaultAction().receivers(widget.defaultAction().capture_failed) > 0
    assert widget.defaultAction().receivers(widget.defaultAction().event_fetch_failed) > 0
    assert widget.defaultAction().receivers(widget.defaultAction().model_changed) > 0


@pytest.mark.asyncio
def test_init_provided_action_retains_parent(qtbot: QtBot, logbook_model):
    another_parent = QWidget()
    qtbot.add_widget(another_parent)
    widget = ScreenshotButton(action=ScreenshotAction(model=logbook_model, parent=another_parent))
    qtbot.add_widget(widget)
    assert widget.defaultAction().parent() is another_parent


@pytest.mark.asyncio
def test_set_default_action_provided_action_retains_parent(qtbot: QtBot, logbook_model, qapp):
    # Using qapp as parent to avoid premature action destruction in tests which causes segfault
    widget = ScreenshotButton(action=ScreenshotAction(model=logbook_model, parent=qapp))
    qtbot.add_widget(widget)
    assert widget.defaultAction().parent() is qapp
    another_parent = QWidget()
    qtbot.add_widget(another_parent)
    action = ScreenshotAction(model=logbook_model, parent=another_parent)
    widget.setDefaultAction(action)
    assert action.parent() is another_parent


@pytest.mark.asyncio
def test_set_default_action_disconnects_old_action(qtbot: QtBot, logbook_model, qapp):
    old_action = ScreenshotAction(model=logbook_model, parent=qapp)
    widget = ScreenshotButton(action=old_action)
    qtbot.add_widget(widget)
    assert old_action.receivers(old_action.capture_finished) > 0
    assert old_action.receivers(old_action.capture_failed) > 0
    assert old_action.receivers(old_action.event_fetch_failed) > 0
    assert old_action.receivers(old_action.model_changed) > 0
    widget.setDefaultAction(ScreenshotAction(model=logbook_model))
    assert old_action.receivers(old_action.capture_finished) == 0
    assert old_action.receivers(old_action.capture_failed) == 0
    assert old_action.receivers(old_action.event_fetch_failed) == 0
    assert old_action.receivers(old_action.model_changed) == 0


@pytest.mark.asyncio
def test_set_default_action_connects_new_action(qtbot: QtBot, logbook_model, qapp):
    widget = ScreenshotButton(action=ScreenshotAction(model=logbook_model, parent=qapp))
    qtbot.add_widget(widget)
    action = ScreenshotAction(model=logbook_model)
    assert action.receivers(action.capture_finished) == 0
    assert action.receivers(action.capture_failed) == 0
    assert action.receivers(action.event_fetch_failed) == 0
    assert action.receivers(action.model_changed) == 0
    widget.setDefaultAction(action)
    assert action.receivers(action.capture_finished) > 0
    assert action.receivers(action.capture_failed) > 0
    assert action.receivers(action.event_fetch_failed) > 0
    assert action.receivers(action.model_changed) > 0


@pytest.mark.parametrize("prev_type,new_type,expect_signal", [
    (QAction, QAction, False),
    (QAction, CustomAction, False),
    (CustomAction, QAction, False),
    (CustomAction, CustomAction, False),
    (ScreenshotAction, QAction, True),
    (QAction, ScreenshotAction, True),
    (ScreenshotAction, ScreenshotAction, True),
    (CustomAction, ScreenshotAction, True),
    (ScreenshotAction, CustomAction, True),
])
def test_set_default_action_fires_model_change_signal(qtbot: QtBot, qapp, prev_type, new_type, expect_signal, logbook):

    def make_action(action_type):
        if action_type is ScreenshotAction:
            act = ScreenshotAction(model=LogbookModel(logbook=logbook), parent=qapp)
            qtbot.add_widget(act.menu())
            return act
        return action_type()

    widget = ScreenshotButton(action=make_action(prev_type))
    qtbot.add_widget(widget)
    with qtbot.wait_signal(widget.modelChanged, raising=False, timeout=100) as blocker:
        widget.setDefaultAction(make_action(new_type))
    assert blocker.signal_triggered == expect_signal


@pytest.mark.parametrize("widget_prop_name,action_prop_name,new_val", [
    ("maxMenuDays", "max_menu_days", -1),
    ("maxMenuDays", "max_menu_days", 0),
    ("maxMenuDays", "max_menu_days", 1),
    ("maxMenuDays", "max_menu_days", 10),
    ("maxMenuDays", "max_menu_days", 54364),
    ("maxMenuEntries", "max_menu_entries", -1),
    ("maxMenuEntries", "max_menu_entries", 0),
    ("maxMenuEntries", "max_menu_entries", 1),
    ("maxMenuEntries", "max_menu_entries", 10),
    ("maxMenuEntries", "max_menu_entries", 54364),
    ("includeWindowDecorations", "include_window_decorations", True),
    ("includeWindowDecorations", "include_window_decorations", False),
    ("source", "source", QWidget),
])
def test_scalar_prop_with_proper_action(qtbot: QtBot, logbook_model, new_val, widget_prop_name, action_prop_name):
    action = ScreenshotAction(model=logbook_model)
    widget = ScreenshotButton(action=action)
    qtbot.add_widget(widget)
    expected_val = new_val
    if new_val is QWidget:
        new_val = QWidget()
        qtbot.add_widget(new_val)
        expected_val = [new_val]
    assert getattr(widget, widget_prop_name) == getattr(action, action_prop_name)
    setattr(widget, widget_prop_name, new_val)
    assert getattr(widget, widget_prop_name) == getattr(action, action_prop_name) == expected_val


@pytest.mark.parametrize("prop_name,expected_value", [
    ("includeWindowDecorations", False),
    ("message", None),
])
@pytest.mark.parametrize("action_type", [QAction, CustomAction])
def test_prop_getter_succeeds_with_generic_action(qtbot: QtBot, action_type, prop_name, expected_value):
    widget = ScreenshotButton(action=action_type())
    qtbot.add_widget(widget)
    assert getattr(widget, prop_name) == expected_value


@pytest.mark.parametrize("prop_name", ["maxMenuDays", "maxMenuEntries", "source"])
@pytest.mark.parametrize("action_type,expected_error", [
    (QAction, "Cannot retrieve/update ScreenshotAction-related property on the action of type QAction"),
    (CustomAction, "Cannot retrieve/update ScreenshotAction-related property on the action of type CustomAction"),
])
def test_prop_getter_fails_with_generic_action(qtbot: QtBot, action_type, expected_error, prop_name):
    widget = ScreenshotButton(action=action_type())
    qtbot.add_widget(widget)
    with pytest.raises(AssertionError, match=expected_error):
        _ = getattr(widget, prop_name)


@pytest.mark.parametrize("prop_name,new_val", [
    ("maxMenuDays", 5),
    ("maxMenuEntries", 15),
    ("includeWindowDecorations", True),
    ("includeWindowDecorations", False),
    ("message", None),
    ("message", ""),
    ("message", "Test message"),
    ("source", QWidget),
])
@pytest.mark.parametrize("action_type,expected_error", [
    (QAction, "Cannot retrieve/update ScreenshotAction-related property on the action of type QAction"),
    (CustomAction, "Cannot retrieve/update ScreenshotAction-related property on the action of type CustomAction"),
])
def test_prop_setter_fails_with_generic_action(qtbot: QtBot, action_type, expected_error, prop_name, new_val):
    widget = ScreenshotButton(action=action_type())
    qtbot.add_widget(widget)
    if new_val is QWidget:
        new_val = QWidget()
        qtbot.add_widget(new_val)
    with pytest.raises(AssertionError, match=expected_error):
        setattr(widget, prop_name, new_val)
