import pytest
import logging
import re
from pytestqt.qtbot import QtBot
from unittest import mock
from typing import Dict, Optional
from qtpy.QtCore import QAbstractAnimation, Qt, QPoint
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QAction, QDialog
from accwidgets.log_console import (LogConsole, LogConsoleModel, LogConsoleFormatter, LogConsoleRecord, LogLevel,
                                    LogConsoleDock)
from accwidgets.log_console._viewer import (LogConsoleCollapseButton, LogConsoleLastMessageEdit, FmtConfiguration,
                                            _format_html_message)
from .fixtures import *  # noqa: F401,F403


@pytest.fixture(scope="function", autouse=True)
def test_fn_wrapper():
    # Reset logger cache
    logging.root = logging.RootLogger(logging.WARNING)
    logging.Logger.root = logging.root
    logging.Logger.manager = logging.Manager(logging.Logger.root)
    yield


@pytest.fixture
def capture_context_menu_actions():

    mapping: Dict[str, QAction] = {}

    def side_effect(*args):
        callback = args[-1]
        action = QAction(*args[0:-1])
        action.triggered.connect(callback)
        mapping[action.text()] = action
        return action

    return side_effect, mapping


@pytest.mark.parametrize("provide_model,should_connect", [
    (True, True),
    (False, False),
])
def test_log_console_init_connects_model_if_provided(qtbot: QtBot, provide_model, should_connect):
    model = LogConsoleModel()
    assert model.receivers(model.new_log_record_received) == 0
    assert model.receivers(model.freeze_changed) == 0
    widget = LogConsole(model=model if provide_model else None)
    qtbot.add_widget(widget)
    if should_connect:
        assert model.receivers(model.new_log_record_received) == 1
        assert model.receivers(model.freeze_changed) == 1
    else:
        assert model.receivers(model.new_log_record_received) == 0
        assert model.receivers(model.freeze_changed) == 0


@pytest.mark.parametrize("provide_model,should_inherit_parent", [
    (True, True),
    (False, False),
])
def test_log_console_init_takes_ownership_of_model_if_provided(qtbot: QtBot, provide_model, should_inherit_parent):
    model = LogConsoleModel()
    assert model.parent() is None
    widget = LogConsole(model=model if provide_model else None)
    qtbot.add_widget(widget)
    if should_inherit_parent:
        assert model.parent() == widget
    else:
        assert model.parent() is None


@pytest.mark.parametrize("provide_model,should_belong", [
    (True, True),
    (False, False),
])
def test_log_console_init_model_belongs_to_widget_if_provided(qtbot: QtBot, provide_model, should_belong):
    model = LogConsoleModel()
    widget = LogConsole(model=model if provide_model else None)
    qtbot.add_widget(widget)
    if should_belong:
        assert widget.model is model
    else:
        assert widget.model is not None
        assert widget.model is not model


