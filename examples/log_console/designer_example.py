"""
This example shows the integration of LogConsole via Qt Designer. To show the additional features, compared to
code_example.py, Qt Designer file sets up signal-slot connection for custom buttons to freeze the console.
It will attach to the root Python logger. Buttons allow simulating log entries.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton
from qtpy.uic import loadUi
from accwidgets.log_console import LogConsole
from accwidgets.qt import exec_app_interruptable
from utils import LogConsoleExampleButtons


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btn_code: QPushButton = None
        self.console: LogConsole = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)
        self.btn_code.clicked.connect(self.console.toggleFreeze)
        self.centralWidget().layout().addWidget(LogConsoleExampleButtons())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
