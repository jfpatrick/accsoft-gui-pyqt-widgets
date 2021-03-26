"""
This example shows how to use a custom model implementation by subclassing the AbstractLogConsoleModel. This
example implementation does not benefit from Python loggers at all, and rather generates log events based on
the simulated timer.
"""

import random
import sys
from datetime import datetime
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget
from accwidgets.log_console import AbstractLogConsoleModel, LogLevel, LogConsoleRecord, LogConsole
from accwidgets.qt import exec_app_interruptable
from utils import GibberishGenerator


class MyConsoleModel(AbstractLogConsoleModel, GibberishGenerator):

    def __init__(self):
        AbstractLogConsoleModel.__init__(self)
        GibberishGenerator.__init__(self)
        self._storage = []
        self._frozen: bool = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._emit_record)
        self._timer.start(1000)
        self._buffer_size = 5

    def _emit_record(self):
        if self._frozen:
            return
        levels = list(LogLevel.real_levels())
        random_index = random.randint(0, len(levels) - 1)
        random_level = levels[random_index]
        new_record = LogConsoleRecord(logger_name="MAIN",
                                      message=self.generate_phrase(),
                                      level=random_level,
                                      timestamp=datetime.now().timestamp())
        self._storage.append(new_record)
        if len(self._storage) > self.buffer_size:
            pop_first = True
            self._storage = self._storage[1:]
        else:
            pop_first = False

        self.new_log_record_received.emit(new_record, pop_first)

    @property
    def all_records(self):
        return iter(self._storage)

    def clear(self):
        self._storage.clear()

    @property
    def buffer_size(self):
        return self._buffer_size

    @buffer_size.setter
    def buffer_size(self, new_size):
        self._buffer_size = new_size
        if len(self._storage) > new_size:
            self._storage = self._storage[-new_size:new_size]

    def freeze(self):
        self._frozen = True
        self.freeze_changed.emit(self._frozen)

    def unfreeze(self):
        self._frozen = False
        self.freeze_changed.emit(self._frozen)

    @property
    def frozen(self):
        return self._frozen

    @property
    def selected_logger_levels(self):
        return {"MAIN": LogLevel.DEBUG}

    @selected_logger_levels.setter
    def selected_logger_levels(self, _):
        pass

    @property
    def visible_levels(self):
        return set(LogLevel.real_levels())

    @visible_levels.setter  # type: ignore
    def visible_levels(self, _):
        pass


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LogConsole custom model example")
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)
        model = MyConsoleModel()
        layout.addWidget(LogConsole(model=model))
        self.resize(360, 223)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
