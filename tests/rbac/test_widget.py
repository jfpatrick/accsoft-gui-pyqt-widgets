import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from pytestqt.exceptions import TimeoutError as QtBotTimeoutError
from typing import cast
from pyrbac import Token
from pathlib import Path
from qtpy.QtGui import QColor, QIcon
from qtpy.QtCore import QObject, Qt, QSize, QTimer, QPoint
from qtpy.QtWidgets import (QToolButton, QToolBar, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QSizePolicy,
                            QWidgetAction, QDialog, QApplication, QStackedWidget)
from accwidgets.qt import make_icon
from accwidgets.rbac import RbaButton, RbaButtonModel, RbaToken
from accwidgets.rbac._widget import RbaUserButton, RbaAuthButton, RbaAuthPopupWidget, RbaRolePicker
from .fixtures import make_token


def test_rba_button_set_model_changes_ownership(qtbot: QtBot):
    view = RbaButton()
    qtbot.add_widget(view)
    model = RbaButtonModel()
    assert model.parent() != view
    view.model = model
    assert model.parent() == view


def test_rba_button_set_model_disconnects_old_model(qtbot: QtBot):
    model = RbaButtonModel()
    view = RbaButton(model=model)
    qtbot.add_widget(view)
    assert model.receivers(model.login_succeeded) > 0
    assert model.receivers(model.login_failed) > 0
    assert model.receivers(model.login_started) > 0
    assert model.receivers(model.login_finished) > 0
    assert model.receivers(model.logout_finished) > 0
    assert model.receivers(model.token_expired) > 0
    view.model = RbaButtonModel()
    assert model.receivers(model.login_succeeded) == 0
    assert model.receivers(model.login_failed) == 0
    assert model.receivers(model.login_started) == 0
    assert model.receivers(model.login_finished) == 0
    assert model.receivers(model.logout_finished) == 0
    assert model.receivers(model.token_expired) == 0


def test_rba_button_set_model_connects_new_model(qtbot: QtBot):
    view = RbaButton()
    qtbot.add_widget(view)
    model = RbaButtonModel()
    assert model.receivers(model.login_succeeded) == 0
    assert model.receivers(model.login_failed) == 0
    assert model.receivers(model.login_started) == 0
    assert model.receivers(model.login_finished) == 0
    assert model.receivers(model.logout_finished) == 0
    assert model.receivers(model.token_expired) == 0
    view.model = model
    assert model.receivers(model.login_succeeded) > 0
    assert model.receivers(model.login_failed) > 0
    assert model.receivers(model.login_started) > 0
    assert model.receivers(model.login_finished) > 0
    assert model.receivers(model.logout_finished) > 0
    assert model.receivers(model.token_expired) > 0


def test_rba_button_init_connects_implicit_model(qtbot: QtBot):
    view = RbaButton()
    qtbot.add_widget(view)
    assert view.model.receivers(view.model.login_succeeded) > 0
    assert view.model.receivers(view.model.login_failed) > 0
    assert view.model.receivers(view.model.login_started) > 0
    assert view.model.receivers(view.model.login_finished) > 0
    assert view.model.receivers(view.model.logout_finished) > 0
    assert view.model.receivers(view.model.token_expired) > 0


def test_rba_button_init_connects_provided_model(qtbot: QtBot):
    model = RbaButtonModel()
    assert model.receivers(model.login_succeeded) == 0
    assert model.receivers(model.login_failed) == 0
    assert model.receivers(model.login_started) == 0
    assert model.receivers(model.login_finished) == 0
    assert model.receivers(model.logout_finished) == 0
    assert model.receivers(model.token_expired) == 0
    view = RbaButton(model=model)
    qtbot.add_widget(view)
    assert model.receivers(model.login_succeeded) > 0
    assert model.receivers(model.login_failed) > 0
    assert model.receivers(model.login_started) > 0
    assert model.receivers(model.login_finished) > 0
    assert model.receivers(model.logout_finished) > 0
    assert model.receivers(model.token_expired) > 0


@pytest.mark.parametrize("belongs_to_view,should_destroy", [
    (True, True),
    (False, False),
])
def test_rba_button_destroys_old_model_when_disconnecting(qtbot: QtBot, belongs_to_view, should_destroy):
    model = RbaButtonModel()
    view = RbaButton(model=model)
    qtbot.add_widget(view)
    assert model.parent() == view
    random_parent = QObject()
    if not belongs_to_view:
        model.setParent(random_parent)

    with mock.patch.object(model, "deleteLater") as deleteLater:
        view.model = RbaButtonModel()
        if should_destroy:
            deleteLater.assert_called_once()
            assert model.parent() is None
        else:
            deleteLater.assert_not_called()
            assert model.parent() is random_parent


