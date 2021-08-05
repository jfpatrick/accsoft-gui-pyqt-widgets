"""
This example shows the way of using ParameterLineEditColumnDelegate inside a table view. Example model is configured
to contain 2 columns: the left one will accommodate ParameterLineEdit widgets, while on the right the read-only
value is displayed, corresponding to the ParameterLineEdit of the same row. "Enable protocols" checkbox allows
configuring additional protocol UI in the dialogs, just as displayed in protocol_example.py.
"""

import sys
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QHeaderView, QCheckBox, QWidget, QVBoxLayout
from accwidgets.parameter_selector import ParameterLineEditColumnDelegate
from accwidgets.qt import exec_app_interruptable, PersistentEditorTableView, AbstractTableModel


class CustomTableModel(AbstractTableModel):

    def __init__(self, parent):
        super().__init__(data=["device1/property1#field1", "device2/property2"], parent=parent)

    def columnCount(self, *_):
        return 2

    def column_name(self, section):
        if section == 0:
            return "Column selector"
        else:
            return "Selected value"

    def get_cell_data(self, index, row):
        return row

    def set_cell_data(self, index, row, value):
        self._data[index.row()] = value

    def flags(self, index):
        if index.column() == 1:
            return Qt.ItemNeverHasChildren
        return super().flags(index)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ParameterLineEditColumnDelegate table example")

        widget = QWidget()
        layout = QVBoxLayout()

        table = PersistentEditorTableView()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.set_persistent_editor_for_column(0)
        table.setItemDelegateForColumn(0, ParameterLineEditColumnDelegate(self))
        model = CustomTableModel(self)
        table.setModel(model)
        self._table = table

        layout.addWidget(table)
        layout.addStretch()

        checkbox = QCheckBox("Allow protocol selection")
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        checkbox.setChecked(False)
        layout.addWidget(checkbox)
        widget.setLayout(layout)

        self.setCentralWidget(widget)
        self.resize(600, 200)

    def _on_checkbox_changed(self, state: Qt.CheckState):
        enable_protocols = state == Qt.Checked
        self._table.setItemDelegateForColumn(0, ParameterLineEditColumnDelegate(parent=self,
                                                                                enable_protocols=enable_protocols))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
