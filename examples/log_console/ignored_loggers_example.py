"""
This example shows how LogConsole can ignore messages from certain loggers. To achieve that, we pass custom loggers
to the model that we want to handle, and make sure to not pass the root logger (usually created with the call
``logging.getLogger()`` without arguments) that would otherwise handle the rest of all messages. In this example, only
"logger1" messages appear in the console, while "logger2" are completely ignored. Buttons allow simulating log entries
for each of the available loggers.
"""

import sys
import logging
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from accwidgets.log_console import LogConsole, LogConsoleModel
from accwidgets.qt import exec_app_interruptable
from utils import LogConsoleExampleButtons


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LogConsole ignored loggers example")
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)

        logger1 = logging.getLogger("logger1")
        logger2 = logging.getLogger("logger2")

        model = LogConsoleModel(loggers=[logger1], level_changes_modify_loggers=True)
        layout.addWidget(LogConsole(model=model))
        layout.addWidget(LogConsoleExampleButtons(logger=logger1))
        layout.addWidget(LogConsoleExampleButtons(logger=logger2))
        self.resize(360, 423)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
