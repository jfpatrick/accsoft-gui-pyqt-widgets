"""
This example shows the simplest way of using RbaButton widget. The only thing that it does, is print token
information to the console when login has succeeded.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("RBAC simple example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        widget = RbaButton()
        widget.loginSucceeded.connect(print)
        toolbar.addWidget(widget)
        self.resize(360, 223)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
