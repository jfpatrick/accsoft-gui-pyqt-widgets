import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from pyrbac import Token
from qtpy.QtCore import Qt
from accwidgets.rbac import RbaToken
from accwidgets.rbac._rbac_dialog import RbaAuthDialogWidget, RbaAuthDialog, RbaAuthPopupWidget


@pytest.mark.parametrize("initial_username,login_tab,password_should_focus,expected_username_text,expected_username_enabled,expected_username_clear", [
    (None, RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, False, "", True, True),
    ("", RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, False, "", True, True),
    ("test", RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, True, "test", False, False),
    ("USER_secret", RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, True, "USER_secret", False, False),
    (None, RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, "", True, True),
    ("", RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, "", True, True),
    ("test", RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, "test", False, False),
    ("USER_secret", RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, "USER_secret", False, False),
])
def test_rbac_dialog_configures_for_predefined_username(qtbot: QtBot, initial_username, password_should_focus, login_tab,
                                                        expected_username_clear, expected_username_enabled, expected_username_text):
    widget = RbaAuthDialogWidget(initial_username=initial_username, focused_tab=login_tab)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.username.text() == expected_username_text
    assert widget.username.isEnabled() == expected_username_enabled
    assert widget.username.isClearButtonEnabled() == expected_username_clear
    assert widget.password.hasFocus() == password_should_focus


@pytest.mark.parametrize("default_tab,selected_index,location_button_visible,explicit_button_visible", [
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, 0, True, False),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, 1, False, True),
])
def test_rbac_dialog_focuses_default_tab(qtbot: QtBot, default_tab, selected_index, location_button_visible,
                                         explicit_button_visible):
    widget = RbaAuthDialogWidget(focused_tab=default_tab)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.tabs.currentIndex() == selected_index
    assert widget.loc_btn.isVisible() == location_button_visible
    assert widget.user_btn.isVisible() == explicit_button_visible


@pytest.mark.parametrize("roles,default_tab,roles_explicit_chbkx_visible,roles_loc_chkbx_visible", [
    (None, RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, True),
    (None, RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, True, False),
    ([], RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, False),
    ([], RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, False, False),
    (["Role1"], RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, False),
    (["Role1"], RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, False, False),
    (["Role1", "MCS-Role2"], RbaAuthDialogWidget.DefaultLoginTab.LOCATION, False, False),
    (["Role1", "MCS-Role2"], RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, False, False),
])
def test_rbac_dialog_configures_for_predefined_roles(qtbot: QtBot, roles, default_tab, roles_explicit_chbkx_visible,
                                                     roles_loc_chkbx_visible):
    widget = RbaAuthDialogWidget(focused_tab=default_tab, roles=roles)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.roles_explicit.isVisible() == roles_explicit_chbkx_visible
    assert widget.roles_loc.isVisible() == roles_loc_chkbx_visible


@pytest.mark.parametrize("default_tab,primary_notice,secondary_notice,primary_checkbox,secondary_checkbox", [
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, "loc_auto_info", "user_auto_info", "roles_loc", "roles_explicit"),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, "user_auto_info", "loc_auto_info", "roles_explicit", "roles_loc"),
])
def test_rbac_dialog_displays_roles_notice_on_first_checkbox_click(qtbot: QtBot, default_tab, primary_notice,
                                                                   secondary_notice, primary_checkbox,
                                                                   secondary_checkbox):
    widget = RbaAuthDialogWidget(focused_tab=default_tab)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    primary_notice_label = getattr(widget, primary_notice)
    secondary_notice_label = getattr(widget, secondary_notice)
    primary_check = getattr(widget, primary_checkbox)
    secondary_check = getattr(widget, secondary_checkbox)
    switch_tab = lambda: widget.tabs.setCurrentIndex(abs(widget.tabs.currentIndex() - 1))
    assert not primary_notice_label.isVisible()
    assert not secondary_notice_label.isVisible()
    primary_check.click()
    assert primary_check.isChecked()
    assert primary_notice_label.isVisible()
    assert not secondary_notice_label.isVisible()
    switch_tab()
    assert secondary_check.isChecked()
    assert not primary_notice_label.isVisible()
    assert secondary_notice_label.isVisible()
    switch_tab()
    assert primary_notice_label.isVisible()
    assert not secondary_notice_label.isVisible()
    assert primary_check.isChecked()
    primary_check.click()
    assert not primary_check.isChecked()
    assert primary_notice_label.isVisible()
    assert not secondary_notice_label.isVisible()
    switch_tab()
    assert not secondary_check.isChecked()
    assert not primary_notice_label.isVisible()
    assert secondary_notice_label.isVisible()
    secondary_check.click()
    assert secondary_check.isChecked()
    assert not primary_notice_label.isVisible()
    assert secondary_notice_label.isVisible()
    switch_tab()
    assert primary_check.isChecked()
    assert primary_notice_label.isVisible()
    assert not secondary_notice_label.isVisible()


