"""
This example shows the way of setting custom icons in a RbaButton widget. The rest of the logic is identical to
"basic_example.py".
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable, make_icon


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("RBAC custom icons example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        widget = RbaButton()
        widget.set_icons(online=make_icon(Path(__file__).parent / "icons" / "logout.gif"),
                         offline=make_icon(Path(__file__).parent / "icons" / "login.gif"))
        widget.loginSucceeded.connect(print)
        toolbar.addWidget(widget)
        self.resize(360, 223)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
