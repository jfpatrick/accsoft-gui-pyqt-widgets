"""
This example shows the simplest and the most minimalistic use of ApplicationFrame window with the default setup
in code. By default, it will enable only LogConsoleDock, a widget that does not require additional connections,
and thus additional setup. Menus here are configured to partially recreate the experience provided by
"CERN Application Frame" Qt Designer template.
"""

import sys
from qtpy.QtWidgets import QApplication, QLabel, QMenuBar, QAction
from qtpy.QtCore import Qt
from accwidgets.app_frame import ApplicationFrame

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = QLabel("My custom application contents")
    my_widget.setStyleSheet("background-color: yellow; color: black")
    my_widget.setAlignment(Qt.AlignCenter)
    font = my_widget.font()
    font.setPointSize(32)
    my_widget.setFont(font)
    window = ApplicationFrame()
    window.setWindowTitle("Programmatic Example")
    window.setCentralWidget(my_widget)
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
    sys.exit(app.exec_())
