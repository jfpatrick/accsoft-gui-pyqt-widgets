"""
This example shows the way of assigning a key sequence as a shortcut for triggering the action without necessarily
pushing the button. It can be done with a standalone ScreenshotAction or the one that belongs to the ScreenshotButton.
For the sake of example, we are using custom model that does connect to the TEST e-logbook server.
"""

import sys
from qtpy.QtWidgets import QApplication
from accwidgets.qt import exec_app_interruptable
from action_example import MainWindow  # type: ignore


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("ScreenshotButton shortcut example")
    window.logbook_action.setShortcut("Ctrl+P")
    window.show()
    sys.exit(exec_app_interruptable(app))
