import pytest
from pytestqt.qtbot import QtBot
from freezegun import freeze_time
from typing import cast, List
from unittest import mock
from datetime import datetime
from qtpy.QtWidgets import QFormLayout, QLabel, QApplication
from qtpy.QtGui import QPalette
from accwidgets.rbac import RbaRole, RbaToken
from accwidgets.rbac._token_dialog import RbaTokenDialog
from .fixtures import make_token, mocked_account_type_to_str


@freeze_time("2020-01-01 12:55:22")
@pytest.mark.parametrize("login_method", [RbaToken.LoginMethod.UNKNOWN, RbaToken.LoginMethod.EXPLICIT, RbaToken.LoginMethod.LOCATION])
@pytest.mark.parametrize("valid,valid_str", [
    (True, "true"),
    (False, "false"),
])
@pytest.mark.parametrize("auto_renewable,auto_renewable_str", [
    (True, "true"),
    (False, "false"),
])
@pytest.mark.parametrize("loc_auth,loc_auth_str", [
    (True, "true"),
    (False, "false"),
])
@pytest.mark.parametrize("roles,roles_str", [
    ([
        RbaRole(name="Role1"),
        RbaRole(name="Role2", lifetime=10),
        RbaRole(name="Role3", active=True),
        RbaRole(name="Role4", lifetime=10, active=True),
        RbaRole(name="MCS-Role1"),
        RbaRole(name="MCS-Role2", lifetime=20),
        RbaRole(name="MCS-Role3", active=True),
        RbaRole(name="MCS-Role4", lifetime=20, active=True),
    ], "MCS-Role3 [critical=true; lifetime=-1]\n"
       "MCS-Role4 [critical=true; lifetime=20]\n"
       "Role3 [critical=false; lifetime=-1]\n"
       "Role4 [critical=false; lifetime=10]"),
    ([
        RbaRole(name="Role1"),
        RbaRole(name="Role2", lifetime=10),
        RbaRole(name="MCS-Role1"),
        RbaRole(name="MCS-Role2", lifetime=20),
    ], ""),
    ([], ""),
])
@mock.patch("accwidgets.rbac._token.account_type_to_string", side_effect=mocked_account_type_to_str)
def test_token_dialog_displays_data(_, qtbot: QtBot, valid, valid_str, loc_auth, loc_auth_str,
                                    roles, roles_str, login_method, auto_renewable, auto_renewable_str):
    token = make_token(valid=valid,
                       loc_auth_reqd=loc_auth,
                       roles=roles,
                       auth_timestamp=datetime(2020, 1, 1, 12, 53, 23),
                       expiration_timestamp=datetime(2020, 1, 1, 13, 0, 0))
    dialog = RbaTokenDialog(token=RbaToken(original_token=token,
                                           available_roles=[r.name for r in roles],
                                           login_method=login_method,
                                           auto_renewable=auto_renewable))
    qtbot.add_widget(dialog)
    assert dialog.form.itemAt(0, QFormLayout.LabelRole).widget().text() == "User Name"
    assert dialog.form.itemAt(0, QFormLayout.FieldRole).widget().text() == "TEST_USERNAME [TEST_FULL_NAME, TEST_EMAIL]"
    assert dialog.form.itemAt(1, QFormLayout.LabelRole).widget().text() == "Account Type"
    assert dialog.form.itemAt(1, QFormLayout.FieldRole).widget().text() == "AT_SERVICE"
    assert dialog.form.itemAt(2, QFormLayout.LabelRole).widget().text() == "Is Valid ?"
    assert dialog.form.itemAt(2, QFormLayout.FieldRole).widget().text() == valid_str
    assert dialog.form.itemAt(3, QFormLayout.LabelRole).widget().text() == "Start Time"
    assert dialog.form.itemAt(3, QFormLayout.FieldRole).widget().text() == "2020-01-01 12:53:23 (About 1 min. 59 sec. ago)"
    assert dialog.form.itemAt(4, QFormLayout.LabelRole).widget().text() == "Expiration Time"
    assert dialog.form.itemAt(4, QFormLayout.FieldRole).widget().text() == "2020-01-01 13:00:00 (About 4 min. 38 sec. from now)"
    assert dialog.form.itemAt(5, QFormLayout.LabelRole).widget().text() == "Renewed automatically ?"
    assert dialog.form.itemAt(5, QFormLayout.FieldRole).widget().text() == auto_renewable_str
    assert dialog.form.itemAt(6, QFormLayout.LabelRole).widget().text() == "Roles"
    assert dialog.form.itemAt(6, QFormLayout.FieldRole).widget().text() == roles_str
    assert dialog.form.itemAt(7, QFormLayout.LabelRole).widget().text() == "Application"
    assert dialog.form.itemAt(7, QFormLayout.FieldRole).widget().text() == "TEST_APP"
    assert dialog.form.itemAt(8, QFormLayout.LabelRole).widget().text() == "Location"
    assert dialog.form.itemAt(8, QFormLayout.FieldRole).widget().text() == f"TEST_LOC [address=10.10.255.255; auth-reqd={loc_auth_str}]"
    assert dialog.form.itemAt(9, QFormLayout.LabelRole).widget().text() == "Serial ID"
    assert dialog.form.itemAt(9, QFormLayout.FieldRole).widget().text() == "0xc0decafe"


