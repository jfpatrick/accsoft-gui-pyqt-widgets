"""
Example for an system that not only emits single live points but also
saved points that will be emitted later. Even though the points are not
emitted in the order of their timestamps, they are still displayed in the
right position.
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):

    """
    Main Window that contains one plot with one curve which is attached
    to a source that emits live data as well as logged data to a later
    time. The logged data will arrive after the live data with a newer
    timestamp but placed right according to each points timestamp and not
    by their time of arrival.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is some example implementation of the UpdateSource
        # that we receive our data from
        data_source = example_sources.LoggingCurveDataSource(
            updates_per_second=60
        )
        # Create a scrolling plot that shows 25 seconds of data
        self.plot = accgraph.ScrollingPlotWidget(
            time_span=25.0,
            time_progress_line=False,
            is_xrange_fixed=True,
            fixed_xrange_offset=0.0
        )
        # Add a blue curve with a thickness of 2 to our plot
        # Data for the curve is received by the passed data source
        self.plot.addCurve(
            data_source=data_source,
            pen={"color": "b", "width": 2}
        )
        self.plot.setYRange(-1, 1)
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


def run() -> None:
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
