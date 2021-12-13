"""
This example shows the simplest way of using ScreenshotButton widget.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar
from pylogbook import NamedServer
from accwidgets.rbac import RbaButton
from accwidgets.screenshot import ScreenshotButton
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ScreenshotButton example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        logbook_button = ScreenshotButton(widget=self,
                                          message='Qt-Logbook integration example',
                                          server_url=NamedServer.TEST,
                                          activities='LINAC_4')
        logbook_button.capture_succeeded.connect(self.capture_succeeded)
        logbook_button.capture_failed.connect(self.capture_failed)
        toolbar.addWidget(logbook_button)

        # RBAC button is required to produce a valid token for the e-logbook communications
        rbac_button = RbaButton()
        rbac_button.loginSucceeded.connect(logbook_button.set_rbac_token)
        rbac_button.logoutFinished.connect(logbook_button.clear_rbac_token)
        rbac_button.tokenExpired.connect(logbook_button.clear_rbac_token)
        toolbar.addWidget(rbac_button)

        self.resize(360, 223)

    def capture_succeeded(self, event_id):
        print("Captured to event id={0}".format(event_id))

    def capture_failed(self, message):
        print("Capture failed: {0}".format(message))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
