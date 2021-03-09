"""
This is the example of stylizing the widget with custom colors programmatically.
We are presenting the color scheme that matches the dark mode style.
For the sake of example, we are using custom model that does not require connection to real devices.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from accwidgets.timing_bar import TimingBar
from accwidgets.qt import exec_app_interruptable
from dark_mode import dark_mode_style
from sample_model import SampleTimingBarModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("TimingBar palette example")
        self.setStyleSheet(dark_mode_style)

        timing_bar = TimingBar(model=SampleTimingBarModel())
        timing_bar.highlightedUser = "USER2"
        palette = timing_bar.color_palette
        palette.timing_mark = Qt.red
        palette.normal_cycle = QColor(191, 191, 191)
        palette.highlighted_cycle = QColor(236, 228, 182)
        palette.bg_pattern = Qt.black
        palette.bg_pattern_alt = QColor(48, 48, 48)
        palette.bg_top = QColor(79, 79, 79)
        palette.bg_bottom = QColor(38, 38, 38)
        palette.bg_top_alt = QColor(85, 85, 85)
        palette.bg_bottom_alt = QColor(49, 49, 49)
        palette.text = QColor(238, 238, 238)
        palette.error_text = QColor(221, 9, 2)
        palette.frame = Qt.black
        timing_bar.color_palette = palette

        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        layout.addWidget(timing_bar)
        self.centralWidget().setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
