"""
This is the same example as basic_example.py, but integrating with Qt Designer widget, instead of the
programmatically created one. The newly chosen cycle selector is printed to the console. Because Qt Designer does
not allow placing widgets into toolbars, only PlsSelector is available there, while CycleSelectorAction and
PlsSelectorDialog are left for the programmatic use.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy.uic import loadUi
from accwidgets.pls import PlsSelector
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.widget: PlsSelector = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)
        self.centralWidget().layout().setContentsMargins(9, 9, 9, 9)
        self.widget.valueChanged.connect(lambda sel: print(f"New selector: {sel}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
