"""
This example shows the way of using ScreenshotButton widget with multiple sources. These sources should not necessarily
be windows, it can be individual subwidgets, which are represented here by 2 separate labels, colored in cyan and
yellow. For the sake of example, we are using custom model
that does connect to the TEST e-logbook server.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar, QLabel, QHBoxLayout, QWidget
from accwidgets.rbac import RbaButton
from accwidgets.screenshot import ScreenshotButton
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleScreenshotAction  # type: ignore


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ScreenshotButton multiple sources example")
        layout = QHBoxLayout()
        src1 = QLabel("Source 1")
        src1.setStyleSheet("background-color: cyan")
        layout.addWidget(src1)
        src2 = QLabel("Source 2")
        src2.setStyleSheet("background-color: yellow")
        layout.addWidget(src2)
        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        logbook_button = ScreenshotButton(action=SampleScreenshotAction())
        logbook_button.source = src1, src2
        logbook_button.captureFinished.connect(lambda event_id: print(f"Captured to event id={event_id}"))
        logbook_button.captureFailed.connect(lambda e: print(f"Capture failed: {e}"))
        logbook_button.activitiesFailed.connect(lambda e: print(f"Failed to change activities: {e}"))
        toolbar.addWidget(logbook_button)

        # RBAC button is required to produce a valid token for the e-logbook communications
        rbac_button = RbaButton()
        logbook_button.defaultAction().connect_rbac(rbac_button)
        toolbar.addWidget(rbac_button)

        self.resize(360, 223)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