@pytest.mark.parametrize("valid,expected_color", [
    (True, "#66ff66"),
    (False, "#ff5050"),
])
@pytest.mark.parametrize("login_method", [RbaToken.LoginMethod.LOCATION, RbaToken.LoginMethod.EXPLICIT, RbaToken.LoginMethod.UNKNOWN])
@pytest.mark.parametrize("auto_renewable", [True, False])
@mock.patch("accwidgets.rbac._token.account_type_to_string", side_effect=mocked_account_type_to_str)
def test_token_dialog_colors_validity(_, qtbot: QtBot, valid, expected_color, login_method, auto_renewable):
    token = make_token(valid=valid,
                       roles=cast(List[str], []),
                       auth_timestamp=datetime.now(),
                       expiration_timestamp=datetime.now())
    dialog = RbaTokenDialog(token=RbaToken(original_token=token, login_method=login_method, auto_renewable=auto_renewable))
    qtbot.add_widget(dialog)
    assert dialog.form.itemAt(2, QFormLayout.FieldRole).widget().palette().color(QPalette.Background).name() == expected_color


@freeze_time("2020-01-01 12:55:22")
@pytest.mark.parametrize("expiration_time,expected_label,expected_color,expected_qss_role", [
    (datetime(2020, 1, 1, 13, 0, 0), "2020-01-01 13:00:00 (About 4 min. 38 sec. from now)", None, None),
    (datetime(2020, 1, 2, 13, 0, 0), "2020-01-02 13:00:00 (About 1 day 4 min. 38 sec. from now)", None, None),
    (datetime(2020, 1, 2, 12, 55, 22), "2020-01-02 12:55:22 (About 1 day from now)", None, None),
    (datetime(2020, 7, 1, 13, 0, 0), "2020-07-01 13:00:00 (About 182 days 4 min. 38 sec. from now)", None, None),
    (datetime(2021, 1, 1, 13, 0, 0), "2021-01-01 13:00:00 (About 366 days 4 min. 38 sec. from now)", None, None),
    (datetime(2020, 1, 1, 12, 53, 25), "2020-01-01 12:53:25 (About 1 min. 57 sec. ago)", "#ff5050", "critical"),
    (datetime(2019, 12, 31, 12, 53, 25), "2019-12-31 12:53:25 (About 1 day 1 min. 57 sec. ago)", "#ff5050", "critical"),
    (datetime(2019, 12, 31, 12, 55, 22), "2019-12-31 12:55:22 (About 1 day ago)", "#ff5050", "critical"),
    (datetime(2019, 6, 30, 12, 53, 25), "2019-06-30 12:53:25 (About 185 days 1 min. 57 sec. ago)", "#ff5050", "critical"),
    (datetime(2019, 1, 1, 12, 53, 25), "2019-01-01 12:53:25 (About 365 days 1 min. 57 sec. ago)", "#ff5050", "critical"),
    (datetime(2020, 1, 1, 12, 55, 22), "2020-01-01 12:55:22 (About now)", None, None),
])
@pytest.mark.parametrize("login_method", [RbaToken.LoginMethod.LOCATION, RbaToken.LoginMethod.EXPLICIT, RbaToken.LoginMethod.UNKNOWN])
@pytest.mark.parametrize("auto_renewable", [True, False])
@mock.patch("accwidgets.rbac._token.account_type_to_string", side_effect=mocked_account_type_to_str)
def test_token_dialog_expiration(_, qtbot: QtBot, expiration_time, expected_color, expected_label, login_method,
                                 auto_renewable, expected_qss_role):
    token = make_token(valid=True,
                       loc_auth_reqd=False,
                       roles=cast(List[str], []),
                       auth_timestamp=datetime(2020, 1, 1, 12, 53, 23),
                       expiration_timestamp=expiration_time)
    dialog = RbaTokenDialog(token=RbaToken(original_token=token, login_method=login_method, auto_renewable=auto_renewable))
    qtbot.add_widget(dialog)
    label: QLabel = dialog.form.itemAt(4, QFormLayout.FieldRole).widget()
    assert label.text() == expected_label
    assert label.property("qss-role") == expected_qss_role
    if expected_color is None:
        assert label.palette().color(QPalette.WindowText) == QApplication.instance().palette().color(QPalette.WindowText)
    else:
        assert label.palette().color(QPalette.WindowText).name() == expected_color