@pytest.mark.parametrize("initial_error", [None, "", "test error"])
@pytest.mark.parametrize("dialog_shown,token_received,initial_password_text,expected_password_text", [
    (True, True, None, ""),
    (True, True, "", ""),
    (True, True, "test_password", ""),
    (True, False, None, ""),
    (True, False, "", ""),
    (True, False, "test_password", "test_password"),
    (False, True, None, ""),
    (False, True, "", ""),
    (False, True, "test_password", ""),
    (False, False, None, ""),
    (False, False, "", ""),
    (False, False, "test_password", ""),

])
def test_rbac_dialog_clears_on_successful_login(qtbot: QtBot, dialog_shown, token_received, initial_error,
                                                initial_password_text, expected_password_text):
    widget = RbaAuthDialogWidget()
    qtbot.add_widget(widget)
    if dialog_shown:
        with qtbot.wait_exposed(widget):
            widget.show()
    widget.user_error.setText(initial_error)
    widget.loc_error.setText(initial_error)
    widget.password.setText(initial_password_text)
    widget.on_login_status_changed(Token.create_empty_token() if token_received else None)
    assert widget.user_error.text() == ""
    assert widget.loc_error.text() == ""
    assert widget.password.text() == expected_password_text


@pytest.mark.parametrize("dialog_shown,login_method,expected_tab,error_msg,expected_loc_error,expected_explicit_error", [
    (True, RbaToken.LoginMethod.LOCATION, 0, "", "", None),
    (True, RbaToken.LoginMethod.LOCATION, 0, "test_error", "test_error", None),
    (True, RbaToken.LoginMethod.EXPLICIT, 1, "", None, ""),
    (True, RbaToken.LoginMethod.EXPLICIT, 1, "test_error", None, "test_error"),
    (True, RbaToken.LoginMethod.UNKNOWN, 0, "", None, None),
    (True, RbaToken.LoginMethod.UNKNOWN, 0, "test_error", None, None),
    (False, RbaToken.LoginMethod.LOCATION, 0, "", None, None),
    (False, RbaToken.LoginMethod.LOCATION, 0, "test_error", None, None),
    (False, RbaToken.LoginMethod.EXPLICIT, 0, "", None, None),
    (False, RbaToken.LoginMethod.EXPLICIT, 0, "test_error", None, None),
    (False, RbaToken.LoginMethod.UNKNOWN, 0, "", None, None),
    (False, RbaToken.LoginMethod.UNKNOWN, 0, "test_error", None, None),
])
def test_rbac_dialog_displays_errors_on_failed_login(qtbot: QtBot, dialog_shown, login_method, error_msg, expected_tab,
                                                     expected_loc_error, expected_explicit_error):
    widget = RbaAuthDialogWidget()
    qtbot.add_widget(widget)
    if dialog_shown:
        with qtbot.wait_exposed(widget):
            widget.show()
    widget.on_login_failed(error_msg, login_method.value)
    assert widget.user_error.isVisible() == (expected_explicit_error is not None)
    assert widget.loc_error.isVisible() == (expected_loc_error is not None)
    assert widget.tabs.currentIndex() == expected_tab
    if expected_explicit_error is not None:
        assert widget.user_error.text() == expected_explicit_error
    if expected_loc_error is not None:
        assert widget.loc_error.text() == expected_loc_error