def test_log_console_default_collapsible(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.collapsible is False


def test_log_console_default_expanded(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.expanded is True


def test_log_console_default_model(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.model is not None
    assert isinstance(widget.model, LogConsoleModel)


def test_log_console_default_color_scheme(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.errorColor.name().upper() == "#D32727"
    assert widget.warningColor.name().upper() == "#E67700"
    assert widget.criticalColor.name().upper() == "#D32727"
    assert widget.infoColor.name().upper() == "#1D7D00"
    assert widget.debugColor.name().upper() == "#000000"


def test_log_console_set_formatter_noop_on_the_same_value(qtbot: QtBot):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    fmt = widget.formatter
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        widget.formatter = fmt
        setHtml.assert_not_called()


def test_log_console_set_formatter_rerenders_contents(qtbot: QtBot):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    fmt = LogConsoleFormatter()
    assert widget.formatter != fmt
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        widget.formatter = fmt
        setHtml.assert_called_once()


def test_log_console_set_model_noop_on_the_same_value(qtbot: QtBot):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    model = widget.model
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        widget.model = model
        setHtml.assert_not_called()


def test_log_console_set_model_rerenders_contents(qtbot: QtBot):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    model = LogConsoleModel()
    assert widget.model != model
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        widget.model = model
        setHtml.assert_called_once()


def test_log_console_set_model_disconnects_old_model(qtbot: QtBot):
    orig_model = LogConsoleModel()
    widget = LogConsole(model=orig_model)
    qtbot.add_widget(widget)
    assert orig_model.receivers(orig_model.new_log_record_received) == 1
    assert orig_model.receivers(orig_model.freeze_changed) == 1
    widget.model = LogConsoleModel()
    assert orig_model.receivers(orig_model.new_log_record_received) == 0
    assert orig_model.receivers(orig_model.freeze_changed) == 0


def test_log_console_set_model_destroys_old_model(qtbot: QtBot):
    orig_model = LogConsoleModel()
    widget = LogConsole(model=orig_model)
    qtbot.add_widget(widget)
    with qtbot.wait_signal(orig_model.destroyed) as blocker:
        widget.model = LogConsoleModel()
    assert blocker.signal_triggered


def test_log_console_set_model_connects_new_model(qtbot: QtBot):
    new_model = LogConsoleModel()
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    assert new_model.receivers(new_model.new_log_record_received) == 0
    assert new_model.receivers(new_model.freeze_changed) == 0
    widget.model = new_model
    assert new_model.receivers(new_model.new_log_record_received) == 1
    assert new_model.receivers(new_model.freeze_changed) == 1


def test_log_console_set_model_takes_ownership_of_new_model(qtbot: QtBot):
    new_model = LogConsoleModel()
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    assert new_model.parent() is None
    widget.model = new_model
    assert new_model.parent() == widget


def test_log_console_clear_clears_model(qtbot: QtBot):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    with mock.patch.object(model, "clear") as clear:
        widget.clear()
        clear.assert_called_once()


def test_log_console_clear_clears_last_message_text(qtbot: QtBot):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    logging.warning("test message")
    assert "test message" in widget._last_msg_line.text()
    widget.clear()
    assert widget._last_msg_line.text() == ""


def test_log_console_clear_stops_last_message_animation(qtbot: QtBot):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    logging.warning("test message")
    assert widget._last_msg_line._bg_anim.state() == QAbstractAnimation.Running
    assert widget._last_msg_line._fg_anim.state() == QAbstractAnimation.Running
    widget.clear()
    assert widget._last_msg_line._bg_anim.state() != QAbstractAnimation.Running
    assert widget._last_msg_line._fg_anim.state() != QAbstractAnimation.Running


def test_log_console_freeze(qtbot: QtBot):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    with mock.patch.object(model, "freeze") as freeze:
        widget.freeze()
        freeze.assert_called_once()


def test_log_console_unfreeze(qtbot: QtBot):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    with mock.patch.object(model, "unfreeze") as unfreeze:
        widget.unfreeze()
        unfreeze.assert_called_once()


@pytest.mark.parametrize("initial_frozen,should_call_freeze,should_call_unfreeze", [
    (True, False, True),
    (False, True, False),
])
def test_log_console_toggle_freeze(qtbot: QtBot, initial_frozen, should_call_freeze, should_call_unfreeze):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    if initial_frozen:
        widget.freeze()
    else:
        widget.unfreeze()
    with mock.patch.object(widget, "unfreeze") as unfreeze:
        with mock.patch.object(widget, "freeze") as freeze:
            widget.toggleFreeze()
            if should_call_freeze:
                freeze.assert_called_once()
            else:
                freeze.assert_not_called()
            if should_call_unfreeze:
                unfreeze.assert_called_once()
            else:
                unfreeze.assert_not_called()


@pytest.mark.parametrize("initial_expanded,expected_new_expanded", [
    (True, False),
    (False, True),
])
def test_log_console_toggle_expanded_mode(qtbot: QtBot, initial_expanded, expected_new_expanded):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    widget.expanded = initial_expanded
    widget.toggleExpandedMode()
    assert widget.expanded == expected_new_expanded


def test_log_console_frozen_prop(qtbot: QtBot):
    model = LogConsoleModel()
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    assert widget.model == model
    assert widget.frozen == widget.model.frozen
    with qtbot.wait_signal(model.freeze_changed):
        widget.toggleFreeze()
    assert widget.frozen == widget.model.frozen


@pytest.mark.parametrize("initial_expanded,initial_collapsible,new_expanded,expected_collapsible", [
    (True, True, True, True),
    (True, False, True, False),
    (False, True, True, True),
    (True, True, False, True),
    (True, False, False, True),
    (False, True, False, True),
])
def test_log_console_set_expanded_toggles_collapsible(qtbot: QtBot, initial_expanded, initial_collapsible, new_expanded,
                                                      expected_collapsible):
    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.expanded = initial_expanded
    widget.collapsible = initial_collapsible
    assert widget.expanded == initial_expanded
    assert widget.collapsible == initial_collapsible
    widget.expanded = new_expanded
    assert widget.expanded == new_expanded
    assert widget.collapsible == expected_collapsible


@pytest.mark.parametrize("initial_expanded,expected_initial_icon,new_expanded,expected_new_icon", [
    (True, Qt.DownArrow, True, Qt.DownArrow),
    (False, Qt.UpArrow, True, Qt.DownArrow),
    (True, Qt.DownArrow, False, Qt.UpArrow),
    (False, Qt.UpArrow, False, Qt.UpArrow),
])
def test_log_console_set_expanded_updates_button_icon(qtbot: QtBot, initial_expanded, expected_initial_icon,
                                                      new_expanded, expected_new_icon):
    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.collapsible = True
    assert widget._btn_toggle.arrowType() == Qt.DownArrow  # type: ignore
    widget.expanded = initial_expanded
    assert widget._btn_toggle.arrowType() == expected_initial_icon  # type: ignore
    widget.expanded = new_expanded
    assert widget._btn_toggle.arrowType() == expected_new_icon  # type: ignore


@pytest.mark.parametrize("initial_expanded,new_expanded,expect_emits_signal", [
    (True, False, True),
    (True, True, False),
    (False, False, False),
    (False, True, True),
])
def test_log_console_set_expanded_emits_signal(qtbot: QtBot, initial_expanded, new_expanded, expect_emits_signal):
    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.expanded = initial_expanded

    if expect_emits_signal:
        with qtbot.wait_signal(widget.expandedStateChanged) as blocker:
            widget.expanded = new_expanded
        assert blocker.args == [new_expanded]
    else:
        with qtbot.assert_not_emitted(widget.expandedStateChanged):
            widget.expanded = new_expanded


@pytest.mark.parametrize("initial_expanded,expect_initial_visible,new_expanded,expect_new_visible", [
    (True, True, True, True),
    (True, True, False, False),
    (False, False, False, False),
    (False, False, True, True),
])
def test_log_console_set_expanded_updates_visibility_of_contents(qtbot: QtBot, initial_expanded, new_expanded,
                                                                 expect_initial_visible, expect_new_visible):
    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.expanded = initial_expanded
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget._contents.isVisible() == expect_initial_visible
    widget.expanded = new_expanded
    assert widget._contents.isVisible() == expect_new_visible


@pytest.mark.parametrize("initial_expanded,initial_collapsible,new_collapsible,expected_expanded", [
    (True, True, True, True),
    (True, False, True, True),
    (False, True, True, False),
    (True, True, False, True),
    (True, False, False, True),
    (False, True, False, True),
])
def test_log_console_set_collapsible_toggles_expanded(qtbot: QtBot, initial_expanded, initial_collapsible, new_collapsible,
                                                      expected_expanded):
    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.collapsible = initial_collapsible
    widget.expanded = initial_expanded
    assert widget.expanded == initial_expanded
    assert widget.collapsible == initial_collapsible
    widget.collapsible = new_collapsible
    assert widget.collapsible == new_collapsible
    assert widget.expanded == expected_expanded


@pytest.mark.parametrize("initial_collapsible,expect_initial_button_exist,new_collapsible,expected_button_exist", [
    (True, True, True, True),
    (True, True, False, False),
    (False, False, True, True),
    (False, False, False, False),
])
def test_log_console_set_collapsible_affects_button_placement(qtbot: QtBot, initial_collapsible, new_collapsible,
                                                              expected_button_exist, expect_initial_button_exist):
    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.collapsible = initial_collapsible
    orig_buttons = [btn for btn in widget.children() if isinstance(btn, LogConsoleCollapseButton)]
    orig_btn: Optional[LogConsoleCollapseButton]
    if expect_initial_button_exist:
        assert len(orig_buttons) == 1
        orig_btn = orig_buttons[0]
    else:
        assert len(orig_buttons) == 0
        orig_btn = None
    if orig_btn is not None:
        with qtbot.wait_signal(orig_btn.destroyed, timeout=500, raising=False) as blocker:
            widget.collapsible = new_collapsible

        assert blocker.signal_triggered != expected_button_exist
    else:
        widget.collapsible = new_collapsible
    new_buttons = [btn for btn in widget.children() if isinstance(btn, LogConsoleCollapseButton)]
    if expected_button_exist:
        assert len(new_buttons) == 1
    else:
        assert len(new_buttons) == 0


def test_log_console_error_color_prop(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.errorColor.name() != "#232323"
    widget.errorColor = QColor("#232323")
    assert widget.errorColor.name() == "#232323"


def test_log_console_warning_color_prop(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.warningColor.name() != "#232323"
    widget.warningColor = QColor("#232323")
    assert widget.warningColor.name() == "#232323"


def test_log_console_critical_color_prop(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.criticalColor.name() != "#232323"
    widget.criticalColor = QColor("#232323")
    assert widget.criticalColor.name() == "#232323"


def test_log_console_info_color_prop(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.infoColor.name() != "#232323"
    widget.infoColor = QColor("#232323")
    assert widget.infoColor.name() == "#232323"


def test_log_console_debug_color_prop(qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    assert widget.debugColor.name() != "#232323"
    widget.debugColor = QColor("#232323")
    assert widget.debugColor.name() == "#232323"


@pytest.mark.parametrize("initial_scroll,initial_content,new_content,expected_scroll", [
    ("minimum", [], [], "minimum"),
    ("minimum", [], ["msg1"], "minimum"),
    ("minimum", [], ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], "minimum"),
    ("minimum",
     ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"],
     ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"],
     "minimum"),
    ("minimum", ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], ["msg1"], "minimum"),
    ("minimum", ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], [], "minimum"),
    ("maximum", [], ["msg1"], "maximum"),
    ("maximum", [], ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], "maximum"),
    ("maximum",
     ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"],
     ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"],
     "maximum"),
    ("maximum", ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], ["msg1"], "maximum"),
    ("maximum", ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], [], "maximum"),
    (5,
     ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"],
     ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"],
     5),
    (5, ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], ["msg1"], 5),
    (5, ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7", "msg8", "msg9", "msg10", "msg11", "msg12", "msg13", "msg14"], [], 5),
])
@mock.patch("accwidgets.log_console.LogConsoleModel.all_records", new_callable=mock.PropertyMock)
def test_log_console_rerender_contents_preserves_scroll(all_records, qtbot: QtBot, initial_scroll, initial_content,
                                                        new_content, expected_scroll):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    for msg in initial_content:
        logging.warning(msg)
    scrollbar = widget._contents.verticalScrollBar()
    if initial_scroll == "minimum":
        scrollbar.setValue(scrollbar.minimum())
    elif initial_scroll == "maximum":
        scrollbar.setValue(scrollbar.maximum())
    else:
        scrollbar.setValue(initial_scroll)
    widget.freeze()
    all_records.return_value = [LogConsoleRecord(message=msg,
                                                 logger_name="root",
                                                 level=LogLevel.WARNING,
                                                 timestamp=0)
                                for msg in new_content]
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        widget.unfreeze()
        all_records.assert_called()
        setHtml.assert_called_once()
        if expected_scroll == "minimum":
            assert scrollbar.value() == scrollbar.minimum()
        elif expected_scroll == "maximum":
            assert scrollbar.value() == scrollbar.maximum()
        else:
            assert scrollbar.value() == expected_scroll


@pytest.mark.parametrize("new_formatter_options,expected_html", [
    ({"show_date": False, "show_time": False, "show_logger_name": True}, '<p><span class="WARNING">root - WARNING - message 1</span></p><p><span class="WARNING">root - WARNING - message 2</span></p>'),
    ({"show_date": False, "show_time": False, "show_logger_name": False}, '<p><span class="WARNING">WARNING - message 1</span></p><p><span class="WARNING">WARNING - message 2</span></p>'),
])
def test_log_console_rerender_contents_updates_html(qtbot: QtBot, new_formatter_options, expected_html):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    logging.warning("message 1")
    logging.warning("message 2")
    new_fmt = LogConsoleFormatter(**new_formatter_options)
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        widget.formatter = new_fmt
        setHtml.assert_called_once_with(expected_html)


def test_log_console_rerender_contents_does_not_call_append_html(qtbot: QtBot):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        with mock.patch.object(widget._contents, "appendHtml") as appendHtml:
            widget.formatter = LogConsoleFormatter()
            setHtml.assert_called_once()
            appendHtml.assert_not_called()


@pytest.mark.parametrize("all_records_val,should_update_color", [
    ([], False),
    (["msg1"], True),
    (["msg1", "msg2"], True),
])
@mock.patch("accwidgets.log_console.LogConsoleModel.all_records", new_callable=mock.PropertyMock)
def test_log_console_rerender_contents_updates_last_message_edit_color(all_records, qtbot: QtBot, all_records_val, should_update_color):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    last_msg_edit = [w for w in widget.children() if isinstance(w, LogConsoleLastMessageEdit)][0]
    widget.freeze()
    all_records.return_value = [LogConsoleRecord(message=msg,
                                                 logger_name="root",
                                                 level=LogLevel.WARNING,
                                                 timestamp=0)
                                for msg in all_records_val]
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        with mock.patch.object(last_msg_edit, "set_styled_text") as set_styled_text:
            widget.unfreeze()
            setHtml.assert_called_once()
            if should_update_color:
                set_styled_text.assert_called_once()
            else:
                set_styled_text.assert_not_called()


@mock.patch("accwidgets.log_console._viewer.QMenu")
def test_log_console_context_menu(QMenu, qtbot: QtBot):
    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.customContextMenuRequested.emit(QPoint())
    QMenu.return_value.exec_.assert_called_once()
    call_clear = mock.call(mock.ANY, "Clear", mock.ANY)
    call_find = mock.call(mock.ANY, "Find", mock.ANY)
    call_print = mock.call(mock.ANY, "Print", mock.ANY)
    call_freeze = mock.call("Freeze", mock.ANY)
    call_prefs = mock.call("Preferences", mock.ANY)
    QMenu.return_value.addAction.assert_has_calls([call_clear, call_find, call_freeze, call_print, call_prefs], any_order=True)


@pytest.mark.parametrize("reply_yes,expect_proceed", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.QMessageBox")
def test_log_console_clear_actions_requires_confirmation(QMessageBox, QMenu, qtbot: QtBot, reply_yes, expect_proceed,
                                                         capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect
    QMessageBox.return_value.question.return_value = QMessageBox.Yes if reply_yes else QMessageBox.No

    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Clear"]
    QMessageBox.return_value.question.reset_mock()
    with mock.patch.object(widget, "clear") as clear:
        action.trigger()
        QMessageBox.return_value.question.assert_called_once_with(widget,
                                                                  "Please confirm",
                                                                  "Do you really want to clear all logs?",
                                                                  QMessageBox.Yes,
                                                                  QMessageBox.No)
        if expect_proceed:
            clear.assert_called_once()
        else:
            clear.assert_not_called()


@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.LogSearchDialog")
def test_log_console_search_action_opens_dialog(LogSearchDialog, QMenu, qtbot: QtBot, capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Find"]
    LogSearchDialog.return_value.exec_.assert_not_called()
    action.trigger()
    LogSearchDialog.return_value.exec_.assert_called_once()


@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.LogSearchDialog.exec_")
@mock.patch("accwidgets.log_console._viewer.LogSearchDialog.search_requested", new_callable=mock.PropertyMock)
@mock.patch("accwidgets.log_console._viewer.LogSearchDialog.search_direction_changed", new_callable=mock.PropertyMock)
def test_log_console_search_dialog_connects_signal(search_direction_changed, search_requested, _, QMenu, qtbot: QtBot,
                                                   capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Find"]
    assert widget.receivers(widget._sig_match_result) == 0
    search_direction_changed.return_value.connect.assert_not_called()
    search_requested.return_value.connect.assert_not_called()
    action.trigger()
    search_direction_changed.return_value.connect.assert_called_once()
    search_requested.return_value.connect.assert_called_once()
    assert widget.receivers(widget._sig_match_result) == 1


@pytest.mark.parametrize("has_initial_selection,should_clear", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.LogSearchDialog.exec_")
def test_log_console_search_action_clears_selection(_, QMenu, qtbot: QtBot, has_initial_selection, should_clear,
                                                    capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Find"]
    logging.warning("msg1")
    logging.warning("msg2")
    with mock.patch.object(widget._contents, "setTextCursor"):
        with mock.patch.object(widget._contents, "textCursor") as textCursor:
            textCursor.return_value.hasSelection.return_value = has_initial_selection
            with mock.patch.object(widget._contents.textCursor(), "clearSelection") as clearSelection:
                action.trigger()
                if should_clear:
                    clearSelection.assert_called_once()
                else:
                    clearSelection.assert_not_called()


@pytest.mark.parametrize("buffer_size,should_fail", [
    (0, True),
    (10, False),
])
@mock.patch("accwidgets.log_console._viewer.LogPreferencesDialog.exec_")
@mock.patch("accwidgets.log_console._viewer.ModelConfiguration.validate")
def test_log_console_prefs_dialog_action_fails_with_invalid_model(validate, _, qtbot: QtBot, buffer_size, should_fail):
    if should_fail:
        validate.side_effect = ValueError
    model = LogConsoleModel(buffer_size=buffer_size)
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)

    # Somehow, triggering actions here produces duplicate error raise, which fails the test even when anticipating the
    # exception
    if should_fail:
        with pytest.raises(ValueError):
            widget._open_prefs_dialog()
    else:
        widget._open_prefs_dialog()


@pytest.mark.parametrize("dialog_saved,should_update_model", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.LogPreferencesDialog")
def test_log_console_prefs_dialog_action_updates_model(LogPreferencesDialog, QMenu, qtbot: QtBot, dialog_saved, should_update_model,
                                                       capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    LogPreferencesDialog.return_value.model_config.buffer_size = 10
    LogPreferencesDialog.return_value.model_config.visible_levels = {LogLevel.INFO}
    LogPreferencesDialog.return_value.model_config.selected_logger_levels = {"root": LogLevel.ERROR}
    LogPreferencesDialog.return_value.exec_.return_value = QDialog.Accepted if dialog_saved else QDialog.Rejected

    logging.getLogger().setLevel(LogLevel.NOTSET)
    model = LogConsoleModel(buffer_size=40, visible_levels={LogLevel.ERROR})
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)

    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Preferences"]

    assert model.visible_levels == {LogLevel.ERROR}
    assert model.buffer_size == 40
    assert model.selected_logger_levels == {"root": LogLevel.NOTSET}
    action.trigger()

    if should_update_model:
        assert model.visible_levels == {LogLevel.INFO}
        assert model.buffer_size == 10
        assert model.selected_logger_levels == {"root": LogLevel.ERROR}
    else:
        assert model.visible_levels == {LogLevel.ERROR}
        assert model.buffer_size == 40
        assert model.selected_logger_levels == {"root": LogLevel.NOTSET}


@pytest.mark.parametrize("dialog_saved,should_update_palette", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.LogPreferencesDialog")
def test_log_console_prefs_dialog_action_updates_palette(LogPreferencesDialog, QMenu, qtbot: QtBot, dialog_saved, should_update_palette,
                                                         capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    LogPreferencesDialog.return_value.view_config.color_map = {
        LogLevel.DEBUG: ("#ffffff", False),
        LogLevel.INFO: ("#ffffff", False),
        LogLevel.WARNING: ("#ffffff", True),
        LogLevel.ERROR: ("#ffffff", False),
        LogLevel.CRITICAL: ("#ffffff", False),
    }
    LogPreferencesDialog.return_value.exec_.return_value = QDialog.Accepted if dialog_saved else QDialog.Rejected

    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)

    LogPreferencesDialog.return_value.model_config.buffer_size = widget.model.buffer_size
    LogPreferencesDialog.return_value.model_config.visible_levels = widget.model.visible_levels
    LogPreferencesDialog.return_value.model_config.selected_logger_levels = widget.model.selected_logger_levels

    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Preferences"]

    assert widget.errorColor.name() != "#ffffff"
    assert widget.warningColor.name() != "#ffffff"
    assert widget.debugColor.name() != "#ffffff"
    assert widget.infoColor.name() != "#ffffff"
    assert widget.criticalColor.name() != "#ffffff"
    action.trigger()

    if should_update_palette:
        assert widget.errorColor.name() == "#ffffff"
        assert widget.warningColor.name() == "#ffffff"
        assert widget.debugColor.name() == "#ffffff"
        assert widget.infoColor.name() == "#ffffff"
        assert widget.criticalColor.name() == "#ffffff"
    else:
        assert widget.errorColor.name() != "#ffffff"
        assert widget.warningColor.name() != "#ffffff"
        assert widget.debugColor.name() != "#ffffff"
        assert widget.infoColor.name() != "#ffffff"
        assert widget.criticalColor.name() != "#ffffff"


@pytest.mark.parametrize("dialog_saved,should_update_fmt", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.LogPreferencesDialog")
def test_log_console_prefs_dialog_action_updates_formatter(LogPreferencesDialog, QMenu, qtbot: QtBot, dialog_saved, should_update_fmt,
                                                           capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    LogPreferencesDialog.return_value.view_config.fmt_config = {
        "show_date": FmtConfiguration(value=False, title=""),
        "show_time": FmtConfiguration(value=True, title=""),
        "show_logger_name": FmtConfiguration(value=False, title=""),
    }
    LogPreferencesDialog.return_value.exec_.return_value = QDialog.Accepted if dialog_saved else QDialog.Rejected

    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)

    LogPreferencesDialog.return_value.model_config.buffer_size = widget.model.buffer_size
    LogPreferencesDialog.return_value.model_config.visible_levels = widget.model.visible_levels
    LogPreferencesDialog.return_value.model_config.selected_logger_levels = widget.model.selected_logger_levels

    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Preferences"]

    assert widget.formatter.show_date is True
    assert widget.formatter.show_time is True
    assert widget.formatter.show_logger_name is True
    action.trigger()

    if should_update_fmt:
        assert widget.formatter.show_date is False
        assert widget.formatter.show_time is True
        assert widget.formatter.show_logger_name is False
    else:
        assert widget.formatter.show_date is True
        assert widget.formatter.show_time is True
        assert widget.formatter.show_logger_name is True


@pytest.mark.parametrize("dialog_saved,should_rerender", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.LogPreferencesDialog")
def test_log_console_prefs_dialog_accept_rerenders_contents(LogPreferencesDialog, QMenu, qtbot: QtBot, dialog_saved, should_rerender,
                                                            capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    LogPreferencesDialog.return_value.exec_.return_value = QDialog.Accepted if dialog_saved else QDialog.Rejected

    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)

    LogPreferencesDialog.return_value.model_config.buffer_size = widget.model.buffer_size
    LogPreferencesDialog.return_value.model_config.visible_levels = widget.model.visible_levels
    LogPreferencesDialog.return_value.model_config.selected_logger_levels = widget.model.selected_logger_levels

    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Preferences"]

    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        action.trigger()
        if should_rerender:
            setHtml.assert_called_once()
        else:
            setHtml.assert_not_called()


@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.QPrintPreviewDialog")
def test_log_console_print_dialog_action_opens_dialog(QPrintPreviewDialog, QMenu, qtbot: QtBot, capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Print"]
    QPrintPreviewDialog.return_value.exec_.assert_not_called()
    action.trigger()
    QPrintPreviewDialog.return_value.exec_.assert_called_once()


@mock.patch("accwidgets.log_console._viewer.QMenu")
@mock.patch("accwidgets.log_console._viewer.QPrintPreviewDialog.exec_")
@mock.patch("accwidgets.log_console._viewer.QPrintPreviewDialog.paintRequested", new_callable=mock.PropertyMock)
def test_log_console_print_dialog_connects_signals(paintRequested, _, QMenu, qtbot: QtBot,
                                                   capture_context_menu_actions):
    side_effect, mapping = capture_context_menu_actions
    QMenu.return_value.addAction.side_effect = side_effect

    widget = LogConsole()
    qtbot.add_widget(widget)
    widget.customContextMenuRequested.emit(QPoint())
    action = mapping["Print"]
    paintRequested.return_value.connect.assert_not_called()
    action.trigger()
    paintRequested.return_value.connect.assert_called_once()


@pytest.mark.parametrize("initial_frozen,expected_initial_lock_visible,new_frozen,expected_new_lock_visible", [
    (True, True, True, True),
    (False, False, True, True),
    (True, True, False, False),
    (False, False, False, False),
])
def test_log_console_lock_icon_reflects_frozen_state(qtbot: QtBot, initial_frozen, expected_initial_lock_visible,
                                                     new_frozen, expected_new_lock_visible):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    last_msg_edit = [w for w in widget.children() if isinstance(w, LogConsoleLastMessageEdit)][0]
    if initial_frozen:
        widget.freeze()
    else:
        widget.unfreeze()
    assert last_msg_edit._showing_lock == expected_initial_lock_visible
    if new_frozen:
        widget.freeze()
    else:
        widget.unfreeze()
    assert last_msg_edit._showing_lock == expected_new_lock_visible


@pytest.mark.parametrize("buffer_size,messages", [
    (1, ["msg"]),
    (1, ["msg", "msg2"]),
    (2, ["msg", "msg2"]),
    (2, ["msg"]),
])
def test_log_console_new_message_does_not_cause_rerender_contents(qtbot: QtBot, buffer_size, messages):
    model = LogConsoleModel(buffer_size=buffer_size)
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    with mock.patch.object(widget._contents.document(), "setHtml") as setHtml:
        for msg in messages:
            logging.warning(msg)
        setHtml.assert_not_called()


@pytest.mark.parametrize("messages,severities,expected_colors", [
    (["test message"], [logging.WARNING], ["warningColor"]),
    (["test message"], [logging.ERROR], ["errorColor"]),
    (["test message", "test message 2"], [logging.WARNING, logging.WARNING], ["warningColor", "warningColor"]),
    (["test message", "test message 2"], [logging.ERROR, logging.ERROR], ["errorColor", "errorColor"]),
    (["test message", "test message 2"], [logging.WARNING, logging.ERROR], ["warningColor", "errorColor"]),
    (["test message", "test message 2"], [logging.ERROR, logging.CRITICAL], ["errorColor", "criticalColor"]),
])
def test_log_console_new_message_colors_last_message_line(qtbot: QtBot, messages, severities, expected_colors):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    last_msg_edit = [w for w in widget.children() if isinstance(w, LogConsoleLastMessageEdit)][0]
    with mock.patch.object(last_msg_edit, "set_styled_text") as set_styled_text:
        for msg, level, expected_color_getter in zip(messages, severities, expected_colors):
            expected_color_name = getattr(widget, expected_color_getter).name()
            set_styled_text.reset_mock()
            logging.log(level, msg)
            set_styled_text.assert_called_once()
            assert msg in set_styled_text.call_args[1]["text"]
            assert set_styled_text.call_args[1]["background_color"].name() == expected_color_name


@pytest.mark.parametrize("buffer_size,messages", [
    (1, ["msg"]),
    (1, ["msg", "msg2"]),
    (2, ["msg", "msg2"]),
    (2, ["msg"]),
])
def test_log_console_new_message_appends(qtbot: QtBot, buffer_size, messages):
    model = LogConsoleModel(buffer_size=buffer_size)
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    with mock.patch.object(widget._contents, "appendHtml") as appendHtml:
        for msg in messages:
            appendHtml.reset_mock()
            logging.warning(msg)
            appendHtml.assert_called_once()


@pytest.mark.parametrize("buffer_size,initial_messages,expected_initial_contents,new_message,expected_new_contents", [
    (1, [], [""], "test message", ["WARNING - test message"]),
    (1, ["test message"], ["WARNING - test message"], "test message 2", ["WARNING - test message 2"]),
    (1, ["test message", "test message 2"], ["WARNING - test message 2"], "test message 3", ["WARNING - test message 3"]),
    (2, [], [""], "test message", ["WARNING - test message"]),
    (2, ["test message"], ["WARNING - test message"], "test message 2", ["WARNING - test message", "WARNING - test message 2"]),
    (2, ["test message", "test message 2"], ["WARNING - test message", "WARNING - test message 2"], "test message 3", ["WARNING - test message 2", "WARNING - test message 3"]),
    (2, ["test message", "test message 2", "test message 3"], ["WARNING - test message 2", "WARNING - test message 3"], "test message 4", ["WARNING - test message 3", "WARNING - test message 4"]),
    (1, ["test\nmessage"], ["WARNING - test\u2028message"], "test\nmessage\n2", ["WARNING - test\u2028message\u20282"]),
    (1, ["test\nmessage", "test\nmessage\n2"], ["WARNING - test\u2028message\u20282"], "test\nmessage\n3", ["WARNING - test\u2028message\u20283"]),
    (2, ["test\nmessage"], ["WARNING - test\u2028message"], "test\nmessage\n2", ["WARNING - test\u2028message", "WARNING - test\u2028message\u20282"]),
    (2, ["test\nmessage", "test\nmessage\n2"], ["WARNING - test\u2028message", "WARNING - test\u2028message\u20282"], "test\nmessage\n3", ["WARNING - test\u2028message\u20282", "WARNING - test\u2028message\u20283"]),
])
def test_log_console_new_message_pops_first_when_overflown(qtbot: QtBot, buffer_size, initial_messages, expected_initial_contents,
                                                           new_message, expected_new_contents):
    model = LogConsoleModel(buffer_size=buffer_size)
    widget = LogConsole(model=model)
    qtbot.add_widget(widget)
    fmt = LogConsoleFormatter(show_logger_name=False, show_time=False, show_date=False)
    widget.formatter = fmt
    for msg in initial_messages:
        logging.warning(msg)
    doc = widget._contents.document()
    assert doc.blockCount() == len(expected_initial_contents)
    for idx, expected_msg in enumerate(expected_initial_contents):
        assert doc.findBlockByNumber(idx).text() == expected_msg
    logging.warning(new_message)
    assert doc.blockCount() == len(expected_new_contents)
    for idx, expected_msg in enumerate(expected_new_contents):
        assert doc.findBlockByNumber(idx).text() == expected_msg


@pytest.mark.parametrize("messages,expected_html_extract", [
    (["test\nmessage"], r"<span[^>]*>WARNING - test<br[ \t]*\/>message<\/span>"),
    (["test\nmessage", "test message\n2"], r"<span[^>]*>WARNING - test<br[ \t]*\/>message<\/span>.*<span[^>]*>WARNING - test message<br[ \t]*\/>2<\/span>"),
])
def test_log_console_message_new_line_replaced_with_html_break(qtbot: QtBot, messages, expected_html_extract):
    widget = LogConsole(model=LogConsoleModel())
    qtbot.add_widget(widget)
    fmt = LogConsoleFormatter(show_logger_name=False, show_time=False, show_date=False)
    widget.formatter = fmt
    for msg in messages:
        logging.warning(msg)
    match = re.search(expected_html_extract, str(widget._contents.document().toHtml()), re.DOTALL)
    # assert expected_html_extract in widget._contents.document().toHtml()
    print(widget._contents.document().toHtml())
    assert match is not None


@pytest.mark.parametrize("left", [True, False])
@pytest.mark.parametrize("top", [True, False])
@pytest.mark.parametrize("right", [True, False])
@pytest.mark.parametrize("bottom", [True, False])
def test_log_console_dock_init_allowed_areas_with_args(qtbot: QtBot, left, top, right, bottom):
    flag = Qt.DockWidgetAreas()
    if left:
        flag |= Qt.LeftDockWidgetArea
    if top:
        flag |= Qt.TopDockWidgetArea
    if bottom:
        flag |= Qt.BottomDockWidgetArea
    if right:
        flag |= Qt.RightDockWidgetArea
    widget = LogConsoleDock(allowed_areas=flag)
    qtbot.add_widget(widget)
    assert widget.allowedAreas() == flag


def test_log_console_dock_init_allowed_areas_without_args(qtbot: QtBot):
    widget = LogConsoleDock()
    qtbot.add_widget(widget)
    assert widget.allowedAreas() == (Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)


def test_log_console_dock_set_allowed_areas_does_nothing(qtbot: QtBot):
    widget = LogConsoleDock()
    qtbot.add_widget(widget)
    assert widget.allowedAreas() != Qt.RightDockWidgetArea
    widget.setAllowedAreas(Qt.RightDockWidgetArea)
    assert widget.allowedAreas() != Qt.RightDockWidgetArea


def test_log_console_dock_console_prop_with_no_console_passed(qtbot: QtBot):
    widget = LogConsoleDock()
    qtbot.add_widget(widget)
    assert isinstance(widget.console, LogConsole)


def test_log_console_dock_console_prop_fails_if_unexpected_widget_is_used(qtbot: QtBot):
    console = LogConsole()
    qtbot.add_widget(console)
    widget1 = LogConsoleDock()
    qtbot.add_widget(widget1)
    widget2 = LogConsoleDock(console=console)
    qtbot.add_widget(widget2)
    assert widget1.console != console
    assert widget2.console == console


@pytest.mark.parametrize("level,expected_class", [
    (LogLevel.CRITICAL, "CRITICAL"),
    (LogLevel.WARNING, "WARNING"),
    (LogLevel.ERROR, "ERROR"),
    (LogLevel.INFO, "INFO"),
    (LogLevel.DEBUG, "DEBUG"),
])
def test_formatted_message_css_class_corresponds_to_severity(level, expected_class):
    record = LogConsoleRecord(message="", level=level, timestamp=0, logger_name="test_logger")
    assert _format_html_message(record=record, formatted_message="") == f'<p><span class="{expected_class}"></span></p>'


@pytest.mark.parametrize("input,expected_message", [
    ("<br/>", "&lt;br/&gt;"),
    ('"quote"', "&quot;quote&quot;"),
])
def test_formatted_message_escapes_html_chars(input, expected_message):
    record = LogConsoleRecord(message="", level=LogLevel.DEBUG, timestamp=0, logger_name="test_logger")
    formatted_msg = _format_html_message(record=record, formatted_message=input)
    match = re.match(r"<p><span.*?>(?P<contents>[^<]*)<\/span><\/p>", formatted_msg)
    assert match is not None
    assert match.group("contents") == expected_message


@pytest.mark.parametrize("input,expected_message", [
    ("test\nmessage", "test<br/>message"),
    ("test message", "test message"),
    ("test\ndouble\nmessage", "test<br/>double<br/>message"),
])
def test_formatted_message_replaces_line_breaks(input, expected_message):
    record = LogConsoleRecord(message="", level=LogLevel.DEBUG, timestamp=0, logger_name="test_logger")
    formatted_msg = _format_html_message(record=record, formatted_message=input)
    match = re.match(r"<p><span.*?>(?P<contents>.*?)<\/span><\/p>", formatted_msg)
    assert match is not None
    assert match.group("contents") == expected_message


def test_log_console_renders_with_custom_qss_before_show(qtbot: QtBot, custom_model_class):
    widget = LogConsole(model=custom_model_class())
    qtbot.add_widget(widget)
    assert widget.errorColor.name() != "#232323"
    widget.setStyleSheet("LogConsole{qproperty-errorColor: #232323;}")
    assert widget.errorColor.name() != "#232323"
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.errorColor.name() == "#232323"


def test_log_console_renders_with_custom_qss_after_show(qtbot: QtBot, custom_model_class):
    widget = LogConsole(model=custom_model_class())
    qtbot.add_widget(widget)
    assert widget.errorColor.name() != "#232323"
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.errorColor.name() != "#232323"
    widget.setStyleSheet("LogConsole{qproperty-errorColor: #232323;}")
    assert widget.errorColor.name() == "#232323"
