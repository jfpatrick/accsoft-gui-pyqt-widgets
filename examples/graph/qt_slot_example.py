"""
This example features a plot with a single curve. Instead of the curve being created from an update source,
data is directly pushed into the plot widget's slot. This slot in turn takes care of curve creation. This slot is a
useful shortcut, when plot widget needs to be directly connected in Qt Designer, and there's no necessarily room
for custom code that instantiates update source objects.
"""

import sys
import random
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from qtpy.QtCore import QTimer, QObject, Signal
from qtpy.QtGui import QColor
from accwidgets.graph import ScrollingPlotWidget, TimeSpan, SymbolOptions
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Graph example of data propagation via Qt Slot")
        self.plot = ScrollingPlotWidget(time_span=TimeSpan(left=10.0))
        # Create an object that emits value through a signal
        self.object_with_signal = ObjectWithSignal()
        # Connect the signal of the object to the value slot in the plot
        # Both float and integers are accepted by the slot
        self.plot.pushDataItemPenColor = QColor(255, 0, 0)
        self.plot.pushDataItemBrushColor = QColor(0, 255, 0)
        self.plot.pushDataItemPenWidth = 2
        self.plot.pushDataItemSymbol = SymbolOptions.Circle
        self.object_with_signal.new_point_available[float].connect(self.plot.pushData)
        self.object_with_signal.new_point_available[int].connect(self.plot.pushData)

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.resize(800, 600)


class ObjectWithSignal(QObject):

    new_point_available = Signal([float], [int])

    def __init__(self):
        """Some object that emits a signal with a single float or int."""
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.emit)
        self.timer.start(1000)

    def emit(self):
        """Emit new integer and float value through the signal"""
        self.new_point_available[float].emit(random.uniform(0.0, 10.0))
        self.new_point_available[int].emit(int(random.uniform(0.0, 10.0)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
