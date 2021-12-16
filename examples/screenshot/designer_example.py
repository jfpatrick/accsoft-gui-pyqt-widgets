"""
This is an example integrating ScreenshotButton, produced using Qt Designer, instead of the programmatically created one.
Because Qt Designer does not allow placing widgets into toolbars, it can only be added to the main widget.
When required to use inside QToolBar, consider creating ScreenshotButton programmatically. For the sake of example,
we are using custom model that does connect to the TEST e-logbook server.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy.uic import loadUi
from accwidgets.screenshot import ScreenshotButton
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleScreenshotAction  # type: ignore


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logbook_btn: ScreenshotButton = None
        self.rbac: RbaButton = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)
        action = SampleScreenshotAction()
        action.connect_rbac(self.rbac)
        self.logbook_btn.setDefaultAction(action)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
