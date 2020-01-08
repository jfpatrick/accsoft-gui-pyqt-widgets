"""
Example of one plot with a simple standard curve with
the standard plot configuration.
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__(*args, **kwargs)
        # One source of data for our curve
        data_source_1 = example_sources.SinusCurveSource(x_offset=0.0, y_offset=0, updates_per_second=5)
        # Our plot we want to add our curve to
        self.plot = accgraph.ScrollingPlotWidget(
            parent=self,
            time_span=accgraph.TimeSpan(10.0),
        )
        # A curve receiving its data from the prior defined
        # data source.
        self.plot.addCurve(data_source=data_source_1)
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
