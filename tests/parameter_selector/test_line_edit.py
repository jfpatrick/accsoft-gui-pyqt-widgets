import pytest
from pytestqt.qtbot import QtBot
from typing import Type, Optional
from unittest import mock
from qtpy.QtCore import QLocale, QAbstractListModel, QObject, QPersistentModelIndex
from qtpy.QtWidgets import QWidget, QStyleOptionViewItem, QDialog
from accwidgets.qt import AbstractListModel, _STYLED_ITEM_DELEGATE_INDEX
from accwidgets.parameter_selector import ParameterLineEditColumnDelegate, ParameterLineEdit


@pytest.fixture
def concrete_list_model_impl() -> Type[QAbstractListModel]:
    class TestListModel(AbstractListModel, QAbstractListModel):

        def __init__(self, data, parent: Optional[QObject] = None):
            AbstractListModel.__init__(self, data)
            QAbstractListModel.__init__(self, parent)

        def create_row(self):
            return 1

    return TestListModel


def test_widget_default_config(qtbot: QtBot):
    widget = ParameterLineEdit()
    qtbot.add_widget(widget)
    assert widget.placeholderText == "device/property#field"
    assert widget.enableProtocols is False


@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("initial_val", ["", "test"])
@mock.patch("accwidgets.parameter_selector._line_edit.ParameterSelectorDialog")
def test_widget_btn_click_opens_dialog(ParameterSelectorDialog, qtbot: QtBot, enable_protocols, initial_val):
    widget = ParameterLineEdit()
    qtbot.add_widget(widget)
    widget.enableProtocols = enable_protocols
    widget.value = initial_val
    ParameterSelectorDialog.assert_not_called()
    widget._btn.click()
    ParameterSelectorDialog.assert_called_once_with(initial_value=initial_val,
                                                    enable_protocols=enable_protocols,
                                                    parent=widget)
    ParameterSelectorDialog.return_value.exec_.assert_called_once()


def test_widget_typing_notifies_value(qtbot: QtBot):
    widget = ParameterLineEdit()
    qtbot.add_widget(widget)
    for letter, expected_str in zip("text", ("t", "te", "tex", "text")):
        with qtbot.wait_signal(widget.valueChanged) as blocker:
            qtbot.keyClick(widget._line_edit, letter)
        assert blocker.args == [expected_str]


@mock.patch("accwidgets.parameter_selector._line_edit.ParameterSelectorDialog")
def test_widget_dialog_notifies_value(ParameterSelectorDialog, qtbot: QtBot):
    widget = ParameterLineEdit()
    qtbot.add_widget(widget)
    ParameterSelectorDialog.return_value.value = "test_text"
    ParameterSelectorDialog.return_value.exec_.return_value = QDialog.Accepted
    with qtbot.wait_signal(widget.valueChanged) as blocker:
        widget._btn.click()
    assert blocker.args == ["test_text"]


@pytest.mark.parametrize("initial_val", ["", "some_value"])
def test_widget_clear(qtbot: QtBot, initial_val):
    widget = ParameterLineEdit()
    qtbot.add_widget(widget)
    widget.value = initial_val
    with qtbot.wait_signal(widget.valueChanged) as blocker:
        widget.clear()
    assert blocker.args == [""]
    assert widget.value == ""
    assert widget._line_edit.text() == ""


@pytest.mark.parametrize("initial_val,expected_initial,new_val,expected_new,expect_signal", [
    ("", "", "", "", False),
    ("", "", "test", "test", True),
    ("test", "test", "", "", True),
    ("test", "test", "test", "test", False),
    ("test", "test", "test2", "test2", True),
])
def test_widget_value_prop(qtbot: QtBot, initial_val, expected_initial, new_val, expected_new, expect_signal):
    widget = ParameterLineEdit()
    qtbot.add_widget(widget)
    widget.value = initial_val
    assert widget.value == expected_initial
    with qtbot.wait_signal(widget.valueChanged, raising=False, timeout=100) as blocker:
        widget.value = new_val
    assert blocker.signal_triggered == expect_signal
    if expect_signal:
        assert blocker.args == [expected_new]
    assert widget.value == expected_new


