import pytest
import asyncio
from asyncio import CancelledError
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import QDialogButtonBox, QDialog
from accwidgets.parameter_selector._dialog import ParameterSelector, ParameterSelectorDialog
from ..async_shim import AsyncMock


@pytest.fixture(scope="function")
def retain_no_protocol_option():
    orig_option = ParameterSelectorDialog.no_protocol_option
    yield
    ParameterSelectorDialog.no_protocol_option = orig_option


@pytest.mark.parametrize("enable,no_proto_name,expect_visible,expected_items", [
    (False, "", False, []),
    (False, "DEFAULT", False, []),
    (True, "", True, ["", "RDA3", "RDA", "TGM", "NO", "RMI"]),
    (True, "DEFAULT", True, ["DEFAULT", "RDA3", "RDA", "TGM", "NO", "RMI"]),
    (True, "default", True, ["default", "RDA3", "RDA", "TGM", "NO", "RMI"]),
])
def test_widget_init_protocol(qtbot: QtBot, enable, expect_visible, no_proto_name, expected_items):
    widget = ParameterSelector(enable_protocols=enable, no_protocol_option=no_proto_name)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.protocol_combo.isVisible() == expect_visible
    available_items = [widget.protocol_combo.itemText(i) for i in range(widget.protocol_combo.count())]
    assert available_items == expected_items


