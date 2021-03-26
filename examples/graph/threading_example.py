"""
Example with a plot that receives data updates from a separate thread. Plot and update source are created in the main
GUI thread. The new data on the other hand is sent in an extra thread.

ATTENTION: You do not NEED a multi-threaded application necessarily. This example is simply for demonstrating
the ability to properly display data produced in another thread. This is ensured by curve and UpdateSource
communicating over Qt signals, which can transmit data across threads.

An example use-case for multi-threaded scenario could be JAPC callbacks that are executed in a separate thread
from Java thread pool.
"""

import threading
import sys
from qtpy.QtCore import QThread
from qtpy.QtWidgets import QMainWindow, QApplication
from accwidgets.graph import ScrollingPlotWidget, TimeSpan
from accwidgets.qt import exec_app_interruptable
from example_sources import SinusCurveSource


class BackgroundSinusCurveSource(SinusCurveSource):

    UPDATE_FREQ = 60

    def __init__(self, *args, **kwargs):
        kwargs["auto_start"] = False
        kwargs["updates_per_second"] = self.UPDATE_FREQ
        super().__init__(*args, **kwargs)

    def send_data(self, *args, **kwargs):
        print(f"BackgroundSinusCurveSource.send_data: {threading.currentThread().getName()}")
        super().send_data(*args, **kwargs)

    def start(self):
        print(f"BackgroundSinusCurveSource.start: {threading.currentThread().getName()}")
        self.timer.start(1000 / self.UPDATE_FREQ)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Graph multi-threading example")
        print(f"Creating BackgroundSinusCurveSource in {threading.currentThread().getName()}")
        self.bkg_thread = QThread()
        self.src = BackgroundSinusCurveSource(y_offset=0, x_offset=0.0)
        self.src.moveToThread(self.bkg_thread)
        self.bkg_thread.started.connect(self.src.start)

        self.plot = ScrollingPlotWidget(parent=self, time_span=TimeSpan(left=10.0))
        self.plot.addCurve(data_source=self.src)

        self.setCentralWidget(self.plot)
        self.resize(800, 600)

    def start_threads(self):
        self.bkg_thread.start()

    def stop_threads(self):
        self.bkg_thread.quit()
        self.bkg_thread.wait()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.start_threads()
    ret = exec_app_interruptable(app)
    window.stop_threads()
    sys.exit(ret)
