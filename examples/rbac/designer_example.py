"""
This is an example integrating RbaButton, produced using Qt Designer, instead of the programmatically created one.
Because Qt Designer does not allow placing widgets into toolbars, it can only be added to the main widget.
When required to use inside QToolBar, consider creating RbaButton programmatically.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton
from qtpy.uic import loadUi
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btn_code: QPushButton = None
        self.rbac: RbaButton = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
