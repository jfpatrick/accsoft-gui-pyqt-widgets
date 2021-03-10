"""
This is the example of stylizing the widget with custom colors when QSS is not involved. We are presenting the color
scheme that could be used in the dark mode style.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("RBAC styling example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        widget = RbaButton()
        widget.loginSucceeded.connect(self.status_changed)
        toolbar.addWidget(widget)
        self.resize(360, 223)

    def status_changed(self, token):
        print(token)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    style = Path(__file__).parent / "dark.qss"
    dark_mode = style.read_text()
    dark_mode += """
RbaButton { qproperty-mcsColor: #ff0000; }
RbaButton QLabel[qss-role="error"], RbaButton QLabel[qss-role="critical"] { color: red; }
RbaButton QLabel[qss-role="info"] { color: cyan; }
RbaButton QLabel[qss-role="bg-positive"] { background-color: #003b00; }
RbaButton QLabel[qss-role="bg-critical"] { background-color: red; }
"""
    app.setStyleSheet(dark_mode)
    sys.exit(exec_app_interruptable(app))
