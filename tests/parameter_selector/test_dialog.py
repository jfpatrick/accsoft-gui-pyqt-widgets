import pytest
import functools
from asyncio import CancelledError
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import QDialogButtonBox, QDialog
from accwidgets.parameter_selector._dialog import ParameterSelector, ParameterSelectorDialog, ParameterName
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
    widget = ParameterSelector(enable_protocols=enable, enable_fields=True, no_protocol_option=no_proto_name)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.protocol_combo.isVisible() == expect_visible
    available_items = [widget.protocol_combo.itemText(i) for i in range(widget.protocol_combo.count())]
    assert available_items == expected_items


@pytest.mark.parametrize("enable,expect_visible", [
    (False, False),
    (True, True),
])
def test_widget_init_fields(qtbot: QtBot, enable, expect_visible):
    widget = ParameterSelector(enable_fields=enable, enable_protocols=False, no_protocol_option="")
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    widget._update_from_status(ParameterSelector.NetworkRequestStatus.COMPLETE)
    assert widget.field_list.isVisible() == expect_visible
    assert widget.field_title.isVisible() == expect_visible


@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_init_default_page(qtbot: QtBot, enable_protocols):
    widget = ParameterSelector(enable_protocols=enable_protocols, enable_fields=True, no_protocol_option="")
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert not widget.activity_indicator.animating
    assert widget.stack_widget.currentIndex() == 2
    assert widget.search_edit.isEnabled()
    assert widget.search_edit.text() == ""
    assert not widget.search_btn.isEnabled()
    assert widget.results_group.isEnabled()