@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_init_default_page(qtbot: QtBot, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert not widget.activity_indicator.animating
    assert widget.stack_widget.currentIndex() == 2
    assert widget.search_edit.isEnabled()
    assert widget.search_edit.text() == ""
    assert not widget.search_btn.isEnabled()
    assert widget.results_group.isEnabled()


@pytest.mark.parametrize("enable_protocols,initial_val,expected_initial,new_val,expected_new", [
    (True, "", "", "", ""),
    (True, "", "", "test/prop", "test/prop"),
    (True, "", "", "test/prop#field", "test/prop#field"),
    (True, "", "", "proto:///test/prop", "test/prop"),
    (True, "", "", "proto:///test/prop#field", "test/prop#field"),
    (True, "", "", "proto://srv/test/prop", "test/prop"),
    (True, "", "", "proto://srv/test/prop#field", "test/prop#field"),
    (True, "", "", "rda3:///test/prop", "rda3:///test/prop"),
    (True, "", "", "rda3:///test/prop#field", "rda3:///test/prop#field"),
    (True, "", "", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, "", "", "rda3://srv/test/prop#field", "rda3://srv/test/prop#field"),
    (True, "test/prop", "test/prop", "", ""),
    (True, "test/prop", "test/prop", "test/prop", "test/prop"),
    (True, "test/prop", "test/prop", "test/prop#field", "test/prop#field"),
    (True, "test/prop", "test/prop", "proto:///test/prop", "test/prop"),
    (True, "test/prop", "test/prop", "proto:///test/prop#field", "test/prop#field"),
    (True, "test/prop", "test/prop", "proto://srv/test/prop", "test/prop"),
    (True, "test/prop", "test/prop", "proto://srv/test/prop#field", "test/prop#field"),
    (True, "test/prop", "test/prop", "rda3:///test/prop", "rda3:///test/prop"),
    (True, "test/prop", "test/prop", "rda3:///test/prop#field", "rda3:///test/prop#field"),
    (True, "test/prop", "test/prop", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, "test/prop", "test/prop", "rda3://srv/test/prop#field", "rda3://srv/test/prop#field"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "", ""),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "test/prop", "test/prop"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "test/prop#field", "test/prop#field"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto:///test/prop", "test/prop"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto:///test/prop#field", "test/prop#field"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto://srv/test/prop", "test/prop"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto://srv/test/prop#field", "test/prop#field"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3:///test/prop", "rda3:///test/prop"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3:///test/prop#field"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3://srv/test/prop#field", "rda3://srv/test/prop#field"),
    (False, "", "", "", ""),
    (False, "", "", "test/prop", "test/prop"),
    (False, "", "", "test/prop#field", "test/prop#field"),
    (False, "", "", "proto:///test/prop", "test/prop"),
    (False, "", "", "proto:///test/prop#field", "test/prop#field"),
    (False, "", "", "proto://srv/test/prop", "test/prop"),
    (False, "", "", "proto://srv/test/prop#field", "test/prop#field"),
    (False, "", "", "rda3:///test/prop", "test/prop"),
    (False, "", "", "rda3:///test/prop#field", "test/prop#field"),
    (False, "", "", "rda3://srv/test/prop", "test/prop"),
    (False, "", "", "rda3://srv/test/prop#field", "test/prop#field"),
    (False, "test/prop", "test/prop", "", ""),
    (False, "test/prop", "test/prop", "test/prop", "test/prop"),
    (False, "test/prop", "test/prop", "test/prop#field", "test/prop#field"),
    (False, "test/prop", "test/prop", "proto:///test/prop", "test/prop"),
    (False, "test/prop", "test/prop", "proto:///test/prop#field", "test/prop#field"),
    (False, "test/prop", "test/prop", "proto://srv/test/prop", "test/prop"),
    (False, "test/prop", "test/prop", "proto://srv/test/prop#field", "test/prop#field"),
    (False, "test/prop", "test/prop", "rda3:///test/prop", "test/prop"),
    (False, "test/prop", "test/prop", "rda3:///test/prop#field", "test/prop#field"),
    (False, "test/prop", "test/prop", "rda3://srv/test/prop", "test/prop"),
    (False, "test/prop", "test/prop", "rda3://srv/test/prop#field", "test/prop#field"),
    (False, "rda3:///test/prop#field", "test/prop#field", "", ""),
    (False, "rda3:///test/prop#field", "test/prop#field", "test/prop", "test/prop"),
    (False, "rda3:///test/prop#field", "test/prop#field", "test/prop#field", "test/prop#field"),
    (False, "rda3:///test/prop#field", "test/prop#field", "proto:///test/prop", "test/prop"),
    (False, "rda3:///test/prop#field", "test/prop#field", "proto:///test/prop#field", "test/prop#field"),
    (False, "rda3:///test/prop#field", "test/prop#field", "proto://srv/test/prop", "test/prop"),
    (False, "rda3:///test/prop#field", "test/prop#field", "proto://srv/test/prop#field", "test/prop#field"),
    (False, "rda3:///test/prop#field", "test/prop#field", "rda3:///test/prop", "test/prop"),
    (False, "rda3:///test/prop#field", "test/prop#field", "rda3:///test/prop#field", "test/prop#field"),
    (False, "rda3:///test/prop#field", "test/prop#field", "rda3://srv/test/prop", "test/prop"),
    (False, "rda3:///test/prop#field", "test/prop#field", "rda3://srv/test/prop#field", "test/prop#field"),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_value_prop(_, qtbot: QtBot, initial_val, expected_new, new_val, expected_initial, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.value = initial_val
    assert widget.value == expected_initial
    widget.value = new_val
    assert widget.value == expected_new


@pytest.mark.parametrize("enable_protocols,no_proto_val,value,expected_protocol,expected_label", [
    (False, "", "", "", ""),
    (False, "", "test/prop", "", "test/prop"),
    (False, "", "test/prop#field", "", "test/prop#field"),
    (False, "", "rda3:///test/prop", "", "test/prop"),
    (False, "", "rda3:///test/prop#field", "", "test/prop#field"),
    (False, "", "rda3://srv/test/prop", "", "test/prop"),
    (False, "", "rda3://srv/test/prop#field", "", "test/prop#field"),
    (False, "", "unknown:///test/prop", "", "test/prop"),
    (False, "", "unknown:///test/prop#field", "", "test/prop#field"),
    (False, "", "unknown://srv/test/prop", "", "test/prop"),
    (False, "", "unknown://srv/test/prop#field", "", "test/prop#field"),
    (False, "", "--incorrect--", "", ""),
    (False, "", "--incorrect--", "", ""),
    (True, "", "", "", ""),
    (True, "", "test/prop", "", "test/prop"),
    (True, "", "test/prop#field", "", "test/prop#field"),
    (True, "", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    (True, "", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    (True, "", "rda3://srv/test/prop", "RDA3", "rda3://srv/test/prop"),
    (True, "", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
    (True, "", "unknown:///test/prop", "", "test/prop"),
    (True, "", "unknown:///test/prop#field", "", "test/prop#field"),
    (True, "", "unknown://srv/test/prop", "", "test/prop"),
    (True, "", "unknown://srv/test/prop#field", "", "test/prop#field"),
    (True, "", "--incorrect--", "", ""),
    (True, "", "--incorrect--", "", ""),
    (True, "test-default", "", "test-default", ""),
    (True, "test-default", "test/prop", "test-default", "test/prop"),
    (True, "test-default", "test/prop#field", "test-default", "test/prop#field"),
    (True, "test-default", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    (True, "test-default", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    (True, "test-default", "rda3://srv/test/prop", "RDA3", "rda3://srv/test/prop"),
    (True, "test-default", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
    (True, "test-default", "unknown:///test/prop", "test-default", "test/prop"),
    (True, "test-default", "unknown:///test/prop#field", "test-default", "test/prop#field"),
    (True, "test-default", "unknown://srv/test/prop", "test-default", "test/prop"),
    (True, "test-default", "unknown://srv/test/prop#field", "test-default", "test/prop#field"),
    (True, "test-default", "--incorrect--", "test-default", ""),
    (True, "test-default", "--incorrect--", "test-default", ""),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_value_setter_succeeds_sets_ui(_, qtbot: QtBot, enable_protocols, no_proto_val, value,
                                              expected_protocol, expected_label):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option=no_proto_val)
    qtbot.add_widget(widget)
    assert widget.protocol_combo.currentText() == no_proto_val
    assert widget.selector_label.text() == ""
    widget.value = value
    assert widget.protocol_combo.currentText() == expected_protocol
    assert widget.selector_label.text() == expected_label


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("value,expected_search_string", [
    ("", ""),
    ("test/prop", "test/prop"),
    ("test/prop#field", "test/prop#field"),
    ("rda3:///test/prop", "test/prop"),
    ("rda3:///test/prop#field", "test/prop#field"),
    ("rda3://srv/test/prop", "test/prop"),
    ("rda3://srv/test/prop#field", "test/prop#field"),
    ("unknown:///test/prop", "test/prop"),
    ("unknown:///test/prop#field", "test/prop#field"),
    ("unknown://srv/test/prop", "test/prop"),
    ("unknown://srv/test/prop#field", "test/prop#field"),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_value_setter_succeeds_requests_new_search(qtbot: QtBot, value, expected_search_string, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    with mock.patch.object(widget, "_on_search_requested", return_value=asyncio.coroutine(lambda: None)()) as on_search_requested:
        assert widget.search_edit.text() == ""
        on_search_requested.assert_not_called()
        widget.value = value
        on_search_requested.assert_called_once_with(expected_search_string)
        assert widget.search_edit.text() == expected_search_string


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("initial_val", ["", "test/prop"])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_value_setter_fails_search_not_requested(qtbot: QtBot, initial_val, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    with mock.patch.object(widget, "_on_search_requested", return_value=asyncio.coroutine(lambda: None)()) as on_search_requested:
        widget.value = initial_val
        assert widget.search_edit.text() == initial_val
        on_search_requested.reset_mock()
        widget.value = "--incorrect--"
        on_search_requested.assert_not_called()
        assert widget.search_edit.text() == initial_val


@pytest.mark.parametrize("enable_protocols,initial_val,expected_initial_proto,expected_initial_label", [
    (False, "", "", ""),
    (False, "test/prop", "", "test/prop"),
    (False, "rda3:///test/prop", "", "test/prop"),
    (True, "", "", ""),
    (True, "test/prop", "", "test/prop"),
    (True, "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_value_setter_fails_no_ui_set(_, qtbot: QtBot, initial_val, expected_initial_proto, enable_protocols,
                                             expected_initial_label):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.value = initial_val
    assert widget.protocol_combo.currentText() == expected_initial_proto
    assert widget.selector_label.text() == expected_initial_label
    widget.value = "--incorrect--"
    assert widget.protocol_combo.currentText() == expected_initial_proto
    assert widget.selector_label.text() == expected_initial_label


@pytest.mark.parametrize("key,expect_fire", [
    (Qt.Key_Enter, False),
    (Qt.Key_Return, False),
    (Qt.Key_E, True),
    (Qt.Key_5, True),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
@mock.patch("qtpy.QtWidgets.QWidget.keyPressEvent")
def test_widget_enter_key_not_closing(keyPressEvent, qtbot: QtBot, key, expect_fire, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    # We don't use qtbot QtTest API because for some reason key passed to the widget does not correspond
    # to the specified one
    widget.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, key, Qt.NoModifier))
    if expect_fire:
        keyPressEvent.assert_called_once()
        assert keyPressEvent.call_args[0][0].key() == key
    else:
        keyPressEvent.assert_not_called()


@pytest.mark.parametrize("enable_protocols", [True, False])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._cancel_running_tasks")
def test_widget_stops_active_tasks_on_hide(cancel_running_tasks, qtbot: QtBot, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    cancel_running_tasks.assert_not_called()
    widget.hide()
    cancel_running_tasks.assert_called_once()


@pytest.mark.parametrize("no_proto_text,initial_val,selected_proto,expected_val", [
    ("", "", "", ""),
    ("", "", "RDA3", ""),
    ("DEF", "", "DEF", ""),
    ("DEF", "", "RDA3", ""),
    ("", "test/prop", "", "test/prop"),
    ("", "test/prop", "RDA3", "rda3:///test/prop"),
    ("DEF", "test/prop", "DEF", "test/prop"),
    ("DEF", "test/prop", "RDA3", "rda3:///test/prop"),
    ("", "test/prop#field", "", "test/prop#field"),
    ("", "test/prop#field", "RDA3", "rda3:///test/prop#field"),
    ("DEF", "test/prop#field", "DEF", "test/prop#field"),
    ("DEF", "test/prop#field", "RDA3", "rda3:///test/prop#field"),
    ("", "rda3:///test/prop", "", "test/prop"),
    ("", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    ("DEF", "rda3:///test/prop", "DEF", "test/prop"),
    ("DEF", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    ("", "tgm:///test/prop", "", "test/prop"),
    ("", "tgm:///test/prop", "RDA3", "rda3:///test/prop"),
    ("DEF", "tgm:///test/prop", "DEF", "test/prop"),
    ("DEF", "tgm:///test/prop", "RDA3", "rda3:///test/prop"),
    ("", "rda3:///test/prop#field", "", "test/prop#field"),
    ("", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    ("DEF", "rda3:///test/prop#field", "DEF", "test/prop#field"),
    ("DEF", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    ("", "tgm:///test/prop#field", "", "test/prop#field"),
    ("", "tgm:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    ("DEF", "tgm:///test/prop#field", "DEF", "test/prop#field"),
    ("DEF", "tgm:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    ("", "rda3://srv/test/prop#field", "", "test/prop#field"),
    ("", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
    ("DEF", "rda3://srv/test/prop#field", "DEF", "test/prop#field"),
    ("DEF", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
    ("", "tgm://srv/test/prop#field", "", "test/prop#field"),
    ("", "tgm://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
    ("DEF", "tgm://srv/test/prop#field", "DEF", "test/prop#field"),
    ("DEF", "tgm://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_protocol_selection_affects_result(_, qtbot: QtBot, no_proto_text, initial_val, selected_proto,
                                                  expected_val):
    widget = ParameterSelector(enable_protocols=True, no_protocol_option=no_proto_text)
    qtbot.add_widget(widget)
    widget.value = initial_val
    # Simulate user selection event
    widget.protocol_combo.setCurrentText(selected_proto)
    widget.protocol_combo.activated.emit(widget.protocol_combo.currentIndex())
    assert widget.value == expected_val


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("text", [
    "",
    "test",
    "test/prop#field",
])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_start_search_calls_method_with_text(qtbot: QtBot, text, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.search_edit.setText(text)
    with mock.patch.object(widget, "_on_search_requested", return_value=asyncio.coroutine(lambda: None)()) as on_search_requested:
        # Originally, it was attempted to use widget.search_btn.click(),
        # but the button click signal does not get propagated inside the test, so using target slot instead
        widget._start_search()
        on_search_requested.assert_called_once_with(text)


@pytest.mark.parametrize("status,expect_animation_started,expected_page_idx,expect_search_enabled,expect_results_enabled", [
    (ParameterSelector.NetworkRequestStatus.COMPLETE, False, 0, True, True),
    (ParameterSelector.NetworkRequestStatus.IN_PROGRESS, True, 1, False, False),
    (ParameterSelector.NetworkRequestStatus.FAILED, False, 2, True, True),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_update_from_status(qtbot: QtBot, status, expect_animation_started, expect_results_enabled,
                                   expect_search_enabled, expected_page_idx, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget._update_from_status(status)
    assert widget.activity_indicator.animating == expect_animation_started
    assert widget.stack_widget.currentIndex() == expected_page_idx
    assert widget.search_btn.isEnabled() == expect_search_enabled
    assert widget.search_edit.isEnabled() == expect_search_enabled
    assert widget.results_group.isEnabled() == expect_results_enabled
    # Stop timers running inside animation so that consecutive tests don't break
    widget.activity_indicator.stopAnimation()


@pytest.mark.parametrize("enable_protocols,starting_val,expected_initial_label,expected_initial_dev,expected_initial_prop,expected_initial_field,expected_initial_proto", [
    (True, "", "", "", "", None, None),
    (True, "test/prop", "test/prop", "test", "prop", None, None),
    (True, "test/prop#field", "test/prop#field", "test", "prop", "field", None),
    (True, "rda3:///test/prop", "rda3:///test/prop", "test", "prop", None, "rda3"),
    (False, "", "", "", "", None, None),
    (False, "test/prop", "test/prop", "test", "prop", None, None),
    (False, "test/prop#field", "test/prop#field", "test", "prop", "field", None),
    (False, "rda3:///test/prop", "test/prop", "test", "prop", None, None),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_reset_selected_value(_, qtbot: QtBot, enable_protocols, starting_val, expected_initial_proto,
                                     expected_initial_dev, expected_initial_field, expected_initial_prop,
                                     expected_initial_label):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.value = starting_val
    assert widget._selected_value.device == expected_initial_dev
    assert widget._selected_value.prop == expected_initial_prop
    assert widget._selected_value.field == expected_initial_field
    assert widget._selected_value.protocol == expected_initial_proto
    assert widget.selector_label.text() == expected_initial_label
    widget._reset_selected_value()
    assert widget._selected_value.device == ""
    assert widget._selected_value.prop == ""
    assert widget._selected_value.field is None
    assert widget._selected_value.protocol == expected_initial_proto
    assert widget.selector_label.text() == ""


@pytest.mark.parametrize("task_exists,should_cancel", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_cancel_running_tasks(qtbot: QtBot, should_cancel, task_exists, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    task_mock = mock.Mock()
    widget._active_ccda_task = task_mock if task_exists else None
    widget._cancel_running_tasks()
    if should_cancel:
        task_mock.cancel.assert_called_once_with()
    else:
        task_mock.cancel.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("search_string", ["", " ", "  ", "\t", "\n"])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_on_search_requested_noop_with_empty_string(qtbot: QtBot, enable_protocols, search_string):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    with mock.patch.object(widget, "_update_from_status") as update_from_status:
        with mock.patch.object(widget, "_reset_selected_value") as reset_selected_value:
            await widget._on_search_requested(search_string)
            update_from_status.assert_not_called()
            reset_selected_value.assert_not_called()
            assert widget._active_ccda_task is None


@pytest.mark.asyncio
@pytest.mark.parametrize("search_string,expected_hint,expected_lookup", [
    ("TEST.DEV", "Searching TEST.DEV...", "TEST.DEV"),
    ("TEST.DEV ", "Searching TEST.DEV...", "TEST.DEV"),
    (" TEST.DEV", "Searching TEST.DEV...", "TEST.DEV"),
    ("test/prop", "Searching test...", "test"),
    ("test/prop ", "Searching test...", "test"),
    (" test/prop", "Searching test...", "test"),
    ("test/prop#field", "Searching test...", "test"),
    ("test/prop#field ", "Searching test...", "test"),
    (" test/prop#field", "Searching test...", "test"),
    ("rda3:///test/prop#field", "Searching test...", "test"),
    ("rda3:///test/prop#field ", "Searching test...", "test"),
    (" rda3:///test/prop#field", "Searching test...", "test"),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_on_search_requested_sets_in_progress_ui(qtbot: QtBot, enable_protocols, search_string,
                                                              expected_hint, expected_lookup):

    class TestException(Exception):
        pass

    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    assert widget.activity_indicator.hint == ""

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, side_effect=TestException) as look_up_ccda:
        look_up_ccda.assert_not_called()
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            with mock.patch.object(widget, "_reset_selected_value") as reset_selected_value:
                await widget._on_search_requested(search_string)
                # The second call is expected to be a failure, because we purposefully throw an exception for early exit,
                # so it will re-render the UI to failure.
                update_from_status.call_args_list == [mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                                                      mock.call(ParameterSelector.NetworkRequestStatus.FAILED)]
                reset_selected_value.assert_called_once_with()
                look_up_ccda.assert_called_once_with(expected_lookup)
                assert widget.activity_indicator.hint == expected_hint
                assert widget._active_ccda_task is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("prev_status,expected_new_status", [
    (ParameterSelector.NetworkRequestStatus.COMPLETE, ParameterSelector.NetworkRequestStatus.COMPLETE),
    (ParameterSelector.NetworkRequestStatus.FAILED, ParameterSelector.NetworkRequestStatus.FAILED),
    (ParameterSelector.NetworkRequestStatus.IN_PROGRESS, ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
])
@pytest.mark.parametrize("search_string", ["TEST.DEV", "test/prop#field "])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_on_search_requested_rolls_back_ui_on_cancel(qtbot: QtBot, enable_protocols, search_string,
                                                                  prev_status, expected_new_status):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    widget._update_from_status(prev_status)
    assert widget.err_label.text() == "Start by typing the device name into the field above!"

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, side_effect=CancelledError):
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            await widget._on_search_requested(search_string)
            # First call inevitably will be with IN_PROGRESS, because that's what activating the background task
            # does
            update_from_status.call_args_list == [mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                                                  mock.call(expected_new_status)]
            assert widget.err_label.text() == "Start by typing the device name into the field above!"


@pytest.mark.asyncio
@pytest.mark.parametrize("prev_status", [
    ParameterSelector.NetworkRequestStatus.COMPLETE,
    ParameterSelector.NetworkRequestStatus.FAILED,
    ParameterSelector.NetworkRequestStatus.IN_PROGRESS,
])
@pytest.mark.parametrize("search_string", ["TEST.DEV", "test/prop#field "])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_on_search_requested_sets_ui_on_error(qtbot: QtBot, enable_protocols, search_string, prev_status):
    class TestException(Exception):
        pass

    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    orig_results_name = widget.results_group.title()
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    widget._update_from_status(prev_status)  # Just check that this does not influence anything
    assert widget.err_label.text() == "Start by typing the device name into the field above!"

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, side_effect=TestException("test error message")):
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            await widget._on_search_requested(search_string)
            # First call inevitably will be with IN_PROGRESS, because that's what activating the background task
            # does
            update_from_status.call_args_list == [mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                                                  mock.call(ParameterSelector.NetworkRequestStatus.FAILED)]
            assert widget.err_label.text() == "test error message"
            assert widget.results_group.title() == orig_results_name


@pytest.mark.asyncio
@pytest.mark.parametrize("prev_status", [
    ParameterSelector.NetworkRequestStatus.COMPLETE,
    ParameterSelector.NetworkRequestStatus.FAILED,
    ParameterSelector.NetworkRequestStatus.IN_PROGRESS,
])
@pytest.mark.parametrize("search_string,expected_group_name", [
    ("TEST.DEV", 'Results for search query "TEST.DEV":'),
    ("test/prop#field ", 'Results for search query "test/prop#field":'),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_on_search_requested_success_sets_ui(qtbot: QtBot, enable_protocols, search_string, prev_status,
                                                          expected_group_name):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    mocked_model = mock.MagicMock()
    widget._search_results_model = mocked_model
    widget._update_from_status(prev_status)  # Just check that this does not influence anything
    assert widget.err_label.text() == "Start by typing the device name into the field above!"

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, return_value=[]):
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            await widget._on_search_requested(search_string)
            # First call inevitably will be with IN_PROGRESS, because that's what activating the background task
            # does
            update_from_status.call_args_list == [mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                                                  mock.call(ParameterSelector.NetworkRequestStatus.COMPLETE)]
            assert widget.err_label.text() == "Start by typing the device name into the field above!"
            assert widget.results_group.title() == expected_group_name
            mocked_model.set_data.assert_called_once_with([])


@pytest.mark.asyncio
@pytest.mark.parametrize("prev_status", [
    ParameterSelector.NetworkRequestStatus.COMPLETE,
    ParameterSelector.NetworkRequestStatus.FAILED,
    ParameterSelector.NetworkRequestStatus.IN_PROGRESS,
])
@pytest.mark.parametrize("results,expect_select_first", [
    ([], False),
    (["dev1"], True),
])
@pytest.mark.parametrize("search_string", ["TEST.DEV", "test/prop#field "])
@pytest.mark.parametrize("enable_protocols", [True, False])
async def test_widget_on_search_requested_success_selects_when_only_result(qtbot: QtBot, enable_protocols, search_string,
                                                                           prev_status, results, expect_select_first):
    widget = ParameterSelector(enable_protocols=enable_protocols, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    mocked_model = mock.MagicMock()
    widget._search_results_model = mocked_model
    widget._update_from_status(prev_status)  # Just check that this does not influence anything
    assert widget.err_label.text() == "Start by typing the device name into the field above!"

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, return_value=results):
        await widget._on_search_requested(search_string)
        if expect_select_first:
            mocked_model.select_device.assert_called_once_with(0)
        else:
            mocked_model.select_device.assert_not_called()


@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("val", ["", "test/prop", "test/prop#field", "rda3:///test/prop#field"])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector.value", new_callable=mock.PropertyMock)
def test_dialog_value_getter(value, qtbot: QtBot, val, enable_protocols):
    value.return_value = val
    dialog = ParameterSelectorDialog(enable_protocols=enable_protocols)
    qtbot.add_widget(dialog)
    assert dialog.value == val


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("enable_protocols,initial_val,expected_val", [
    (False, "", ""),
    (False, "test/prop", "test/prop"),
    (False, "test/prop#field", "test/prop#field"),
    (False, "rda3:///test/prop#field", "test/prop#field"),
    (True, "", ""),
    (True, "test/prop", "test/prop"),
    (True, "test/prop#field", "test/prop#field"),
    (True, "rda3:///test/prop#field", "rda3:///test/prop#field"),
])
async def test_dialog_initial_value_affects_widget(qtbot: QtBot, enable_protocols, initial_val, expected_val):
    dialog = ParameterSelectorDialog(enable_protocols=enable_protocols, initial_value=initial_val)
    qtbot.add_widget(dialog)
    assert dialog.value == expected_val


@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("set_no_proto,expected_no_proto", [
    (None, "Omit protocol"),
    ("", ""),
    ("Test", "Test"),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector")
@mock.patch("accwidgets.parameter_selector._dialog.QVBoxLayout.addWidget")
def test_dialog_enable_protocols_affects_widget(_, ParameterSelector, qtbot: QtBot, enable_protocols, set_no_proto,
                                                expected_no_proto, retain_no_protocol_option):
    _ = retain_no_protocol_option
    if set_no_proto is not None:
        ParameterSelectorDialog.no_protocol_option = set_no_proto
    dialog = ParameterSelectorDialog(enable_protocols=enable_protocols)
    qtbot.add_widget(dialog)
    ParameterSelector.assert_called_once_with(parent=dialog,
                                              enable_protocols=enable_protocols,
                                              no_protocol_option=expected_no_proto)


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("btn,expected_result", [
    (QDialogButtonBox.Ok, QDialog.Accepted),
    (QDialogButtonBox.Cancel, QDialog.Rejected),
])
async def test_dialog_buttonbox_trigger(qtbot: QtBot, btn, expected_result):
    dialog = ParameterSelectorDialog()
    qtbot.add_widget(dialog)
    buttons = next(iter(c for c in dialog.children() if isinstance(c, QDialogButtonBox)))
    dialog_button = buttons.button(btn)
    print(dialog_button)
    qtbot.mouseClick(dialog_button, Qt.LeftButton)
    assert dialog.result() == expected_result
