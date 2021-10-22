"""
This is the example of stylizing the widget with custom colors using QSS stylesheets. For the sake of example,
we are using custom model that does not require connection to LSA servers.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from accwidgets.lsa_selector import LsaSelector
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleLsaSelectorModel  # type: ignore


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LsaSelector QSS example")
        self.setStyleSheet("""
LsaSelector {
    qproperty-residentBackgroundColor: white;
    qproperty-userColor: black;
    qproperty-activeColor: darkgreen;
    qproperty-spareColor: darkblue;
    qproperty-residentColor: darkgray;
    qproperty-residentNonMultiplexedColor: darkorange;
    qproperty-selectionBackgroundColor: lightgray;
    qproperty-selectionColor: black;
    qproperty-nonResidentNonMultiplexedColor: #5b4900;
    qproperty-nonResidentColor: black;
    qproperty-nonResidentBackgroundColor: #ff8c8c;
    qproperty-canBecomeResidentBackgroundColor: #c8c8f0;
}
""")

        lsa_selector = LsaSelector(parent=self, model=SampleLsaSelectorModel(resident_only=False))
        lsa_selector.contextSelectionChanged.connect(lambda ctx: print(f"New LSA context: {ctx}"))

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
