from typing import Optional
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QWidget, QDialogButtonBox, QVBoxLayout, QFrame
from ._model import CycleSelectorModel
from ._common import CycleSelectorWrapper


class CycleSelectorDialog(QDialog, CycleSelectorWrapper):

    def __init__(self, parent: Optional[QWidget] = None, model: Optional[CycleSelectorModel] = None):
        """
        Dialog that embeds :class:`~accwidgets.cycle_selector.CycleSelector` widget in a window with
        "Ok" and "Cancel" buttons.

        Args:
            parent: Owning widget.
            model: The model to be passed into the :class:`~accwidgets.cycle_selector.CycleSelector` initializer.
        """
        QDialog.__init__(self, parent, (Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint))
        CycleSelectorWrapper.__init__(self, model=model)
        self.setWindowTitle("Choose cycle selector…")
        layout = QVBoxLayout()
        layout.addWidget(self._sel)
        sep = QFrame()
        sep.setFrameStyle(QFrame.HLine)
        layout.addWidget(sep)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setMaximumHeight(126)
