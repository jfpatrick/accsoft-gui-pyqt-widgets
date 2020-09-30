"""
This example shows how to use a custom formatter implementation by subclassing the AbstractLogConsoleFormatter.
Here, the custom formatter has a single configuration option “Show smiley face”, which will prefix messages
with ":)". Buttons allow simulating log entries for each of the generated logger.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from accwidgets.log_console import LogConsole, AbstractLogConsoleFormatter
from utils import LogConsoleExampleButtons

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MyFormatter(AbstractLogConsoleFormatter):

    def __init__(self, show_emoji: bool = False):
        super().__init__()
        self.show_emoji = show_emoji

    def format(self, record):
        res = ""
        if self.show_emoji:
            res += ":)   "
        res += record.message
        return res

    @classmethod
    def configurable_attributes(cls):
        return {
            "show_emoji": "Show smiley face",
        }


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LogConsole custom formatter example")
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)
        layout.addWidget(LogConsole(formatter=MyFormatter()))
        layout.addWidget(LogConsoleExampleButtons())
        self.resize(360, 223)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
