import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialogButtonBox, QDialog
from accwidgets.cycle_selector import CycleSelectorDialog, CycleSelectorModel, CycleSelectorValue


def test_cycle_dialog_init_model_propagated(qtbot: QtBot):
    model = CycleSelectorModel()
    dialog = CycleSelectorDialog(model=model)
    qtbot.add_widget(dialog)
    assert dialog._sel.model is model


@pytest.mark.parametrize("only_users", [True, False])
@pytest.mark.parametrize("allow_all", [True, False])
@pytest.mark.parametrize("enforced_domain", [None, "LHC"])
@pytest.mark.parametrize("require_selector,value", [
    (True, CycleSelectorValue(domain="LHC", group="USER", line="ALL")),
    (True, "LHC.USER.ALL"),
    (False, None),
    (False, CycleSelectorValue(domain="LHC", group="USER", line="ALL")),
    (False, "LHC.USER.ALL"),
])
def test_cycle_dialog_proxies_props(qtbot: QtBot, only_users, allow_all, enforced_domain, require_selector, value):
    dialog = CycleSelectorDialog()
    qtbot.add_widget(dialog)
    dialog.onlyUsers = only_users
    dialog.allowAllUser = allow_all
    dialog.enforcedDomain = enforced_domain
    dialog.value = value
    dialog.requireSelector = require_selector
    assert dialog._sel.onlyUsers is only_users
    assert dialog._sel.allowAllUser is allow_all
    assert dialog._sel.enforcedDomain == enforced_domain
    assert dialog._sel.requireSelector is require_selector
    assert str(dialog._sel.value) == str(value)


@pytest.mark.parametrize("orig_val,new_val,expected_signal_payload", [
    (None, None, None),
    (None, "LHC.USER.ALL", "LHC.USER.ALL"),
    ("LHC.USER.ALL", None, ""),
    ("LHC.USER.ALL", "SPS.USER.MD1", "SPS.USER.MD1"),
])
def test_cycle_dialog_value_signal(qtbot: QtBot, orig_val, new_val, expected_signal_payload):
    dialog = CycleSelectorDialog()
    qtbot.add_widget(dialog)
    dialog.value = orig_val
    with qtbot.wait_signal(dialog.valueChanged, raising=False, timeout=100) as blocker:
        dialog.value = new_val
    if expected_signal_payload is None:
        assert not blocker.signal_triggered
    else:
        assert blocker.args == [expected_signal_payload]


@pytest.mark.parametrize("btn,expected_result", [
    (QDialogButtonBox.Ok, QDialog.Accepted),
    (QDialogButtonBox.Cancel, QDialog.Rejected),
])
def test_dialog_buttonbox_trigger(qtbot: QtBot, btn, expected_result, event_loop):
    dialog = CycleSelectorDialog()
    qtbot.add_widget(dialog)
    buttons = next(iter(c for c in dialog.children() if isinstance(c, QDialogButtonBox)))
    dialog_button = buttons.button(btn)
    qtbot.mouseClick(dialog_button, Qt.LeftButton)
    assert dialog.result() == expected_result