def test_rba_button_init_creates_buttons(qtbot: QtBot):
    view = RbaButton()
    qtbot.add_widget(view)
    assert view.layout().count() == 2
    assert all(isinstance(view.layout().itemAt(i).widget(), QToolButton) for i in range(view.layout().count()))


def test_rba_button_mcs_color(qtbot: QtBot):
    view = RbaButton()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.mcsColor).name() != new_color.name()
    view.mcsColor = new_color
    assert QColor(view.mcsColor).name() == new_color.name()


def test_rba_button_tracks_when_added_to_toolbar(qtbot: QtBot):
    toolbar = QToolBar()
    qtbot.add_widget(toolbar)
    view = RbaButton()
    orig_icon_receivers = toolbar.receivers(toolbar.iconSizeChanged)
    orig_orientation_receivers = toolbar.receivers(toolbar.orientationChanged)
    toolbar.addWidget(view)
    assert toolbar.receivers(toolbar.iconSizeChanged) > orig_icon_receivers
    assert toolbar.receivers(toolbar.orientationChanged) > orig_orientation_receivers


@pytest.mark.parametrize("toolbar_w,toolbar_h", [
    (10, 10),
    (64, 64),
    (100, 200),
    (200, 100),
])
@pytest.mark.parametrize("toolbar_icon_size,new_icon_size", [
    (24, 24),
    (8, 8),
])
@pytest.mark.parametrize("orig_orientation,expected_orig_layout,toolbar_orientation,new_layout", [
    (Qt.Horizontal, QHBoxLayout, Qt.Horizontal, QHBoxLayout),
    (Qt.Horizontal, QHBoxLayout, Qt.Vertical, QVBoxLayout),
    (Qt.Vertical, QVBoxLayout, Qt.Horizontal, QHBoxLayout),
    (Qt.Vertical, QVBoxLayout, Qt.Vertical, QVBoxLayout),
])
def test_rba_button_adapts_layout_when_added_to_toolbar(qtbot: QtBot, orig_orientation, expected_orig_layout,
                                                        toolbar_icon_size, toolbar_orientation, new_layout, new_icon_size,
                                                        toolbar_w, toolbar_h):
    toolbar = QToolBar()
    toolbar.setOrientation(toolbar_orientation)
    toolbar.setIconSize(QSize(toolbar_icon_size, toolbar_icon_size))
    toolbar.resize(toolbar_w, toolbar_h)
    qtbot.add_widget(toolbar)
    view = RbaButton()
    view._on_orientation_changed(orig_orientation)
    with qtbot.wait_exposed(toolbar):
        toolbar.show()
    assert isinstance(view.layout(), expected_orig_layout)
    assert view._auth_btn.iconSize() == QSize(16, 16)
    toolbar.addWidget(view)
    assert isinstance(view.layout(), new_layout)
    assert view._auth_btn.iconSize() == QSize(new_icon_size, new_icon_size)


def test_rba_button_tracks_when_moved_to_toolbar_from_another_parent(qtbot: QtBot):
    toolbar = QToolBar()
    qtbot.add_widget(toolbar)
    orig_icon_receivers = toolbar.receivers(toolbar.iconSizeChanged)
    orig_orientation_receivers = toolbar.receivers(toolbar.orientationChanged)
    another_parent = QWidget()
    qtbot.add_widget(another_parent)
    another_parent.setLayout(QVBoxLayout())
    view = RbaButton()
    another_parent.layout().addWidget(view)
    toolbar.addWidget(view)
    assert toolbar.receivers(toolbar.iconSizeChanged) > orig_icon_receivers
    assert toolbar.receivers(toolbar.orientationChanged) > orig_orientation_receivers