@pytest.mark.parametrize("enable_protocols,enable_fields,initial_val,expected_initial,new_val,expected_new", [
    (True, True, "", "", "", ""),
    (True, True, "", "", "test/prop", "test/prop"),
    (True, True, "", "", "test/prop#field", "test/prop#field"),
    (True, True, "", "", "proto:///test/prop", "test/prop"),
    (True, True, "", "", "proto:///test/prop#field", "test/prop#field"),
    (True, True, "", "", "proto://srv/test/prop", "test/prop"),
    (True, True, "", "", "proto://srv/test/prop#field", "test/prop#field"),
    (True, True, "", "", "rda3:///test/prop", "rda3:///test/prop"),
    (True, True, "", "", "rda3:///test/prop#field", "rda3:///test/prop#field"),
    (True, True, "", "", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, True, "", "", "rda3://srv/test/prop#field", "rda3://srv/test/prop#field"),
    (True, True, "test/prop", "test/prop", "", ""),
    (True, True, "test/prop", "test/prop", "test/prop", "test/prop"),
    (True, True, "test/prop", "test/prop", "test/prop#field", "test/prop#field"),
    (True, True, "test/prop", "test/prop", "proto:///test/prop", "test/prop"),
    (True, True, "test/prop", "test/prop", "proto:///test/prop#field", "test/prop#field"),
    (True, True, "test/prop", "test/prop", "proto://srv/test/prop", "test/prop"),
    (True, True, "test/prop", "test/prop", "proto://srv/test/prop#field", "test/prop#field"),
    (True, True, "test/prop", "test/prop", "rda3:///test/prop", "rda3:///test/prop"),
    (True, True, "test/prop", "test/prop", "rda3:///test/prop#field", "rda3:///test/prop#field"),
    (True, True, "test/prop", "test/prop", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, True, "test/prop", "test/prop", "rda3://srv/test/prop#field", "rda3://srv/test/prop#field"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "", ""),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "test/prop", "test/prop"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "test/prop#field", "test/prop#field"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto:///test/prop", "test/prop"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto:///test/prop#field", "test/prop#field"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto://srv/test/prop", "test/prop"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "proto://srv/test/prop#field", "test/prop#field"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3:///test/prop", "rda3:///test/prop"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3:///test/prop#field"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, True, "rda3:///test/prop#field", "rda3:///test/prop#field", "rda3://srv/test/prop#field", "rda3://srv/test/prop#field"),
    (False, True, "", "", "", ""),
    (False, True, "", "", "test/prop", "test/prop"),
    (False, True, "", "", "test/prop#field", "test/prop#field"),
    (False, True, "", "", "proto:///test/prop", "test/prop"),
    (False, True, "", "", "proto:///test/prop#field", "test/prop#field"),
    (False, True, "", "", "proto://srv/test/prop", "test/prop"),
    (False, True, "", "", "proto://srv/test/prop#field", "test/prop#field"),
    (False, True, "", "", "rda3:///test/prop", "test/prop"),
    (False, True, "", "", "rda3:///test/prop#field", "test/prop#field"),
    (False, True, "", "", "rda3://srv/test/prop", "test/prop"),
    (False, True, "", "", "rda3://srv/test/prop#field", "test/prop#field"),
    (False, True, "test/prop", "test/prop", "", ""),
    (False, True, "test/prop", "test/prop", "test/prop", "test/prop"),
    (False, True, "test/prop", "test/prop", "test/prop#field", "test/prop#field"),
    (False, True, "test/prop", "test/prop", "proto:///test/prop", "test/prop"),
    (False, True, "test/prop", "test/prop", "proto:///test/prop#field", "test/prop#field"),
    (False, True, "test/prop", "test/prop", "proto://srv/test/prop", "test/prop"),
    (False, True, "test/prop", "test/prop", "proto://srv/test/prop#field", "test/prop#field"),
    (False, True, "test/prop", "test/prop", "rda3:///test/prop", "test/prop"),
    (False, True, "test/prop", "test/prop", "rda3:///test/prop#field", "test/prop#field"),
    (False, True, "test/prop", "test/prop", "rda3://srv/test/prop", "test/prop"),
    (False, True, "test/prop", "test/prop", "rda3://srv/test/prop#field", "test/prop#field"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "", ""),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "test/prop", "test/prop"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "test/prop#field", "test/prop#field"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "proto:///test/prop", "test/prop"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "proto:///test/prop#field", "test/prop#field"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "proto://srv/test/prop", "test/prop"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "proto://srv/test/prop#field", "test/prop#field"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "rda3:///test/prop", "test/prop"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "rda3:///test/prop#field", "test/prop#field"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "rda3://srv/test/prop", "test/prop"),
    (False, True, "rda3:///test/prop#field", "test/prop#field", "rda3://srv/test/prop#field", "test/prop#field"),
    (True, False, "", "", "", ""),
    (True, False, "", "", "test/prop", "test/prop"),
    (True, False, "", "", "test/prop#field", "test/prop"),
    (True, False, "", "", "proto:///test/prop", "test/prop"),
    (True, False, "", "", "proto:///test/prop#field", "test/prop"),
    (True, False, "", "", "proto://srv/test/prop", "test/prop"),
    (True, False, "", "", "proto://srv/test/prop#field", "test/prop"),
    (True, False, "", "", "rda3:///test/prop", "rda3:///test/prop"),
    (True, False, "", "", "rda3:///test/prop#field", "rda3:///test/prop"),
    (True, False, "", "", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, False, "", "", "rda3://srv/test/prop#field", "rda3://srv/test/prop"),
    (True, False, "test/prop", "test/prop", "", ""),
    (True, False, "test/prop", "test/prop", "test/prop", "test/prop"),
    (True, False, "test/prop", "test/prop", "test/prop#field", "test/prop"),
    (True, False, "test/prop", "test/prop", "proto:///test/prop", "test/prop"),
    (True, False, "test/prop", "test/prop", "proto:///test/prop#field", "test/prop"),
    (True, False, "test/prop", "test/prop", "proto://srv/test/prop", "test/prop"),
    (True, False, "test/prop", "test/prop", "proto://srv/test/prop#field", "test/prop"),
    (True, False, "test/prop", "test/prop", "rda3:///test/prop", "rda3:///test/prop"),
    (True, False, "test/prop", "test/prop", "rda3:///test/prop#field", "rda3:///test/prop"),
    (True, False, "test/prop", "test/prop", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, False, "test/prop", "test/prop", "rda3://srv/test/prop#field", "rda3://srv/test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "", ""),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "test/prop", "test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "test/prop#field", "test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "proto:///test/prop", "test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "proto:///test/prop#field", "test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "proto://srv/test/prop", "test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "proto://srv/test/prop#field", "test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "rda3:///test/prop", "rda3:///test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "rda3:///test/prop#field", "rda3:///test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "rda3://srv/test/prop", "rda3://srv/test/prop"),
    (True, False, "rda3:///test/prop#field", "rda3:///test/prop", "rda3://srv/test/prop#field", "rda3://srv/test/prop"),
    (False, False, "", "", "", ""),
    (False, False, "", "", "test/prop", "test/prop"),
    (False, False, "", "", "test/prop#field", "test/prop"),
    (False, False, "", "", "proto:///test/prop", "test/prop"),
    (False, False, "", "", "proto:///test/prop#field", "test/prop"),
    (False, False, "", "", "proto://srv/test/prop", "test/prop"),
    (False, False, "", "", "proto://srv/test/prop#field", "test/prop"),
    (False, False, "", "", "rda3:///test/prop", "test/prop"),
    (False, False, "", "", "rda3:///test/prop#field", "test/prop"),
    (False, False, "", "", "rda3://srv/test/prop", "test/prop"),
    (False, False, "", "", "rda3://srv/test/prop#field", "test/prop"),
    (False, False, "test/prop", "test/prop", "", ""),
    (False, False, "test/prop", "test/prop", "test/prop", "test/prop"),
    (False, False, "test/prop", "test/prop", "test/prop#field", "test/prop"),
    (False, False, "test/prop", "test/prop", "proto:///test/prop", "test/prop"),
    (False, False, "test/prop", "test/prop", "proto:///test/prop#field", "test/prop"),
    (False, False, "test/prop", "test/prop", "proto://srv/test/prop", "test/prop"),
    (False, False, "test/prop", "test/prop", "proto://srv/test/prop#field", "test/prop"),
    (False, False, "test/prop", "test/prop", "rda3:///test/prop", "test/prop"),
    (False, False, "test/prop", "test/prop", "rda3:///test/prop#field", "test/prop"),
    (False, False, "test/prop", "test/prop", "rda3://srv/test/prop", "test/prop"),
    (False, False, "test/prop", "test/prop", "rda3://srv/test/prop#field", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "", ""),
    (False, False, "rda3:///test/prop#field", "test/prop", "test/prop", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "test/prop#field", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "proto:///test/prop", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "proto:///test/prop#field", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "proto://srv/test/prop", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "proto://srv/test/prop#field", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "rda3:///test/prop", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "rda3:///test/prop#field", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "rda3://srv/test/prop", "test/prop"),
    (False, False, "rda3:///test/prop#field", "test/prop", "rda3://srv/test/prop#field", "test/prop"),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_value_prop(_, qtbot: QtBot, initial_val, expected_new, new_val, expected_initial, enable_protocols,
                           enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    widget.value = initial_val
    assert widget.value == expected_initial
    widget.value = new_val
    assert widget.value == expected_new


@pytest.mark.parametrize("enable_protocols,enable_fields,no_proto_val,value,expected_protocol,expected_label", [
    (False, True, "", "", "", ""),
    (False, True, "", "test/prop", "", "test/prop"),
    (False, True, "", "test/prop#field", "", "test/prop#field"),
    (False, True, "", "rda3:///test/prop", "", "test/prop"),
    (False, True, "", "rda3:///test/prop#field", "", "test/prop#field"),
    (False, True, "", "rda3://srv/test/prop", "", "test/prop"),
    (False, True, "", "rda3://srv/test/prop#field", "", "test/prop#field"),
    (False, True, "", "unknown:///test/prop", "", "test/prop"),
    (False, True, "", "unknown:///test/prop#field", "", "test/prop#field"),
    (False, True, "", "unknown://srv/test/prop", "", "test/prop"),
    (False, True, "", "unknown://srv/test/prop#field", "", "test/prop#field"),
    (False, True, "", "--incorrect--", "", ""),
    (False, True, "", "--incorrect--", "", ""),
    (True, True, "", "", "", ""),
    (True, True, "", "test/prop", "", "test/prop"),
    (True, True, "", "test/prop#field", "", "test/prop#field"),
    (True, True, "", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    (True, True, "", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    (True, True, "", "rda3://srv/test/prop", "RDA3", "rda3://srv/test/prop"),
    (True, True, "", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
    (True, True, "", "unknown:///test/prop", "", "test/prop"),
    (True, True, "", "unknown:///test/prop#field", "", "test/prop#field"),
    (True, True, "", "unknown://srv/test/prop", "", "test/prop"),
    (True, True, "", "unknown://srv/test/prop#field", "", "test/prop#field"),
    (True, True, "", "--incorrect--", "", ""),
    (True, True, "", "--incorrect--", "", ""),
    (True, True, "test-default", "", "test-default", ""),
    (True, True, "test-default", "test/prop", "test-default", "test/prop"),
    (True, True, "test-default", "test/prop#field", "test-default", "test/prop#field"),
    (True, True, "test-default", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    (True, True, "test-default", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    (True, True, "test-default", "rda3://srv/test/prop", "RDA3", "rda3://srv/test/prop"),
    (True, True, "test-default", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop#field"),
    (True, True, "test-default", "unknown:///test/prop", "test-default", "test/prop"),
    (True, True, "test-default", "unknown:///test/prop#field", "test-default", "test/prop#field"),
    (True, True, "test-default", "unknown://srv/test/prop", "test-default", "test/prop"),
    (True, True, "test-default", "unknown://srv/test/prop#field", "test-default", "test/prop#field"),
    (True, True, "test-default", "--incorrect--", "test-default", ""),
    (True, True, "test-default", "--incorrect--", "test-default", ""),
    (False, False, "", "", "", ""),
    (False, False, "", "test/prop", "", "test/prop"),
    (False, False, "", "test/prop#field", "", "test/prop"),
    (False, False, "", "rda3:///test/prop", "", "test/prop"),
    (False, False, "", "rda3:///test/prop#field", "", "test/prop"),
    (False, False, "", "rda3://srv/test/prop", "", "test/prop"),
    (False, False, "", "rda3://srv/test/prop#field", "", "test/prop"),
    (False, False, "", "unknown:///test/prop", "", "test/prop"),
    (False, False, "", "unknown:///test/prop#field", "", "test/prop"),
    (False, False, "", "unknown://srv/test/prop", "", "test/prop"),
    (False, False, "", "unknown://srv/test/prop#field", "", "test/prop"),
    (False, False, "", "--incorrect--", "", ""),
    (False, False, "", "--incorrect--", "", ""),
    (True, False, "", "", "", ""),
    (True, False, "", "test/prop", "", "test/prop"),
    (True, False, "", "test/prop#field", "", "test/prop"),
    (True, False, "", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    (True, False, "", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop"),
    (True, False, "", "rda3://srv/test/prop", "RDA3", "rda3://srv/test/prop"),
    (True, False, "", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop"),
    (True, False, "", "unknown:///test/prop", "", "test/prop"),
    (True, False, "", "unknown:///test/prop#field", "", "test/prop"),
    (True, False, "", "unknown://srv/test/prop", "", "test/prop"),
    (True, False, "", "unknown://srv/test/prop#field", "", "test/prop"),
    (True, False, "", "--incorrect--", "", ""),
    (True, False, "", "--incorrect--", "", ""),
    (True, False, "test-default", "", "test-default", ""),
    (True, False, "test-default", "test/prop", "test-default", "test/prop"),
    (True, False, "test-default", "test/prop#field", "test-default", "test/prop"),
    (True, False, "test-default", "rda3:///test/prop", "RDA3", "rda3:///test/prop"),
    (True, False, "test-default", "rda3:///test/prop#field", "RDA3", "rda3:///test/prop"),
    (True, False, "test-default", "rda3://srv/test/prop", "RDA3", "rda3://srv/test/prop"),
    (True, False, "test-default", "rda3://srv/test/prop#field", "RDA3", "rda3://srv/test/prop"),
    (True, False, "test-default", "unknown:///test/prop", "test-default", "test/prop"),
    (True, False, "test-default", "unknown:///test/prop#field", "test-default", "test/prop"),
    (True, False, "test-default", "unknown://srv/test/prop", "test-default", "test/prop"),
    (True, False, "test-default", "unknown://srv/test/prop#field", "test-default", "test/prop"),
    (True, False, "test-default", "--incorrect--", "test-default", ""),
    (True, False, "test-default", "--incorrect--", "test-default", ""),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_value_setter_succeeds_sets_ui(_, qtbot: QtBot, enable_protocols, no_proto_val, value,
                                              expected_protocol, expected_label, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option=no_proto_val)
    qtbot.add_widget(widget)
    assert widget.protocol_combo.currentText() == no_proto_val
    assert widget.selector_label.text() == ""
    widget.value = value
    assert widget.protocol_combo.currentText() == expected_protocol
    assert widget.selector_label.text() == expected_label


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("enable_fields,value,expected_search_string", [
    (True, "", ""),
    (True, "test/prop", "test/prop"),
    (True, "test/prop#field", "test/prop#field"),
    (True, "rda3:///test/prop", "test/prop"),
    (True, "rda3:///test/prop#field", "test/prop#field"),
    (True, "rda3://srv/test/prop", "test/prop"),
    (True, "rda3://srv/test/prop#field", "test/prop#field"),
    (True, "unknown:///test/prop", "test/prop"),
    (True, "unknown:///test/prop#field", "test/prop#field"),
    (True, "unknown://srv/test/prop", "test/prop"),
    (True, "unknown://srv/test/prop#field", "test/prop#field"),
    (False, "", ""),
    (False, "test/prop", "test/prop"),
    (False, "test/prop#field", "test/prop"),
    (False, "rda3:///test/prop", "test/prop"),
    (False, "rda3:///test/prop#field", "test/prop"),
    (False, "rda3://srv/test/prop", "test/prop"),
    (False, "rda3://srv/test/prop#field", "test/prop"),
    (False, "unknown:///test/prop", "test/prop"),
    (False, "unknown:///test/prop#field", "test/prop"),
    (False, "unknown://srv/test/prop", "test/prop"),
    (False, "unknown://srv/test/prop#field", "test/prop"),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_value_setter_succeeds_requests_new_search(qtbot: QtBot, value, expected_search_string,
                                                          enable_protocols, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    with mock.patch.object(widget, "_on_search_requested", new_callable=AsyncMock) as on_search_requested:
        assert widget.search_edit.text() == ""
        on_search_requested.assert_not_called()
        widget.value = value
        on_search_requested.assert_called_once_with(expected_search_string)
        assert widget.search_edit.text() == expected_search_string


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("initial_val", ["", "test/prop"])
@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("enable_fields", [True, False])
def test_widget_value_setter_fails_search_not_requested(qtbot: QtBot, initial_val, enable_protocols, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    with mock.patch.object(widget, "_on_search_requested", new_callable=AsyncMock) as on_search_requested:
        widget.value = initial_val
        assert widget.search_edit.text() == initial_val
        on_search_requested.reset_mock()
        widget.value = "--incorrect--"
        on_search_requested.assert_not_called()
        assert widget.search_edit.text() == initial_val


@pytest.mark.parametrize("enable_protocols,enable_fields,initial_val,expected_initial_proto,expected_initial_label", [
    (False, True, "", "", ""),
    (False, True, "test/prop", "", "test/prop"),
    (False, True, "rda3:///test/prop#field", "", "test/prop#field"),
    (True, True, "", "", ""),
    (True, True, "test/prop", "", "test/prop"),
    (True, True, "rda3:///test/prop#field", "RDA3", "rda3:///test/prop#field"),
    (False, False, "", "", ""),
    (False, False, "test/prop", "", "test/prop"),
    (False, False, "rda3:///test/prop#field", "", "test/prop"),
    (True, False, "", "", ""),
    (True, False, "test/prop", "", "test/prop"),
    (True, False, "rda3:///test/prop#field", "RDA3", "rda3:///test/prop"),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_value_setter_fails_no_ui_set(_, qtbot: QtBot, initial_val, expected_initial_proto, enable_protocols,
                                             expected_initial_label, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
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
@pytest.mark.parametrize("enable_fields", [True, False])
@mock.patch("qtpy.QtWidgets.QWidget.keyPressEvent")
def test_widget_enter_key_not_closing(keyPressEvent, qtbot: QtBot, key, expect_fire, enable_protocols, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
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
@pytest.mark.parametrize("enable_fields", [True, False])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._cancel_running_tasks")
def test_widget_stops_active_tasks_on_hide(cancel_running_tasks, qtbot: QtBot, enable_protocols, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
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
    widget = ParameterSelector(enable_protocols=True, enable_fields=True, no_protocol_option=no_proto_text)
    qtbot.add_widget(widget)
    widget.value = initial_val
    # Simulate user selection event
    widget.protocol_combo.setCurrentText(selected_proto)
    widget.protocol_combo.activated.emit(widget.protocol_combo.currentIndex())
    assert widget.value == expected_val


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("enable_protocols,enable_fields,proto,selected_dev,selected_prop,selected_field,expected_dev,expected_prop,expected_field,expected_label", [
    (False, True, None, 0, 0, -1, "dev1", "prop1", None, "dev1/prop1"),
    (False, True, None, 1, 0, -1, "dev2", "prop2", None, "dev2/prop2"),
    (False, True, None, 1, 0, 99, "dev2", "prop2", None, "dev2/prop2"),
    (False, True, None, 1, 0, 0, "dev2", "prop2", "field2", "dev2/prop2#field2"),
    (False, True, None, 2, 0, 0, "dev3", "prop3.1", "field3.1.1", "dev3/prop3.1#field3.1.1"),
    (False, True, None, 2, 1, 0, "dev3", "prop3.2", "field3.2.1", "dev3/prop3.2#field3.2.1"),
    (False, True, None, 2, 1, 1, "dev3", "prop3.2", "field3.2.2", "dev3/prop3.2#field3.2.2"),
    (True, True, "", 0, 0, -1, "dev1", "prop1", None, "dev1/prop1"),
    (True, True, "", 1, 0, -1, "dev2", "prop2", None, "dev2/prop2"),
    (True, True, "", 1, 0, 99, "dev2", "prop2", None, "dev2/prop2"),
    (True, True, "", 1, 0, 0, "dev2", "prop2", "field2", "dev2/prop2#field2"),
    (True, True, "", 2, 0, 0, "dev3", "prop3.1", "field3.1.1", "dev3/prop3.1#field3.1.1"),
    (True, True, "", 2, 1, 0, "dev3", "prop3.2", "field3.2.1", "dev3/prop3.2#field3.2.1"),
    (True, True, "", 2, 1, 1, "dev3", "prop3.2", "field3.2.2", "dev3/prop3.2#field3.2.2"),
    (True, True, "rda3", 0, 0, -1, "dev1", "prop1", None, "rda3:///dev1/prop1"),
    (True, True, "rda3", 1, 0, -1, "dev2", "prop2", None, "rda3:///dev2/prop2"),
    (True, True, "rda3", 1, 0, 99, "dev2", "prop2", None, "rda3:///dev2/prop2"),
    (True, True, "rda3", 1, 0, 0, "dev2", "prop2", "field2", "rda3:///dev2/prop2#field2"),
    (True, True, "rda3", 2, 0, 0, "dev3", "prop3.1", "field3.1.1", "rda3:///dev3/prop3.1#field3.1.1"),
    (True, True, "rda3", 2, 1, 0, "dev3", "prop3.2", "field3.2.1", "rda3:///dev3/prop3.2#field3.2.1"),
    (True, True, "rda3", 2, 1, 1, "dev3", "prop3.2", "field3.2.2", "rda3:///dev3/prop3.2#field3.2.2"),
    (False, False, None, 0, 0, -1, "dev1", "prop1", None, "dev1/prop1"),
    (False, False, None, 1, 0, -1, "dev2", "prop2", None, "dev2/prop2"),
    (False, False, None, 1, 0, 99, "dev2", "prop2", None, "dev2/prop2"),
    (False, False, None, 1, 0, 0, "dev2", "prop2", None, "dev2/prop2"),
    (False, False, None, 2, 0, 0, "dev3", "prop3.1", None, "dev3/prop3.1"),
    (False, False, None, 2, 1, 0, "dev3", "prop3.2", None, "dev3/prop3.2"),
    (False, False, None, 2, 1, 1, "dev3", "prop3.2", None, "dev3/prop3.2"),
    (True, False, "", 0, 0, -1, "dev1", "prop1", None, "dev1/prop1"),
    (True, False, "", 1, 0, -1, "dev2", "prop2", None, "dev2/prop2"),
    (True, False, "", 1, 0, 99, "dev2", "prop2", None, "dev2/prop2"),
    (True, False, "", 1, 0, 0, "dev2", "prop2", None, "dev2/prop2"),
    (True, False, "", 2, 0, 0, "dev3", "prop3.1", None, "dev3/prop3.1"),
    (True, False, "", 2, 1, 0, "dev3", "prop3.2", None, "dev3/prop3.2"),
    (True, False, "", 2, 1, 1, "dev3", "prop3.2", None, "dev3/prop3.2"),
    (True, False, "rda3", 0, 0, -1, "dev1", "prop1", None, "rda3:///dev1/prop1"),
    (True, False, "rda3", 1, 0, -1, "dev2", "prop2", None, "rda3:///dev2/prop2"),
    (True, False, "rda3", 1, 0, 99, "dev2", "prop2", None, "rda3:///dev2/prop2"),
    (True, False, "rda3", 1, 0, 0, "dev2", "prop2", None, "rda3:///dev2/prop2"),
    (True, False, "rda3", 2, 0, 0, "dev3", "prop3.1", None, "rda3:///dev3/prop3.1"),
    (True, False, "rda3", 2, 1, 0, "dev3", "prop3.2", None, "rda3:///dev3/prop3.2"),
    (True, False, "rda3", 2, 1, 1, "dev3", "prop3.2", None, "rda3:///dev3/prop3.2"),
])
def test_widget_on_result_changed_sets_new_value(qtbot: QtBot, selected_dev, selected_field, selected_prop, proto,
                                                 expected_label, expected_field, expected_prop, expected_dev,
                                                 enable_protocols, enable_fields):
    data = [
        ("dev1", [("prop1", [])]),
        ("dev2", [("prop2", ["field2"])]),
        ("dev3", [("prop3.1", ["field3.1.1"]), ("prop3.2", ["field3.2.1", "field3.2.2"])]),
    ]
    widget = ParameterSelector(enable_protocols=enable_protocols, enable_fields=enable_fields, no_protocol_option="")
    qtbot.add_widget(widget)
    if enable_protocols:
        widget.protocol_combo.setCurrentText(proto.upper())
        widget._on_protocol_selected()
    assert widget.selector_label.text() == ""
    widget._root_model.set_data(mock.MagicMock(), data)  # type: ignore
    widget.dev_proxy.selected_idx = selected_dev
    widget.prop_proxy.selected_idx = selected_prop
    widget.field_proxy.selected_idx = selected_field
    widget._on_result_changed()
    assert widget._selected_value == ParameterName(device=expected_dev,
                                                   prop=expected_prop,
                                                   field=expected_field,
                                                   service=None,
                                                   protocol=proto or None)
    assert widget.selector_label.text() == expected_label


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("enable_protocols,proto,selected_dev,selected_prop,selected_field", [
    (False, None, -1, 0, -1),
    (False, None, 0, -1, -1),
    (False, None, -1, 0, 0),
    (False, None, 0, -1, 0),
    (False, None, 3, 0, -1),
    (True, "", -1, 0, -1),
    (True, "", 0, -1, -1),
    (True, "", -1, 0, 0),
    (True, "", 0, -1, 0),
    (True, "", 3, 0, -1),
    (True, "rda3", -1, 0, -1),
    (True, "rda3", 0, -1, -1),
    (True, "rda3", -1, 0, 0),
    (True, "rda3", 0, -1, 0),
    (True, "rda3", 3, 0, -1),
])
def test_widget_on_result_changed_fails_to_set_new_value(qtbot: QtBot, selected_dev, selected_field, selected_prop,
                                                         proto, enable_protocols):
    data = [
        ("dev1", [("prop1", [])]),
        ("dev2", [("prop2", ["field2"])]),
        ("dev3", [("prop3.1", ["field3.1.1"]), ("prop3.2", ["field3.2.1", "field3.2.2"])]),
        ("#wrong#device#name", [("prop4", [])]),
    ]
    widget = ParameterSelector(enable_protocols=enable_protocols, enable_fields=True, no_protocol_option="")
    qtbot.add_widget(widget)
    if enable_protocols:
        widget.protocol_combo.setCurrentText(proto.upper())
        widget._on_protocol_selected()
    assert widget.selector_label.text() == ""
    widget._root_model.set_data(mock.MagicMock(), data)  # type: ignore
    widget.dev_proxy.selected_idx = selected_dev
    widget.prop_proxy.selected_idx = selected_prop
    widget.field_proxy.selected_idx = selected_field
    widget._on_result_changed()
    assert widget._selected_value == ParameterName(device="",
                                                   prop="",
                                                   protocol=proto or None)
    assert widget.selector_label.text() == ""


@pytest.mark.parametrize("loading,expect_shown", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("initially_shown", [True, False])
@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("enable_fields", [True, False])
def test_widget_on_model_loading_changed_controls_aux_indicator(qtbot: QtBot, loading, expect_shown, enable_protocols,
                                                                initially_shown, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols, enable_fields=enable_fields, no_protocol_option="")
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    start = mock.Mock()
    stop = mock.Mock()
    widget.aux_activity_indicator.startAnimation = start
    widget.aux_activity_indicator.stopAnimation = stop
    if initially_shown:
        widget.aux_activity_indicator.show()
    start.assert_not_called()
    stop.assert_not_called()
    widget.stack_widget.setCurrentIndex(ParameterSelector.NetworkRequestStatus.COMPLETE.value)  # To expose aux indicator
    widget._on_model_loading_changed(loading)
    if expect_shown:
        assert widget.aux_activity_indicator.isVisible()
        start.assert_called_once_with()
        stop.assert_not_called()
    else:
        assert widget.aux_activity_indicator.isHidden()
        start.assert_not_called()
        stop.assert_called_once_with()


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("text", [
    "",
    "test",
    "test/prop#field",
])
@pytest.mark.parametrize("enable_fields", [True, False])
@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_start_search_calls_method_with_text(qtbot: QtBot, text, enable_protocols, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    widget.search_edit.setText(text)
    with mock.patch.object(widget, "_on_search_requested", new_callable=AsyncMock) as on_search_requested:
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
@pytest.mark.parametrize("enable_fields", [True, False])
def test_widget_update_from_status(qtbot: QtBot, status, expect_animation_started, expect_results_enabled,
                                   expect_search_enabled, expected_page_idx, enable_protocols, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    widget._update_from_status(status)
    assert widget.activity_indicator.animating == expect_animation_started
    assert widget.stack_widget.currentIndex() == expected_page_idx
    assert widget.search_btn.isEnabled() == expect_search_enabled
    assert widget.search_edit.isEnabled() == expect_search_enabled
    assert widget.results_group.isEnabled() == expect_results_enabled
    # Stop timers running inside animation so that consecutive tests don't break
    widget.activity_indicator.stopAnimation()


@pytest.mark.parametrize("enable_protocols,enable_fields,starting_val,expected_initial_label,expected_initial_dev,expected_initial_prop,expected_initial_field,expected_initial_proto", [
    (True, True, "", "", "", "", None, None),
    (True, True, "test/prop", "test/prop", "test", "prop", None, None),
    (True, True, "test/prop#field", "test/prop#field", "test", "prop", "field", None),
    (True, True, "rda3:///test/prop", "rda3:///test/prop", "test", "prop", None, "rda3"),
    (False, True, "", "", "", "", None, None),
    (False, True, "test/prop", "test/prop", "test", "prop", None, None),
    (False, True, "test/prop#field", "test/prop#field", "test", "prop", "field", None),
    (False, True, "rda3:///test/prop", "test/prop", "test", "prop", None, None),
    (True, False, "", "", "", "", None, None),
    (True, False, "test/prop", "test/prop", "test", "prop", None, None),
    (True, False, "test/prop#field", "test/prop", "test", "prop", None, None),
    (True, False, "rda3:///test/prop", "rda3:///test/prop", "test", "prop", None, "rda3"),
    (False, False, "", "", "", "", None, None),
    (False, False, "test/prop", "test/prop", "test", "prop", None, None),
    (False, False, "test/prop#field", "test/prop", "test", "prop", None, None),
    (False, False, "rda3:///test/prop", "test/prop", "test", "prop", None, None),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector._start_search")
def test_widget_reset_selected_value(_, qtbot: QtBot, enable_protocols, starting_val, expected_initial_proto,
                                     expected_initial_dev, expected_initial_field, expected_initial_prop,
                                     expected_initial_label, enable_fields):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
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
    widget = ParameterSelector(enable_protocols=enable_protocols, enable_fields=True, no_protocol_option="")
    qtbot.add_widget(widget)
    task_mock = mock.Mock()
    widget._active_ccda_task = task_mock if task_exists else None
    root_model_mock = mock.MagicMock()
    widget._root_model = root_model_mock
    widget._cancel_running_tasks()
    if should_cancel:
        task_mock.cancel.assert_called_once_with()
    else:
        task_mock.cancel.assert_not_called()
    root_model_mock.cancel_active_requests.assert_called_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize("search_string", ["", " ", "  ", "\t", "\n"])
@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("enable_fields", [True, False])
def test_widget_on_search_requested_noop_with_empty_string(qtbot: QtBot, enable_protocols, enable_fields,
                                                           search_string, event_loop):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    with mock.patch.object(widget, "_update_from_status") as update_from_status:
        with mock.patch.object(widget, "_reset_selected_value") as reset_selected_value:
            event_loop.run_until_complete(widget._on_search_requested(search_string))
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
@pytest.mark.parametrize("enable_fields", [True, False])
def test_widget_on_search_requested_sets_in_progress_ui(qtbot: QtBot, enable_protocols, search_string, event_loop,
                                                        expected_hint, expected_lookup, enable_fields):

    class TestException(Exception):
        pass

    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    assert widget.activity_indicator.hint == ""

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, side_effect=TestException) as look_up_ccda:
        look_up_ccda.assert_not_called()
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            with mock.patch.object(widget, "_reset_selected_value") as reset_selected_value:
                event_loop.run_until_complete(widget._on_search_requested(search_string))
                # The second call is expected to be a failure, because we purposefully throw an exception for early exit,
                # so it will re-render the UI to failure.
                assert update_from_status.call_args_list == [
                    mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                    mock.call(ParameterSelector.NetworkRequestStatus.FAILED),
                ]
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
def test_widget_on_search_requested_rolls_back_ui_on_cancel(qtbot: QtBot, enable_protocols, search_string,
                                                            prev_status, expected_new_status, event_loop):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=True,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    widget._update_from_status(prev_status)  # Sets to curr_search_status
    widget._update_from_status(ParameterSelector.NetworkRequestStatus.COMPLETE)  # Elevates to prev_search_status
    assert widget.err_label.text() == "Start by typing the device name into the field above!"

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, side_effect=CancelledError):
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            event_loop.run_until_complete(widget._on_search_requested(search_string))
            # First call inevitably will be with IN_PROGRESS, because that's what activating the background task
            # does
            assert update_from_status.call_args_list == [
                mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                mock.call(expected_new_status),
            ]
            assert widget.err_label.text() == "Start by typing the device name into the field above!"


@pytest.mark.asyncio
@pytest.mark.parametrize("prev_status", [
    ParameterSelector.NetworkRequestStatus.COMPLETE,
    ParameterSelector.NetworkRequestStatus.FAILED,
    ParameterSelector.NetworkRequestStatus.IN_PROGRESS,
])
@pytest.mark.parametrize("search_string", ["TEST.DEV", "test/prop#field "])
@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("enable_fields", [True, False])
def test_widget_on_search_requested_sets_ui_on_error(qtbot: QtBot, enable_protocols, search_string, prev_status,
                                                     enable_fields, event_loop):
    class TestException(Exception):
        pass

    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    orig_results_name = widget.results_group.title()
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    widget._update_from_status(prev_status)  # Just check that this does not influence anything
    assert widget.err_label.text() == "Start by typing the device name into the field above!"

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, side_effect=TestException("test error message")):
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            event_loop.run_until_complete(widget._on_search_requested(search_string))
            # First call inevitably will be with IN_PROGRESS, because that's what activating the background task
            # does
            assert update_from_status.call_args_list == [
                mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                mock.call(ParameterSelector.NetworkRequestStatus.FAILED),
            ]
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
@pytest.mark.parametrize("results", [
    [],
    [("dev1", [])],
    [("dev1", []), ("dev2", [("prop1", [])]), ("dev3", [("prop2", ["field1"])])],
])
@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("enable_fields", [True, False])
def test_widget_on_search_requested_success_sets_ui(qtbot: QtBot, enable_protocols, search_string, prev_status,
                                                    expected_group_name, results, enable_fields, event_loop):
    widget = ParameterSelector(enable_protocols=enable_protocols,
                               enable_fields=enable_fields,
                               no_protocol_option="")
    qtbot.add_widget(widget)
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    root_model = mock.MagicMock()
    widget._root_model = root_model
    widget._update_from_status(prev_status)  # Just check that this does not influence anything
    assert widget.err_label.text() == "Start by typing the device name into the field above!"
    mocked_iterator = mock.MagicMock()

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, return_value=(mocked_iterator, results)):
        with mock.patch.object(widget, "_update_from_status") as update_from_status:
            event_loop.run_until_complete(widget._on_search_requested(search_string))
            # First call inevitably will be with IN_PROGRESS, because that's what activating the background task
            # does
            assert update_from_status.call_args_list == [
                mock.call(ParameterSelector.NetworkRequestStatus.IN_PROGRESS),
                mock.call(ParameterSelector.NetworkRequestStatus.COMPLETE),
            ]
            assert widget.err_label.text() == "Start by typing the device name into the field above!"
            assert widget.results_group.title() == expected_group_name
            root_model.set_data.assert_called_once_with(mocked_iterator, results)


@pytest.mark.asyncio
@pytest.mark.parametrize("prev_status", [
    ParameterSelector.NetworkRequestStatus.COMPLETE,
    ParameterSelector.NetworkRequestStatus.FAILED,
    ParameterSelector.NetworkRequestStatus.IN_PROGRESS,
])
@pytest.mark.parametrize("results,expect_select_first", [
    ([], False),
    ([("dev1", [])], True),
    ([("dev1", []), ("dev2", [("prop1", [])]), ("dev3", [("prop2", ["field1"])])], False),
])
@pytest.mark.parametrize("search_string", ["TEST.DEV", "test/prop#field "])
@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_on_search_requested_success_selects_when_only_result(qtbot: QtBot, enable_protocols, search_string,
                                                                     prev_status, results, expect_select_first,
                                                                     event_loop):
    widget = ParameterSelector(enable_protocols=enable_protocols, enable_fields=True, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
    mocked_proxy = mock.MagicMock()
    widget.dev_proxy = mocked_proxy
    widget._root_model = mock.MagicMock()  # Prevent set_data being called into the real model
    widget._update_from_status(prev_status)  # Just check that this does not influence anything
    assert widget.err_label.text() == "Start by typing the device name into the field above!"
    mocked_iterator = mock.MagicMock()

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, return_value=(mocked_iterator, results)):
        event_loop.run_until_complete(widget._on_search_requested(search_string))
        if expect_select_first:
            mocked_proxy.update_selection.assert_called_once_with(0)
        else:
            mocked_proxy.update_selection.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("search_string,expect_dev,expect_prop,expect_field", [
    ("nonexisting", -1, -1, -1),
    ("dev1", 0, -1, -1),
    ("dev1/prop1", 0, 0, -1),
    ("dev1/prop1#nonexistingfield", 0, 0, -1),
    ("dev2", 1, -1, -1),
    ("dev2/prop2", 1, 0, -1),
    ("dev2/prop2#field2", 1, 0, 0),
    ("dev3", 2, -1, -1),
    ("dev3/prop3.1", 2, 0, -1),
    ("dev3/prop3.2", 2, 1, -1),
    ("dev3/prop3.1#field3.1.1", 2, 0, 0),
    ("dev3/prop3.2#field3.2.1", 2, 1, 0),
    ("dev3/prop3.2#field3.2.2", 2, 1, 1),
    ("dev3/prop3.2#nonexisting", 2, 1, -1),
])
@pytest.mark.parametrize("enable_protocols", [True, False])
def test_widget_on_search_requested_success_selects_appropriate_result(qtbot: QtBot, enable_protocols,
                                                                       search_string, expect_dev, expect_field,
                                                                       expect_prop, event_loop):
    data = [
        ("dev1", [("prop1", [])]),
        ("dev2", [("prop2", ["field2"])]),
        ("dev3", [("prop3.1", ["field3.1.1"]), ("prop3.2", ["field3.2.1", "field3.2.2"])]),
    ]
    widget = ParameterSelector(enable_protocols=enable_protocols, enable_fields=True, no_protocol_option="")
    qtbot.add_widget(widget)
    widget.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error

    def update_selection(val, proxy):
        proxy.selected_idx = val

    dev_proxy = mock.MagicMock()
    dev_proxy.selected_idx = -1
    prop_proxy = mock.MagicMock()
    prop_proxy.selected_idx = -1
    field_proxy = mock.MagicMock()
    field_proxy.selected_idx = -1
    dev_proxy.update_selection.side_effect = functools.partial(update_selection, proxy=dev_proxy)
    prop_proxy.update_selection.side_effect = functools.partial(update_selection, proxy=prop_proxy)
    field_proxy.update_selection.side_effect = functools.partial(update_selection, proxy=field_proxy)
    widget.dev_proxy = dev_proxy
    widget.prop_proxy = prop_proxy
    widget.field_proxy = field_proxy
    widget._root_model = mock.MagicMock()  # Prevent set_data being called into the real model
    mocked_iterator = mock.MagicMock()

    # This mock has to stay in the test body, otherwise it's not propagated and is recognized as original function
    with mock.patch("accwidgets.parameter_selector._dialog.look_up_ccda", new_callable=AsyncMock, return_value=(mocked_iterator, data)):
        event_loop.run_until_complete(widget._on_search_requested(search_string))
        for proxy, expected_idx in zip([dev_proxy, prop_proxy, field_proxy], [expect_dev, expect_prop, expect_field]):
            assert proxy.selected_idx == expected_idx


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
def test_dialog_initial_value_affects_widget(qtbot: QtBot, enable_protocols, initial_val, expected_val):
    dialog = ParameterSelectorDialog(enable_protocols=enable_protocols, initial_value=initial_val)
    qtbot.add_widget(dialog)
    assert dialog.value == expected_val


@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("enable_fields", [True, False])
@pytest.mark.parametrize("set_no_proto,expected_no_proto", [
    (None, "Omit protocol"),
    ("", ""),
    ("Test", "Test"),
])
@mock.patch("accwidgets.parameter_selector._dialog.ParameterSelector")
@mock.patch("accwidgets.parameter_selector._dialog.QVBoxLayout.addWidget")
def test_dialog_enable_protocols_affects_widget(_, ParameterSelector, qtbot: QtBot, enable_protocols, set_no_proto,
                                                expected_no_proto, retain_no_protocol_option, enable_fields):
    _ = retain_no_protocol_option
    if set_no_proto is not None:
        ParameterSelectorDialog.no_protocol_option = set_no_proto
    dialog = ParameterSelectorDialog(enable_protocols=enable_protocols, enable_fields=enable_fields)
    qtbot.add_widget(dialog)
    ParameterSelector.assert_called_once_with(parent=dialog,
                                              enable_protocols=enable_protocols,
                                              enable_fields=enable_fields,
                                              no_protocol_option=expected_no_proto)


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("btn,expected_result", [
    (QDialogButtonBox.Ok, QDialog.Accepted),
    (QDialogButtonBox.Cancel, QDialog.Rejected),
])
def test_dialog_buttonbox_trigger(qtbot: QtBot, btn, expected_result):
    dialog = ParameterSelectorDialog()
    qtbot.add_widget(dialog)
    buttons = next(iter(c for c in dialog.children() if isinstance(c, QDialogButtonBox)))
    dialog_button = buttons.button(btn)
    print(dialog_button)
    qtbot.mouseClick(dialog_button, Qt.LeftButton)
    assert dialog.result() == expected_result
