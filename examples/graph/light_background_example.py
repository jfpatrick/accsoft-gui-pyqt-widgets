"""
This example shows the way to create plots with a light background color and dark axes,
all of which fits the default Qt window look.
"""

import sys
import pyqtgraph as pg
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from qtpy.QtGui import QPalette
from accwidgets.graph import StaticPlotWidget
from accwidgets.qt import exec_app_interruptable
from example_sources import WaveformSinusSource, SinusCurveSourceEmitTypes


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Light background color graph example")

        # We want to use the colors fitting to the window colors, per default
        # these are dark items on a light background. Depending how the window
        # is styled, this could be different.
        pg.setConfigOption("background", QPalette().color(QPalette.Window))
        pg.setConfigOption("foreground", QPalette().color(QPalette.Text))

        source = WaveformSinusSource(curve_length=100,
                                     type=SinusCurveSourceEmitTypes.POINT)
        self.plot = StaticPlotWidget()

        # The curve will be colored in red
        self.plot.addCurve(data_source=source, pen=pg.mkPen(color="r", width=2))

        self.plot.setRange(yRange=[-1, 1])

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