@pytest.mark.parametrize("another_layout", [QVBoxLayout, QHBoxLayout, QGridLayout])
@pytest.mark.parametrize("toolbar_icon_size,new_icon_w,new_icon_h", [
    (24, 24, 24),
    (8, 8, 8),
])
@pytest.mark.parametrize("toolbar_w,toolbar_h", [
    (10, 10),
    (64, 64),
    (100, 200),
    (200, 100),
])
@pytest.mark.parametrize("toolbar_orientation,new_layout", [
    (Qt.Horizontal, QHBoxLayout),
    (Qt.Vertical, QVBoxLayout),
])
@pytest.mark.parametrize("another_parent_w,another_parent_h,expected_orig_w,expected_orig_h", [
    (10, 10, 25, 25),
    (64, 64, 58, 58),
    (100, 200, 94, 194),
    (200, 100, 194, 94),
])
def test_rba_button_adapts_layout_when_moved_to_toolbar_from_another_parent(qtbot: QtBot, another_layout,
                                                                            toolbar_icon_size, toolbar_orientation,
                                                                            new_layout, new_icon_h, new_icon_w,
                                                                            another_parent_h, another_parent_w,
                                                                            expected_orig_h, expected_orig_w,
                                                                            toolbar_h, toolbar_w):
    # We show and hide parent widgets separately: toolbar and another_parent
    # While 2 simultaneously work well on a dev machine, inside CI container, dwm struggles to present them, therefore
    # qtbot times out waiting for the second window to be exposed.
    # It is still not possible reliably layout things that stretching window keeps the button to its absolute minimum,
    # therefore it can be skipped.
    another_parent = QWidget()
    another_parent.setLayout(another_layout())
    another_parent.layout().setContentsMargins(0, 0, 0, 0)
    view = RbaButton()
    another_parent.layout().addWidget(view)
    another_parent.resize(another_parent_w, another_parent_h)
    with qtbot.wait_exposed(another_parent):
        another_parent.show()
    if another_parent.width() >= 300 or another_parent.height() >= 300:
        pytest.skip("Got unexpected window size. Presumably running in tiling window manager. Skipping...")
    assert isinstance(view.layout(), QHBoxLayout)
    assert view._auth_btn.iconSize() == QSize(expected_orig_w, expected_orig_h)
    another_parent.hide()
    toolbar = QToolBar()
    qtbot.add_widget(toolbar)
    toolbar.resize(toolbar_w, toolbar_h)
    toolbar.setOrientation(toolbar_orientation)
    toolbar.setIconSize(QSize(toolbar_icon_size, toolbar_icon_size))
    toolbar.addWidget(view)
    with qtbot.wait_exposed(toolbar):
        toolbar.show()
    assert isinstance(view.layout(), new_layout)
    assert view._auth_btn.iconSize() == QSize(new_icon_w, new_icon_h)


def test_rba_button_stops_tracking_when_moved_from_toolbar_to_another_parent(qtbot: QtBot):
    toolbar = QToolBar()
    qtbot.add_widget(toolbar)
    view = RbaButton()
    toolbar.addWidget(view)
    with qtbot.wait_exposed(toolbar):
        toolbar.show()
    orig_icon_receivers = toolbar.receivers(toolbar.iconSizeChanged)
    orig_orientation_receivers = toolbar.receivers(toolbar.orientationChanged)
    another_parent = QWidget()
    qtbot.add_widget(another_parent)
    another_parent.setLayout(QVBoxLayout())
    another_parent.layout().addWidget(view)
    with qtbot.wait_exposed(another_parent):
        another_parent.show()
    assert toolbar.receivers(toolbar.iconSizeChanged) == orig_icon_receivers - 1
    assert toolbar.receivers(toolbar.orientationChanged) == orig_orientation_receivers - 1


@pytest.mark.parametrize("another_layout", [QVBoxLayout, QHBoxLayout, QGridLayout])
@pytest.mark.parametrize("toolbar_w,toolbar_h", [
    (10, 10),
    (64, 64),
    (100, 200),
    (200, 100),
])
@pytest.mark.parametrize("toolbar_icon_size,expected_orig_icon_size", [
    (24, 24),
    (8, 8),
])
@pytest.mark.parametrize("toolbar_orientation,expected_orig_layout", [
    (Qt.Horizontal, QHBoxLayout),
    (Qt.Vertical, QVBoxLayout),
    (Qt.Horizontal, QHBoxLayout),
    (Qt.Vertical, QVBoxLayout),
])
@pytest.mark.parametrize("another_parent_w,another_parent_h,expected_new_w,expected_new_h", [
    (10, 10, 25, 25),
    (64, 64, 58, 58),
    (100, 200, 94, 194),
    (200, 100, 194, 94),
])
def test_rba_button_resets_layout_when_moved_from_toolbar_to_another_parent(qtbot: QtBot, expected_orig_icon_size,
                                                                            toolbar_w, toolbar_h,
                                                                            expected_orig_layout, another_layout,
                                                                            toolbar_icon_size, toolbar_orientation,
                                                                            another_parent_w, another_parent_h,
                                                                            expected_new_w, expected_new_h):
    # Create a single container in order to show a single window, instead of two separate: toolbar and another_parent
    # While 2 separate work well on a dev machine, inside CI container, dwm struggles to present them, therefore
    # qtbot times out waiting for the second window to be exposed.
    container = QStackedWidget()
    qtbot.add_widget(container)
    container.resize(toolbar_w, toolbar_h)
    toolbar = QToolBar()
    toolbar.setOrientation(toolbar_orientation)
    toolbar.setIconSize(QSize(toolbar_icon_size, toolbar_icon_size))
    container.addWidget(toolbar)
    another_parent = QWidget()
    another_parent.setLayout(another_layout())
    another_parent.layout().setContentsMargins(0, 0, 0, 0)
    container.addWidget(another_parent)
    view = RbaButton()
    toolbar.addWidget(view)
    with qtbot.wait_exposed(container):
        container.show()
    assert isinstance(view.layout(), expected_orig_layout)
    assert view._auth_btn.iconSize() == QSize(expected_orig_icon_size, expected_orig_icon_size)
    another_parent.layout().addWidget(view)
    container.setCurrentIndex(1)
    container.resize(another_parent_w, another_parent_h)
    with qtbot.wait_exposed(view):
        view.show()  # When changing parents the widget becomes hidden, and it needs to be explicitly shown again (https://stackoverflow.com/a/52261810)
    assert isinstance(view.layout(), QHBoxLayout)
    assert view._auth_btn.iconSize() == QSize(expected_new_w, expected_new_h)


