import random
from logging import Logger, getLogger
from typing import Optional
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton, QGroupBox, QSizePolicy
from accwidgets.log_console import LogLevel


class GibberishGenerator:

    words = ["study", "the", "past", "if", "you", "would", "define", "future"]

    def generate_phrase(self) -> str:
        random.shuffle(self.words)
        message = " ".join(self.words)
        return message


class LogConsoleExampleButtons(QGroupBox, GibberishGenerator):

    levels = [LogLevel.level_name(lvl) for lvl in LogLevel.real_levels()]

    def __init__(self, logger: Optional[Logger] = None, parent: Optional[QWidget] = None):
        QGroupBox.__init__(self, parent)
        GibberishGenerator.__init__(self)
        self.logger = logger or getLogger()
        self.setTitle(f"Logger = {self.logger.name}")
        layout = QHBoxLayout()
        layout.setContentsMargins(9, 0, 9, 0)
        for lvl in self.levels:
            btn = QPushButton(lvl)
            btn.clicked.connect(self.generate_msg)
            btn.setMinimumWidth(60)
            layout.addWidget(btn)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

    def generate_msg(self):
        btn: QPushButton = self.sender()
        level = LogLevel[btn.text()]
        self.logger.log(level=level.value, msg=self.generate_phrase())
