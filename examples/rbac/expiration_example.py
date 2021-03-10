"""
This example shows how token expiration can be handled, when using RbaButton widget. RbaButton will
automatically renew tokens when they expire, but only if user roles have not been specifically configured. Custom user
roles produce non-renewable tokens. This example logs the events of login/logout/token expiration. It also configures
RBAC behavior to generate tokens with lifetime of 1 minute, the shortest possible time frame. Try different ways of
logging in and observe the logged messages in the main window.
"""

import os
os.environ["RBAC_TOKEN_LIFETIME_MINS"] = "1"  # Set the expiration of the token to 1 minute (min possible value)

import sys
from datetime import datetime
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar, QListWidget
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("RBAC expiration example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        widget = RbaButton()
        toolbar.addWidget(widget)
        self.resize(360, 223)

        self.list = QListWidget()
        self.setCentralWidget(self.list)

        widget.loginSucceeded.connect(lambda token: self.list.addItem(f"Token obtained at {datetime.now().strftime('%H:%M:%S')} (id: {hex(token.get_serial_id())})"))
        widget.tokenExpired.connect(lambda token: self.list.addItem(f"Token expired at {datetime.now().strftime('%H:%M:%S')} (id: {hex(token.get_serial_id())})"))
        widget.logoutFinished.connect(lambda: self.list.addItem(f"Token removed at {datetime.now().strftime('%H:%M:%S')}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
