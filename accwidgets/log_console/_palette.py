from typing import Optional, Dict, List, Set
from qtpy.QtGui import QColor
from ._config import ColorMap, LogLevel


PaletteColorMap = Dict[LogLevel, QColor]


class LogConsolePalette:

    def __init__(self, color_map: Optional[ColorMap] = None):
        super().__init__()
        self._alt_color_map: PaletteColorMap = {}
        self._color_map: PaletteColorMap = {}
        self._inverted_levels: Set[LogLevel] = set()
        self.update_color_map(color_map or _DEFAULT_COLOR_MAP)

    def update_color_map(self, new_val: ColorMap):
        self._color_map.clear()
        self._alt_color_map.clear()
        self._inverted_levels.clear()
        for level, val in new_val.items():
            color_hash, invert = val
            if invert:
                self._inverted_levels.add(level)
            main_color = QColor(color_hash)
            self._color_map[level] = main_color
            self._alt_color_map[level] = color_alternate_to(main_color)

    def color(self, level: LogLevel, alternate: bool = False) -> QColor:
        if alternate:
            return self._alt_color_map[level]
        return self._color_map[level]

    @property
    def color_map(self) -> ColorMap:
        return {level: (color.name(), self.invert(level)) for level, color in self._color_map.items()}

    def invert(self, level: LogLevel) -> bool:
        return level in self._inverted_levels

    def style_sheet(self, base_color: QColor) -> str:
        blocks: List[str] = []
        for level, main_color in self._color_map.items():
            if self.invert(level):
                fg_color = self._alt_color_map[level]
                bg_color = main_color
            else:
                fg_color = main_color
                bg_color = base_color
            blocks.append(".{class_name} {{"
                          " color: {fg_color};"
                          " background-color: {bg_color};"
                          " margin-left: 5px;"
                          " margin-right: 5px; "
                          "}}".format(class_name=LogLevel.level_name(level),
                                      fg_color=fg_color.name(),
                                      bg_color=bg_color.name()))
        return "\n".join(blocks)


_DEFAULT_COLOR_MAP: ColorMap = {
    LogLevel.DEBUG: ("#000000", False),
    LogLevel.INFO: ("#1D7D00", False),
    LogLevel.WARNING: ("#E67700", False),
    LogLevel.ERROR: ("#D32727", False),
    LogLevel.CRITICAL: ("#D32727", True),  # Same as error, but will be inverted
}


def color_alternate_to(main_color: QColor) -> QColor:
    """
    Calculates grayscale color, that is visible against the main color.

    This is useful to pick a foreground color, that is readable on a custom background color.
    This color always stays binary, either black or white, but can be applied to any colored background.

    Args:
        main_color: Main color to calculate alternate for:

    Returns:
        Alternate color object.
    """

    # Invert text color using HSV model to make it readable on the background:
    # https://doc.qt.io/qt-5/qcolor.html#the-hsv-color-model
    brightness = main_color.value()
    new_val = 0 if brightness >= 220 else 255
    new_color = QColor.fromHsv(0, 0, new_val)
    return new_color
