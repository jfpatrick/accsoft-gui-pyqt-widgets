import pytest
from pytestqt.qtbot import QtBot
from typing import cast
from qtpy.QtCore import QTimer, Qt, QPoint
from qtpy.QtWidgets import QWidget, QToolButton, QWidgetAction
from accwidgets.cycle_selector import CycleSelectorAction, CycleSelectorValue, CycleSelectorModel


@pytest.mark.parametrize("text,value,expected_text", [
    (None, None, "Selector: ---"),
    ("", None, "Selector: ---"),
    ("Action name", None, "Action name"),
    (None, "LHC.USER.ALL", "Selector: LHC.USER.ALL"),
    ("", "LHC.USER.ALL", "Selector: LHC.USER.ALL"),
    ("Action name", "LHC.USER.ALL", "Action name"),
])
@pytest.mark.parametrize("parent_type", [None, QWidget])
def test_cycle_action_init(parent_type, qtbot: QtBot, text, expected_text, value):
    parent = None if parent_type is None else parent_type()
    if isinstance(parent, QWidget):
        qtbot.add_widget(parent)
    action = CycleSelectorAction(parent=parent, text=text)
    qtbot.add_widget(action.menu())
    action.value = value
    assert action.menu() is not None
    assert action.parent() is parent
    assert action.toolTip() == expected_text
    assert action.text() == expected_text


def test_cycle_action_init_model_propagated(qtbot):
    model = CycleSelectorModel()
    dialog = CycleSelectorAction(model=model)
    assert dialog._sel.model is model


@pytest.mark.parametrize("orig_val,new_val,expected_signal_payload", [
    (None, None, None),
    (None, "LHC.USER.ALL", "LHC.USER.ALL"),
    ("LHC.USER.ALL", None, ""),
    ("LHC.USER.ALL", "SPS.USER.MD1", "SPS.USER.MD1"),
])
def test_cycle_action_value_signal(qtbot, orig_val, new_val, expected_signal_payload):
    action = CycleSelectorAction()
    action.value = orig_val
    with qtbot.wait_signal(action.valueChanged, raising=False, timeout=100) as blocker:
        action.value = new_val
    if expected_signal_payload is None:
        assert not blocker.signal_triggered
    else:
        assert blocker.args == [expected_signal_payload]


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
def test_cycle_action_proxies_props(qtbot, only_users, allow_all, enforced_domain, require_selector, value):
    action = CycleSelectorAction()
    action.onlyUsers = only_users
    action.allowAllUser = allow_all
    action.enforcedDomain = enforced_domain
    action.value = value
    action.requireSelector = require_selector
    assert action._sel.onlyUsers is only_users
    assert action._sel.allowAllUser is allow_all
    assert action._sel.enforcedDomain == enforced_domain
    assert action._sel.requireSelector is require_selector
    assert str(action._sel.value) == str(value)


def test_cycle_action_does_not_close_menu_on_mouse_click(qtbot: QtBot, visible_qwindow, event_loop, populate_widget_menus):
    # This tests that Mouse click inside the popup does not close it, which is default QMenu behavior
    # See PopupWrapper.event
    import os
    if os.environ.get("CI", None):
        pytest.skip("This test fails in DWM, popup never shows up")

    btn = QToolButton()
    # Do not show the widget, so that we can recognize the popup window later (will be the only one visible)
    # I could not identify other signs that would be different between popup and main window (even flags)
    qtbot.add_widget(btn)
    btn.setAutoRaise(True)
    with qtbot.wait_exposed(btn):
        btn.show()
    action = CycleSelectorAction()
    populate_widget_menus(action._sel, {"LHC": {"USER": ["ALL"]}})
    btn.setDefaultAction(action)
    btn.setPopupMode(QToolButton.InstantPopup)
    menu_widget = cast(QWidgetAction, action.menu().actions()[0]).defaultWidget()

    def on_menu_visible():
        assert menu_widget.isVisible()
        window = visible_qwindow()
        qtbot.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(50, 30))  # Click inside the widget
        assert menu_widget.isVisible()
        qtbot.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(-10, -10))  # Click outside the widget
        assert not menu_widget.isVisible()

    action.menu().aboutToShow.connect(lambda: QTimer.singleShot(150, on_menu_visible))
    with qtbot.wait_signal(action.menu().aboutToHide):
        btn.click()
