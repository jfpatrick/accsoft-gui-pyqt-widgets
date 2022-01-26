"""
This example shows the simplest way of using ScreenshotAction for integrating into user-defined button or menu
without the need of using dedicated ScreenshotButton widget. This action has the same logic, and it is what actually
drives ScreenshotButton under the hood, defining its enabled/disabled state, tooltips and other properties. In this
example, we are reusing the same action for the toolbar button and the menu. For the sake of example, we are using
custom model that does connect to the TEST e-logbook server.
"""

import sys
import qtawesome as qta
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar, QCheckBox, QToolButton, QMenuBar
from accwidgets.rbac import RbaButton
from accwidgets.screenshot import ScreenshotAction
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleLogbookModel  # type: ignore


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ScreenshotAction menu example")

        shared_action = ScreenshotAction(model=SampleLogbookModel())
        shared_action.capture_finished.connect(lambda event_id: print(f"Captured to event id={event_id}"))
        shared_action.capture_failed.connect(lambda e: print(f"Capture failed: {e}"))
        shared_action.activities_failed.connect(lambda e: print(f"Failed to change activities: {e}"))
        self.logbook_action = shared_action

        toolbar = QToolBar()
        self.addToolBar(toolbar)
        btn = QToolButton()
        btn.setIcon(qta.icon("ei.address-book"))
        btn.setDefaultAction(shared_action)
        toolbar.addWidget(btn)

        # RBAC button is required to produce a valid token for the e-logbook communications
        rbac_button = RbaButton()
        shared_action.connect_rbac(rbac_button)
        toolbar.addWidget(rbac_button)

        # Add menu entry: Logbook -> Take screenshot
        menu_bar = QMenuBar()
        menu = menu_bar.addMenu("Logbook")
        menu.addAction(shared_action)
        self.setMenuBar(menu_bar)

        check = QCheckBox("Include window decorations")
        check.setChecked(shared_action.include_window_decorations)
        check.stateChanged.connect(self.on_checked)
        self.setCentralWidget(check)
        self.centralWidget().setContentsMargins(9, 9, 9, 9)

        self.resize(360, 223)

    def on_checked(self, state: Qt.CheckState):
        self.logbook_action.include_window_decorations = (state == Qt.Checked)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
