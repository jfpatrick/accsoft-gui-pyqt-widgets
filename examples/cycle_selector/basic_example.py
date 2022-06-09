"""
This example shows the simplest way of using CycleSelector widget. Whenever selector is updated, it will be
printed to the console.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from accwidgets.cycle_selector import CycleSelector
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("CycleSelector simple example")

        selector = CycleSelector(parent=self)
        selector.valueChanged.connect(lambda sel: print(f"New cycle: {sel}"))
        self.selector = selector

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().addWidget(selector)
        self.resize(400, 70)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
