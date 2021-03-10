"""
This example shows the way of using RbaButton widget with other pyrbac-reliant components. In this example,
ThirdPartyRbacComponent acts as a class that in reality could be coming from some other library. What's important,
it can work with pyrbac objects directly. To simulate its operation, it simply extracts the user name from the RBAC
token and fires it in a signal, to be displayed by the GUI. pyrbac does not keep tokens in a global state,
therefore even though both components are using pyrbac, token propagation is still needed to synchronize the states.
"""

import sys
import pyrbac
from qtpy.QtCore import Qt, QObject, Signal
from qtpy.QtWidgets import QApplication, QMainWindow, QLabel, QToolBar
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable


class ThirdPartyRbacComponent(QObject):

    info_updated = Signal(str)

    def on_token_received(self, token: pyrbac.Token):
        self.info_updated.emit(f"Token received by pyrbac component: {token.get_user_name()}")

    def on_token_removed(self):
        self.info_updated.emit("Token received by pyrbac component: None")

    def on_token_failed(self, err):
        self.info_updated.emit(f"RBAC error: {err!s}")


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("RbaButton-PyRBAC interaction example")
        self.rbac_component = ThirdPartyRbacComponent(self)

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        self.rbac_component.info_updated.connect(label.setText)
        self.setCentralWidget(label)

        toolbar = QToolBar()
        self.addToolBar(toolbar)
        widget = RbaButton()
        widget.loginSucceeded.connect(self.rbac_component.on_token_received)
        widget.loginFailed.connect(self.rbac_component.on_token_failed)
        widget.logoutFinished.connect(self.rbac_component.on_token_removed)
        toolbar.addWidget(widget)

        self.resize(450, 200)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