@pytest.mark.parametrize("another_layout", [QVBoxLayout, QHBoxLayout, QGridLayout])
@pytest.mark.parametrize("new_w,new_h,expected_icon_w,expected_icon_h", [
    (10, 10, 25, 25),
    (64, 64, 58, 58),
    (100, 200, 94, 194),
    (200, 100, 194, 94),
])
def test_rba_button_fills_size_when_added_not_to_toolbar(qtbot: QtBot, another_layout, new_w, new_h, expected_icon_h, expected_icon_w):
    parent = QWidget()
    qtbot.add_widget(parent)
    parent.setLayout(another_layout())
    view = RbaButton()
    parent.layout().addWidget(view)
    parent.layout().setContentsMargins(0, 0, 0, 0)
    parent.resize(100, 100)
    with qtbot.wait_exposed(parent):
        parent.show()  # Required for resizeEvent to be fired on resize
    if parent.width() >= 300 or parent.height() >= 300:
        pytest.skip("Got unexpected window size. Presumably running in tiling window manager. Skipping...")
    assert view._auth_btn.iconSize() == QSize(94, 94)
    parent.resize(new_w, new_h)
    assert view._auth_btn.iconSize() == QSize(expected_icon_w, expected_icon_h)


@pytest.mark.parametrize("initial_login", [True, False])
def test_rba_button_decoration_for_logout(qtbot: QtBot, initial_login):
    view = RbaButton()
    qtbot.add_widget(view)
    with qtbot.wait_exposed(view):
        view.show()
    if initial_login:
        view.model._token = RbaToken(login_method=RbaToken.LoginMethod.UNKNOWN,
                                     original_token=make_token())
        view.model.login_succeeded.emit(Token.create_empty_token())
    view.model.logout_finished.emit()
    assert view._user_btn.isHidden()
    assert view._auth_btn.menu() is not None


@pytest.mark.parametrize("initial_login", [True, False])
def test_rba_button_decoration_for_login(qtbot: QtBot, initial_login):
    view = RbaButton()
    qtbot.add_widget(view)
    with qtbot.wait_exposed(view):
        view.show()
    token = RbaToken(login_method=RbaToken.LoginMethod.UNKNOWN,
                     original_token=make_token())
    if initial_login:
        view.model._token = token
        view.model.login_succeeded.emit(Token.create_empty_token())
    else:
        view.model.logout_finished.emit()
    view.model._token = token
    view.model.login_succeeded.emit(Token.create_empty_token())
    assert view._user_btn.isVisible()
    assert view._user_btn.text() == "TEST_USERNAME"
    assert view._auth_btn.menu() is None


@pytest.mark.parametrize("initial_online,new_online,expected_online", [
    (None, "logout.gif", "logout.gif"),
    (None, None, "DEFAULT"),
    (None, QIcon(), "DEFAULT"),
    ("logout.gif", "logout.gif", "logout.gif"),
    ("logout.gif", None, "logout.gif"),
    ("logout.gif", QIcon(), "DEFAULT"),
])
@pytest.mark.parametrize("initial_offline,new_offline,expected_offline", [
    (None, "login.gif", "login.gif"),
    (None, None, "DEFAULT"),
    (None, QIcon(), "DEFAULT"),
    ("login.gif", "login.gif", "login.gif"),
    ("login.gif", None, "login.gif"),
    ("login.gif", QIcon(), "DEFAULT"),
])
def test_rba_button_set_icons(qtbot: QtBot, initial_offline, initial_online, new_offline, new_online, expected_offline,
                              expected_online):
    view = RbaButton()
    qtbot.add_widget(view)

    def to_image(icon):
        return icon.pixmap(32, 32).toImage()

    default_online_icon = view._auth_btn._online_icon
    default_offline_icon = view._auth_btn._offline_icon

    def make_local_icon(icon):
        if isinstance(icon, str):
            return make_icon(Path(__file__).parent / "icons" / icon)
        return icon

    expected_online = default_online_icon if expected_online == "DEFAULT" else make_local_icon(expected_online)
    expected_offline = default_offline_icon if expected_offline == "DEFAULT" else make_local_icon(expected_offline)

    view.set_icons(online=make_local_icon(initial_online), offline=make_local_icon(initial_offline))
    view.set_icons(online=make_local_icon(new_online), offline=make_local_icon(new_offline))
    assert to_image(view._auth_btn._online_icon) == to_image(expected_online)
    assert to_image(view._auth_btn._offline_icon) == to_image(expected_offline)


