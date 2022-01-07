import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtCore import QObject
from qtpy.QtWidgets import QToolButton, QWidget, QMainWindow, QMenuBar
from pylogbook.models import Activity
from pylogbook.exceptions import LogbookError
from accwidgets.rbac import RbaButton
from accwidgets.screenshot import LogbookModel, ScreenshotAction
from accwidgets.screenshot._menu import LogbookMenu
from .fixtures import *  # noqa: F401,F403
from ..async_shim import AsyncMock


@pytest.mark.parametrize("parent_type", [None, QObject])
def test_init(parent_type, qtbot: QtBot, logbook_model):
    parent = None if parent_type is None else parent_type()
    action = ScreenshotAction(model=logbook_model,
                              parent=parent)
    qtbot.add_widget(action.menu())
    assert isinstance(action.menu(), LogbookMenu)
    assert action.parent() is parent
    assert action.isEnabled() is False
    assert action.toolTip() == "ERROR: Source widget(s) for screenshot is undefined"


@mock.patch("accwidgets.screenshot._model.Client")
@mock.patch("accwidgets.screenshot._model.ActivitiesClient")
def test_init_connects_implicit_model(_, __, qtbot: QtBot):
    action = ScreenshotAction()
    qtbot.add_widget(action.menu())
    assert action.model.receivers(action.model.rbac_token_changed) > 0
    assert action.model.receivers(action.model.activities_changed) > 0


def test_init_connects_provided_model(qtbot: QtBot, logbook):
    model = LogbookModel(logbook=logbook)
    assert model.receivers(model.rbac_token_changed) == 0
    assert model.receivers(model.activities_changed) == 0
    action = ScreenshotAction(model=model)
    qtbot.add_widget(action.menu())
    assert model.receivers(model.rbac_token_changed) > 0
    assert model.receivers(model.activities_changed) > 0


def test_set_model_changes_ownership(qtbot: QtBot, logbook):
    action = ScreenshotAction(model=LogbookModel(logbook=logbook))
    qtbot.add_widget(action.menu())
    model = LogbookModel(logbook=logbook)
    assert model.parent() is not action
    action.model = model
    assert model.parent() is action


