"""
This example shows the recommended way to create plots in a light theme
with dark axes and a light background which fits to the window
"""


import sys

from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from qtpy.QtGui import QPalette

import pyqtgraph as pg
from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We want to use the colors fitting to the window colors, per default
        # these are dark items on a light background. Depending how the window
        # is styled, this could be different.
        pg.setConfigOption("background", QPalette().color(QPalette.Window))
        pg.setConfigOption("foreground", QPalette().color(QPalette.Text))

        source = example_sources.WaveformSinusSource(
            curve_length=100,
            type=example_sources.SinusCurveSourceEmitTypes.POINT)
        self.plot = accgraph.StaticPlotWidget()

        # The curve will be colored in red
        self.plot.addCurve(data_source=source, pen=pg.mkPen(color="r", width=2))

        self.plot.setRange(yRange=[-1, 1])
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
