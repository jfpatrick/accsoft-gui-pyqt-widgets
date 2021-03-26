"""
This example shows the simplest and the most minimalistic integration of LogConsole widgets with the default setup
in code. It will attach to the root Python logger. Buttons allow simulating log entries.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from accwidgets.log_console import LogConsole
from accwidgets.qt import exec_app_interruptable
from utils import LogConsoleExampleButtons


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LogConsole simple example")
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)
        layout.addWidget(LogConsole())
        layout.addWidget(LogConsoleExampleButtons())
        self.resize(360, 223)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
