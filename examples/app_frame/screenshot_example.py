"""
This example shows the use of ApplicationFrame window with ScreenshotButton enabled. Note, this code requires
additional dependencies for ScreenshotButton and RbaButton must be installed (accwidgets[rbac,screenshot]).
ScreenshotButton requires a valid RBAC token to work, therefore it's often being used together with RbaButton.
When both are enabled in ApplicationFrame, they will be automatically connected, so that RBAC token is transferred
automatically. User may need to only define activities, because ScreenshotButton is disabled with no activities
defined (in this case we redefine the whole model in order to connect to the TEST logbook server). Menus here
are configured to partially recreate the experience provided by "CERN Application Frame" Qt Designer template.
In addition to standard menus, we insert the screenshot action into the "File" menu.
"""

import sys
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMenuBar, QAction, QLabel
from accwidgets.app_frame import ApplicationFrame
from accwidgets.qt import exec_app_interruptable
from sample_screenshot_model import SampleScreenshotAction


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ApplicationFrame(use_rbac=True, use_screenshot=True)
    window.setWindowTitle("Screenshot example")
    # Create a new model pointing to the TEST server and having an activity list
    window.screenshot_widget.setDefaultAction(SampleScreenshotAction())

    my_widget = QLabel("My custom application contents")
    my_widget.setStyleSheet("background-color: yellow; color: black")
    my_widget.setAlignment(Qt.AlignCenter)
    font = my_widget.font()
    font.setPointSize(32)
    my_widget.setFont(font)
    window.setCentralWidget(my_widget)

    window.resize(400, 200)
    window.show()

    menu_bar = QMenuBar()
    file = menu_bar.addMenu("File")
    # Add screenshot menu entry as an alternative to toolbar button
    file.addAction(window.screenshot_widget.defaultAction())
    quit = file.addAction("Exit", window.close)
    quit.setMenuRole(QAction.QuitRole)
    menu_bar.addMenu("View")
    help = menu_bar.addMenu("Help")
    about = help.addAction("About", window.showAboutDialog)
    about.setMenuRole(QAction.AboutRole)
    window.setMenuBar(menu_bar)
    sys.exit(exec_app_interruptable(app))
