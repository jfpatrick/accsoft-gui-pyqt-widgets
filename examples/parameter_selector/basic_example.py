"""
This example shows the simplest way of using ParameterLineEdit widget. The newly selected parameter name is printed
to the console.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSizePolicy
from accwidgets.parameter_selector import ParameterLineEdit
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ParameterLineEdit simple example")

        widget = ParameterLineEdit(self)
        widget.valueChanged.connect(lambda name: print(f"New parameter name: {name}"))
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)
        layout.addStretch()
        layout.addWidget(widget)
        layout.addStretch()
        self.resize(400, 70)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
