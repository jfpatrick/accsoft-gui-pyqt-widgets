"""
This is the example of stylizing the LogConsole with custom colors using QSS stylesheets.
We are presenting the color scheme that matches the dark mode style.
It will attach to the root Python logger. Buttons allow simulating log entries.
"""

import sys
import logging
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from accwidgets.log_console import LogConsole
from accwidgets.qt import exec_app_interruptable
from utils import LogConsoleExampleButtons


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCentralWidget(QWidget())
        self.setWindowTitle("LogConsole QSS example")
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)
        layout.addWidget(LogConsole())
        layout.addWidget(LogConsoleExampleButtons())
        self.resize(360, 223)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    style = Path(__file__).parent / "dark.qss"
    dark_mode = style.read_text()
    dark_mode += """
LogConsole {
    qproperty-errorColor: rgb(243, 44, 44);
    qproperty-criticalColor: rgb(243, 44, 44);
    qproperty-warningColor: rgb(245, 127, 0);
    qproperty-infoColor: rgb(55, 235, 0);
    qproperty-debugColor: rgb(221, 221, 221);
}
"""
    app.setStyleSheet(dark_mode)
    sys.exit(exec_app_interruptable(app))
