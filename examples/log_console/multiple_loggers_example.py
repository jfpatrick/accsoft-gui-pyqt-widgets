"""
This example shows the integration of LogConsole with custom loggers. To achieve that, an instance of LogConsoleModel
is created, which receives the list of dynamically generated loggers. Buttons allow simulating log entries for each
of the generated logger.
"""

import sys
import logging
import random
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea, QSplitter
from accwidgets.log_console import LogConsole, LogLevel, LogConsoleModel
from accwidgets.qt import exec_app_interruptable
from utils import LogConsoleExampleButtons


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LogConsole multiple loggers example")
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)
        scroll_area = QScrollArea()
        layout = QVBoxLayout()
        scroll_area_contents = QWidget()
        scroll_area_contents.setLayout(layout)
        scroll_area.setWidget(scroll_area_contents)
        scroll_area_contents.setMinimumSize(self.size())
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        loggers = []
        for idx in range(5):
            logger_name = f"Logger-{idx}"
            logger = logging.getLogger(logger_name)
            level = random.randint(0, len(LogLevel) - 1)
            logger.setLevel(list(LogLevel)[level].value)
            layout.addWidget(LogConsoleExampleButtons(logger=logger))
            loggers.append(logger)

        model = LogConsoleModel(loggers=loggers, level_changes_modify_loggers=True)
        splitter.addWidget(LogConsole(model=model))
        splitter.addWidget(scroll_area)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)
        splitter.setContentsMargins(9, 9, 9, 9)

        self.resize(930, 450)
        splitter.setSizes([200, 730])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
