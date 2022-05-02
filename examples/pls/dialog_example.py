"""
This example shows the way of using CycleSelectorDialog, which wraps CycleSelectorWidget in a simple dialog with
"Ok" and "Cancel" buttons. When the dialog selection is finished, the new value will be printed to the console,
unless the dialog has been cancelled.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QPushButton
from accwidgets.pls import PlsSelectorDialog
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PlsSelector dialog example")

        btn = QPushButton("Press to open dialog")
        btn.clicked.connect(self._open_dialog)

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().addWidget(btn)
        self.resize(100, 50)

    def _open_dialog(self):
        dialog = PlsSelectorDialog(parent=self)
        if dialog.exec_() == PlsSelectorDialog.Accepted:
            print(f"New selector: {dialog.value}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
