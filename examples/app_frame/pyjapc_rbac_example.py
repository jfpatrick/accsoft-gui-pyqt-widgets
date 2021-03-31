"""
This example shows the use of ApplicationFrame window with RbaButton enabled. Note, this code requires
additional dependencies for RbaButton must be installed (accwidgets[rbac]). It is similar to the use-case in
rbac_example.py, except the token is used to authenticate Java client inside PyJapc (to further perform authorized
interaction with the control system via PyJapc). To present the usage of the token
in PyJapc, the username that is extracted from Java RBAC token is printed in the central widget's area.
Menus here are configured to partially recreate the experience provided by "CERN Application Frame" Qt Designer template.
"""

import sys
import jpype
from qtpy.QtWidgets import QApplication, QLabel, QMenuBar, QAction
from qtpy.QtCore import Qt
from pyjapc import PyJapc
from accwidgets.app_frame import ApplicationFrame
from accwidgets.qt import exec_app_interruptable


cern = jpype.JPackage("cern")


class MainWindow(ApplicationFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("RBAC-PyJapc interaction example")
        self.japc = PyJapc(incaAcceleratorName=None)

        self.auth_label = QLabel()
        self.auth_label.setAlignment(Qt.AlignCenter)
        self.auth_label.setWordWrap(True)
        self.setCentralWidget(self.auth_label)

        self.update_login_info()

        rba_button = self.rba_widget
        if rba_button is not None:
            rba_button.loginSucceeded.connect(self.on_pyrbac_login)
            rba_button.loginFailed.connect(self.on_pyrbac_error)
            rba_button.logoutFinished.connect(self.on_pyrbac_logout)

        menu_bar = QMenuBar()
        file = menu_bar.addMenu("File")
        quit = file.addAction("Exit", self.close)
        quit.setMenuRole(QAction.QuitRole)
        menu_bar.addMenu("View")
        help = menu_bar.addMenu("Help")
        about = help.addAction("About", self.showAboutDialog)
        about.setMenuRole(QAction.AboutRole)
        self.setMenuBar(menu_bar)
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
    window = MainWindow(use_rbac=True)
    window.show()
    sys.exit(exec_app_interruptable(app))
