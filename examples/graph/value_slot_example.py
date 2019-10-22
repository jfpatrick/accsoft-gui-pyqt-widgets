"""
Simple example for the usage of the ExtendPlotWidget
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from qtpy.QtCore import QTimer, QObject, Signal

import accsoft_gui_pyqt_widgets.graph as accgraph
import random


class MainWindow(QMainWindow):
    """Example for usage of the singleCurveValueSlot"""

    def __init__(self, *args, **kwargs):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__(*args, **kwargs)
        self.plot = accgraph.ExPlotWidget()
        self.emitting_thingy = DataSource()
        self.emitting_thingy.single_curve_value_signal[float].connect(self.plot.addDataToSingleCurve)
        self.emitting_thingy.single_curve_value_signal[int].connect(self.plot.addDataToSingleCurve)
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


class DataSource(QObject):
    """Some thing that emits a signal with a single float"""

    single_curve_value_signal = Signal([float], [int])

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.emit)
        self.timer.start(1000)

    def emit(self):
        """Emit new float value"""
        self.single_curve_value_signal[float].emit(random.uniform(0.0, 10.0))
        self.single_curve_value_signal[int].emit(int(random.uniform(0.0, 10.0)))


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
