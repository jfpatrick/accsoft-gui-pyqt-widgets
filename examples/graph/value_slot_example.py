"""
Example application of a plot displaying a single curve.
Instead of the curve being created from an update source, data
is directly passed through a slot of the plot that creates a
curve for the user and displays the data passed through the slot in it.
This is the shortest, but also least flexible way of displaying
data on in a plot.
"""

import sys
import random

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from qtpy.QtCore import QTimer, QObject, Signal

from accwidgets import graph as accgraph


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a standard scrolling plot
        self.plot = accgraph.ScrollingPlotWidget(time_span=accgraph.TimeSpan(10.0))
        # Create an object that emits value through a signal
        self.object_with_signal = ObjectWithSignal()
        # Connect the signal of the object to the value slot in the plot
        # Both float and integers are accepted by the slot
        self.object_with_signal.new_point_available[float].connect(self.plot.addDataToSingleCurve)
        self.object_with_signal.new_point_available[int].connect(self.plot.addDataToSingleCurve)
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


class ObjectWithSignal(QObject):
    """Some object that emits a signal with a single float or int"""

    new_point_available = Signal([float], [int])

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.emit)
        self.timer.start(1000)

    def emit(self):
        """Emit new integer and float value through the signal"""
        self.new_point_available[float].emit(random.uniform(0.0, 10.0))
        self.new_point_available[int].emit(int(random.uniform(0.0, 10.0)))


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