@pytest.mark.parametrize("username_text,password_text,expected_user_error", [
    (None, None, "You must type in username and password"),
    ("", None, "You must type in username and password"),
    (None, "", "You must type in username and password"),
    ("", "", "You must type in username and password"),
    ("test", None, "You must type in password"),
    (None, "test", "You must type in username"),
    ("test", "test", None),
    ("test", "", "You must type in password"),
    ("", "test", "You must type in username"),
])
def test_rbac_dialog_displays_errors_when_explicit_fields_are_missing(qtbot: QtBot, username_text, password_text,
                                                                      expected_user_error):
    widget = RbaAuthDialogWidget(focused_tab=RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    widget.username.setText(username_text)
    widget.password.setText(password_text)
    widget.user_btn.click()
    if expected_user_error is None:
        assert widget.user_error.isHidden()
    else:
        assert widget.user_error.isVisible()
        assert widget.user_error.text() == expected_user_error


@pytest.mark.parametrize("focused_tab", [RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, RbaAuthDialogWidget.DefaultLoginTab.LOCATION])
@pytest.mark.parametrize("dialog_shown,should_animate", [
    (True, True),
    (False, False),
])
def test_rbac_dialog_animates_on_login_start(qtbot: QtBot, dialog_shown, should_animate, focused_tab):
    widget = RbaAuthDialogWidget(focused_tab=focused_tab)
    qtbot.add_widget(widget)
    if dialog_shown:
        with qtbot.wait_exposed(widget):
            widget.show()
    with mock.patch.object(widget.activity_indicator, "startAnimation") as startAnimation:
        widget.on_login_started()
        if should_animate:
            startAnimation.assert_called_once()
            assert widget.activity_stack.currentIndex() == 1
        else:
            startAnimation.assert_not_called()
            assert widget.activity_stack.currentIndex() == 0
    widget.on_login_finished()
    assert widget.activity_stack.currentIndex() == 0


@pytest.mark.parametrize("focused_tab", [RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, RbaAuthDialogWidget.DefaultLoginTab.LOCATION])
def test_rbac_dialog_clears_when_hidden(qtbot: QtBot, focused_tab):
    widget = RbaAuthDialogWidget(focused_tab=focused_tab)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    widget.password.setText("test")
    widget.user_error.setText("test")
    widget.loc_error.setText("test")
    widget.hide()
    assert widget.password.text() == ""
    assert widget.user_error.text() == ""
    assert widget.loc_error.text() == ""


@pytest.mark.parametrize("focused_field,pressed_key,expected_password_has_focus,expect_login_clicked", [
    ("username", Qt.Key_Enter, True, False),
    ("password", Qt.Key_Enter, True, True),
    ("roles_explicit", Qt.Key_Enter, False, False),
    ("username", Qt.Key_Return, True, False),
    ("password", Qt.Key_Return, True, True),
    ("roles_explicit", Qt.Key_Return, False, False),
    ("username", Qt.Key_A, False, False),
    ("password", Qt.Key_A, True, False),
    ("roles_explicit", Qt.Key_A, False, False),
    ("username", Qt.Key_Escape, False, False),
    ("password", Qt.Key_Escape, True, False),
    ("roles_explicit", Qt.Key_Escape, False, False),
])
def test_rbac_dialog_return_key_in_explicit_tab(qtbot: QtBot, focused_field, expect_login_clicked,
                                                expected_password_has_focus, pressed_key):
    widget = RbaAuthDialogWidget(focused_tab=RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT)
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    getattr(widget, focused_field).setFocus()
    with mock.patch.object(widget.user_btn, "click") as callout:
        qtbot.keyClick(widget, pressed_key)
        if expect_login_clicked:
            callout.assert_called_once()
        else:
            callout.assert_not_called()
        assert widget.password.hasFocus() == expected_password_has_focus


@pytest.mark.parametrize("default_tab,roles,username,password,checkbox,btn,expected_signal,signal_overload,expected_args", [
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, None, None, None, None, "loc_btn", "location_login", [bool], [False]),
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, [], None, None, None, "loc_btn", "location_login", [list], [[]]),
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, ["Role1"], None, None, None, "loc_btn", "location_login", [list], [["Role1"]]),
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, ["Role1", "MCS-Role2"], None, None, None, "loc_btn", "location_login", [list], [["Role1", "MCS-Role2"]]),
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, None, None, None, "roles_loc", "loc_btn", "location_login", [bool], [True]),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, None, "test_user", "test_pass", None, "user_btn", "explicit_login", [str, str, bool], ["test_user", "test_pass", False]),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, [], "test_user", "test_pass", None, "user_btn", "explicit_login", [str, str, list], ["test_user", "test_pass", []]),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, ["Role1"], "test_user", "test_pass", None, "user_btn", "explicit_login", [str, str, list], ["test_user", "test_pass", ["Role1"]]),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, ["Role1", "MCS-Role2"], "test_user", "test_pass", None, "user_btn", "explicit_login", [str, str, list], ["test_user", "test_pass", ["Role1", "MCS-Role2"]]),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, None, "test_user", "test_pass", "roles_explicit", "user_btn", "explicit_login", [str, str, bool], ["test_user", "test_pass", True]),
])
def test_rbac_dialog_signals_on_login_action(qtbot: QtBot, default_tab, username, password, btn, expected_signal,
                                             expected_args, roles, checkbox, signal_overload):
    widget = RbaAuthDialogWidget(focused_tab=default_tab, roles=roles)
    qtbot.add_widget(widget)
    if username is not None:
        widget.username.setText(username)
    if password is not None:
        widget.password.setText(password)
    if checkbox is not None:
        getattr(widget, checkbox).click()
    with qtbot.wait_signal(getattr(widget, expected_signal)[tuple(signal_overload)]) as blocker:
        getattr(widget, btn).click()
    assert blocker.args == expected_args


