"""
This example is similar to basic_example.py in terms of widget configuration, but adds an additional option
to only select devices and properties, but not fields. The newly selected parameter name is printed to the console.
"""

import sys
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSizePolicy, QCheckBox
from accwidgets.parameter_selector import ParameterLineEdit
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ParameterLineEdit no field example")

        widget = ParameterLineEdit(self)
        widget.enableFields = False
        widget.valueChanged.connect(lambda name: print(f"New parameter name: {name}"))
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.edit = widget

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)
        layout.addStretch()
        layout.addWidget(widget)
        layout.addStretch()
        checkbox = QCheckBox("Allow field selection")
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        checkbox.setChecked(widget.enableFields)
        layout.addWidget(checkbox)
        self.resize(400, 100)

    def _on_checkbox_changed(self, state: Qt.CheckState):
        self.edit.enableFields = state == Qt.Checked


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
