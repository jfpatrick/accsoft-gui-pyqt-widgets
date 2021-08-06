"""
This example shows the simplest way of using ParameterSelectorDialog widget. This is useful if ParameterLineEdit
widget is not fitting the purpose, hence you can issue a selector dialog manually using any action, for instance,
a button press or QAction in the main menu. The newly selected parameter name is printed to the console. User has also
a possibility to configure the dialog for the usage of protocols, just as showcased in protocol_example.py.
"""

import sys
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QCheckBox
from accwidgets.parameter_selector import ParameterSelectorDialog
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ParameterSelectorDialog example")
        button = QPushButton("Open!")
        button.clicked.connect(self._open_dialog)
        self._selected_value = ""
        self._enable_protocols = False
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        layout.addWidget(button)
        layout.addStretch()
        checkbox = QCheckBox("Allow protocol selection")
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        checkbox.setChecked(self._enable_protocols)
        layout.addWidget(checkbox)
        self.resize(400, 70)

    def _open_dialog(self):
        dialog = ParameterSelectorDialog(initial_value=self._selected_value,
                                         enable_protocols=self._enable_protocols,
                                         parent=self)
        if dialog.exec_() == ParameterSelectorDialog.Accepted:
            self._selected_value = dialog.value
            print(f"New parameter name: {dialog.value}")

    def _on_checkbox_changed(self, state: Qt.CheckState):
        self._enable_protocols = state == Qt.Checked


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