def test_set_model_updates_ui(qtbot: QtBot, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    with mock.patch.object(action, "setToolTip") as setToolTip:
        with mock.patch.object(action, "setEnabled") as setEnabled:
            action.model = mock.MagicMock()
            setToolTip.assert_called_once()
            setEnabled.assert_called_once()


def test_set_model_disconnects_old_model(qtbot: QtBot, logbook):
    model = LogbookModel(logbook=logbook)
    action = ScreenshotAction(model=model)
    qtbot.add_widget(action.menu())
    assert model.receivers(model.rbac_token_changed) > 0
    assert model.receivers(model.activities_changed) > 0
    action.model = LogbookModel(logbook=logbook)
    assert model.receivers(model.rbac_token_changed) == 0
    assert model.receivers(model.activities_changed) == 0


def test_set_model_connects_new_model(qtbot: QtBot, logbook, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    model = LogbookModel(logbook=logbook)
    assert model.receivers(model.rbac_token_changed) == 0
    assert model.receivers(model.activities_changed) == 0
    action.model = model
    assert model.receivers(model.rbac_token_changed) > 0
    assert model.receivers(model.activities_changed) > 0


@pytest.mark.parametrize("belongs_to_action,should_destroy", [
    (True, True),
    (False, False),
])
def test_destroys_old_model_when_disconnecting(qtbot: QtBot, belongs_to_action, should_destroy, logbook, logbook_model):
    model = LogbookModel(logbook=logbook)
    action = ScreenshotAction(model=model)
    qtbot.add_widget(action.menu())
    assert model.parent() is action
    random_parent = QObject()
    if not belongs_to_action:
        model.setParent(random_parent)

    with mock.patch.object(model, "deleteLater") as deleteLater:
        action.model = logbook_model
        if should_destroy:
            deleteLater.assert_called_once()
            assert model.parent() is None
        else:
            deleteLater.assert_not_called()
            assert model.parent() is random_parent


@pytest.mark.parametrize("new_val", [None, "", " ", "Test message"])
def test_message_prop(logbook_model, new_val, qtbot: QtBot):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    assert action.message is None
    action.message = new_val
    assert action.message == new_val


@pytest.mark.parametrize("is_iterable,iterable_count", [
    (False, None),
    (True, 0),
    (True, 1),
    (True, 5),
])
def test_source_prop(logbook_model, is_iterable, iterable_count, qtbot: QtBot):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    assert action.source == []
    widget = QWidget()
    qtbot.add_widget(widget)
    if is_iterable:
        new_val = [widget] * iterable_count
        expected_val = new_val
    else:
        new_val = widget
        expected_val = [widget]
    action.source = new_val
    assert action.source == expected_val


@pytest.mark.parametrize("new_val", [True, False])
def test_include_window_decorations_prop(logbook_model, new_val, qtbot: QtBot):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    assert action.include_window_decorations is True
    action.include_window_decorations = new_val
    assert action.include_window_decorations == new_val


@pytest.mark.parametrize("new_val", [-1, 0, 1, 10, 54364])
def test_max_menu_entries_prop(logbook_model, new_val, qtbot: QtBot):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    assert action.max_menu_entries == 10
    action.max_menu_entries = new_val
    assert action.max_menu_entries == new_val


@pytest.mark.parametrize("new_val", [-1, 0, 1, 10, 54364])
def test_max_menu_days_prop(logbook_model, new_val, qtbot: QtBot):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    assert action.max_menu_days == 1
    action.max_menu_days = new_val
    assert action.max_menu_days == new_val


@pytest.mark.asyncio
@pytest.mark.parametrize("max_days", [1, 3])
@pytest.mark.parametrize("max_entries", [1, 5, 10])
def test_max_menu_props_affect_menu_on_show(max_days, max_entries, logbook_model, qtbot: QtBot, event_loop):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    action.max_menu_entries = max_entries
    action.max_menu_days = max_days
    logbook_model.get_logbook_events = AsyncMock(return_value=[])
    # This task is presumed to be launched from show event, tested in test_menu.py
    event_loop.run_until_complete(action.menu()._fetch_event_actions())
    logbook_model.get_logbook_events.assert_awaited_once_with(past_days=max_days,
                                                              max_events=max_entries)


@pytest.mark.parametrize("previously_connected,expect_initially_connected", [
    (True, True),
    (False, False),
])
def test_connect_rbac(logbook, previously_connected, qtbot: QtBot, expect_initially_connected):
    client, _ = logbook
    action = ScreenshotAction(model=LogbookModel(logbook=logbook))
    qtbot.add_widget(action.menu())
    btn = RbaButton()
    qtbot.add_widget(btn)
    if previously_connected:
        action.connect_rbac(btn)
    if expect_initially_connected:
        assert btn.receivers(btn.loginSucceeded) > 0
        assert btn.receivers(btn.logoutFinished) > 0
        assert btn.receivers(btn.tokenExpired) > 0
    else:
        assert btn.receivers(btn.loginSucceeded) == 0
        assert btn.receivers(btn.logoutFinished) == 0
        assert btn.receivers(btn.tokenExpired) == 0
    action.connect_rbac(btn)
    assert btn.receivers(btn.loginSucceeded) > 0
    assert btn.receivers(btn.logoutFinished) > 0
    assert btn.receivers(btn.tokenExpired) > 0

    # Check RbaButton deleting rbac affects model
    assert client.rbac_b64_token == ""
    client.rbac_b64_token = "abc123"
    with qtbot.wait_signal(btn.logoutFinished):
        btn.logoutFinished.emit()
    assert client.rbac_b64_token == ""


@pytest.mark.parametrize("previously_connected,expect_initially_connected", [
    (True, True),
    (False, False),
])
def test_disconnect_rbac(logbook_model, previously_connected, qtbot: QtBot, expect_initially_connected):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    btn = RbaButton()
    qtbot.add_widget(btn)
    if previously_connected:
        action.connect_rbac(btn)
    if expect_initially_connected:
        assert btn.receivers(btn.loginSucceeded) > 0
        assert btn.receivers(btn.logoutFinished) > 0
        assert btn.receivers(btn.tokenExpired) > 0
    else:
        assert btn.receivers(btn.loginSucceeded) == 0
        assert btn.receivers(btn.logoutFinished) == 0
        assert btn.receivers(btn.tokenExpired) == 0
    action.disconnect_rbac(btn)
    assert btn.receivers(btn.loginSucceeded) == 0
    assert btn.receivers(btn.logoutFinished) == 0
    assert btn.receivers(btn.tokenExpired) == 0


def test_sets_window_as_source_on_show_when_none_inside_app_menu(qtbot: QtBot, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    window = QMainWindow()
    qtbot.add_widget(window)
    menu_bar = QMenuBar()
    qtbot.add_widget(menu_bar)
    menu = menu_bar.addMenu("Logbook")
    menu.addAction(action)
    window.setMenuBar(menu_bar)
    assert action.source == []
    with qtbot.wait_exposed(window):
        window.show()
    assert action.source == [window]


def test_sets_window_as_source_on_show_when_none_inside_parent_widget(qtbot: QtBot, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    window = QMainWindow()
    qtbot.add_widget(window)
    parent = QToolButton()
    qtbot.add_widget(parent)
    parent.setDefaultAction(action)
    action.setParent(parent)
    window.setCentralWidget(parent)
    assert action.source == []
    with qtbot.wait_exposed(window):
        window.show()
    assert action.source == [window]


def test_does_not_set_anything_as_source_on_show_when_no_window_exists(qtbot: QtBot, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    parent = QToolButton()
    qtbot.add_widget(parent)
    parent.setDefaultAction(action)
    action.setParent(parent)
    assert action.source == []
    with qtbot.wait_exposed(parent):
        parent.show()
    assert action.source == []


def test_default_trigger_takes_screenshot_to_new_event(qtbot: QtBot, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    with mock.patch.object(action, "_take_screenshot") as take_screenshot:
        action.trigger()
        qtbot.wait(150)  # There's a 100ms delay allowing menus to hide
        take_screenshot.assert_called_once_with(None)


@pytest.mark.parametrize("menu_event_id,expected_screenshot_id", [
    (-1, None),
    (-2, -2),
    (0, 0),
    (123456, 123456),
])
def test_menu_trigger_takes_screenshot_to_existing_event(menu_event_id, expected_screenshot_id, qtbot: QtBot,
                                                         logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    with mock.patch.object(action, "_take_screenshot") as take_screenshot:
        with qtbot.wait_signal(action.menu().event_clicked):
            action.menu().event_clicked.emit(menu_event_id)
        qtbot.wait(150)  # There's a 100ms delay allowing menus to hide
        take_screenshot.assert_called_once_with(expected_screenshot_id)


@mock.patch("accwidgets.screenshot._action.grab_png_screenshot")
def test_take_screenshot_fails_when_no_message_provided_after_prompt(grab_png_screenshot, qtbot: QtBot, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    source = QWidget()
    qtbot.add_widget(source)
    action.source = source
    with mock.patch.object(action, "_prepare_message", return_value=""):
        with qtbot.wait_signal(action.capture_finished, raising=False, timeout=100) as blocker1:
            with qtbot.wait_signal(action.capture_failed) as blocker2:
                action._take_screenshot(None)
            assert blocker2.args == ["Logbook message cannot be empty"]
        assert not blocker1.signal_triggered
    logbook_model.attach_screenshot.assert_not_called()
    logbook_model.create_logbook_event.assert_not_called()
    grab_png_screenshot.assert_not_called()


@pytest.mark.parametrize("event_id,expected_event_id,expect_create_called,expect_get_called,expect_message_prompt", [
    (None, 123456, True, False, True),
    (-1, -1, False, True, False),
    (0, 0, False, True, False),
    (1, 1, False, True, False),
    (10, 10, False, True, False),
])
@pytest.mark.parametrize("source_count,expect_attach_screenshot_seqs", [
    (1, [0]),
    (2, [0, 1]),
    (4, [0, 1, 2, 3]),
])
@pytest.mark.parametrize("include_window_decorations", [True, False])
@mock.patch("accwidgets.screenshot._action.grab_png_screenshot", return_value=b"png_bytes")
def test_take_screenshot_remote_call_succeeds(grab_png_screenshot, expect_create_called, expect_attach_screenshot_seqs,
                                              expect_get_called, logbook_model, source_count, event_id, qtbot: QtBot,
                                              include_window_decorations, expected_event_id, expect_message_prompt):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    action.include_window_decorations = include_window_decorations
    source = QWidget()
    qtbot.add_widget(source)
    action.source = [source] * source_count
    event = mock.MagicMock()
    event.event_id = event_id if event_id is not None else 123456
    logbook_model.get_logbook_event.return_value = event
    logbook_model.create_logbook_event.return_value = event
    with mock.patch.object(action, "_prepare_message", return_value="Returned message") as prepare_message:
        with qtbot.wait_signal(action.capture_failed, raising=False, timeout=100) as blocker1:
            with qtbot.wait_signal(action.capture_finished) as blocker2:
                action._take_screenshot(event_id)
            assert blocker2.args == [expected_event_id]
        assert not blocker1.signal_triggered
        if expect_message_prompt:
            prepare_message.assert_called_once()
        else:
            prepare_message.assert_not_called()
    assert logbook_model.attach_screenshot.call_args_list == [mock.call(event=event,
                                                                        screenshot=b"png_bytes",
                                                                        seq=i) for i in expect_attach_screenshot_seqs]
    assert grab_png_screenshot.call_args_list == len(expect_attach_screenshot_seqs) * [
        mock.call(source=source,
                  include_window_decorations=include_window_decorations),
    ]
    if expect_get_called:
        logbook_model.get_logbook_event.assert_called_once_with(event_id)
    else:
        logbook_model.get_logbook_event.assert_not_called()
    if expect_create_called:
        logbook_model.create_logbook_event.assert_called_once_with("Returned message")
    else:
        logbook_model.create_logbook_event.assert_not_called()


@pytest.mark.parametrize("event_id,expected_error", [
    (None, "Test create error"),
    (-1, "Test get error"),
    (0, "Test get error"),
    (1, "Test get error"),
    (10, "Test get error"),
])
@mock.patch("accwidgets.screenshot._action.grab_png_screenshot")
def test_take_screenshot_remote_call_fails(grab_png_screenshot, event_id, qtbot: QtBot, expected_error, logbook_model):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    source = QWidget()
    qtbot.add_widget(source)
    action.source = source
    logbook_model.create_logbook_event.side_effect = LogbookError("Test create error", response=mock.MagicMock())
    logbook_model.get_logbook_event.side_effect = LogbookError("Test get error", response=mock.MagicMock())
    with mock.patch.object(action, "_prepare_message", return_value="Returned message"):
        with qtbot.wait_signal(action.capture_finished, raising=False, timeout=100) as blocker1:
            with qtbot.wait_signal(action.capture_failed) as blocker2:
                action._take_screenshot(event_id)
            assert blocker2.args == [expected_error]
        assert not blocker1.signal_triggered
    logbook_model.attach_screenshot.assert_not_called()
    grab_png_screenshot.assert_not_called()


@pytest.mark.parametrize("message,expect_opens_dialog", [
    (None, True),
    ("", True),
    ("Msg", False),
])
@mock.patch("accwidgets.screenshot._action.QInputDialog.getText", return_value=("Result", None))
def test_prepare_message_issues_prompt_with_no_defined_message(getText, message, expect_opens_dialog, logbook_model,
                                                               qtbot: QtBot):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    action.message = message
    getText.assert_not_called()
    action._prepare_message()
    if expect_opens_dialog:
        getText.assert_called_once_with(mock.ANY, "Logbook", "Enter a logbook message:")
    else:
        getText.assert_not_called()


@pytest.mark.parametrize("set_parent,expect_menu_parent", [
    (True, False),
    (False, True),
])
@mock.patch("accwidgets.screenshot._action.QInputDialog.getText", return_value=("Result", None))
def test_prepare_message_opens_dialog_with_parent_widget(getText, qtbot: QtBot, logbook_model, set_parent,
                                                         expect_menu_parent):
    action = ScreenshotAction(model=logbook_model)
    qtbot.add_widget(action.menu())
    if set_parent:
        parent = QToolButton()
        qtbot.add_widget(parent)
        parent.setDefaultAction(action)
        action.setParent(parent)
    getText.assert_not_called()
    action._prepare_message()
    expected_parent = action.menu() if expect_menu_parent else action.parent()
    getText.assert_called_once_with(expected_parent, "Logbook", "Enter a logbook message:")


@pytest.mark.parametrize("activity", [None, "TEST"])
@pytest.mark.parametrize("new_token", [None, "cde567"])
@mock.patch("accwidgets.screenshot.ScreenshotAction.setToolTip")
@mock.patch("accwidgets.screenshot.ScreenshotAction.setEnabled")
def test_model_rbac_updates_ui(setEnabled, setToolTip, logbook, qtbot: QtBot, activity, new_token):
    client, activity_client = logbook
    # Without rbac token, activities cache in the model won't be flushed and signal won't be fired
    client.rbac_b64_token = "abc123"
    if activity is not None:
        obj = mock.MagicMock(spec=Activity)
        obj.name = "TEST"
        activity_client.activities = [obj]
    model = LogbookModel(logbook=logbook)
    action = ScreenshotAction(model=model)
    qtbot.add_widget(action.menu())
    setEnabled.reset_mock()
    setToolTip.reset_mock()
    with qtbot.wait_signal(model.rbac_token_changed, timeout=100):
        with qtbot.wait_signal(model.activities_changed, timeout=100, raising=False) as blocker:
            model.reset_rbac_token(new_token)
        # Verify that update UI was triggered by rbac token signal and not activities flush
        assert not blocker.signal_triggered
    setEnabled.assert_called_once()
    setToolTip.assert_called_once()


@mock.patch("accwidgets.screenshot.ScreenshotAction.setToolTip")
@mock.patch("accwidgets.screenshot.ScreenshotAction.setEnabled")
def test_model_activities_update_ui(setEnabled, setToolTip, logbook, qtbot: QtBot):
    client, _ = logbook
    # Without rbac token, activities cache in the model won't be flushed and signal won't be fired
    client.rbac_b64_token = "abc123"
    model = LogbookModel(logbook=logbook)
    action = ScreenshotAction(model=model)
    qtbot.add_widget(action.menu())
    setEnabled.reset_mock()
    setToolTip.reset_mock()
    activity = mock.MagicMock(spec=Activity)
    activity.name = "TEST"
    with qtbot.wait_signal(model.activities_changed, timeout=100):
        model.logbook_activities = [activity]
    setEnabled.assert_called_once()
    setToolTip.assert_called_once()


@mock.patch("accwidgets.screenshot.ScreenshotAction.setToolTip")
@mock.patch("accwidgets.screenshot.ScreenshotAction.setEnabled")
def test_source_change_updates_ui(setEnabled, setToolTip, logbook, qtbot: QtBot):
    model = LogbookModel(logbook=logbook)
    action = ScreenshotAction(model=model)
    qtbot.add_widget(action.menu())
    setEnabled.reset_mock()
    setToolTip.reset_mock()
    widget = QWidget()
    qtbot.add_widget(widget)
    with qtbot.wait_signal(model.rbac_token_changed, timeout=100, raising=False) as blocker:
        with qtbot.wait_signal(model.activities_changed, timeout=100, raising=False) as blocker2:
            action.source = widget
        # Verify that update UI was triggered by source change and not model activity
        assert not blocker.signal_triggered
    assert not blocker2.signal_triggered
    setEnabled.assert_called_once()
    setToolTip.assert_called_once()
