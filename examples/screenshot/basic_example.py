"""
This example shows the simplest way of using ScreenshotButton widget. When no sources are specified, the button will
grab a screenshot of the parent window. We can control the appearance of the window screenshot with
"includeWindowDecorations" property.
"""

import sys
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar, QCheckBox
from pylogbook import NamedServer
from accwidgets.rbac import RbaButton
from accwidgets.screenshot import ScreenshotButton
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ScreenshotButton basic example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        logbook_button = ScreenshotButton(source=self,
                                          message="Qt-Logbook integration example",
                                          server_url=NamedServer.TEST,
                                          activities="LINAC_4")
        self.logbook_button = logbook_button
        logbook_button.captureFinished.connect(lambda event_id: print(f"Captured to event id={event_id}"))
        logbook_button.captureFailed.connect(lambda e: print(f"Capture failed: {e}"))
        toolbar.addWidget(logbook_button)

        # RBAC button is required to produce a valid token for the e-logbook communications
        rbac_button = RbaButton()
        rbac_button.loginSucceeded.connect(logbook_button.set_rbac_token)
        rbac_button.logoutFinished.connect(logbook_button.clear_rbac_token)
        rbac_button.tokenExpired.connect(logbook_button.clear_rbac_token)
        toolbar.addWidget(rbac_button)

        check = QCheckBox("Include window decorations")
        check.setChecked(logbook_button.includeWindowDecorations)
        check.stateChanged.connect(self.on_checked)
        self.setCentralWidget(check)
        self.centralWidget().setContentsMargins(9, 9, 9, 9)

        self.resize(360, 223)

    def on_checked(self, state: Qt.CheckState):
        self.logbook_button.includeWindowDecorations = (state == Qt.Checked)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
