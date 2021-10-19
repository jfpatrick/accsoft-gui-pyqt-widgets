"""
This is the example of stylizing the widget with custom colors when QSS is not involved. For the sake of example,
we are using custom model that does not require connection to LSA servers.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from accwidgets.lsa_selector import LsaSelector
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleLsaSelectorModel  # type: ignore


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LsaSelector styling example")

        lsa_selector = LsaSelector(parent=self, model=SampleLsaSelectorModel(resident_only=False))
        lsa_selector.contextSelectionChanged.connect(lambda ctx: print(f"New LSA context: {ctx}"))
        lsa_selector.residentBackgroundColor = Qt.white
        lsa_selector.userColor = Qt.black
        lsa_selector.activeColor = QColor("darkgreen")
        lsa_selector.spareColor = QColor("darkblue")
        lsa_selector.residentColor = QColor("darkgray")
        lsa_selector.residentNonMultiplexedColor = QColor("darkorange")
        lsa_selector.selectionBackgroundColor = QColor("lightgray")
        lsa_selector.selectionColor = Qt.black
        lsa_selector.nonResidentNonMultiplexedColor = QColor(91, 73, 0)
        lsa_selector.nonResidentColor = Qt.black
        lsa_selector.nonResidentBackgroundColor = QColor(255, 140, 140)
        lsa_selector.canBecomeResidentBackgroundColor = QColor(200, 200, 240)

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().addWidget(lsa_selector)
        self.resize(400, 200)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
