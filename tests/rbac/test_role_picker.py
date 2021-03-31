import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QDialogButtonBox, QWidget
from qtpy.QtCore import Qt, QVariant, QEvent
from qtpy.QtGui import QBrush, QColor, QKeyEvent
from accwidgets.rbac import RbaRole
from accwidgets.rbac._role_picker import RbaRolePicker, select_roles_interactively


@pytest.mark.parametrize("roles,mcs_only,visible_roles", [
    ([
        RbaRole(name="Role1"),
        RbaRole(name="Role2", lifetime=10),
        RbaRole(name="Role3", active=True),
        RbaRole(name="Role4", lifetime=10, active=True),
        RbaRole(name="MCS-Role1"),
        RbaRole(name="MCS-Role2", lifetime=20),
        RbaRole(name="MCS-Role3", active=True),
        RbaRole(name="MCS-Role4", lifetime=20),
    ], True, [
        # Role name, is checked, color (or None for default)
        ("MCS-Role1", False, Qt.red),
        ("MCS-Role2", False, Qt.red),
        ("MCS-Role3", True, Qt.red),
        ("MCS-Role4", False, Qt.red),
    ]),
    ([
        RbaRole(name="Role1"),
        RbaRole(name="Role2", lifetime=10),
        RbaRole(name="Role3", active=True),
        RbaRole(name="Role4", lifetime=10, active=True),
        RbaRole(name="MCS-Role1"),
        RbaRole(name="MCS-Role2", lifetime=20),
        RbaRole(name="MCS-Role3", active=True),
        RbaRole(name="MCS-Role4", lifetime=20),
    ], False, [
        # Role name, is checked, color (or None for default)
        ("MCS-Role1", False, Qt.red),
        ("MCS-Role2", False, Qt.red),
        ("MCS-Role3", True, Qt.red),
        ("MCS-Role4", False, Qt.red),
        ("Role1", False, None),
        ("Role2", False, None),
        ("Role3", True, None),
        ("Role4", True, None),
    ]),
    ([
        RbaRole(name="Role3", active=True),
        RbaRole(name="Role4", lifetime=10, active=True),
    ], True, []),
    ([
        RbaRole(name="Role3", active=True),
        RbaRole(name="Role4", lifetime=10, active=True),
    ], False, [
        # Role name, is checked, color (or None for default)
        ("Role3", True, None),
        ("Role4", True, None),
    ]),
    ([
        RbaRole(name="Role1"),
        RbaRole(name="Role2", lifetime=10),
        RbaRole(name="MCS-Role1"),
        RbaRole(name="MCS-Role2", lifetime=20),
    ], True, [
        # Role name, is checked, color (or None for default)
        ("MCS-Role1", False, Qt.red),
        ("MCS-Role2", False, Qt.red),
    ]),
    ([
        RbaRole(name="Role1"),
        RbaRole(name="Role2", lifetime=10),
        RbaRole(name="MCS-Role1"),
        RbaRole(name="MCS-Role2", lifetime=20),
    ], False, [
        # Role name, is checked, color (or None for default)
        ("MCS-Role1", False, Qt.red),
        ("MCS-Role2", False, Qt.red),
        ("Role1", False, None),
        ("Role2", False, None),
    ]),
    ([], True, []),
    ([], False, []),
])
@mock.patch("accwidgets.rbac._palette.find_palette_holder")
def test_role_picker_displays_sorted_roles(find_palette_holder, qtbot: QtBot, roles, mcs_only, visible_roles):
    find_palette_holder.return_value._color_palette.color.return_value = Qt.red
    dialog = RbaRolePicker(roles=roles)
    qtbot.add_widget(dialog)
    dialog.mcs_checkbox.setChecked(mcs_only)
    assert dialog.btn_clear_all.isHidden() == mcs_only
    assert dialog.btn_select_all.isHidden() == mcs_only
    model = dialog.role_view.model()
    assert model.rowCount() == len(visible_roles)
    for i, visible_role in enumerate(visible_roles):
        idx = model.index(i, 0)
        name, checked, color = visible_role
        assert model.data(idx, Qt.DisplayRole) == name
        assert model.data(idx, Qt.CheckStateRole) == (Qt.Checked if checked else Qt.Unchecked)
        assert model.data(idx, Qt.ForegroundRole) == (QVariant() if color is None else QBrush(QColor(color)))


