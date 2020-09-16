from typing import Optional
from qtpy.QtWidgets import QWidget, QToolButton, QMenu, QSizePolicy, QHBoxLayout, QAction


class RbaToolbarWidget(QWidget):

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Set of buttons that assist with authentication & authorization via RBAC.

        Args:
            parent: Parent widget to hold this object.
        """
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self._user_btn = RbaUserButton(self)
        layout.addWidget(self._user_btn)


class RbaUserButton(QToolButton):

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Button that is embedded into the toolbar to open the dialog.

        Args:
            parent: Parent widget to hold this object.
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setAutoRaise(True)
        menu = QMenu(self)
        self.setMenu(menu)
        self.setText("rbaguest")
        act_roles = QAction("Select Roles", self)
        menu.addAction(act_roles)
        menu.addSeparator()
        act_token = QAction("Show Existing RBAC Token", self)
        menu.addAction(act_token)
