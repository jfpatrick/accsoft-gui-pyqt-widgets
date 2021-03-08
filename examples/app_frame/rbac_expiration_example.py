"""
This example shows the use of ApplicationFrame window with RbaButton enabled. Note, this code requires
additional dependencies for RbaButton must be installed (accwidgets[rbac]). This example presents the
events of token creation/expiration and removal. For this reason, the token lifetime is forced to 1 minute
(the shortest possible time). When logged in without selecting roles to preserve auto-renewal, after
approximately 30 seconds the list should print events about token expiration and renewal.
"""

import os
os.environ["RBAC_TOKEN_LIFETIME_MINS"] = "1"  # Set the expiration of the token to 1 minute (min possible value)

import sys
from datetime import datetime
from qtpy.QtWidgets import QApplication, QListWidget
from accwidgets.app_frame import ApplicationFrame
from accwidgets.qt import exec_app_interruptable


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ApplicationFrame(use_rbac=True)
    window.setWindowTitle("RBAC expiration example")
    my_widget = QListWidget()
    window.setCentralWidget(my_widget)
    window.rba_widget.loginSucceeded.connect(lambda token: my_widget.addItem(f"Token obtained at {datetime.now().strftime('%H:%M:%S')} "
                                                                             f"(id: {hex(token.get_serial_id())})"))
    window.rba_widget.tokenExpired.connect(lambda token: my_widget.addItem(f"Token expired at {datetime.now().strftime('%H:%M:%S')} "
                                                                           f"(id: {hex(token.get_serial_id())})"))
    window.rba_widget.logoutFinished.connect(lambda: my_widget.addItem(f"Token removed at {datetime.now().strftime('%H:%M:%S')}"))
    window.resize(400, 200)
    window.show()
    sys.exit(exec_app_interruptable(app))
