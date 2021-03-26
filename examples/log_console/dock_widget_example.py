"""
This example shows how to integrate a LogConsoleDock into the QMainWindow. In this example, floating and collapsing
of the dock is disabled.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QDockWidget
from qtpy.QtCore import Qt
from accwidgets.log_console import LogConsoleDock
from accwidgets.qt import exec_app_interruptable
from utils import LogConsoleExampleButtons


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LogConsoleDock example")
        self.setCentralWidget(LogConsoleExampleButtons())
        dock = LogConsoleDock()
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)   # Disable floating and collapsing (dock-level)
        dock.console.expanded = False  # Make collapsed by default
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)
        self.resize(360, 223)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
