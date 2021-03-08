"""
This example shows that ApplicationFrame may accept any widget as a RBAC button, not necessarily derivative of
accwidgets' RbaButton. Menus here are configured to partially recreate the experience provided by
"CERN Application Frame" Qt Designer template.
"""

import sys
from qtpy.QtWidgets import QApplication, QLabel, QMenuBar, QAction
from qtpy.QtCore import Qt
from accwidgets.app_frame import ApplicationFrame
from accwidgets.qt import exec_app_interruptable


class CustomRbaButton(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Custom RBAC contents")
        self.setStyleSheet("background-color: lightgreen; color: black; padding: 10px")
        self.setAlignment(Qt.AlignCenter)
        font = my_widget.font()
        font.setPointSize(16)
        self.setFont(font)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = QLabel("My custom application contents")
    my_widget.setStyleSheet("background-color: yellow; color: black")
    my_widget.setAlignment(Qt.AlignCenter)
    font = my_widget.font()
    font.setPointSize(32)
    my_widget.setFont(font)
    window = ApplicationFrame()
    window.setWindowTitle("Custom RBAC Example")
    window.setCentralWidget(my_widget)
    window.rba_widget = CustomRbaButton()
    window.resize(800, 600)
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
