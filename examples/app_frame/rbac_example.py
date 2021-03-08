"""
This example shows the use of ApplicationFrame window with RbaButton enabled. Note, this code requires
additional dependencies for RbaButton must be installed (accwidgets[rbac]). To present the usage of the token
in the application, the username is printed in the central widget's area. Menus here are configured to
partially recreate the experience provided by "CERN Application Frame" Qt Designer template.
"""

import sys
from qtpy.QtWidgets import QApplication, QLabel, QMenuBar, QAction
from qtpy.QtCore import Qt
from accwidgets.app_frame import ApplicationFrame
from accwidgets.qt import exec_app_interruptable


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = QLabel("RBAC Token: None")
    my_widget.setWordWrap(True)
    my_widget.setAlignment(Qt.AlignCenter)
    window = ApplicationFrame(use_rbac=True)
    window.setWindowTitle("RBAC example")
    window.setCentralWidget(my_widget)
    window.rba_widget.loginSucceeded.connect(lambda token: my_widget.setText(f"RBAC Token: {token.get_user_name()}"))
    window.rba_widget.loginFailed.connect(my_widget.setText)
    window.resize(400, 200)
    window.show()
    menu_bar = QMenuBar()
    file = menu_bar.addMenu("File")
    quit = file.addAction("Exit", window.close)
    quit.setMenuRole(QAction.QuitRole)
    menu_bar.addMenu("View")
    help = menu_bar.addMenu("Help")
    about = help.addAction("About", window.showAboutDialog)
    about.setMenuRole(QAction.AboutRole)
    window.setMenuBar(menu_bar)
    sys.exit(exec_app_interruptable(app))
