"""
This is the example of stylizing the widget with custom colors using QSS. We are presenting the color
scheme that could be used in the dark mode style. The widget is reused from the basic_example.py.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication
from accwidgets.qt import exec_app_interruptable
from basic_example import MainWindow  # type: ignore


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("ScreenshotButton styling example")
    window.show()
    style = Path(__file__).parent.parent / "_common" / "dark.qss"
    dark_mode = style.read_text()
    app.setStyleSheet(dark_mode)
    sys.exit(exec_app_interruptable(app))
