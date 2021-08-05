"""
This is the example of stylizing the widget with custom colors using QSS stylesheets. We are presenting the color
scheme that matches the dark mode style. You will find all ways of accessing the selector dialog in this single
example: using ParameterLineEdit, ParameterSelectorDialog, or ParameterLineEditColumnDelegate. The first two are
connected together and print/reconfigure the same selector value. ParameterLineEditColumnDelegate is not connected
with those, and follows the same logic as in table_example.py (except protocols are always disabled), just to
display a characteristic styling of the table view.
"""

import sys
from pathlib import Path
from qtpy.QtCore import QSignalBlocker
from qtpy.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QSizePolicy, QPushButton, QHeaderView,
                            QFrame)
from accwidgets.parameter_selector import ParameterLineEdit, ParameterSelectorDialog, ParameterLineEditColumnDelegate
from accwidgets.qt import exec_app_interruptable, PersistentEditorTableView
from table_example import CustomTableModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Parameter selector styling example")
        self._current_value = ""

        widget = ParameterLineEdit(self)
        widget.valueChanged.connect(self._on_value_changed)
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self._edit = widget

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)
        layout.addWidget(widget)
        button = QPushButton("Open dialog")
        button.clicked.connect(self._open_dialog)
        layout.addWidget(button)
        layout.addStretch()
        line = QFrame()
        line.setFrameStyle(QFrame.HLine)
        layout.addWidget(line)
        layout.addStretch()
        table = PersistentEditorTableView()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.set_persistent_editor_for_column(0)
        table.setItemDelegateForColumn(0, ParameterLineEditColumnDelegate(table))
        model = CustomTableModel(self)
        table.setModel(model)
        layout.addWidget(table)

        self.resize(600, 220)

    def _on_value_changed(self, new_val: str):
        self._current_value = new_val
        print(f"New parameter name: {new_val}")

        # Propagate value to self._edit, so that it becomes visible in lined edit, but prevent any side effects
        blocker = QSignalBlocker(self._edit)
        self._edit.value = new_val
        blocker.unblock()

    def _open_dialog(self):
        dialog = ParameterSelectorDialog(initial_value=self._current_value,
                                         enable_protocols=False,
                                         parent=self)
        if dialog.exec_() == ParameterSelectorDialog.Accepted:
            self._on_value_changed(dialog.value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    style = Path(__file__).parent.parent / "_common" / "dark.qss"
    dark_mode = style.read_text()
    app.setStyleSheet(dark_mode)
    window.show()
    sys.exit(exec_app_interruptable(app))
