"""
This example shows the simplest way of using LsaSelector widget. For the sake of example, we are using custom model
that does not require connection to LSA servers.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from accwidgets.lsa_selector import LsaSelector
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleLsaSelectorModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LsaSelector simple example")

        lsa_selector = LsaSelector(parent=self, model=SampleLsaSelectorModel())
        lsa_selector.contextSelectionChanged.connect(lambda ctx: print(f"New LSA context: {ctx}"))
        self.lsa = lsa_selector

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