@pytest.mark.parametrize("initial_val,expected_initial,new_val,expected_new", [
    ("", "", "", ""),
    ("", "", "test", "test"),
    ("test", "test", "", ""),
    ("test", "test", "test", "test"),
    ("test", "test", "test2", "test2"),
])
def test_widget_placeholder_prop(qtbot: QtBot, initial_val, expected_initial, new_val, expected_new):
    widget = ParameterLineEdit()
    qtbot.add_widget(widget)
    widget.placeholderText = initial_val
    assert widget.placeholderText == expected_initial
    assert widget._line_edit.placeholderText() == expected_initial
    widget.placeholderText = new_val
    assert widget.placeholderText == expected_new
    assert widget._line_edit.placeholderText() == expected_new


@pytest.mark.parametrize("enable_protocols", [True, False])
@pytest.mark.parametrize("placeholder,expected_placeholder", [
    (None, "device/property#field"),
    ("", ""),
    ("Custom placeholder", "Custom placeholder"),
])
def test_delegate_create_editor_configuration(qtbot: QtBot, concrete_list_model_impl, placeholder, enable_protocols,
                                              expected_placeholder):
    model = concrete_list_model_impl([True, False])
    delegate = ParameterLineEditColumnDelegate(enable_protocols=enable_protocols, placeholder=placeholder)

    widget = QWidget()
    qtbot.add_widget(widget)

    editor = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(3, 5))
    assert isinstance(editor, ParameterLineEdit)
    assert editor.enableProtocols == enable_protocols
    assert editor.placeholderText == expected_placeholder


def test_delegate_create_editor_has_index(qtbot: QtBot, concrete_list_model_impl):
    model = concrete_list_model_impl([True, False])
    delegate = ParameterLineEditColumnDelegate()

    widget = QWidget()
    qtbot.add_widget(widget)

    editor = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(3, 5))
    assert isinstance(editor, ParameterLineEdit)
    index = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX)
    assert isinstance(index, QPersistentModelIndex)
    assert index.row() == 3
    assert index.column() == 5


def test_delegate_set_editor_data_succeeds(qtbot: QtBot, concrete_list_model_impl):
    model = concrete_list_model_impl(["", "param/name"])
    delegate = ParameterLineEditColumnDelegate()

    widget = QWidget()
    qtbot.add_widget(widget)

    editor: ParameterLineEdit = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(0, 0))
    delegate.setEditorData(editor, model.createIndex(0, 0))
    assert editor.value == ""
    index = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX)
    assert isinstance(index, QPersistentModelIndex)
    assert index.row() == 0
    assert index.column() == 0

    delegate.setEditorData(editor, model.createIndex(1, 0))
    assert editor.value == "param/name"
    index = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX)
    assert isinstance(index, QPersistentModelIndex)
    assert index.row() == 1
    assert index.column() == 0


def test_delegate_reacts_to_value_change(qtbot: QtBot, concrete_list_model_impl):
    model = concrete_list_model_impl(["", "param/name"])
    delegate = ParameterLineEditColumnDelegate()

    widget = QWidget()
    qtbot.add_widget(widget)

    editor: ParameterLineEdit = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(0, 0))
    assert editor.value == ""
    delegate.setEditorData(editor, model.createIndex(0, 0))
    assert editor.value == ""
    assert model.raw_data == ["", "param/name"]
    editor.value = "test1"
    assert model.raw_data == ["test1", "param/name"]
    delegate.setEditorData(editor, model.createIndex(1, 0))
    assert editor.value == "param/name"
    editor.value = "test2"
    assert model.raw_data == ["test1", "test2"]


@pytest.mark.parametrize("locale", [QLocale.system(), QLocale("de")])
@pytest.mark.parametrize("value", [True, False, None, 1, "string"])
def test_delegate_display_text_empty(locale, value):
    delegate = ParameterLineEditColumnDelegate()
    assert delegate.displayText(value, locale) == ""
