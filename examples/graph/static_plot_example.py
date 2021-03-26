"""
Example application of a plot displaying two curves displaying continuously changing data. The two displayed
sin curves are being scaled in Y direction. As a new sinus curve is emitted, it is replacing the old one.
StaticPlotWidget, in contrast with other plot widget types, replaces the entire contents of the graph with the new
data every time. Hence, it is perfect for displaying waveforms.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow
from accwidgets.graph import StaticPlotWidget
from accwidgets.qt import exec_app_interruptable
from example_sources import WaveformSinusSource, SinusCurveSourceEmitTypes


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Static plot example")
        self.plot = StaticPlotWidget()
        self.plot.addCurve(pen="r",
                           data_source=WaveformSinusSource(curve_length=100,
                                                           type=SinusCurveSourceEmitTypes.POINT))
        self.plot.addBarGraph(width=0.5,
                              data_source=WaveformSinusSource(curve_length=11,
                                                              y_offset=1.0,
                                                              type=SinusCurveSourceEmitTypes.BAR))
        self.plot.addInjectionBar(beam=0.05,
                                  pen="b",
                                  data_source=WaveformSinusSource(curve_length=11,
                                                                  y_offset=2.0,
                                                                  type=SinusCurveSourceEmitTypes.INJECTION_BAR))
        self.plot.addTimestampMarker(data_source=WaveformSinusSource(x_start=2,
                                                                     x_stop=5,
                                                                     curve_length=3,
                                                                     y_offset=2.0,
                                                                     type=SinusCurveSourceEmitTypes.INFINITE_LINE))
        self.plot.setRange(yRange=[-1, 3])
        self.setCentralWidget(self.plot)
        self.resize(800, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
