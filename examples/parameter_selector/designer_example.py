"""
This is the the same example as basic_example.py, but integrating with Qt Designer widget, instead of the
programmatically created one. The newly selected parameter name is printed to the console.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy.uic import loadUi
from accwidgets.parameter_selector import ParameterLineEdit
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.widget: ParameterLineEdit = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)
        self.centralWidget().layout().setContentsMargins(9, 9, 9, 9)
        self.widget.valueChanged.connect(lambda name: print(f"New parameter name: {name}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
