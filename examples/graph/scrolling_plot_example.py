"""
Example application of a plot displaying two curves displaying
continuously emitted data. As soon as new data arrives, the new
point will be inserted into the curve. As time progresses, the
plot will scroll to show new data on the right side while moving
older data outside of the view on the left side.

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

    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a source for timing update to control the time span shown by the plot
        timing_source = example_sources.LocalTimerTimingSource()
        # Create 2 sources for our curves that will continuously emit new points that
        # are then displayed by our curve when they arrive
        data_source_1 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=0, updates_per_second=60
        )
        data_source_2 = example_sources.SinusCurveSource(
            x_offset=-1.0, y_offset=3, updates_per_second=60
        )
        # We want the plot to display a scrolling 10 second time span at all times
        # Let's create our plot fitting to these requirements with the separate source
        # for timing updates attached
        self.plot = accgraph.ScrollingPlotWidget(
            timing_source=timing_source,
            time_span=10.0,
            time_progress_line=True,
            is_xrange_fixed=True,
        )
        # Now we can add 2 curves in different colors that are displaying the
        # data coming from out source.
        self.plot.addCurve(data_source=data_source_1, pen="r")
        self.plot.addCurve(data_source=data_source_2, pen="y")
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