@pytest.mark.parametrize("roles", [
    None,
    [],
    ["Role1"],
    ["MCS-Role2"],
])
@pytest.mark.parametrize("default_tab,username,password,checkbox,btn", [
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, None, None, None, "loc_btn"),
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, None, None, "roles_loc", "loc_btn"),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, "test_user", "test_pass", None, "user_btn"),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, "test_user", "test_pass", "roles_explicit", "user_btn"),
])
def test_rbac_dialog_hides_errors_on_login_action(qtbot: QtBot, default_tab, roles, username, password, checkbox, btn):
    widget = RbaAuthDialogWidget(focused_tab=default_tab, roles=roles)
    qtbot.add_widget(widget)
    if username is not None:
        widget.username.setText(username)
    if password is not None:
        widget.password.setText(password)
    if checkbox is not None:
        getattr(widget, checkbox).click()
    with qtbot.wait_exposed(widget):
        widget.show()
    widget.loc_error.setText("Test error")
    widget.user_error.setText("Test error")
    widget.loc_error.show()
    widget.user_error.show()
    getattr(widget, btn).click()
    assert widget.loc_error.isHidden()
    assert widget.user_error.isHidden()


@pytest.mark.parametrize("roles", [
    None,
    [],
    ["Role1"],
    ["Role1", "MCS-Role2"],
])
@pytest.mark.parametrize("display_location_tab,tabs_count,loc_btn_visible", [
    (True, 2, True),
    (False, 1, False),
])
def test_rbac_dialog_roles_wrapper_removes_location_tab(qtbot: QtBot, display_location_tab, tabs_count, roles,
                                                        loc_btn_visible):
    widget = RbaAuthDialog(display_location_tab=display_location_tab,
                           new_roles=roles,
                           username="test_username")
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget._main_widget.tabs.count() == tabs_count
    assert widget._main_widget.loc_btn.isVisible() == loc_btn_visible
    assert widget._main_widget.user_btn.isVisible() != loc_btn_visible
    widget._main_widget.tabs.setCurrentIndex(1)
    assert not widget._main_widget.loc_btn.isVisible()
    assert widget._main_widget.user_btn.isVisible()


