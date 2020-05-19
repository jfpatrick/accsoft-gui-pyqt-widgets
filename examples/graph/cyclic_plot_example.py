"""
Example application of a plot displaying two curves displaying
continuously emitted data. Instead of the plot moving as new data
arrives, the curves will start to overdraw themselves from the
beginning as soon as the drawing of the curve reaches the right
border of the plot.

Additionally the plot is attached to an extra source for timing
updates which controls the time span of data shown by the plot.
If points with a time span newer than the current time provided
by the timing source is emitted, it won't be visible until it is
revealed as soon as the timing source progresses.
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Create a source for timing update to control the time span shown by the plot
        timing_source = example_sources.LocalTimerTimingSource()
        # Create 2 sources for our curves that will continuously emit new points that
        data_source_1 = example_sources.SinusCurveSource(x_offset=0.0, y_offset=0)
        data_source_2 = example_sources.SinusCurveSource(x_offset=-1.0, y_offset=3)
        # We want the plot to display a 10 second time span at all times, but instead
        # of scrolling in a sliding pointer way. Additionally we attach it to our created
        # source for timing updates
        self.plot = accgraph.CyclicPlotWidget(
            timing_source=timing_source,
            time_span=accgraph.TimeSpan(left=10.0, right=0.0),
            time_progress_line=True,
        )
        # Add 2 curves attached to our sources for data updates, each displayed
        # in a different color.
        self.plot.addCurve(data_source=data_source_1, pen="r")
        self.plot.addCurve(data_source=data_source_2, pen="g")
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


def run():
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