def test_user_btn_init(qtbot: QtBot):
    btn = RbaUserButton()
    qtbot.add_widget(btn)
    assert btn.sizePolicy() == QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    assert btn.popupMode() == QToolButton.InstantPopup
    assert btn.autoRaise()
    assert btn.menu() is not None
    assert len(btn.menu().actions()) == 3
    assert btn.menu().actions()[0].text() == "Select Roles"
    assert btn.menu().actions()[1].isSeparator()
    assert btn.menu().actions()[2].text() == "Show Existing RBAC Token"


@pytest.mark.parametrize("roles_can_be_trusted,should_show_warning,token_renewable,should_display_renewable_loss_notice", [
    (True, False, True, True),
    (True, False, False, False),
    (False, True, True, None),
    (False, True, False, None),
])
@mock.patch("accwidgets.rbac._widget.RbaRolePicker")
@mock.patch("accwidgets.rbac._widget.QMessageBox")
def test_user_btn_role_picker_disabled_when_roles_unreliable(QMessageBox, rba_role_picker, qtbot: QtBot, roles_can_be_trusted,
                                                             should_show_warning, token_renewable, should_display_renewable_loss_notice):
    token = RbaToken(login_method=RbaToken.LoginMethod.UNKNOWN,
                     original_token=make_token(),
                     auto_renewable=token_renewable)
    token._roles_can_be_trusted = roles_can_be_trusted
    view = RbaButton()
    qtbot.add_widget(view)
    view.model.update_token(Token.create_empty_token())
    view.model._token = token
    action = view._user_btn.menu().actions()[0]
    assert action.text() == "Select Roles"
    action.trigger()
    if should_show_warning:
        QMessageBox.assert_called_once()
        QMessageBox.return_value.information.assert_called_once_with(view._user_btn,
                                                                     "Action required",
                                                                     "Available roles cannot be reliably obtained. Please logout and login "
                                                                     'again, while checking "Select roles at login".',
                                                                     QMessageBox.Ok)
        rba_role_picker.assert_not_called()
    else:
        QMessageBox.assert_not_called()
        rba_role_picker.assert_called_once_with(roles=mock.ANY,
                                                display_auto_renewable_notice=should_display_renewable_loss_notice,
                                                parent=view._user_btn)
        rba_role_picker.return_value.exec_.assert_called_once()


@pytest.mark.parametrize("roles", [
    [],
    ["Role1"],
    ["Role1", "Role2"],
    ["Role1", "MCS-Role3"],
])
def test_user_btn_role_picker_on_picked_by_location(qtbot: QtBot, roles):
    token = RbaToken(login_method=RbaToken.LoginMethod.LOCATION,
                     original_token=make_token())
    view = RbaButton()
    qtbot.add_widget(view)
    view.model.update_token(Token.create_empty_token())
    view.model._token = token
    with mock.patch.object(view.model, "login_by_location_with_roles") as login_by_location_with_roles:
        picker = mock.MagicMock()
        view._user_btn._on_roles_selected(roles, picker)
        login_by_location_with_roles.assert_called_once_with(preselected_roles=roles)
        picker.accept.assert_called_once()


@pytest.mark.parametrize("roles", [
    [],
    ["Role1"],
    ["Role1", "Role2"],
    ["Role1", "MCS-Role3"],
])
@pytest.mark.parametrize("login_method,should_display_location_tab", [
    (RbaToken.LoginMethod.EXPLICIT, False),
    (RbaToken.LoginMethod.UNKNOWN, True),
])
@pytest.mark.parametrize("dialog_result,should_accept_role_picker", [
    (QDialog.Accepted, True),
    (QDialog.Rejected, False),
])
@mock.patch("accwidgets.rbac._widget.RbaAuthDialog")
def test_user_btn_role_picker_on_picked_explicitly(RbaAuthDialog, qtbot: QtBot, roles, login_method,
                                                   should_display_location_tab, dialog_result,
                                                   should_accept_role_picker):
    token = RbaToken(login_method=login_method,
                     original_token=make_token())
    view = RbaButton()
    qtbot.add_widget(view)
    view.model.update_token(Token.create_empty_token())
    view.model._token = token
    picker = mock.MagicMock()
    RbaAuthDialog.return_value.exec_.return_value = dialog_result
    RbaAuthDialog.assert_not_called()
    view._user_btn._on_roles_selected(roles, picker)
    RbaAuthDialog.assert_called_once_with(new_roles=roles,
                                          display_location_tab=should_display_location_tab,
                                          username="TEST_USERNAME",
                                          parent=view._user_btn)
    RbaAuthDialog.return_value.setWindowTitle.assert_called_once_with("Authenticate to apply new roles")
    if should_accept_role_picker:
        picker.accept.assert_called_once()
    else:
        picker.accept.assert_not_called()