@pytest.mark.parametrize("roles", [
    None,
    [],
    ["Role1"],
    ["Role1", "MCS-Role2"],
])
@pytest.mark.parametrize("display_location_tab", [True, False])
@pytest.mark.parametrize("orig_sig,orig_overload,test_payload,expected_sig,expected_overload", [
    ("location_login", [bool], [True], "location_login", [bool]),
    ("location_login", [bool], [False], "location_login", [bool]),
    ("location_login", [list], [["test"]], "location_login", [list]),
    ("explicit_login", [str, str, bool], ["test", "test", True], "explicit_login", [str, str, bool]),
    ("explicit_login", [str, str, list], ["test", "test", ["test"]], "explicit_login", [str, str, list]),
])
def test_rbac_dialog_roles_wrapper_forwards_signals(qtbot: QtBot, orig_overload, orig_sig, test_payload, roles,
                                                    expected_overload, expected_sig, display_location_tab):
    widget = RbaAuthDialog(display_location_tab=display_location_tab,
                           new_roles=roles,
                           username="test_username")
    qtbot.add_widget(widget)
    with qtbot.wait_signal(getattr(widget, expected_sig)[tuple(expected_overload)]):
        getattr(widget._main_widget, orig_sig)[tuple(orig_overload)].emit(*test_payload)


@pytest.mark.parametrize("roles", [
    None,
    [],
    ["Role1"],
    ["Role1", "MCS-Role2"],
])
@pytest.mark.parametrize("display_location_tab", [True, False])
@pytest.mark.parametrize("orig_slot,test_payload,expected_slot", [
    ("on_login_status_changed", [None], "on_login_status_changed"),
    ("on_login_failed", ["Test error", RbaToken.LoginMethod.EXPLICIT.value], "on_login_failed"),
    ("on_login_failed", ["Test error", RbaToken.LoginMethod.UNKNOWN.value], "on_login_failed"),
    ("on_login_failed", ["Test error", RbaToken.LoginMethod.LOCATION.value], "on_login_failed"),
    ("on_login_started", [RbaToken.LoginMethod.LOCATION.value], "on_login_started"),
    ("on_login_started", [RbaToken.LoginMethod.UNKNOWN.value], "on_login_started"),
    ("on_login_started", [RbaToken.LoginMethod.EXPLICIT.value], "on_login_started"),
    ("on_login_finished", [], "on_login_finished"),
])
def test_rbac_dialog_roles_wrapper_forwards_slots(qtbot: QtBot, orig_slot, test_payload, roles, expected_slot,
                                                  display_location_tab):
    widget = RbaAuthDialog(display_location_tab=display_location_tab,
                           new_roles=roles,
                           username="test_username")
    qtbot.add_widget(widget)
    with mock.patch.object(widget._main_widget, expected_slot) as slot:
        getattr(widget, orig_slot)(*test_payload)
        slot.assert_called_once_with(*test_payload)


@pytest.mark.parametrize("roles", [
    None,
    [],
    ["Role1"],
    ["Role1", "MCS-Role2"],
])
@pytest.mark.parametrize("display_location_tab", [True, False])
def test_rbac_dialog_roles_wrapper_closes_on_successful_login(qtbot: QtBot, roles,
                                                              display_location_tab):
    widget = RbaAuthDialog(display_location_tab=display_location_tab,
                           new_roles=roles,
                           username="test_username")
    qtbot.add_widget(widget)
    with mock.patch.object(widget, "accept") as accept:
        with mock.patch.object(widget._main_widget, "on_login_status_changed") as inner_slot:
            widget.on_login_status_changed(Token.create_empty_token())
            inner_slot.assert_not_called()
            accept.assert_called_once()


@pytest.mark.parametrize("default_tab,initial_username,expect_location_button_focused,expect_username_focused,expect_password_focused", [
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, None, True, False, False),
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, "", True, False, False),
    (RbaAuthDialogWidget.DefaultLoginTab.LOCATION, "test_username", True, False, False),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, None, False, True, False),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, "", False, True, False),
    (RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT, "test_username", False, False, True),
])
def test_rbac_dialog_popup_wrapper_default_focus(qtbot: QtBot, default_tab, expect_location_button_focused,
                                                 expect_username_focused, expect_password_focused, initial_username):
    widget = RbaAuthPopupWidget(focused_tab=default_tab, initial_username=initial_username)
    with qtbot.wait_exposed(widget):
        widget.show()
    qtbot.wait(100)
    assert widget.loc_btn.hasFocus() == expect_location_button_focused
    assert widget.username.hasFocus() == expect_username_focused
    assert widget.password.hasFocus() == expect_password_focused
