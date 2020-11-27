"""
Example application of a plot displaying two curves displaying continuously emitted data. As soon as new data
arrives, the new point will be inserted into the curve. As time progresses, the plot scrolls to show new data on
the right side, while moving older data outside of the view on the left side.

Additionally, the plot is attached to an extra source for timing updates, which controls the time span of data
shown by the plot. If a point with a time span newer than the current time provided by the timing source is emitted,
it won't be visible until it is revealed as soon as the timing source progresses.
"""

import sys
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import ScrollingPlotWidget, TimeSpan
from example_sources import LocalTimerTimingSource, SinusCurveSource

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Scrolling plot example")
        timing_source = LocalTimerTimingSource()
        # We want the plot to display a scrolling 10 second time span at all times
        self.plot = ScrollingPlotWidget(timing_source=timing_source,
                                        time_span=TimeSpan(left=10.0, right=0.0),
                                        time_progress_line=True)
        # Now we can add 2 curves in different colors that are displaying the data coming from out source.
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=0.0, y_offset=0, updates_per_second=60), pen="r")
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=-1.0, y_offset=3, updates_per_second=60), pen="y")

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
    sys.exit(app.exec_())
