"""
Example of a window displaying two cyclic plot curves placed against two independent Y-axes. A cyclic plot
curve overwrites itself when the visible time span fills up. The Y-axes are part of "layer" concept that
is composed of a view box (containing the curve) and the corresponding Y-axis. In this example, both left
and right Y-axes can be panned or zoomed individually to influence the related curves. When panning or dragging
on main plot canvas, the action is synchronized across all Y-axes. This plot is attached to an extra source
for timing updates which controls the time span of data shown by the plot.
"""

import sys
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import CyclicPlotWidget, TimeSpan
from accwidgets.qt import exec_app_interruptable
from example_sources import SinusCurveSource, LocalTimerTimingSource


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Multiple Y-axes CyclicPlotWidget example")
        timing_source = LocalTimerTimingSource()
        # Create a sliding plot that shows 10 seconds of data, the current time should
        # be represented as a vertical line with time stamp
        self.plot = CyclicPlotWidget(timing_source=timing_source,
                                     time_span=TimeSpan(left=10.0),
                                     time_progress_line=True)
        # Add a layer with y-axis on which our second curve should be plotted
        self.plot.add_layer(layer_id="layer_0")
        # Plot a curve against the plot's standard y axis on the left side
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=0.0, y_offset=3), pen="y")
        # Plot a curve against our new layer's y-axis by passing its identifier
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=0.0, y_offset=0), layer="layer_0", pen="r")

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