@pytest.mark.parametrize("auto_renewable", [True, False])
@pytest.mark.parametrize("login_method", [RbaToken.LoginMethod.UNKNOWN, RbaToken.LoginMethod.LOCATION, RbaToken.LoginMethod.EXPLICIT])
@mock.patch("accwidgets.rbac._widget.RbaTokenDialog")
def test_user_btn_show_token_details(RbaTokenDialog, qtbot: QtBot, auto_renewable, login_method):
    token = RbaToken(login_method=login_method,
                     original_token=make_token(),
                     auto_renewable=auto_renewable)
    view = RbaButton()
    qtbot.add_widget(view)
    view.model.update_token(Token.create_empty_token())
    view.model._token = token
    action = view._user_btn.menu().actions()[2]
    assert action.text() == "Show Existing RBAC Token"
    RbaTokenDialog.assert_not_called()
    action.trigger()
    RbaTokenDialog.assert_called_once_with(token=token, parent=view._user_btn)
    RbaTokenDialog.return_value.exec_.assert_called_once()


@pytest.mark.parametrize("action_idx,expected_action_name", [
    (0, "Select Roles"),
    (2, "Show Existing RBAC Token"),
])
@pytest.mark.qt_no_exception_capture
def test_user_btn_throws_when_no_token_available(qtbot: QtBot, action_idx, expected_action_name):
    view = RbaButton()
    qtbot.add_widget(view)
    with qtbot.wait_exposed(view):
        view.show()
    assert view._user_btn.isHidden()
    # For show to introduce unsupported condition
    view._user_btn.show()
    action = view._user_btn.menu().actions()[action_idx]
    assert action.text() == expected_action_name
    # We can't catch exceptions raised in Qt functors, because it crashes interpreter with abort() call
    # https://pytest-qt.readthedocs.io/en/latest/virtual_methods.html
    # Therefore we use qtbot.capture_exceptions() instead of pytest.raises()
    with qtbot.capture_exceptions() as exceptions:
        action.trigger()
    assert len(exceptions) == 1
    assert exceptions[0][0] is RuntimeError  # container is sys.exc_info


@pytest.mark.parametrize("roles", [
    [],
    ["Role1"],
    ["Role1", "Role2"],
    ["Role1", "MCS-Role3"],
])
@pytest.mark.parametrize("login_method", [RbaToken.LoginMethod.UNKNOWN, RbaToken.LoginMethod.LOCATION, RbaToken.LoginMethod.EXPLICIT])
@mock.patch("accwidgets.rbac._widget.RbaRolePicker.accept")
@mock.patch("accwidgets.rbac._widget.RbaRolePicker.reject")
def test_user_btn_warns_when_token_has_been_removed_before_roles_applied(reject, accept, qtbot: QtBot, roles,
                                                                         login_method):
    view = RbaButton()
    qtbot.add_widget(view)
    token = RbaToken(login_method=login_method,
                     original_token=make_token())
    token._roles_can_be_trusted = True
    view.model.update_token(Token.create_empty_token())
    view.model._token = token
    action = view._user_btn.menu().actions()[0]
    assert action.text() == "Select Roles"

    class TestPicker(RbaRolePicker):
        # Way of mocking instance method, so that "self" is available, without mocking the rest of the class / object
        # (and with object) not available directly, because it is created and destroyed within the called function.

        def exec_(self) -> QDialog.DialogCode:
            view.model.logout()  # Logout before roles application has finished, to trigger problematic condition
            self.roles_selected.emit(roles, self)
            return QDialog.Accepted

    with mock.patch("accwidgets.rbac._widget.RbaRolePicker", side_effect=TestPicker):
        accept.assert_not_called()
        reject.assert_not_called()
        with pytest.warns(UserWarning, match="Token has been removed in the meantime. Roles will not be updated."):
            action.trigger()
        accept.assert_not_called()
        reject.assert_called_once()


def test_auth_btn_init(qtbot: QtBot):
    btn = RbaAuthButton()
    qtbot.add_widget(btn)
    assert btn.sizePolicy() == QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    assert btn.popupMode() == QToolButton.InstantPopup
    assert btn.autoRaise()
    assert btn.menu() is not None
    assert len(btn.menu().actions()) == 1
    assert isinstance(btn.menu().actions()[0], QWidgetAction)
    assert isinstance(cast(QWidgetAction, btn.menu().actions()[0]).defaultWidget(), RbaAuthPopupWidget)


