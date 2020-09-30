import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtGui import QTextDocument
from accwidgets.log_console._search_dialog import LogSearchDialog


def test_search_dialog_init_label_empty(qtbot: QtBot):
    widget = LogSearchDialog()
    qtbot.add_widget(widget)
    assert widget.warn_label.text() == ""


@pytest.mark.parametrize("found,expected_label", [
    (True, ""),
    (False, "No results were found!"),
])
def test_search_dialog_on_search_result_sets_label(qtbot: QtBot, found, expected_label):
    widget = LogSearchDialog()
    qtbot.add_widget(widget)
    widget.on_search_result(found)
    assert widget.warn_label.text() == expected_label


@pytest.mark.parametrize("check_case,check_wrap,check_reverse,search_text,expected_args", [
    (False, False, False, "custom text", ["custom text", QTextDocument.FindFlag()]),
    (False, False, True, "custom text", ["custom text", QTextDocument.FindBackward]),
    (False, True, False, "custom text", ["custom text", QTextDocument.FindWholeWords]),
    (False, True, True, "custom text", ["custom text", QTextDocument.FindWholeWords | QTextDocument.FindBackward]),
    (True, False, False, "custom text", ["custom text", QTextDocument.FindCaseSensitively]),
    (True, False, True, "custom text", ["custom text", QTextDocument.FindCaseSensitively | QTextDocument.FindBackward]),
    (True, True, False, "custom text", ["custom text", QTextDocument.FindCaseSensitively | QTextDocument.FindWholeWords]),
    (True, True, True, "custom text", ["custom text", QTextDocument.FindCaseSensitively | QTextDocument.FindWholeWords | QTextDocument.FindBackward]),
    (False, False, False, "", ["", QTextDocument.FindFlag()]),
    (False, False, True, "", ["", QTextDocument.FindBackward]),
    (False, True, False, "", ["", QTextDocument.FindWholeWords]),
    (False, True, True, "", ["", QTextDocument.FindWholeWords | QTextDocument.FindBackward]),
    (True, False, False, "", ["", QTextDocument.FindCaseSensitively]),
    (True, False, True, "", ["", QTextDocument.FindCaseSensitively | QTextDocument.FindBackward]),
    (True, True, False, "", ["", QTextDocument.FindCaseSensitively | QTextDocument.FindWholeWords]),
    (True, True, True, "", ["", QTextDocument.FindCaseSensitively | QTextDocument.FindWholeWords | QTextDocument.FindBackward]),
])
def test_search_dialog_on_search_emits_signal(qtbot: QtBot, check_reverse, check_wrap, check_case, search_text, expected_args):
    widget = LogSearchDialog()
    qtbot.add_widget(widget)
    widget.check_wrap.setChecked(check_wrap)
    widget.check_case.setChecked(check_case)
    widget.check_reverse.setChecked(check_reverse)
    widget.search_edit.setText(search_text)
    with qtbot.wait_signal(widget.search_requested) as blocker:
        widget.search_btn.click()
    assert blocker.args == expected_args


@pytest.mark.parametrize("initial_checked,new_val,expect_notify,notify_payload", [
    (False, False, False, False),
    (False, True, True, True),
    (True, False, True, False),
    (True, True, False, False),
])
def test_search_dialog_reverse_checkbox_emits_signal(qtbot: QtBot, initial_checked, new_val, expect_notify, notify_payload):
    widget = LogSearchDialog()
    qtbot.add_widget(widget)
    widget.check_reverse.setChecked(initial_checked)
    if expect_notify:
        with qtbot.wait_signal(widget.search_direction_changed) as blocker:
            widget.check_reverse.setChecked(new_val)
        assert blocker.args == [notify_payload]
    else:
        with qtbot.assert_not_emitted(widget.search_direction_changed):
            widget.check_reverse.setChecked(new_val)