@pytest.mark.parametrize("init_roles,clicked_row,in_mcs_mode,final_roles", [
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="X2"),
    ], 0, False, [
        ("A1", True),
        ("MCS-A3", False),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2"),
    ], 1, False, [
        ("A1", False),
        ("MCS-A3", True),
        ("MCS-A4", False),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2"),
    ], 0, True, [
        ("A1", False),
        ("MCS-A3", True),
        ("MCS-A4", False),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2", active=True),
    ], 1, False, [
        ("A1", True),
        ("MCS-A3", True),
        ("MCS-A4", False),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2", active=True),
    ], 0, True, [
        ("A1", True),
        ("MCS-A3", True),
        ("MCS-A4", False),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3", active=True),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2"),
    ], 2, False, [
        ("A1", False),
        ("MCS-A3", False),
        ("MCS-A4", True),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3", active=True),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2"),
    ], 1, True, [
        ("A1", False),
        ("MCS-A3", False),
        ("MCS-A4", True),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3", active=True),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2", active=True),
    ], 2, False, [
        ("A1", True),
        ("MCS-A3", False),
        ("MCS-A4", True),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3", active=True),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2", active=True),
    ], 1, True, [
        ("A1", True),
        ("MCS-A3", False),
        ("MCS-A4", True),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3"),
        RbaRole(name="X2"),
    ], 2, False, [
        ("A1", True),
        ("MCS-A3", False),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3"),
        RbaRole(name="X2"),
    ], 0, False, [
        ("A1", False),
        ("MCS-A3", False),
        ("X2", False),
    ]),
])
def test_role_picker_allows_only_one_mcs_role(qtbot: QtBot, init_roles, clicked_row, in_mcs_mode, final_roles):
    dialog = RbaRolePicker(roles=init_roles)
    qtbot.add_widget(dialog)
    model = dialog.role_view.model()

    if in_mcs_mode:
        dialog.mcs_checkbox.setChecked(True)

    index = model.index(clicked_row, 0)
    check_state = index.data(Qt.CheckStateRole)
    model.setData(index, Qt.Unchecked if check_state == Qt.Checked else Qt.Checked, Qt.CheckStateRole)

    if in_mcs_mode:
        dialog.mcs_checkbox.setChecked(False)

    assert model.rowCount() == len(final_roles)
    for i, visible_role in enumerate(final_roles):
        idx = model.index(i, 0)
        name, checked = visible_role
        assert model.data(idx, Qt.DisplayRole) == name
        assert model.data(idx, Qt.CheckStateRole) == (Qt.Checked if checked else Qt.Unchecked)


@pytest.mark.parametrize("init_roles,final_roles", [
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="X2"),
    ], [
        ("A1", True),
        ("MCS-A3", False),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3", active=True),
        RbaRole(name="X2"),
    ], [
        ("A1", True),
        ("MCS-A3", True),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2"),
    ], [
        ("A1", True),
        ("MCS-A3", False),
        ("MCS-A4", False),
        ("X2", True),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4", active=True),
        RbaRole(name="X2", active=True),
    ], [
        ("A1", True),
        ("MCS-A3", False),
        ("MCS-A4", True),
        ("X2", True),
    ]),
])
def test_role_picker_select_all(qtbot: QtBot, init_roles, final_roles):
    dialog = RbaRolePicker(roles=init_roles)
    qtbot.add_widget(dialog)
    model = dialog.role_view.model()

    dialog.btn_select_all.click()

    assert model.rowCount() == len(final_roles)
    for i, visible_role in enumerate(final_roles):
        idx = model.index(i, 0)
        name, checked = visible_role
        assert model.data(idx, Qt.DisplayRole) == name
        assert model.data(idx, Qt.CheckStateRole) == (Qt.Checked if checked else Qt.Unchecked)


