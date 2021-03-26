"""
This example shows the integration of LogConsole with child loggers. Python's logging module maintains a parent-child
relationships of loggers, based on their names. Likewise, handlers can be used to capture concrete logger's records or
records of its child loggers. In this example, model is set up to track "logger1" and "logger2" and root. "logger1"
has no children, whereas "logger2" has a child "logger2.child". While only configuration of "logger2" is available in
the console's preferences, it affects "logger2.child" in the same way. In addition, "logger3" and "logger4.child" are
used to emit log messages, but are not explicitly tracked by the model. They will be handled by the "root" handler. If
"root" handler was not added to the model, these logs would be ignored. Buttons allow simulating log entries for each
of the available loggers.
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
        self.setWindowTitle("LogConsole child loggers example")
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)

        logger1 = logging.getLogger("logger1")
        logger2 = logging.getLogger("logger2")
        logger2_child = logging.getLogger("logger2.child")
        logger3 = logging.getLogger("logger3")
        logger4_child = logging.getLogger("logger4.child")

        model = LogConsoleModel(loggers=[logger1, logger2, logging.getLogger()], level_changes_modify_loggers=True)
        layout.addWidget(LogConsole(model=model))
        layout.addWidget(LogConsoleExampleButtons(logger=logger1))
        layout.addWidget(LogConsoleExampleButtons(logger=logger2))
        layout.addWidget(LogConsoleExampleButtons(logger=logger2_child))
        layout.addWidget(LogConsoleExampleButtons(logger=logger3))
        layout.addWidget(LogConsoleExampleButtons(logger=logger4_child))
        self.resize(360, 623)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
