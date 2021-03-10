"""
This example shows how authentication performed outside of RbaButton can be propagated into the widget to display
the relevant status and information. Here we are using PyJapc.rbacLogin method to authenticate (which calls
into Java libraries under the hood of PyJapc), and send a serialized token to the widget, to be recreated as
pyrbac C++ token inside. The same technique can be used with other authentication methods or libraries, as long as they
can produce one of the accepted token types: pyrbac.Token object, encoded bytes array, or base64-serialized string.
Use the UI in the main window to login, and observe how RbaButton adapts to the new token.
"""

import sys
import jpype
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar, QPushButton, QLineEdit, QVBoxLayout, QWidget
from accwidgets.rbac import RbaButton
from accwidgets.qt import exec_app_interruptable
from pyjapc import PyJapc


cern = jpype.JPackage("cern")


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PyJapc-RbaButton interaction example")
        self.japc = PyJapc(incaAcceleratorName=None)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Login")
        btn.clicked.connect(self.on_login)

        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(btn)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        toolbar = QToolBar()
        self.addToolBar(toolbar)
        rba_widget = RbaButton()
        toolbar.addWidget(rba_widget)
        self.rba_widget = rba_widget

        self.resize(450, 200)

    def on_login(self):
        try:
            self.japc.rbacLogin(username=self.username.text(),
                                password=self.password.text())
        except Exception:  # noqa: B902
            self.rba_widget.model.logout()
        else:
            self.rba_widget.model.update_token(self.japc.rbacGetSerializedToken())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
