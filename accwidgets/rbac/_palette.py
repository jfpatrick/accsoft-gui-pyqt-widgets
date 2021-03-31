from typing import Union, Dict, TYPE_CHECKING
from enum import IntEnum, auto
from qtpy.QtGui import QColor, QPalette
from qtpy.QtCore import Qt, QObject
if TYPE_CHECKING:
    from accwidgets.rbac import RbaButton


Color = Union[Qt.GlobalColor, QColor]


class ColorRole(IntEnum):
    MCS = auto()


class Palette:

    def __init__(self):
        super().__init__()
        self._color_scheme: Dict[ColorRole, QColor] = {
            ColorRole.MCS: QColor("#ff5050"),
        }

    def color(self, role: ColorRole) -> QColor:
        return self._color_scheme[role]

    def set_color(self, role: ColorRole, new_val: Color):
        self._color_scheme[role] = QColor(new_val) if not isinstance(new_val, QColor) else new_val


def find_palette_holder(consumer: QObject) -> "RbaButton":
    from accwidgets.rbac import RbaButton

    while True:
        parent = consumer.parent()
        if parent is None:
            raise AttributeError
        if isinstance(parent, RbaButton):
            return parent
        consumer = parent


def get_color(consumer: QObject, role: ColorRole) -> QColor:
    widget = find_palette_holder(consumer)
    return widget._color_palette.color(role)


css_palette_prop: Dict[QPalette.ColorRole, str] = {
    QPalette.WindowText: "color",
    QPalette.Window: "background-color",
}
