"""
This example shows how LogConsole works when logging messages from multiple threads. Python's logging module
is thread-safe and there is no specific logic that is needed to handle multi-threading. For the sake of example,
logs are emitted automatically using timers.
"""

import sys
import logging
from threading import current_thread
from qtpy.QtCore import QTimer, QThread
from qtpy.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget
from accwidgets.log_console import LogConsoleModel, LogConsole
from accwidgets.qt import exec_app_interruptable
from utils import GibberishGenerator


class MessageEmitter(QThread, GibberishGenerator):

    def __init__(self, name: str):
        QThread.__init__(self)
        GibberishGenerator.__init__(self)
        self.name = name
        self._timer = None

    def start(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.trigger_log)
        self._timer.start(FIRE_INTERVAL)

    def trigger_log(self):
        message = f'Broadcasting from thread "{current_thread().name}" - {self.generate_phrase()}'
        logging.getLogger(self.name).warning(message)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LogConsole threading example")
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)

        self.main_emitter = MessageEmitter(name="main_thread")
        self.main_emitter.start()
        self.bkg_emitters = []
        self.bkg_threads = []
        for i in range(NUM_THREADS):
            emitter = MessageEmitter(name=f"bkg_thread_{i+1}")
            thread = QThread()
            thread.setObjectName(f"bkg_QThread_{i+1}")
            emitter.moveToThread(thread)
            thread.started.connect(emitter.start)
            self.bkg_emitters.append(emitter)
            self.bkg_threads.append(thread)
            QTimer.singleShot((float(i + 1) / float(NUM_THREADS + 1)) * FIRE_INTERVAL, thread.start)

        model = LogConsoleModel(loggers=[logging.getLogger(self.main_emitter.name)] + [logging.getLogger(log.name) for log in self.bkg_emitters], buffer_size=30)
        layout.addWidget(LogConsole(model=model))
        self.resize(660, 523)

    def stop_threads(self):
        for thread in self.bkg_threads:
            thread.quit()
            thread.wait()


FIRE_INTERVAL = 200
NUM_THREADS = 10


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    ret = exec_app_interruptable(app)
    window.stop_threads()
    sys.exit(ret)
