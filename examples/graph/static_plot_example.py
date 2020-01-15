"""
Example application of a plot displaying two curves displaying
continuously changing data. The two displayed sinus curves are
being scaled in y direction. As a new sinus curve is emitted,
it is replacing the old one.
"""


import sys

from qtpy.QtWidgets import QApplication, QMainWindow

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        curve_ds = example_sources.WaveformSinusSource(
            curve_length=100,
            type=example_sources.SinusCurveSourceEmitTypes.POINT)
        bars_ds = example_sources.WaveformSinusSource(
            curve_length=11,
            y_offset=1.0,
            type=example_sources.SinusCurveSourceEmitTypes.BAR)
        injection_ds = example_sources.WaveformSinusSource(
            curve_length=11,
            y_offset=2.0,
            type=example_sources.SinusCurveSourceEmitTypes.INJECTIONBAR)
        marker_ds = example_sources.WaveformSinusSource(
            x_start=2,
            x_stop=5,
            curve_length=3,
            y_offset=2.0,
            type=example_sources.SinusCurveSourceEmitTypes.INFINITELINE)
        self.plot = accgraph.StaticPlotWidget()
        self.plot.addCurve(data_source=curve_ds, pen="r")
        self.plot.addBarGraph(data_source=bars_ds, width=0.5)
        self.plot.addInjectionBar(data_source=injection_ds, beam=0.05, pen="b")
        self.plot.addTimestampMarker(data_source=marker_ds)
        self.plot.setRange(yRange=[-1, 3])
        self.show()
        self.resize(800, 600)
        self.setCentralWidget(self.plot)


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
