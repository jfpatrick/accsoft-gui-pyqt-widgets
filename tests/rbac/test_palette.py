import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt, QObject
from qtpy.QtGui import QColor
from accwidgets.rbac import RbaButton
from accwidgets.rbac._palette import ColorRole, Palette, find_palette_holder, get_color


@pytest.mark.parametrize("role,expected_initial_color,new_color,expected_new_color", [
    (ColorRole.MCS, "#ff5050", QColor("#ff0000"), "#ff0000"),
    (ColorRole.MCS, "#ff5050", Qt.red, "#ff0000"),
    (ColorRole.MCS, "#ff5050", QColor("#00ff00"), "#00ff00"),
    (ColorRole.MCS, "#ff5050", Qt.green, "#00ff00"),
])
def test_palette_colors(role, expected_initial_color, new_color, expected_new_color):
    palette = Palette()
    assert palette.color(role).name() == expected_initial_color
    palette.set_color(role, new_color)
    assert palette.color(role).name() == expected_new_color


@pytest.mark.parametrize("parental_depth", [1, 2, 3, 5])
def test_find_palette_holder_succeeds(qtbot: QtBot, parental_depth):
    widget = RbaButton()
    qtbot.add_widget(widget)
    refcount_container = []
    leaf = widget
    for _ in range(parental_depth):
        leaf = QObject(leaf)
        refcount_container.append(leaf)  # Avoid object destruction in the end of loop scope
    assert find_palette_holder(leaf) == widget


@pytest.mark.parametrize("parental_depth", [0, 1, 2, 3, 5])
def test_find_palette_holder_fails(parental_depth):
    leaf = QObject()
    refcount_container = [leaf]
    for _ in range(parental_depth):
        leaf = QObject(leaf)
        refcount_container.append(leaf)  # Avoid object destruction in the end of loop scope
    with pytest.raises(AttributeError):
        find_palette_holder(leaf)


@pytest.mark.parametrize("role,expected_initial_color,new_color,expected_new_color", [
    (ColorRole.MCS, "#ff5050", QColor("#ff0000"), "#ff0000"),
    (ColorRole.MCS, "#ff5050", Qt.red, "#ff0000"),
    (ColorRole.MCS, "#ff5050", QColor("#00ff00"), "#00ff00"),
    (ColorRole.MCS, "#ff5050", Qt.green, "#00ff00"),
])
@mock.patch("accwidgets.rbac._palette.find_palette_holder")
def test_get_color(find_palette_holder, role, expected_new_color, expected_initial_color, new_color):
    palette = Palette()
    find_palette_holder.return_value._color_palette = palette
    consumer = QObject()
    assert get_color(consumer, role).name() == expected_initial_color
    palette.set_color(role, new_color)
    assert get_color(consumer, role).name() == expected_new_color


def test_available_roles():
    # Meant to fail, if we add new roles and forget to test it
    assert list(ColorRole) == [
        ColorRole.MCS,
    ]
