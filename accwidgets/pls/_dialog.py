from typing import Optional
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QWidget, QDialogButtonBox, QVBoxLayout, QFrame
from ._model import PlsSelectorModel
from ._common import PlsSelectorWrapper


class PlsSelectorDialog(QDialog, PlsSelectorWrapper):

    def __init__(self, parent: Optional[QWidget] = None, model: Optional[PlsSelectorModel] = None):
        """
        Dialog that embeds :class:`~accwidgets.cycle_selector.CycleSelector` widget in a window with
        "Ok" and "Cancel" buttons.

        Args:
            parent: Owning widget.
            model: The model to be passed into the :class:`~accwidgets.cycle_selector.CycleSelector` initializer.
        """
        QDialog.__init__(self, parent, (Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint))
        PlsSelectorWrapper.__init__(self, model=model)
        self.setWindowTitle("Select PLS value…")
        layout = QVBoxLayout()
        layout.addWidget(self._pls)
        sep = QFrame()
        sep.setFrameStyle(QFrame.HLine)
        layout.addWidget(sep)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setMaximumHeight(126)
