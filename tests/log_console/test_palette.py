import pytest
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from accwidgets.log_console._palette import color_alternate_to


@pytest.mark.parametrize("main_color,expected_alternate_color", [
    ("#c61f9f", Qt.white),
    ("#1dd13e", Qt.white),
    ("#000000", Qt.white),
    ("#1D7D00", Qt.white),
    ("#E67700", Qt.black),
    ("#D32727", Qt.white),
    ("#f32c2c", Qt.black),
    ("#f57f00", Qt.black),
    ("#37eb00", Qt.black),
    ("#dddddd", Qt.black),
])
def test_color_alternate_to(main_color, expected_alternate_color):
    assert color_alternate_to(QColor(main_color)).name() == QColor(expected_alternate_color).name()