@pytest.mark.parametrize("initial_connected,expected_initial_icon,expect_initial_menu,new_connected,expected_new_icon,expect_new_menu", [
    (True, "online.ico", False, True, "online.ico", False),
    (False, "offline.ico", True, True, "online.ico", False),
    (None, "offline.ico", True, True, "online.ico", False),
    (True, "online.ico", False, False, "offline.ico", True),
    (False, "offline.ico", True, False, "offline.ico", True),
    (None, "offline.ico", True, False, "offline.ico", True),
    (True, "online.ico", False, None, "online.ico", False),
    (False, "offline.ico", True, None, "offline.ico", True),
    (None, "offline.ico", True, None, "offline.ico", True),
])
def test_auth_btn_decorate(qtbot: QtBot, initial_connected, expect_initial_menu, expect_new_menu, expected_initial_icon,
                           expected_new_icon, new_connected):
    btn = RbaAuthButton()
    qtbot.add_widget(btn)

    def expect_auth_btn_config(icon_name: str, expect_menu: bool):
        import accwidgets.rbac
        expected_icon = make_icon(Path(accwidgets.rbac.__file__).parent / "icons" / icon_name)

        def to_image(icon):
            return icon.pixmap(32, 32).toImage()

        assert to_image(btn.icon()) == to_image(expected_icon)
        assert (btn.menu() is not None) == expect_menu

    expect_auth_btn_config("offline.ico", True)
    btn.decorate(initial_connected)
    expect_auth_btn_config(expected_initial_icon, expect_initial_menu)
    btn.decorate(new_connected)
    expect_auth_btn_config(expected_new_icon, expect_new_menu)


@pytest.mark.parametrize("width,height,expected_width,expected_height", [
    (16, 16, 10, 10),
    (64, 64, 58, 58),
    (100, 200, 94, 194),
    (200, 100, 194, 94),
])
def test_auth_btn_set_margin_icon_size(qtbot: QtBot, width, height, expected_height, expected_width):
    btn = RbaAuthButton()
    qtbot.add_widget(btn)
    with mock.patch.object(btn, "setIconSize") as setIconSize:
        btn.set_margin_icon_size(QSize(width, height))
        setIconSize.assert_called_once_with(QSize(expected_width, expected_height))


@pytest.mark.parametrize("parent_width,parent_height", [
    (32, 32),
    (64, 64),
    (200, 50),
    (50, 150),
])
@pytest.mark.parametrize("is_in_toolbar,toolbar_icon_size,expected_hint_width,expected_hint_height", [
    (True, 10, 18, 17),
    (True, 32, 40, 39),
    (True, 64, 72, 71),
    (False, None, 31, 31),
])
def test_auth_btn_minimum_size_hint(qtbot: QtBot, is_in_toolbar, parent_height, parent_width, expected_hint_height,
                                    expected_hint_width, toolbar_icon_size):
    parent = QToolBar() if is_in_toolbar else QWidget()
    qtbot.add_widget(parent)
    with qtbot.wait_exposed(parent):
        parent.show()
    view = RbaButton()
    if is_in_toolbar:
        parent.setIconSize(QSize(toolbar_icon_size, toolbar_icon_size))
        parent.addWidget(view)
    else:
        parent.setLayout(QVBoxLayout())
        parent.layout().setContentsMargins(0, 0, 0, 0)
        parent.layout().addWidget(view)
    parent.resize(parent_width, parent_height)
    assert view._auth_btn.minimumSizeHint() == QSize(expected_hint_width, expected_hint_height)


@pytest.mark.parametrize("connected,should_show_menu,should_logout_model", [
    (True, False, True),
    (False, True, False),
])
def test_auth_btn_click(qtbot: QtBot, connected, should_logout_model, should_show_menu):
    view = RbaButton()
    qtbot.add_widget(view)
    view._auth_btn.decorate(connected)
    with qtbot.wait_exposed(view):
        view.show()
    # Hide as soon as shown (give time for qtbot verification)
    view._auth_btn._menu.aboutToShow.connect(lambda: QTimer.singleShot(150, view._auth_btn._menu.hide))
    menu_widget = cast(QWidgetAction, view._auth_btn._menu.actions()[0]).defaultWidget()
    with mock.patch.object(view.model, "logout") as logout:
        if should_show_menu:
            with qtbot.wait_exposed(menu_widget):
                view._auth_btn.click()
        else:
            with pytest.raises(QtBotTimeoutError):  # Should not show, and qtbot should throw TimeoutError
                with qtbot.wait_exposed(menu_widget, timeout=100):
                    view._auth_btn.click()
        if should_logout_model:
            logout.assert_called_once()
        else:
            logout.assert_not_called()


