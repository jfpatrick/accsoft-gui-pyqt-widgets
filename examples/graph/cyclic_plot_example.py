"""
Example application of a plot displaying two curves of continuously emitted data. Instead of the plot continuously
moving as new data arrives, the curves will start to redraw themselves from the beginning as soon as the curve
reaches the right border of the plot. Additionally, the plot is attached to an extra source for timing updates that
controls the time span of data shown by the plot. If points with a timestamp more recent than the configured time
span are emitted, it won't be visible until it is revealed as soon as the timing source progresses.
"""

import sys
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import CyclicPlotWidget, TimeSpan
from accwidgets.qt import exec_app_interruptable
from example_sources import LocalTimerTimingSource, SinusCurveSource


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyclic plot example")
        timing_source = LocalTimerTimingSource()
        # We want the plot to display a 10 second time span at all times
        time_span = TimeSpan(left=10.0, right=0.0)
        self.plot = CyclicPlotWidget(timing_source=timing_source,
                                     time_span=time_span,
                                     time_progress_line=True)
        # Add 2 curves attached to our sources for data updates, each represented by its own color
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=0.0, y_offset=0), pen="r")
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=-1.0, y_offset=3), pen="g")
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
