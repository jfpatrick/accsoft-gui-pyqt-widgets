from typing import Optional
from pathlib import Path
from qtpy.QtWidgets import QDialog, QLineEdit, QCheckBox, QPushButton, QWidget, QLabel
from qtpy.QtCore import Signal
from qtpy.QtGui import QTextDocument
from qtpy.uic import loadUi


class LogSearchDialog(QDialog):

    search_requested = Signal(str, QTextDocument.FindFlag)
    search_direction_changed = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.search_btn: QPushButton = None
        self.search_edit: QLineEdit = None
        self.check_wrap: QCheckBox = None
        self.check_reverse: QCheckBox = None
        self.check_case: QCheckBox = None
        self.warn_label: QLabel = None

        loadUi(Path(__file__).parent / "search.ui", self)

        self.search_btn.clicked.connect(self._on_search)
        self.check_reverse.stateChanged.connect(self._on_search_direction_change)
        self.on_search_result(True)

    def on_search_result(self, found: bool):
        # Do not hide label, but rather remove text, to preserve the height of the label,
        # so that the window size does not jump between button presses
        self.warn_label.setText("" if found else "No results were found!")

    def _on_search(self):
        flags = QTextDocument.FindFlag()
        if self.check_case.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.check_wrap.isChecked():
            flags |= QTextDocument.FindWholeWords
        if self.check_reverse.isChecked():
            flags |= QTextDocument.FindBackward
        self.search_requested.emit(self.search_edit.text(), flags)

    def _on_search_direction_change(self):
        self.search_direction_changed.emit(self.check_reverse.isChecked())
