"""
This example shows the simplest way of using CycleSelector widget. Whenever selector is updated, it will be
printed to the console.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from accwidgets.pls import PlsSelector
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PlsSelector simple example")

        pls_selector = PlsSelector(parent=self)
        pls_selector.valueChanged.connect(lambda sel: print(f"New selector: {sel}"))
        self.pls = pls_selector

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().addWidget(pls_selector)
        self.resize(400, 70)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
