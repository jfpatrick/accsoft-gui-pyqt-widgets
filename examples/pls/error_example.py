"""
This is the example of how communication error is displayed to the user. Since the widget communicates with
CCDA, a communication error may happen. In that case, the error message will be displayed in place of widget
UI controls.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from accwidgets.pls import PlsSelector, PlsSelectorModel, PlsSelectorConnectionError
from accwidgets.qt import exec_app_interruptable


class ErrorModel(PlsSelectorModel):

    async def fetch(self):
        raise PlsSelectorConnectionError("Sample error")


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PlsSelector error example")

        pls_selector = PlsSelector(parent=self, model=ErrorModel())

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
