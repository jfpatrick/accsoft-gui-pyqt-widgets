"""
Example application of a plot displaying two cyclic plot
curves plotted against two independent y axes. A cyclic plot
curve displays data similar to a heart rate monitor by overdrawing
itself when new data arrives. The y axes are part of a so called
'layer' that is composed from an view box, the are the curve is
drawn in, and an to its view range attached y-axis. Both y-axes
can be moved individually to set each's axis range by dragging
the axis with the mouse, as well as together, to move all layers
around at the same pace, when dragged in the drawing area of the
plot in the center.

Additionally the plot is attached to an extra source for timing
updates which controls the time span of data shown by the plot.
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
        # Create a source for timing update to control the time span shown by the plot
        timing_source = example_sources.LocalTimerTimingSource()
        # Create two source for data updates for our sliding pointer curves
        data_source_1 = example_sources.SinusCurveSource(x_offset=0.0, y_offset=0)
        data_source_2 = example_sources.SinusCurveSource(x_offset=0.0, y_offset=3)
        # Create a sliding plot that shows 10 seconds of data, the current time should
        # be represented as a vertical line with time stamp
        self.plot = accgraph.CyclicPlotWidget(
            timing_source=timing_source,
            time_span=accgraph.TimeSpan(10.0),
            time_progress_line=True,
        )
        # Add a layer with y-axis on which our second curve should be plotted
        self.plot.add_layer(layer_id="layer_0")
        # Plot a curve against the plot's standard y axis on the left side
        self.plot.addCurve(data_source=data_source_2, pen="y")
        # Plot a curve against our new layer's y-axis by passing its identifier
        self.plot.addCurve(
            data_source=data_source_1, layer="layer_0", pen="r"
        )
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
