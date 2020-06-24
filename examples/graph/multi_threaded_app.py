"""Example with a plot that receives data updates from a separate thread.
Plot and update source are created in the main GUI Thread. The new data
on the other hand is sent in an extra thread.

ATTENTION: You do not NEED a Multi-Threaded Application necessarily.
This example is simply for demonstrating, that it is no problem, if new
data is set to the plot in another Tread, since Curve and Update Source
communicate through signals and slots. One example for such a scenario
is JAPC callbacks which are executed in a separate Thread.
"""

import threading
import time
import sys
import numpy as np
from qtpy.QtWidgets import QMainWindow, QApplication
import accwidgets.graph as accgraph

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class ThreadSource(accgraph.UpdateSource):

    def __init__(self):
        """All data emitted by the update source will be sent from a
        different Thread."""
        print(f"ThreadSource.__init__        called in {threading.currentThread().getName()}")
        super().__init__()
        self.x = threading.Thread(target=self.update_callback)
        self.x.start()
        self._stop = False

    def update_callback(self):
        """
        Update the curve by sending new data to it. This function is run in
        the separate thread created in __init__, not in the GUI Thread that
        called __init__.
        """
        print(f"ThreadSource.update_callback called in {threading.currentThread().getName()}")
        while True:
            self.send_data(accgraph.CurveData(np.arange(0, 10),
                                              np.random.randint(0, 10, 10)))
            time.sleep(1)
            if self._stop:
                break

    def stop_thread(self):
        """Stop the infinite loop running in our separate thread."""
        self._stop = True


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        print(f"MainWindow.__init__          called in {threading.currentThread().getName()}")
        super().__init__(*args, **kwargs)
        self.src = ThreadSource()
        self.plot = accgraph.StaticPlotWidget()
        self.plot.addCurve(data_source=self.src)
        self.show()
        self.resize(800, 600)
        self.setCentralWidget(self.plot)

    def closeEvent(self, a0) -> None:
        """
        When we close the window, we want to stop the infinite loop
        running in our separate thread to cleanly quit the app.
        """
        self.src.stop_thread()


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