@pytest.mark.parametrize("key", [Qt.Key_Enter, Qt.Key_Return])
@mock.patch("accwidgets.rbac._model.RbaButtonModel.login_explicitly")
def test_auth_btn_does_not_close_menu_on_dbl_return(login_explicitly, qtbot: QtBot, key):
    # Navigate to the explicit tab, double hit the return key, to: 1 - jump to the next field, 2 - initiate login
    # The default behavior of the menu, would hide the popup after the double Return keystroke
    view = RbaButton()
    qtbot.add_widget(view)
    with qtbot.wait_exposed(view):
        view.show()
    menu_widget = cast(RbaAuthPopupWidget, cast(QWidgetAction, view._auth_btn._menu.actions()[0]).defaultWidget())

    def on_menu_visible():
        # Navigate to the explicit tab menu
        app = cast(QApplication, QApplication.instance())
        window = app.topLevelWindows()[1]
        qtbot.keyClick(window, Qt.Key_Tab)
        qtbot.keyClick(window, Qt.Key_Right)
        assert menu_widget.isVisible()
        assert not menu_widget.username.hasFocus()
        qtbot.keyClick(window, Qt.Key_Tab)
        assert menu_widget.isVisible()
        assert menu_widget.username.hasFocus()
        qtbot.keyClick(window, Qt.Key_U)
        qtbot.keyClick(window, Qt.Key_S)
        qtbot.keyClick(window, Qt.Key_E)
        qtbot.keyClick(window, Qt.Key_R)
        qtbot.keyClick(window, key)
        assert menu_widget.isVisible()
        assert not menu_widget.username.hasFocus()
        assert menu_widget.password.hasFocus()
        qtbot.keyClick(window, Qt.Key_P)
        qtbot.keyClick(window, Qt.Key_A)
        qtbot.keyClick(window, Qt.Key_S)
        qtbot.keyClick(window, Qt.Key_S)
        login_explicitly.assert_not_called()
        qtbot.keyClick(window, key)
        login_explicitly.assert_called_once_with(username="user", password="pass", interactively_select_roles=False)
        assert menu_widget.isVisible()
        qtbot.keyClick(window, Qt.Key_Escape)
        assert not menu_widget.isVisible()

    view._auth_btn._menu.aboutToShow.connect(lambda: QTimer.singleShot(150, on_menu_visible))
    with qtbot.wait_signal(view._auth_btn.menu().aboutToHide):
        view._auth_btn.click()


def test_auth_btn_does_not_close_menu_on_mouse_click(qtbot: QtBot):
    # This tests that Mouse click inside the popup does not close it, which is default QMenu behavior
    # See RbaAuthPopupWidget.event
    view = RbaButton()
    qtbot.add_widget(view)
    with qtbot.wait_exposed(view):
        view.show()
    menu_widget = cast(RbaAuthPopupWidget, cast(QWidgetAction, view._auth_btn._menu.actions()[0]).defaultWidget())

    def on_menu_visible():
        # Navigate to the explicit tab menu
        app = cast(QApplication, QApplication.instance())
        window = app.topLevelWindows()[1]
        assert menu_widget.isVisible()
        qtbot.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(10, 10))  # Click inside the widget
        assert menu_widget.isVisible()
        qtbot.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(-10, -10))  # Click outside the widget
        assert not menu_widget.isVisible()

    view._auth_btn._menu.aboutToShow.connect(lambda: QTimer.singleShot(150, on_menu_visible))
    with qtbot.wait_signal(view._auth_btn.menu().aboutToHide):
        view._auth_btn.click()


def test_auth_btn_login_widget_receives_tab(qtbot: QtBot):
    # This tests that Tab keystrokes actually change the focus by the tab order, instead of QMenu default behavior
    # that closes the menu on Tab.
    view = RbaButton()
    qtbot.add_widget(view)
    with qtbot.wait_exposed(view):
        view.show()
    menu_widget = cast(RbaAuthPopupWidget, cast(QWidgetAction, view._auth_btn._menu.actions()[0]).defaultWidget())

    def on_menu_visible():
        # Navigate to the explicit tab menu
        app = cast(QApplication, QApplication.instance())
        window = app.topLevelWindows()[1]
        assert menu_widget.loc_btn.hasFocus()
        assert not menu_widget.roles_loc.hasFocus()
        qtbot.keyClick(window, Qt.Key_Tab)
        assert not menu_widget.loc_btn.hasFocus()
        assert not menu_widget.roles_loc.hasFocus()
        qtbot.keyClick(window, Qt.Key_Tab, Qt.ShiftModifier)
        assert menu_widget.loc_btn.hasFocus()
        assert not menu_widget.roles_loc.hasFocus()
        qtbot.keyClick(window, Qt.Key_Tab, Qt.ShiftModifier)
        assert not menu_widget.loc_btn.hasFocus()
        assert menu_widget.roles_loc.hasFocus()
        qtbot.keyClick(window, Qt.Key_Tab)
        assert menu_widget.loc_btn.hasFocus()
        assert not menu_widget.roles_loc.hasFocus()
        assert menu_widget.isVisible()
        qtbot.keyClick(window, Qt.Key_Escape)
        assert not menu_widget.isVisible()

    view._auth_btn._menu.aboutToShow.connect(lambda: QTimer.singleShot(150, on_menu_visible))
    with qtbot.wait_signal(view._auth_btn.menu().aboutToHide):
        view._auth_btn.click()
