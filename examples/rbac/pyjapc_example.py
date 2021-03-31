"""
This example shows the way of using RbaButton widget with Java RBAC implementation, taking PyJapc as a use-case.
PyJapc is backed by Java libraries, including RBAC components, while pyrbac under the hood of RbaButton relies on
C++ implementation of RBAC. Hence, the token is not automatically synchronized between the two environments,
and user glue code is needed to propagate the token. RbaButton fires a signal, when a token gets created. This token
is of pyrbac.Token type, but it can be serialized into a bytes array and recreated in Java, using Java methods
from cern.rbac package. This example displays a label with the token information, that is retrieved via PyJapc's calls,
to prove that the token is correctly recreated in Java.
"""

import sys
import jpype
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QLabel, QToolBar
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable
from pyjapc import PyJapc


cern = jpype.JPackage("cern")


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("RbaButton-PyJapc interaction example")
        self.japc = PyJapc(incaAcceleratorName=None)

        self.auth_label = QLabel()
        self.auth_label.setAlignment(Qt.AlignCenter)
        self.auth_label.setWordWrap(True)
        self.setCentralWidget(self.auth_label)

        self.update_login_info()

        toolbar = QToolBar()
        self.addToolBar(toolbar)
        widget = RbaButton()
        widget.loginSucceeded.connect(self.on_pyrbac_login)
        widget.loginFailed.connect(self.on_pyrbac_error)
        widget.logoutFinished.connect(self.on_pyrbac_logout)
        toolbar.addWidget(widget)

        self.resize(450, 200)

    def on_pyrbac_login(self, pyrbac_token):
        new_token = cern.rbac.common.RbaToken.parseAndValidate(jpype.java.nio.ByteBuffer.wrap(pyrbac_token.get_encoded()))
        cern.rbac.util.holder.ClientTierTokenHolder.setRbaToken(new_token)

        self.update_login_info()

    def on_pyrbac_error(self, err):
        self.auth_label.setText(f"RBAC error: {err!s}")

    def on_pyrbac_logout(self):
        self.japc.rbacLogout()
        self.update_login_info()

    def update_login_info(self):
        java_token = self.japc.rbacGetToken()
        if not java_token:
            self.auth_label.setText("Token received by PyJapc: None")
        else:
            self.auth_label.setText(f"Token received by PyJapc: {java_token.getUser().getName()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