@pytest.mark.parametrize("init_roles,final_roles", [
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="X2"),
    ], [
        ("A1", False),
        ("MCS-A3", False),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3", active=True),
        RbaRole(name="X2", active=True),
    ], [
        ("A1", False),
        ("MCS-A3", False),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1", active=True),
        RbaRole(name="MCS-A3", active=True),
        RbaRole(name="X2"),
    ], [
        ("A1", False),
        ("MCS-A3", False),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4"),
        RbaRole(name="X2"),
    ], [
        ("A1", False),
        ("MCS-A3", False),
        ("MCS-A4", False),
        ("X2", False),
    ]),
    ([
        RbaRole(name="A1"),
        RbaRole(name="MCS-A3"),
        RbaRole(name="MCS-A4", active=True),
        RbaRole(name="X2", active=True),
    ], [
        ("A1", False),
        ("MCS-A3", False),
        ("MCS-A4", False),
        ("X2", False),
    ]),
])
def test_role_picker_clear_all(qtbot: QtBot, init_roles, final_roles):
    dialog = RbaRolePicker(roles=init_roles)
    qtbot.add_widget(dialog)
    model = dialog.role_view.model()

    dialog.btn_clear_all.click()

    assert model.rowCount() == len(final_roles)
    for i, visible_role in enumerate(final_roles):
        idx = model.index(i, 0)
        name, checked = visible_role
        assert model.data(idx, Qt.DisplayRole) == name
        assert model.data(idx, Qt.CheckStateRole) == (Qt.Checked if checked else Qt.Unchecked)


@pytest.mark.parametrize("force,reacts_to_escape,std_buttons", [
    (True, False, [QDialogButtonBox.Apply]),
    (False, True, [QDialogButtonBox.Cancel, QDialogButtonBox.Apply]),
])
@mock.patch("qtpy.QtWidgets.QDialog.keyPressEvent")
def test_role_picker_force_select(keyPressEvent, qtbot: QtBot, force, reacts_to_escape, std_buttons):
    dialog = RbaRolePicker(roles=[], force_select=force)
    qtbot.add_widget(dialog)
    assert len(dialog.btn_box.buttons()) == len(std_buttons)
    for i, btn_type in enumerate(std_buttons):
        assert dialog.btn_box.buttons()[i] == dialog.btn_box.button(btn_type)

    ev = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
    dialog.keyPressEvent(ev)
    if reacts_to_escape:
        keyPressEvent.assert_called_once_with(ev)
    else:
        keyPressEvent.assert_not_called()


@pytest.mark.parametrize("display_notice,expect_label_visible", [
    (True, True),
    (False, False),
])
def test_role_picker_notice_visible(qtbot: QtBot, display_notice, expect_label_visible):
    dialog = RbaRolePicker(roles=[], display_auto_renewable_notice=display_notice)
    qtbot.add_widget(dialog)
    with qtbot.wait_exposed(dialog):
        dialog.show()
    assert dialog.notice_label.isVisible() == expect_label_visible
    assert dialog.notice_label.property("qss-role") == "info"


@pytest.mark.parametrize("parent_exists", [True, False])
@pytest.mark.parametrize("roles", [
    [],
    [RbaRole(name="Role1")],
    [RbaRole(name="Role1"), RbaRole(name="Role2")],
    [RbaRole(name="Role1"), RbaRole(name="Role2"), RbaRole(name="MCS-Role3")],
])
@mock.patch("accwidgets.rbac._role_picker.RbaRolePicker")
def test_select_roles_interactively_dialog_args(RbaRolePicker, qtbot: QtBot, parent_exists, roles):
    if parent_exists:
        parent = QWidget()
        qtbot.add_widget(parent)
    else:
        parent = None
    select_roles_interactively(roles=roles, parent=parent)
    RbaRolePicker.assert_called_once_with(roles=roles, display_auto_renewable_notice=False, force_select=True,
                                          parent=parent)


@pytest.mark.parametrize("parent_exists", [True, False])
@pytest.mark.parametrize("picked_roles", [
    [],
    ["Role1"],
    ["Role1", "Role2"],
    ["Role1", "MCS-Role3"],
])
@pytest.mark.parametrize("roles", [
    [],
    [RbaRole(name="Role1")],
    [RbaRole(name="Role1"), RbaRole(name="Role2")],
    [RbaRole(name="Role1"), RbaRole(name="Role2"), RbaRole(name="MCS-Role3")],
])
def test_select_roles_interactively_result(qtbot: QtBot, parent_exists, picked_roles, roles):
    if parent_exists:
        parent = QWidget()
        qtbot.add_widget(parent)
    else:
        parent = None
    dialog = RbaRolePicker(roles=roles, display_auto_renewable_notice=False, force_select=True, parent=parent)
    qtbot.add_widget(dialog)

    with mock.patch.object(dialog, "exec_", side_effect=lambda: dialog.roles_selected.emit(picked_roles, dialog)):
        with mock.patch("accwidgets.rbac._role_picker.RbaRolePicker", return_value=dialog):
            with qtbot.wait_signal(dialog.roles_selected):
                assert select_roles_interactively(roles=roles, parent=parent) == picked_roles
