from typing import Optional
from datetime import datetime
from pathlib import Path
from qtpy.QtWidgets import QDialog, QWidget, QLabel
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.uic import loadUi


class AboutDialog(QDialog):

    def __init__(self, app_name: str, version: str, icon: QIcon, parent: Optional[QWidget] = None):
        super().__init__(parent, (Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint))

        self.icon: QLabel = None
        self.contents: QLabel = None

        loadUi(Path(__file__).parent / "about.ui", self)

        self.setWindowIcon(icon)
        self.icon.setPixmap(icon.pixmap(self.icon.maximumSize()))

        self.contents.setText(self.contents.text().format(YEAR=datetime.now().year,
                                                          APP=app_name,
                                                          VERSION=version))
