"""
Example that uses a ScrollingPlotWidget in the standard configuration with the simulated sinus
curve data.
"""

import sys
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import ScrollingPlotWidget, TimeSpan
from accwidgets.qt import exec_app_interruptable
from example_sources import SinusCurveSource


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Simple ScrollingPlotWidget example")
        # Plot will display 10 seconds of data
        self.plot = ScrollingPlotWidget(parent=self, time_span=TimeSpan(left=10.0))
        # A curve receiving its data from the prior defined data source.
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=0.0, y_offset=0, updates_per_second=5))

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.resize(800, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
